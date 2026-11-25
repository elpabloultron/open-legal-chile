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
import os
import pathlib
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

from config import sin_tildes

BASE = pathlib.Path(__file__).resolve().parent
_BASE_DEFAULT = BASE
_FTS_PATH_DEFAULT = pathlib.Path.home() / ".openlegal" / "ambiental_fts.sqlite"
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
        # El motor compartido del proceso: un solo grafo en memoria (con la capa del mapa del
        # corpus cuando está lista) en vez de una copia por módulo.
        from legal_graphify import obtener_motor_compartido
        _ENGINE = obtener_motor_compartido()
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
    return sin_tildes((texto or "").lower())


# Cachés por proceso: el corpus no cambia mientras corre una sesión (el caso real es el servidor
# MCP de larga vida), y leer + normalizar decenas de MB en cada consulta costaba segundos.
_TEXTOS: dict[tuple[str, int], tuple[str, str]] = {}   # (ruta, mtime_ns) → (texto, texto normalizado)
_FILAS: list[dict] | None = None                       # registros de los índices (.jsonl)
_ARCHIVO_POR_ROL: dict[tuple, str] | None = None
_FTS_VERIFICADO: bool = False
_FTS_LOCK = threading.Lock()


def _ruta_fts() -> pathlib.Path:
    override = os.environ.get("OPENLEGAL_AMBIENTAL_FTS", "").strip()
    return pathlib.Path(override) if override else _FTS_PATH_DEFAULT


def _limpiar_caches() -> None:
    """Vacía los cachés por proceso (para pruebas y para releer un corpus que cambió en disco)."""
    global _FILAS, _ARCHIVO_POR_ROL, _FTS_VERIFICADO
    _TEXTOS.clear()
    _FILAS = None
    _ARCHIVO_POR_ROL = None
    _FTS_VERIFICADO = False


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
    global _ARCHIVO_POR_ROL
    if _ARCHIVO_POR_ROL is not None:
        return _ARCHIVO_POR_ROL
    mapa: dict[tuple, str] = {}
    if SENTENCIAS_INDICE.exists():
        for linea in SENTENCIAS_INDICE.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            reg = json.loads(linea)
            mapa[(str(reg.get("tribunal", "")).upper(), str(reg.get("rol", "")))] = reg.get("archivo_md") or ""
    _ARCHIVO_POR_ROL = mapa
    return _ARCHIVO_POR_ROL


def _fragmento(bajo: str, texto: str, terminos: list[str], ancho: int = 360) -> str:
    """El pasaje literal alrededor del mejor término hallado (recibe ya normalizado `bajo`).

    El ancla es el término más largo que calza —«cautelares» antes que «ante»—: un término
    genérico aparece en cualquier parte y ancla el pasaje donde no hay nada que citar. Los
    bordes se ajustan a palabras completas.
    """
    pos = -1
    largo = 0
    for t in terminos:
        for v in _variantes(t):
            p = bajo.find(v)
            if p < 0:
                continue
            if len(t) > largo or (len(t) == largo and (pos < 0 or p < pos)):
                pos, largo = p, len(t)
    if pos < 0:
        return ""
    ini = max(0, pos - ancho // 3)
    fin = min(len(texto), pos + ancho)
    if ini > 0:
        espacio = texto.find(" ", ini)
        if 0 <= espacio - ini <= 60:
            ini = espacio + 1
    if fin < len(texto):
        espacio = texto.rfind(" ", ini, fin)
        if 0 <= fin - espacio <= 80:
            fin = espacio
    frag = re.sub(r"\s+", " ", texto[ini:fin]).strip().replace("**", "")
    return ("… " if ini else "") + frag + (" …" if fin < len(texto) else "")


_MIN_TEXTO_SENTENCIA = 4000   # bajo esto el archivo es una ficha, no el texto del fallo


def _extracto_de_sentencia(archivo: str, terminos: list[str]) -> str:
    """El pasaje literal de la sentencia si su texto completo está en disco.

    Los archivos abren con la ficha (bullets de metadata) y el fallo viene después del primer
    separador: se cita del cuerpo, nunca de la ficha. Las fichas de ~1 KB no son texto del fallo:
    ahí se devuelve vacío y quien llama describe el documento en vez de citarlo como si fuera suyo.
    """
    if not archivo:
        return ""
    ruta = BASE / archivo
    try:
        if not ruta.is_file() or ruta.stat().st_size < _MIN_TEXTO_SENTENCIA:
            return ""
        texto, bajo = _texto_cacheado(ruta)
    except OSError:
        return ""
    corte = texto.find("\n---\n")
    if 0 <= corte <= 4000 and len(texto) - corte > 2000:
        texto, bajo = texto[corte:], bajo[corte:]
    return _fragmento(bajo, texto, terminos, ancho=500)


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


def _asegurar_indice_fts(filas: list[dict]) -> pathlib.Path | None:
    """Construye o valida el índice FTS5 persistente sobre los .md ambientales locales."""
    global _FTS_VERIFICADO
    if BASE != _BASE_DEFAULT:
        return None
    actuales: dict[str, tuple[int, int, pathlib.Path]] = {}
    for reg in filas:
        archivo = reg.get("archivo") or ""
        if not archivo or archivo in actuales:
            continue
        ruta = BASE / archivo
        try:
            if ruta.is_file():
                st = ruta.stat()
                actuales[archivo] = (st.st_mtime_ns, st.st_size, ruta)
        except OSError:
            continue
    if not actuales:
        return None

    db_path = _ruta_fts()
    with _FTS_LOCK:
        if _FTS_VERIFICADO and db_path.is_file():
            return db_path
        if db_path.is_file():
            con: sqlite3.Connection | None = None
            try:
                con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                filas_db = con.execute("SELECT archivo, mtime_ns, size FROM archivos").fetchall()
                huella_db = {(row[0], row[1], row[2]) for row in filas_db}
                huella_fs = {(arch, info[0], info[1]) for arch, info in actuales.items()}
                if huella_db == huella_fs:
                    _FTS_VERIFICADO = True
                    return db_path
            except sqlite3.Error:
                pass
            finally:
                if con is not None:
                    con.close()

        tmp_path = db_path.parent / f"{db_path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        con_w: sqlite3.Connection | None = None
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            con_w = sqlite3.connect(str(tmp_path))
            con_w.execute("PRAGMA journal_mode=DELETE")
            con_w.execute(
                "CREATE TABLE archivos (id INTEGER PRIMARY KEY, archivo TEXT UNIQUE, mtime_ns INTEGER, size INTEGER)"
            )
            con_w.execute(
                "CREATE VIRTUAL TABLE textos_fts USING fts5("
                "cuerpo, content='', tokenize='unicode61 remove_diacritics 2')"
            )
            for idx, (archivo, (mtime_ns, size, ruta)) in enumerate(sorted(actuales.items()), 1):
                with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                    contenido = fh.read()
                con_w.execute(
                    "INSERT INTO archivos (id, archivo, mtime_ns, size) VALUES (?, ?, ?, ?)",
                    (idx, archivo, mtime_ns, size),
                )
                con_w.execute("INSERT INTO textos_fts (rowid, cuerpo) VALUES (?, ?)", (idx, contenido))
            con_w.commit()
            con_w.close()
            con_w = None
            os.replace(tmp_path, db_path)
            _FTS_VERIFICADO = True
            return db_path
        except (OSError, sqlite3.Error):
            if con_w is not None:
                try:
                    con_w.close()
                except sqlite3.Error:
                    pass
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
            return None


def _fts_expr_termino(t: str) -> str:
    partes: list[str] = []
    for v in _variantes(t):
        toks = [tok for tok in re.findall(r"[a-z0-9]+", v) if tok]
        if not toks:
            continue
        if len(toks) == 1:
            partes.append(f'"{toks[0]}"*')
        else:
            partes.append("(" + " ".join(f'"{tok}"*' for tok in toks) + ")")
    return " OR ".join(dict.fromkeys(partes))


def _seleccionar_candidatos_fts(filas: list[dict], terminos: list[str], tope: int) -> list[dict] | None:
    """Pre-filtra candidatos con FTS5 (<5 ms) antes de leer los .md completos en RAM."""
    if not terminos:
        return []
    db_path = _asegurar_indice_fts(filas)
    if db_path is None:
        return None
    con: sqlite3.Connection | None = None
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        id_a_info = {row[0]: (row[1], row[2]) for row in con.execute("SELECT id, archivo, size FROM archivos")}
        conteo_por_archivo: dict[str, int] = {}
        for t in terminos:
            expr = _fts_expr_termino(t)
            if not expr:
                continue
            hits = con.execute("SELECT rowid FROM textos_fts WHERE textos_fts MATCH ?", (expr,)).fetchall()
            for (rid,) in hits:
                info = id_a_info.get(rid)
                if info is not None:
                    arch = info[0]
                    conteo_por_archivo[arch] = conteo_por_archivo.get(arch, 0) + 1
    except sqlite3.Error:
        return None
    finally:
        if con is not None:
            con.close()

    size_por_archivo = {arch: sz for arch, sz in id_a_info.values()}
    puntuados: list[tuple[int, bool, int, int, dict]] = []
    for idx, reg in enumerate(filas):
        archivo = reg.get("archivo") or ""
        titulo = _norm(f"{reg.get('titulo', '')} {reg.get('tipo', '')}")
        en_titulo = sum(1 for t in terminos if _calza(t, titulo))
        coinc = conteo_por_archivo.get(archivo, 0)
        if not en_titulo and not coinc:
            continue
        puntaje_est = 3 * en_titulo + min(4, coinc)
        tam_est = size_por_archivo.get(archivo, 0)
        puntuados.append((-puntaje_est, en_titulo > 0, tam_est, idx, reg))

    puntuados.sort(key=lambda x: (x[0], x[2], x[3]))
    cupo_candidatos = max(32, tope * 4)
    seleccionados = [x[4] for x in puntuados[:cupo_candidatos]]
    if len(puntuados) > cupo_candidatos:
        vistos = {id(r) for r in seleccionados}
        for _, tiene_titulo, _, _, reg in puntuados[cupo_candidatos:]:
            if tiene_titulo and id(reg) not in vistos:
                seleccionados.append(reg)
                vistos.add(id(reg))
    return seleccionados


def _buscar_sentencias_ta(consulta: str, terminos: list[str]) -> tuple[list[dict], str | None]:
    """Busca sentencias de los Tribunales Ambientales y extrae pasajes literales del fallo."""
    encontrados: list[dict] = []
    try:
        from tribunales_ambientales_connector import TribunalesAmbientalesClient
        archivo_por_rol = _archivo_por_rol()
        client = TribunalesAmbientalesClient()
        for r in client.search_jurisprudencia(consulta):
            archivo = archivo_por_rol.get((str(r.get("tribunal", "")).upper(), str(r.get("rol", ""))), "")
            titulo = r.get("titulo") or r.get("caratula") or ""
            resumen = re.sub(r"\s+", " ", str(r.get("criterio") or r.get("materia") or r.get("resuelve") or "")).strip()
            # El pasaje literal manda: si la sentencia tiene su texto completo en disco (2TA/3TA),
            # se cita de ahí; sin texto se describe el fallo, nunca se cita su «materia» como texto.
            fragmento = _extracto_de_sentencia(archivo, terminos)
            if not fragmento:
                descripcion = " · ".join(p for p in (
                    str(r.get("tipo") or "Sentencia").strip(), titulo, str(r.get("fecha") or "").strip()) if p)
                fragmento = re.sub(r"\s+", " ", str(r.get("criterio") or "")).strip()[:400] or descripcion
            # 9 de base (la jurisprudencia manda) + hasta 3 por calzar la consulta: así el caso de
            # humedales sube sobre la reclamación genérica de turno.
            en_sentencia = sum(1 for t in terminos if _calza(t, _norm(f"{titulo} {r.get('materia') or ''} {resumen}")))
            encontrados.append({
                "coleccion": "jurisprudencia_ambiental",
                "titulo": titulo,
                "tipo": r.get("tipo") or r.get("origen") or r.get("materia") or "sentencia",
                "tribunal": r.get("tribunal") or "",
                "archivo": archivo,
                "url_oficial": r.get("link") or "",
                "fragmento": fragmento,
                "puntaje": 9 + min(3, en_sentencia),
                "tamano": 0,
                "cita": f"[Hugging Face - {archivo}]" if archivo else f"[TA - {r.get('tribunal', '')} · {titulo[:70]}]",
                "enlace": f"{HF_BASE}/{archivo}" if archivo else (r.get("link") or ""),
            })
        return encontrados, None
    except Exception as e:  # noqa: BLE001 — el módulo no se cae si el conector falla
        return [], f"sentencias: {str(e)[:120]}"


def _buscar_colecciones(terminos: list[str], tope: int) -> tuple[list[dict], str | None]:
    """Busca publicaciones oficiales, biblioteca y doctrina ambiental con pre-filtro FTS5."""
    filas = _filas_colecciones()
    if not filas:
        return [], "colecciones locales"
    candidatos = _seleccionar_candidatos_fts(filas, terminos, tope)
    if candidatos is None:
        candidatos = filas
    if not candidatos:
        return [], None
    encontrados: list[dict] = []
    trabajadores = min(TRABAJADORES, len(candidatos))
    if trabajadores <= 1:
        for reg in candidatos:
            res = _buscar_en_archivo(reg, terminos)
            if res:
                encontrados.append(res)
    else:
        with ThreadPoolExecutor(max_workers=trabajadores) as pool:
            for res in pool.map(lambda f: _buscar_en_archivo(f, terminos), candidatos):
                if res:
                    encontrados.append(res)
    return encontrados, None


def _buscar_subgrafo(consulta: str) -> dict:
    try:
        res = _engine().consultar_subgrafo(consulta, max_hops=1)
        if isinstance(res, dict):
            return {k: res[k] for k in ("encontrado", "mensaje", "metricas_tokens", "institucion", "central")
                    if k in res}
    except Exception:  # noqa: BLE001 — el subgrafo es aditivo
        pass
    return {}


def consulta_ambiental(consulta: str, limite: int = 8, incluir_subgrafo: bool = False) -> dict:
    """La consulta maestro del módulo: resultados citables del corpus ambiental completo.

    `incluir_subgrafo` es opcional: la carga del grafo cuesta ~0,4 s medidos (2026-09-28) y se
    paga una sola vez por proceso; el módulo no la hace salvo que se pida.
    """
    consulta = (consulta or "").strip()
    terminos = _terminos(consulta)
    tope = max(1, limite)
    resultados: list[dict] = []
    faltantes: list[str] = []

    workers = 3 if incluir_subgrafo else 2
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fut_ta = pool.submit(_buscar_sentencias_ta, consulta, terminos)
        fut_col = pool.submit(_buscar_colecciones, terminos, tope)
        fut_grafo = pool.submit(_buscar_subgrafo, consulta) if incluir_subgrafo else None

        res_ta, err_ta = fut_ta.result()
        res_col, err_col = fut_col.result()
        grafo: dict = fut_grafo.result() if fut_grafo is not None else {}

    resultados.extend(res_ta)
    if err_ta:
        faltantes.append(err_ta)
    resultados.extend(res_col)
    if err_col:
        faltantes.append(err_col)

    # Las sentencias (9) van primero; entre documentos de igual puntaje gana el más breve,
    # que es el más específico frente a compendios y manuales. Pero con la jurisprudencia
    # tapando todos los cupos la consulta salía mono-temática: se reserva hasta un tercio
    # del cupo para documentos (doctrina, guías, manuales) — la otra pata del corpus.
    sentencias = sorted((r for r in resultados if r["coleccion"] == "jurisprudencia_ambiental"),
                        key=lambda x: (-x["puntaje"], x.get("tamano", 0)))
    documentos = sorted((r for r in resultados if r["coleccion"] != "jurisprudencia_ambiental"),
                        key=lambda x: (-x["puntaje"], x.get("tamano", 0)))
    cupo_docs = min(len(documentos), tope // 3)
    seleccion = sentencias[: tope - cupo_docs] + documentos[: cupo_docs]
    if len(seleccion) < tope:
        resto = sentencias[tope - cupo_docs:] + documentos[cupo_docs:]
        seleccion += resto[: tope - len(seleccion)]
    resultados = sorted(seleccion, key=lambda x: (-x["puntaje"], x.get("tamano", 0)))

    citas = []
    for r in resultados:
        if r.get("archivo"):
            citas.append({
                "formato": r["cita"], "texto": r.get("fragmento", ""), "url": r.get("enlace", ""),
                "fuente": "Hugging Face",
            })
        else:
            citas.append({
                "formato": r["cita"], "texto": r.get("fragmento", ""), "url": r.get("url_oficial", ""),
                "fuente": "TA",
            })

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
