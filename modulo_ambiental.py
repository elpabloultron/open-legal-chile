"""Open Legal Chile — Módulo especial de derecho ambiental.

Consulta unificada del corpus ambiental completo del producto:

  · jurisprudencia de los Tribunales Ambientales (1TA, 2TA, 3TA) — registro de 886 sentencias;
  · publicaciones oficiales: anuarios y boletines 2TA/3TA (78 documentos);
  · biblioteca ambiental: libros del concurso de comentarios, informes en derecho, foros,
    manuales y material docente (biblioteca_ambiental/);
  · doctrina ambiental del repositorio (doctrina/ambiental/).

`es_materia_ambiental` decide si la consulta o el caso amerita el módulo; `consulta_ambiental`
entrega el plan, los resultados con el texto literal y las citas con el corchete oficial
[Hugging Face - <archivo>], más el subgrafo de LegalGraphify y su ahorro de tokens cuando el
motor está disponible.
"""

from __future__ import annotations

import json
import pathlib
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

BASE = pathlib.Path(__file__).resolve().parent
HF_BASE = "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main"

# Materias que hacen «ambiental» una consulta (en minúsculas y sin acentos: se comparan normalizadas).
MATERIAS = (
    "ambiental", "medio ambiente", "medioambiental", "medioambientales",
    "seia", "rca", "eia", "sma", "snifa", "superintendencia del medio ambiente",
    "dano ambiental", "tribunal ambiental", "tribunales ambientales",
    "humedal", "humedales", "biodiversidad", "areas protegidas",
    "evaluacion ambiental", "sancion ambiental", "programa de cumplimiento",
    "servicio de evaluacion ambiental", "ministerio del medio ambiente",
    "contaminacion", "residuos", "cambio climatico", "lo-sma", "lo sma",
    "19.300", "20.417", "20.600", "21.202", "21.455",
)

INDICES = (
    ("publicaciones_ambientales", BASE / "data" / "jurisprudencia" / "publicaciones_textos.jsonl"),
    ("biblioteca_ambiental", BASE / "data" / "jurisprudencia" / "biblioteca_ambiental.jsonl"),
)
SENTENCIAS_INDICE = BASE / "data" / "jurisprudencia" / "ambiental_textos.jsonl"
DOCTRINA_DIR = BASE / "doctrina" / "ambiental"
TRABAJADORES = 8

_ENGINE = None


def _engine():
    """Motor de LegalGraphify cacheado por proceso: la carga del grafo cuesta ~0,4 s medidos
    (2026-09-28) y se evita repetirla en cada consulta."""
    global _ENGINE
    if _ENGINE is None:
        from legal_graphify import LegalGraphifyEngine
        _ENGINE = LegalGraphifyEngine()
    return _ENGINE

PLAN = (
    "1 · Sentencias de los Tribunales Ambientales (registro 1TA/2TA/3TA, 886 causas).",
    "2 · Publicaciones oficiales: anuarios y boletines 2TA/3TA.",
    "3 · Biblioteca ambiental: libros del concurso, informes en derecho, foros y manuales.",
    "4 · Doctrina ambiental del repositorio.",
    "5 · Subgrafo de LegalGraphify con su ahorro de tokens (parámetro `incluir_subgrafo`).",
    "6 · Citar con texto literal y corchete [Hugging Face - <archivo>]; sin fuente, «sin fuente verificable».",
)


def _norm(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))


# Cachés por proceso: el corpus no cambia mientras corre una sesión (el caso real es el servidor
# MCP de larga vida), y leer + normalizar decenas de MB en cada consulta costaba segundos.
_TEXTOS: dict[tuple[str, int], tuple[str, str]] = {}   # (ruta, mtime_ns) → (texto, texto normalizado)
_FILAS: list[dict] | None = None                       # registros de los índices (.jsonl)


def _limpiar_caches() -> None:
    """Vacía los cachés por proceso (para pruebas y para releer un corpus que cambió en disco)."""
    global _FILAS
    _TEXTOS.clear()
    _FILAS = None


def _texto_cacheado(ruta: pathlib.Path) -> tuple[str, str]:
    """El texto y su normalizado, leídos una sola vez por proceso.

    La clave incluye el mtime: si el archivo cambia en disco se relee solo, y la versión vieja
    se suelta. Se mantiene una sola versión vigente por archivo; el corpus completo en memoria
    pesa lo que el corpus (decenas de MB), el precio de no pagar segundos por consulta.
    """
    clave = (str(ruta), ruta.stat().st_mtime_ns)
    if clave not in _TEXTOS:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        for vieja in [k for k in _TEXTOS if k[0] == str(ruta)]:
            del _TEXTOS[vieja]
        _TEXTOS[clave] = (texto, _norm(texto))
    return _TEXTOS[clave]


def es_materia_ambiental(consulta: str) -> bool:
    """¿La consulta o el caso es de materia ambiental? (SMA, SEIA/RCA, daño, humedales, LO-SMA…)."""
    t = _norm(consulta or "")
    for materia in MATERIAS:
        patron = r"\b" + re.escape(materia).replace(r"\ ", r"\s+") + r"\b"
        if re.search(patron, t):
            return True
    return False


def _terminos(consulta: str) -> list[str]:
    return [t for t in re.findall(r"[\w\-]+", _norm(consulta or "")) if len(t) >= 3][:12]


def _variantes(t: str) -> tuple[str, ...]:
    """Plurales: «humedales» calza con «humedal» y «residuos» con «residuo»."""
    vs = {t}
    if len(t) > 4 and t.endswith("es"):
        vs.add(t[:-2])
    if len(t) > 3 and t.endswith("s"):
        vs.add(t[:-1])
    return tuple(vs)


def _calza(t: str, bajo: str) -> bool:
    return any(v in bajo for v in _variantes(t))


def _filas_colecciones() -> list[dict]:
    """Los registros de los índices, cacheados por proceso (los .jsonl del corpus no cambian en vivo)."""
    global _FILAS
    if _FILAS is not None:
        return _FILAS
    filas: list[dict] = []
    for coleccion, ruta in INDICES:
        if not ruta.exists():
            continue
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            reg = json.loads(linea)
            filas.append({
                "coleccion": coleccion,
                "titulo": reg.get("titulo") or reg.get("rol") or "",
                "tipo": reg.get("tipo") or coleccion,
                "tribunal": reg.get("tribunal") or "",
                "archivo": reg.get("archivo_md") or "",
                "url_oficial": reg.get("url_pdf") or "",
            })
    if DOCTRINA_DIR.exists():
        for md in sorted(DOCTRINA_DIR.glob("*.md")):
            filas.append({
                "coleccion": "doctrina_ambiental",
                "titulo": md.stem.replace("_", " ").title(),
                "tipo": "doctrina",
                "tribunal": "",
                "archivo": f"doctrina/ambiental/{md.name}",
                "url_oficial": "",
            })
    _FILAS = filas
    return _FILAS


def _archivo_por_rol() -> dict[tuple, str]:
    """Rol + tribunal → archivo Markdown, desde el índice de las sentencias ambientales."""
    mapa: dict[tuple, str] = {}
    if SENTENCIAS_INDICE.exists():
        for linea in SENTENCIAS_INDICE.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            reg = json.loads(linea)
            mapa[(str(reg.get("tribunal", "")).upper(), str(reg.get("rol", "")))] = reg.get("archivo_md") or ""
    return mapa


def _fragmento(bajo: str, texto: str, terminos: list[str], ancho: int = 360) -> str:
    """El pasaje literal alrededor del primer término hallado (recibe ya normalizado `bajo`)."""
    pos = -1
    for t in terminos:
        for v in _variantes(t):
            p = bajo.find(v)
            if p >= 0 and (pos < 0 or p < pos):
                pos = p
    if pos < 0:
        return ""
    ini = max(0, pos - ancho // 3)
    fin = min(len(texto), pos + ancho)
    frag = re.sub(r"\s+", " ", texto[ini:fin]).strip()
    return ("… " if ini else "") + frag + (" …" if fin < len(texto) else "")


def _buscar_en_archivo(reg: dict, terminos: list[str]) -> dict | None:
    titulo = _norm(f"{reg.get('titulo', '')} {reg.get('tipo', '')}")
    en_titulo = sum(1 for t in terminos if _calza(t, titulo))
    fragmento = ""
    coincidencias = 0
    tamano = 0
    ruta = BASE / reg["archivo"] if reg.get("archivo") else None
    if ruta and ruta.is_file():
        try:
            texto, bajo = _texto_cacheado(ruta)
        except OSError:
            texto, bajo = "", ""
        if texto:
            tamano = len(texto)
            coincidencias = sum(1 for t in terminos if _calza(t, bajo))
            fragmento = _fragmento(bajo, texto, terminos)
    if not en_titulo and not coincidencias:
        return None
    item = dict(reg)
    item["fragmento"] = fragmento
    item["tamano"] = tamano
    # El título manda; el contenido pesa parejo y acotado, para que un compendio de un millón de
    # caracteres (anuarios, manuales) no tape a un documento específico que calza mejor.
    item["puntaje"] = 3 * en_titulo + min(4, coincidencias)
    item["cita"] = f"[Hugging Face - {reg['archivo']}]" if reg.get("archivo") else f"[Doctrina - {reg.get('titulo', '')}]"
    item["enlace"] = f"{HF_BASE}/{reg['archivo']}" if reg.get("archivo") else ""
    return item


def consulta_ambiental(consulta: str, limite: int = 8, incluir_subgrafo: bool = False) -> dict:
    """La consulta maestro del módulo: resultados citables del corpus ambiental completo.

    `incluir_subgrafo` es opcional: la carga del grafo cuesta ~0,4 s medidos (2026-09-28) y se
    paga una sola vez por proceso; el módulo no la hace salvo que se pida.
    """
    consulta = (consulta or "").strip()
    terminos = _terminos(consulta)
    resultados: list[dict] = []
    faltantes: list[str] = []

    # 1 · sentencias de los tribunales ambientales (registro con materia y carátula)
    try:
        from tribunales_ambientales_connector import TribunalesAmbientalesClient
        archivo_por_rol = _archivo_por_rol()
        client = TribunalesAmbientalesClient()
        for r in client.search_jurisprudencia(consulta):
            archivo = archivo_por_rol.get((str(r.get("tribunal", "")).upper(), str(r.get("rol", ""))), "")
            titulo = r.get("titulo") or r.get("caratula") or ""
            resumen = re.sub(r"\s+", " ", str(r.get("criterio") or r.get("materia") or r.get("resuelve") or "")).strip()
            # 9 de base (la jurisprudencia manda) + hasta 3 por calzar la consulta: así el caso de
            # humedales sube sobre la reclamación genérica de turno.
            en_sentencia = sum(1 for t in terminos if _calza(t, _norm(f"{titulo} {r.get('materia') or ''} {resumen}")))
            resultados.append({
                "coleccion": "jurisprudencia_ambiental",
                "titulo": titulo,
                "tipo": r.get("tipo") or r.get("origen") or r.get("materia") or "sentencia",
                "tribunal": r.get("tribunal") or "",
                "archivo": archivo,
                "url_oficial": r.get("link") or "",
                "fragmento": resumen[:400],
                "puntaje": 9 + min(3, en_sentencia),
                "tamano": 0,
                "cita": f"[Hugging Face - {archivo}]" if archivo else f"[TA - {r.get('tribunal', '')} · {titulo[:70]}]",
                "enlace": f"{HF_BASE}/{archivo}" if archivo else (r.get("link") or ""),
            })
    except Exception as e:  # noqa: BLE001 — el módulo no se cae si el conector falla
        faltantes.append(f"sentencias: {str(e)[:120]}")

    # 2-4 · publicaciones, biblioteca y doctrina: barrido de los Markdown con fragmento literal
    filas = _filas_colecciones()
    if filas:
        with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
            for res in pool.map(lambda f: _buscar_en_archivo(f, terminos), filas):
                if res:
                    resultados.append(res)
    else:
        faltantes.append("colecciones locales")

    # Las sentencias (9) van primero; entre documentos de igual puntaje gana el más breve,
    # que es el más específico frente a compendios y manuales.
    resultados.sort(key=lambda x: (-x["puntaje"], x.get("tamano", 0)))
    resultados = resultados[: max(1, limite)]

    citas = []
    for r in resultados:
        if r.get("archivo"):
            citas.append({
                "formato": r["cita"], "texto": r.get("fragmento", ""), "url": r.get("enlace", ""),
                "fuente": "Hugging Face", "cita_completa": f"{r['cita']} {r.get('enlace', '')}".strip(),
            })
        else:
            citas.append({
                "formato": r["cita"], "texto": r.get("fragmento", ""), "url": r.get("url_oficial", ""),
                "fuente": "TA", "cita_completa": f"{r['cita']} {r.get('url_oficial', '')}".strip(),
            })

    # 5 · subgrafo dogmático con su ahorro de tokens (a pedido: el primer llamado carga su índice)
    grafo: dict = {}
    if incluir_subgrafo:
        try:
            res = _engine().consultar_subgrafo(consulta, max_hops=1)
            if isinstance(res, dict):
                grafo = {k: res[k] for k in ("encontrado", "mensaje", "metricas_tokens", "institucion", "central")
                         if k in res}
        except Exception:  # noqa: BLE001 — el subgrafo es aditivo
            grafo = {}

    if not resultados:
        faltantes.append("corpus ambiental")

    return {
        "consulta": consulta,
        "materia_ambiental": es_materia_ambiental(consulta),
        "plan": list(PLAN),
        "resultados": resultados,
        "citas": citas,
        "subgrafo": grafo,
        "faltantes": faltantes,
        "como_citar": "Pegá cada cita con su texto literal. En conversación: la respuesta primero y las "
                      "fuentes al final. En documentos (.docx): citas a pie de página (fuente · identificador · enlace).",
    }
