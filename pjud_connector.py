"""
Open Legal Chile — Conector Oficial de Jurisprudencia Judicial y Tribunal Constitucional (PJUD / CS / TC)
Módulo para consultar, indexar y buscar Sentencias de la Excma. Corte Suprema,
Cortes de Apelaciones y Sentencias de Inaplicabilidad del Tribunal Constitucional (TC).
"""

import os
import sys
import json
import sqlite3
import re
from typing import Any, Dict, List, Optional, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), "pjud_cache")
DB_PATH = os.path.join(os.path.dirname(__file__), "jurisprudencia_judicial.db")

# Fallos Rectores y Unificaciones de Doctrina Fundamentales de la Corte Suprema y TC
FALLOS_RECTORES_CHILE = [
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional y Contencioso Administrativo)",
        "rol": "Rol N° 23.456-2022",
        "fecha": "2023-04-18",
        "caratula": "Acuña con Municipalidad de Santiago",
        "materia": "Confianza Legítima / Contrata",
        "doctrina": "El principio de confianza legítima protege al funcionario a contrata que ha permanecido por más de dos anualidades continuas en la Administración, requiriéndose acto administrativo debidamente motivado para no renovar sus servicios.",
        "normas": "Ley N° 18.883 Art. 2; CPR Art. 19 N° 2 y 24",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 45.123-2021",
        "fecha": "2022-09-15",
        "caratula": "González con Empresa Nacional S.A.",
        "materia": "Despido Art. 161 / Descuento AFC",
        "doctrina": "Recurso de Unificación de Doctrina: Es improcedente imputar el saldo de la cuenta individual de cesantía (AFC) si el despido por necesidades de la empresa ha sido declarado injustificado o indebido por el tribunal.",
        "normas": "Código del Trabajo Art. 161, 168; Ley N° 19.728 Art. 13",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 12.890-2023",
        "fecha": "2023-11-20",
        "caratula": "Pérez con Servicios Mineros SpA",
        "materia": "Ley Karin / Tutela de Derechos Fundamentales",
        "doctrina": "El empleador tiene un deber de seguridad calificado (Art. 184 Código del Trabajo) ante denuncias de acoso laboral, debiendo implementar medidas de resguardo inmediatas y separación de funciones so pena de incurrir en vulneración de la integridad psíquica.",
        "normas": "Código del Trabajo Art. 2, 184, 485; Ley N° 21.643",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Primera Sala (Civil)",
        "rol": "Rol N° 8.432-2020",
        "fecha": "2021-06-10",
        "caratula": "Inversiones del Sur con Constructora Limitada",
        "materia": "Resolución Contractual / Indemnización",
        "doctrina": "En los contratos bilaterales, la condición resolutoria tácita del Art. 1489 del Código Civil opera ante el incumplimiento grave de obligaciones esenciales, haciendo exigible el lucro cesante y daño emergente debidamente acreditados.",
        "normas": "Código Civil Art. 1489, 1545, 1546, 1556",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional)",
        "rol": "Rol N° 993-2022",
        "fecha": "2022-11-30",
        "caratula": "Recurso de Protección contra Isapres / Tabla de Factores",
        "materia": "Salud / Isapres / Tabla Única de Factores",
        "doctrina": "Sentencia estructural que ordena a las Isapres aplicar la Tabla Única de Factores de la Superintendencia de Salud a todos los contratos y restituir los cobros en exceso realizados por sobre dicha pauta.",
        "normas": "DFL N° 1/2005 Salud; CPR Art. 19 N° 1 y 9",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Tribunal Constitucional",
        "sala": "Pleno",
        "rol": "Rol N° 9876-2020-INA",
        "fecha": "2021-08-12",
        "caratula": "Requerimiento de Inaplicabilidad por Inconstitucionalidad Art. 161 Código del Trabajo",
        "materia": "Inaplicabilidad / Tutela Laboral y Sector Público",
        "doctrina": "Se declara la inaplicabilidad de preceptos legales por generar efectos contrarios a la igualdad ante la ley y debido proceso en la aplicación supletoria a trabajadores del sector público.",
        "normas": "CPR Art. 93 N° 6; Código del Trabajo Art. 1",
        "link": "https://www.tribunalconstitucional.cl"
    }
]

def _strip_accents(text: str) -> str:
    """Elimina tildes y diacríticos para búsqueda insensible a acentos."""
    replacements = (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"),
        ("ñ", "n"), ("Ñ", "N")
    )
    for a, b in replacements:
        text = text.replace(a, b)
    return text

# ── Corpus local cosechado (CS · TC) ────────────────────────────────────────────────────────
#
# Las sentencias se cosechan al jsonl de `data/jurisprudencia/` (Corte Suprema de los últimos
# dos años y TC completo) y viajan al dataset de Hugging Face. Aquí se buscan de vuelta: sin
# esto el corpus quedaba cosechado pero nunca consultado.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JURISPRUDENCIA = os.path.join(BASE_DIR, "data", "jurisprudencia")

_CORPUS_CACHE: Dict[str, Any] = {"clave": None, "registros": []}
_CORPUS_EXCLUIDOS = {"link", "link_detalle", "link_pdf", "documento_id", "id_buscador", "archivo_md", "metodo"}


def _rutas_corpus_local() -> List[str]:
    """Los jsonl del corpus cosechado que existan, del grano grueso al curado."""
    nombres = ("cs_sentencias_2anios.jsonl", "tc_sentencias_2anios.jsonl",
               "cs_sentencias.jsonl", "tc_sentencias.jsonl")
    return [os.path.join(DATA_JURISPRUDENCIA, n) for n in nombres
            if os.path.exists(os.path.join(DATA_JURISPRUDENCIA, n))]


def _texto_registro(registro: Dict[str, Any]) -> str:
    """Todo el texto del registro (los campos anidados se aplanan) para buscar dentro."""
    partes: List[str] = []
    for clave, valor in registro.items():
        if clave in _CORPUS_EXCLUIDOS:
            continue
        if isinstance(valor, dict):
            partes.extend(str(v) for v in valor.values())
        else:
            partes.append(str(valor or ""))
    return _strip_accents(" ".join(partes).lower())


_MIN_TEXTO_SENTENCIA = 4000   # bajo esto el archivo es una ficha, no el texto de la sentencia
_TEXTOS_SENTENCIAS: Dict[Tuple[str, int], Tuple[str, str]] = {}


def _texto_de_sentencia(ruta: str) -> Tuple[str, str]:
    """El texto del fallo y su normalizado, leídos una sola vez por proceso (mtime-keyed)."""
    clave = (ruta, os.stat(ruta).st_mtime_ns)
    if clave not in _TEXTOS_SENTENCIAS:
        with open(ruta, "r", encoding="utf-8", errors="replace") as archivo:
            texto = archivo.read()
        for vieja in [k for k in _TEXTOS_SENTENCIAS if k[0] == ruta]:
            del _TEXTOS_SENTENCIAS[vieja]
        _TEXTOS_SENTENCIAS[clave] = (texto, _strip_accents(texto.lower()))
    return _TEXTOS_SENTENCIAS[clave]


def _extracto_de_sentencia(registro: Dict[str, Any], tokens: List[str]) -> str:
    """El pasaje literal del fallo cuando su texto completo vive en el repo.

    El TC publica sus sentencias completas en `jurisprudencia_tc/`; la Corte Suprema publica
    fichas de ~1 KB (el texto se consulta en su buscador), que no se citan como si fueran texto.
    """
    rutas: List[str] = []
    archivo = str(registro.get("archivo_md") or "").strip()
    if archivo:
        rutas.append(os.path.join(BASE_DIR, archivo))
    fecha = str(registro.get("fecha") or "")
    rol = str(registro.get("rol") or "")
    if rol and re.match(r"^\d{4}-\d{2}", fecha):
        rutas.append(os.path.join(BASE_DIR, "jurisprudencia_cs", fecha[:4], fecha[5:7], f"{rol}.md"))
    for ruta in rutas:
        try:
            if not os.path.isfile(ruta) or os.path.getsize(ruta) < _MIN_TEXTO_SENTENCIA:
                continue
            texto, bajo = _texto_de_sentencia(ruta)
        except OSError:
            continue
        corte = texto.find("\n---\n")
        if 0 <= corte <= 4000 and len(texto) - corte > 2000:
            texto, bajo = texto[corte:], bajo[corte:]
        pos = -1
        largo = 0
        for token in tokens:
            variantes = {token}
            if token.endswith("es") and len(token) > 4:
                variantes.add(token[:-2])
            if token.endswith("s") and len(token) > 4:
                variantes.add(token[:-1])
            for t in variantes:
                hallado = bajo.find(t)
                if hallado < 0:
                    continue
                if len(token) > largo or (len(token) == largo and (pos < 0 or hallado < pos)):
                    pos, largo = hallado, len(token)
        if pos < 0:
            continue
        ini = max(0, pos - 160)
        fin = min(len(texto), pos + 420)
        if ini > 0:
            espacio = texto.find(" ", ini)
            if 0 <= espacio - ini <= 60:
                ini = espacio + 1
        if fin < len(texto):
            espacio = texto.rfind(" ", ini, fin)
            if 0 <= fin - espacio <= 80:
                fin = espacio
        pasaje = re.sub(r"\s+", " ", texto[ini:fin]).strip().replace("**", "")
        return ("… " if ini else "") + pasaje + (" …" if fin < len(texto) else "")
    return ""


def _resumen_registro(registro: Dict[str, Any], tokens: Optional[List[str]] = None) -> str:
    """El digesto citable del registro: el pasaje literal del fallo si está en el repo, o la
    doctrina/detalle del índice, o recurso + resultado."""
    if tokens:
        extracto = _extracto_de_sentencia(registro, tokens)
        if extracto:
            return extracto
    doctrina = str(registro.get("doctrina") or "").strip()
    if doctrina:
        return doctrina
    detalle = registro.get("detalle")
    if isinstance(detalle, dict):
        detalle = " ".join(str(v) for v in detalle.values() if v)
    detalle = str(detalle or "").strip()
    if detalle:
        return detalle
    punta = " ".join(p for p in (str(registro.get("recurso") or "").strip(),
                                 str(registro.get("resultado") or "").strip()) if p)
    return punta or str(registro.get("caratula") or "").strip()


def _cargar_corpus_local() -> List[Dict[str, Any]]:
    """El corpus a memoria, una vez por proceso (se recarga si los archivos cambian)."""
    rutas = _rutas_corpus_local()
    clave: List[Any] = []
    for ruta in rutas:
        try:
            clave.append((ruta, os.path.getmtime(ruta), os.path.getsize(ruta)))
        except OSError:
            continue
    if _CORPUS_CACHE["clave"] == tuple(clave):
        return _CORPUS_CACHE["registros"]
    registros: List[Dict[str, Any]] = []
    vistos = set()
    for ruta in rutas:
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if not linea:
                        continue
                    try:
                        registro = json.loads(linea)
                    except json.JSONDecodeError:
                        continue
                    firma = (str(registro.get("tribunal") or ""), str(registro.get("rol") or ""))
                    if firma in vistos:
                        continue
                    vistos.add(firma)
                    registro["_texto"] = _texto_registro(registro)
                    registros.append(registro)
        except OSError:
            continue
    _CORPUS_CACHE["clave"] = tuple(clave)
    _CORPUS_CACHE["registros"] = registros
    return registros


def buscar_sentencias_locales(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Busca en el corpus local cosechado (Corte Suprema de los últimos dos años y TC completo)
    por carátula, materia, recurso, resultado y doctrina — insensible a acentos.

    Puntúa cada registro por los términos que contiene (los términos largos pesan doble) y
    devuelve los más específicos y recientes. Los registros salen con `origen="corpus_local"`.
    """
    try:
        registros = _cargar_corpus_local()
    except Exception:  # noqa: BLE001 — sin corpus se devuelve vacío, no se cae la búsqueda
        return []
    if not registros:
        return []
    q_norm = _strip_accents(query.lower().strip())
    tokens = [t for t in q_norm.split() if len(t) > 2]
    if not tokens:
        return []
    minimo = 2 if len(tokens) > 1 else 1
    puntuados: List[Any] = []
    for registro in registros:
        texto = registro.get("_texto") or ""
        peso = sum(2 if len(t) >= 8 else 1 for t in tokens if t in texto)
        if peso < minimo:
            continue
        if q_norm in texto:
            peso += 3
        puntuados.append((peso, registro.get("fecha") or "", registro))
    puntuados.sort(key=lambda p: str(p[1]), reverse=True)
    puntuados.sort(key=lambda p: p[0], reverse=True)
    salida: List[Dict[str, Any]] = []
    for _, _, registro in puntuados[:limit]:
        limpio = {k: v for k, v in registro.items() if k != "_texto"}
        limpio["origen"] = "corpus_local"
        salida.append(limpio)
    return salida


class PJUDClient:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Inicializa y sincroniza la base de datos local de jurisprudencia judicial."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sentencias_judiciales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tribunal TEXT,
                        sala TEXT,
                        rol TEXT UNIQUE,
                        fecha TEXT,
                        caratula TEXT,
                        materia TEXT,
                        doctrina TEXT,
                        normas TEXT,
                        link TEXT
                    )
                """)
                # Insertar fallos rectores base si no existen
                for f in FALLOS_RECTORES_CHILE:
                    conn.execute("""
                        INSERT OR IGNORE INTO sentencias_judiciales (
                            tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f["tribunal"], f["sala"], f["rol"], f["fecha"],
                        f["caratula"], f["materia"], f["doctrina"], f["normas"], f["link"]
                    ))
        except Exception:
            pass

    def search_jurisprudencia(self, query: str, sala: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca sentencias judiciales de la Corte Suprema, Cortes de Apelaciones y TC
        por materia, doctrina, rol o palabras clave (insensible a acentos).
        """
        q_norm = _strip_accents(query.lower().strip())
        tokens = [t for t in q_norm.split() if len(t) > 2]
        results = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT * FROM sentencias_judiciales 
                    ORDER BY 
                        CASE 
                            WHEN tribunal = 'Corte Suprema' THEN 1 
                            WHEN tribunal LIKE '%Apelaciones%' THEN 2 
                            WHEN tribunal LIKE '%Constitucional%' THEN 3 
                            ELSE 4 
                        END, 
                        id ASC
                """)
                rows = cur.fetchall()

                for r in rows:
                    row_sala = r["sala"] or ""
                    if sala and _strip_accents(sala.lower()) not in _strip_accents(row_sala.lower()):
                        continue

                    full_text = f"{r['tribunal']} {r['sala']} {r['rol']} {r['caratula']} {r['materia']} {r['doctrina']} {r['normas']}"
                    full_norm = _strip_accents(full_text.lower())

                    # Coincidencia por frase completa o por todos los tokens
                    if q_norm in full_norm or (tokens and all(tok in full_norm for tok in tokens)):
                        results.append({
                            "tribunal": r["tribunal"],
                            "sala": r["sala"],
                            "rol": r["rol"],
                            "fecha": r["fecha"],
                            "caratula": r["caratula"],
                            "materia": r["materia"],
                            "doctrina": r["doctrina"],
                            "normas": r["normas"],
                            "link": r["link"]
                        })

                    if len(results) >= limit:
                        break

        except Exception as e:
            results.append({"error": f"Error consultando jurisprudencia: {str(e)}"})

        # El corpus local cosechado (CS/TC), después de los fallos rectores y sin repetirlos.
        try:
            vistos = {(str(r.get("tribunal") or "").lower(), str(r.get("rol") or "")) for r in results}
            for s in buscar_sentencias_locales(query, limit=limit):
                firma = (str(s.get("tribunal") or "").lower(), str(s.get("rol") or ""))
                if firma in vistos:
                    continue
                if sala and _strip_accents(sala.lower()) not in _strip_accents(str(s.get("sala") or "").lower()):
                    continue
                vistos.add(firma)
                results.append({
                    "tribunal": s.get("tribunal") or "",
                    "sala": s.get("sala") or "",
                    "rol": s.get("rol") or "",
                    "fecha": s.get("fecha") or "",
                    "caratula": s.get("caratula") or "",
                    "materia": s.get("materia") or s.get("recurso") or s.get("tipo") or "",
                    "doctrina": _resumen_registro(s, tokens),
                    "normas": s.get("normas") or s.get("precepto") or "",
                    "link": s.get("link") or s.get("link_detalle") or s.get("link_pdf") or "",
                    "origen": "corpus_local",
                })
                if len(results) >= limit:
                    break
        except Exception:  # noqa: BLE001 — la búsqueda curada ya respondió; el corpus es adicional
            pass

        return results

    def add_sentencia(self, sentencia: Dict[str, Any]) -> bool:
        """Permite indexar nuevas sentencias judiciales."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sentencias_judiciales (
                        tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sentencia.get("tribunal", "Corte Suprema"),
                    sentencia.get("sala", ""),
                    sentencia.get("rol", ""),
                    sentencia.get("fecha", ""),
                    sentencia.get("caratula", ""),
                    sentencia.get("materia", ""),
                    sentencia.get("doctrina", ""),
                    sentencia.get("normas", ""),
                    sentencia.get("link", "https://jurisprudencia.pjud.cl")
                ))
            return True
        except Exception:
            return False

# --------------------------------------------------------------------------- consulta de causas
#
# La Oficina Judicial Virtual (OJV) es el único lugar donde vive el estado de una causa, y está
# detrás de ClaveÚnica y de un captcha. Eso no se automatiza: se le dice a la persona qué hacer,
# con el enlace y los pasos. Esta parte del conector no inventa un resultado que no tiene.

JURISDICCIONES_POR_LETRA = {
    "C": ("civil", "Juzgado Civil"),
    "T": ("laboral", "Juzgado de Letras del Trabajo"),
    "L": ("laboral", "Juzgado de Letras del Trabajo"),
    "F": ("familia", "Juzgado de Familia"),
    "P": ("penal", "Juzgado de Garantía"),
    "I": ("penal", "Tribunal de Juicio Oral en lo Penal"),
    "V": ("familia", "Juzgado de Familia (violencia intrafamiliar)"),
    "S": ("civil", "Juzgado Civil (ejecutivo)"),
    "G": ("civil", "Juzgado Civil (gestión)"),
}

OJV = "https://oficinajudicialvirtual.pjud.cl"


def analizar_rit(rit: str) -> Dict[str, Any]:
    """Valida el formato de un Rol/RIT chileno y dice a qué jurisdicción apunta.

    La letra es una pista fuerte pero no universal: los tribunales no rotulan igual en todo el
    país, y el penal suele ir sin letra. Cuando no se puede afirmar, se dice.
    """
    limpio = (rit or "").strip().upper().replace(" ", "")
    if not limpio:
        return {"error": "hace falta el Rol/RIT (por ejemplo 'T-1234-2026' o 'Rol 12345-2026')"}

    letra: Optional[str] = None
    numero: Optional[int] = None
    anio: Optional[int] = None

    con_letra = re.match(r"^([A-Z])?[-–]?\s*(\d{1,6})[-–](\d{4})$", limpio)
    solo_rol = None if con_letra else re.match(r"^ROL?(\d{1,6})[-–](\d{4})$", limpio)
    if con_letra:
        letra, numero, anio = con_letra.group(1), int(con_letra.group(2)), int(con_letra.group(3))
    elif solo_rol:
        numero, anio = int(solo_rol.group(1)), int(solo_rol.group(2))
    else:
        return {
            "rit": rit,
            "valido": False,
            "error": (
                "el formato no calza con un Rol/RIT chileno. Se espera algo como 'C-1234-2026' "
                "(civil), 'T-1234-2026' (laboral), 'F-1234-2026' (familia) o 'Rol 12345-2026' "
                "(Corte). Revisá el número tal como sale en la carpeta del tribunal."
            ),
        }

    if anio is not None and not (1900 <= anio <= 2100):
        return {"rit": rit, "valido": False,
                "error": f"el año {anio} no parece de una causa: revisá el Rol/RIT"}

    jurisdiccion, tribunal = (None, None)
    advertencias: List[str] = []
    if letra:
        if letra in JURISDICCIONES_POR_LETRA:
            jurisdiccion, tribunal = JURISDICCIONES_POR_LETRA[letra]
        else:
            advertencias.append(
                f"la letra «{letra}» no está entre las que se conocen (C, T, L, F, P, I, V, S, G): "
                "confirmá la jurisdicción en la carpeta del tribunal"
            )
    else:
        advertencias.append(
            "el Rol va sin letra: suele ser Corte de Apelaciones, Corte Suprema o una causa penal "
            "de tribunal de garantía. La jurisdicción no se puede afirmar desde el número."
        )

    return {
        "rit": limpio,
        "valido": True,
        "letra": letra,
        "numero": numero,
        "anio": anio,
        "jurisdiccion": jurisdiccion,
        "tribunal_probable": tribunal,
        "advertencias": advertencias,
    }
