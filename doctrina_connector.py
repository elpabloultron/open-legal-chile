"""
Open Legal Chile — Conector y Motor de Búsqueda Doctrinal (Doctrina Jurídica Canónica Chilena)
Indexa y consulta tratados dogmáticos y manuales de derecho chileno estructurados en Markdown
de alta densidad de tokens, con búsqueda FTS5 (BM25) y concordancias legales/jurisprudenciales.
"""

import contextlib
import os
import re
import sqlite3
import sys
import threading
from typing import Any, Dict, Iterator, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DB_PATH = os.path.join(BASE_DIR, "doctrina.db")

_RO_TLS = threading.local()
_ESQUEMA_OK: Dict[str, Tuple[int, int, int, int]] = {}
_ESQUEMA_LOCK = threading.Lock()


def _huella_db(abs_path: str) -> Optional[Tuple[int, int, int, int]]:
    try:
        st = os.stat(abs_path)
    except OSError:
        return None
    try:
        wst = os.stat(abs_path + "-wal")
        w_mtime, w_size = (wst.st_mtime_ns, wst.st_size) if wst.st_size > 0 else (-1, -1)
    except OSError:
        w_mtime, w_size = -1, -1
    return (st.st_mtime_ns, st.st_size, w_mtime, w_size)


def _invalidar_cache_lectura(db_path: Optional[str] = None) -> None:
    abs_path = os.path.abspath(db_path or DB_PATH)
    with _ESQUEMA_LOCK:
        _ESQUEMA_OK.pop(abs_path, None)
    cache = getattr(_RO_TLS, "conns", None)
    if isinstance(cache, dict):
        entrada = cache.pop(abs_path, None)
        if entrada is not None:
            try:
                entrada[1].close()
            except Exception:
                pass


def _aplicar_pragmas_lectura(conn: sqlite3.Connection) -> None:
    for pragma in (
        "PRAGMA query_only=ON;",
        "PRAGMA mmap_size=67108864;",
        "PRAGMA cache_size=-16000;",
        "PRAGMA temp_store=MEMORY;",
    ):
        conn.execute(pragma)


def _conexion_lectura(db_path: Optional[str] = None) -> Optional[sqlite3.Connection]:
    """Devuelve una conexión SQLite RO reutilizable por hilo si `doctrina_instituciones` tiene datos."""
    abs_path = os.path.abspath(db_path or DB_PATH)
    huella = _huella_db(abs_path)
    if huella is None:
        _invalidar_cache_lectura(abs_path)
        return None

    cache: Optional[Dict[str, Tuple[Tuple[int, int, int, int], sqlite3.Connection]]] = None
    if os.name != "nt":
        cache = getattr(_RO_TLS, "conns", None)
        if cache is None:
            cache = {}
            _RO_TLS.conns = cache
        prev = cache.get(abs_path)
        if prev is not None and prev[0] == huella:
            return prev[1]
        if prev is not None:
            cache.pop(abs_path, None)
            try:
                prev[1].close()
            except Exception:
                pass

    conn = sqlite3.connect(abs_path, check_same_thread=False)
    try:
        _aplicar_pragmas_lectura(conn)
        with _ESQUEMA_LOCK:
            esquema_vigente = _ESQUEMA_OK.get(abs_path) == huella
        if not esquema_vigente:
            cur = conn.cursor()
            cols = [c[1] for c in cur.execute("PRAGMA table_info(doctrina_instituciones);").fetchall()]
            fts = cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='doctrina_fts';").fetchone()
            if not cols or "operativa_procesal" not in cols or not fts:
                conn.close()
                init_db(abs_path).close()
                huella = _huella_db(abs_path)
                if huella is None:
                    return None
                conn = sqlite3.connect(abs_path, check_same_thread=False)
                _aplicar_pragmas_lectura(conn)
                cur = conn.cursor()
            tiene = cur.execute("SELECT 1 FROM doctrina_instituciones LIMIT 1;").fetchone()
            if not tiene:
                conn.close()
                return None
            huella_actual = _huella_db(abs_path) or huella
            with _ESQUEMA_LOCK:
                _ESQUEMA_OK[abs_path] = huella_actual
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return None

    if cache is not None:
        cache[abs_path] = (_huella_db(abs_path) or huella, conn)
    return conn


@contextlib.contextmanager
def _usar_lectura(db_path: Optional[str] = None) -> Iterator[Optional[sqlite3.Connection]]:
    conn = _conexion_lectura(db_path)
    try:
        yield conn
    finally:
        if conn is not None and os.name == "nt":
            conn.close()


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Inicializa la base de datos SQLite con tablas relacionales y FTS5.

    Las rutas por defecto (DB_PATH, DOCTRINA_DIR) se leen en cada llamada y no al definir la
    función, para que las pruebas puedan apuntarlas a un directorio temporal con monkeypatch.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctrina_instituciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        autor TEXT NOT NULL,
        obra TEXT NOT NULL,
        materia TEXT,
        institucion TEXT NOT NULL,
        definicion TEXT,
        contenido TEXT NOT NULL,
        operativa_procesal TEXT,
        concordancias TEXT,
        fallo_rector TEXT,
        filepath TEXT,
        tokens_aprox INTEGER
    );
    """)

    # Verificar si la columna operativa_procesal existe en instalaciones previas
    cursor.execute("PRAGMA table_info(doctrina_instituciones);")
    cols = [col[1] for col in cursor.fetchall()]
    if cols and "operativa_procesal" not in cols:
        cursor.execute("ALTER TABLE doctrina_instituciones ADD COLUMN operativa_procesal TEXT;")

    # Recrear tabla FTS si no incluye la columna operativa_procesal
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='doctrina_fts';")
    fts_row = cursor.fetchone()
    if fts_row and "operativa_procesal" not in fts_row[0]:
        cursor.execute("DROP TABLE IF EXISTS doctrina_fts;")

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS doctrina_fts USING fts5(
        institucion,
        definicion,
        contenido,
        operativa_procesal,
        concordancias,
        fallo_rector,
        area UNINDEXED,
        autor UNINDEXED,
        obra UNINDEXED,
        tokenize='unicode61'
    );
    """)

    conn.commit()
    _invalidar_cache_lectura(db_path)
    return conn


_TITULOS_ESTRUCTURALES_IGNORADOS = frozenset({
    "",
    "texto del artículo",
    "texto del articulo",
    "contenido del artículo",
    "contenido del articulo",
    "resumen",
    "abstract",
    "palabras clave",
    "keywords",
    "normas y cuerpos legales citados",
    "instituciones y conceptos jurídicos relevantes",
    "instituciones y conceptos juridicos relevantes",
    "véase también",
    "vease tambien",
    "referencias",
    "bibliografía",
    "bibliografia",
    "docentes",
    "índice",
    "indice",
    "sumario",
    "introducción",
    "introduccion",
    "conclusión",
    "conclusion",
    "conclusiones",
    "metadatos",
    "ficha bibliográfica",
    "ficha bibliografica",
})


def _limpiar_titulo_seccion(titulo: str) -> str:
    """Elimina emojis/prefijos decorativos para evaluar si un encabezado es solo estructura."""
    limpio = re.sub(r"^[^\wáéíóúÁÉÍÓÚñÑ]+", "", (titulo or "").strip()).strip().lower()
    return re.sub(r"\s+", " ", limpio)


def _extraer_metadatos_cabecera(text: str, filepath: str) -> Tuple[str, str, str, str]:
    """Extrae obra, autor, área y materia soportando tratados canónicos, revistas y YAML."""
    obra_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    obra = obra_match.group(1).strip() if obra_match else os.path.basename(filepath)

    meta_match = re.search(
        r"\*\*Tratadistas?:\*\*\s*([^|]+)\|\s*\*\*Área:\*\*\s*([^|]+)\|\s*\*\*Materia:\*\*\s*(.+)$",
        text,
        re.MULTILINE,
    )
    if meta_match:
        return obra, meta_match.group(1).strip(), meta_match.group(2).strip(), meta_match.group(3).strip()

    autor = ""
    area = ""
    materia = ""

    # Frontmatter YAML opcional (--- ... ---)
    if text.startswith("---"):
        fm_end = text.find("\n---", 3)
        if fm_end != -1:
            fm = text[3:fm_end]
            m_a = re.search(r"^(?:autor|autores|author)\s*:\s*[\"']?([^\"'\n]+)[\"']?", fm, re.MULTILINE | re.IGNORECASE)
            m_ar = re.search(r"^(?:area|área|disciplina)\s*:\s*[\"']?([^\"'\n]+)[\"']?", fm, re.MULTILINE | re.IGNORECASE)
            m_m = re.search(r"^(?:materia|revista|subject)\s*:\s*[\"']?([^\"'\n]+)[\"']?", fm, re.MULTILINE | re.IGNORECASE)
            if m_a:
                autor = m_a.group(1).strip()
            if m_ar:
                area = m_ar.group(1).strip()
            if m_m:
                materia = m_m.group(1).strip()

    # Metadatos Markdown de revistas académicas (**Autor(es):** / **Revista:** / **Área:**)
    cabecera = text[:2500]
    if not autor:
        m_au = re.search(r"\*\*(?:Autores?|Tratadistas?|Escrito por):\*\*\s*([^\n|]+)", cabecera, re.IGNORECASE)
        if m_au:
            autor = m_au.group(1).strip().strip("*")
    if not area:
        m_ar = re.search(r"\*\*(?:Área|Disciplina|Rama):\*\*\s*([^\n|]+)", cabecera, re.IGNORECASE)
        if m_ar:
            area = m_ar.group(1).strip().strip("*")
    if not materia:
        m_mat = re.search(r"\*\*(?:Materia|Revista|Fuente):\*\*\s*([^\n|]+)", cabecera, re.IGNORECASE)
        if m_mat:
            materia = m_mat.group(1).strip().strip("*")

    # Inferir área desde la carpeta (doctrina/civil/..., doctrina/laboral/..., doctrina/academia_judicial/...)
    if not area:
        partes = [p.lower() for p in os.path.normpath(filepath).split(os.sep)]
        if "civil" in partes:
            area = "Derecho Civil"
        elif "laboral" in partes:
            area = "Derecho del Trabajo"
        elif "penal" in partes:
            area = "Derecho Penal"
        elif "procesal" in partes:
            area = "Derecho Procesal"
        elif "administrativo" in partes:
            area = "Derecho Administrativo"
        elif "constitucional" in partes:
            area = "Derecho Constitucional"
        elif "ambiental" in partes:
            area = "Derecho Ambiental"
        elif "academia_judicial" in partes:
            area = "Academia Judicial"
            if not autor:
                autor = "Academia Judicial de Chile"
        else:
            area = "General"

    return obra, (autor or "Autor Desconocido"), area, materia


def parse_doctrina_file(filepath: str) -> List[Dict[str, Any]]:
    """Parsea un archivo Markdown de doctrina token-optimized en fichas dogmáticas individuales."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    obra, autor, area, materia = _extraer_metadatos_cabecera(text, filepath)

    # Dividir por secciones '## 🏛️ ' o '## '
    secciones = re.split(r"\n##\s+(?:🏛️\s*)?", text)
    instituciones = []

    for sec in secciones[1:]:  # Omitir cabecera
        lines = sec.strip().split("\n")
        if not lines:
            continue
        titulo = lines[0].strip()
        cuerpo = "\n".join(lines[1:]).strip()

        # Descartar encabezados estructurales sin contenido institucional real (p. ej. revistas SciELO)
        if _limpiar_titulo_seccion(titulo) in _TITULOS_ESTRUCTURALES_IGNORADOS:
            continue
        if not titulo or len(cuerpo) < 30:
            continue

        # Extraer Definición Canónica
        def_match = re.search(
            r"\*\*Definición Canónica(?:\s*\([^)]+\))?:\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|\n\*|\Z)",
            cuerpo,
            re.DOTALL
        )
        definicion = def_match.group(1).strip() if def_match else ""

        # Extraer Operativa Procesal Forense si existe
        proc_match = re.search(
            r"\*\*Operativa Procesal Forense:\*\*\s*\n*(.*?)(?=\n\n\*\*|\n\*\*Concordancias|\n\*\*Criterio|\n---\Z|\Z)",
            cuerpo,
            re.DOTALL
        )
        operativa_procesal = proc_match.group(1).strip() if proc_match else ""

        # Extraer Concordancias Legales
        conc_match = re.search(r"\*\*Concordancias Legales:\*\*\s*(.+)", cuerpo)
        concordancias = conc_match.group(1).strip() if conc_match else ""

        # Extraer Criterios Jurisprudenciales
        fallo_match = re.search(r"\*\*Criterio Jurisprudencial Rector:\*\*\s*(.+)", cuerpo)
        fallo_rector = fallo_match.group(1).strip() if fallo_match else ""

        # Tokens aproximados
        tokens_aprox = int(len(cuerpo.split()) * 1.3)

        instituciones.append({
            "area": area,
            "autor": autor,
            "obra": obra,
            "materia": materia,
            "institucion": titulo,
            "definicion": definicion,
            "contenido": cuerpo,
            "operativa_procesal": operativa_procesal,
            "concordancias": concordancias,
            "fallo_rector": fallo_rector,
            "filepath": filepath,
            "tokens_aprox": tokens_aprox
        })

    # Si era un artículo de revista cuyos únicos subtítulos eran estructurales (Resumen/Texto del Artículo),
    # conservar una sola ficha limpia bajo el título real de la obra si tiene autor conocido y texto sustantivo.
    if not instituciones and autor != "Autor Desconocido" and len(text.strip()) >= 200:
        resumen_m = re.search(r"\n##\s+(?:[^\n]*?)Resumen\s*\n+(.*?)(?=\n##\s|\Z)", text, re.DOTALL | re.IGNORECASE)
        definicion_art = resumen_m.group(1).strip()[:600] if resumen_m else ""
        cuerpo_art = text[:4000].strip()
        instituciones.append({
            "area": area,
            "autor": autor,
            "obra": obra,
            "materia": materia,
            "institucion": obra[:160],
            "definicion": definicion_art,
            "contenido": cuerpo_art,
            "operativa_procesal": "",
            "concordancias": "",
            "fallo_rector": "",
            "filepath": filepath,
            "tokens_aprox": int(len(cuerpo_art.split()) * 1.3),
        })

    return instituciones


def _insertar_institucion(cursor: sqlite3.Cursor, inst: Dict[str, Any]) -> None:
    """Inserta una ficha en la tabla relacional y en el índice FTS5 con el mismo rowid."""
    cursor.execute("""
    INSERT INTO doctrina_instituciones 
    (area, autor, obra, materia, institucion, definicion, contenido, operativa_procesal, concordancias, fallo_rector, filepath, tokens_aprox)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        inst["area"], inst["autor"], inst["obra"], inst["materia"],
        inst["institucion"], inst["definicion"], inst["contenido"],
        inst["operativa_procesal"],
        inst["concordancias"], inst["fallo_rector"], inst["filepath"],
        inst["tokens_aprox"]
    ))
    rowid = cursor.lastrowid

    cursor.execute("""
    INSERT INTO doctrina_fts 
    (rowid, institucion, definicion, contenido, operativa_procesal, concordancias, fallo_rector, area, autor, obra)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        rowid, inst["institucion"], inst["definicion"], inst["contenido"],
        inst["operativa_procesal"],
        inst["concordancias"], inst["fallo_rector"], inst["area"],
        inst["autor"], inst["obra"]
    ))


def index_all_doctrina(doctrina_dir: Optional[str] = None, db_path: Optional[str] = None) -> int:
    """Escanea el directorio de doctrina e indexa todos los archivos Markdown en SQLite FTS5."""
    doctrina_dir = doctrina_dir or DOCTRINA_DIR
    if not os.path.exists(doctrina_dir):
        return 0

    conn = init_db(db_path)
    cursor = conn.cursor()

    # Limpiar tablas previas para reconstrucción limpia
    cursor.execute("DELETE FROM doctrina_instituciones;")
    cursor.execute("DELETE FROM doctrina_fts;")

    total_instituciones = 0

    for root, _dirs, files in os.walk(doctrina_dir):
        # Excluir carpetas de trabajo en crudo
        if "doctrina_raw" in root:
            continue
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                filepath = os.path.join(root, f)
                try:
                    instituciones = parse_doctrina_file(filepath)
                    for inst in instituciones:
                        _insertar_institucion(cursor, inst)
                        total_instituciones += 1
                except Exception as e:
                    print(f"Error procesando {filepath}: {e}", file=sys.stderr)

    conn.commit()
    conn.close()
    _invalidar_cache_lectura(db_path)
    return total_instituciones


def index_doctrina_file(
    filepath: str,
    db_path: Optional[str] = None,
    doctrina_dir: Optional[str] = None
) -> Dict[str, int]:
    """
    Indexa (o reindexa) un solo archivo Markdown en doctrina.db sin reconstruir el índice.

    Es lo que usa la ingesta de un documento: reindexar el corpus completo por cada archivo
    nuevo costaba segundos que se suman al grafo y no aportaba nada. Las fichas previas del
    mismo archivo se reemplazan (upsert por ruta), así que reingestar no duplica filas.

    Si la base no existe o está vacía (clon recién hecho), primero se indexa el corpus una vez:
    dejar la base con un solo documento haría que search_doctrina dejara de autoindexar el resto.
    """
    db_path = db_path or DB_PATH
    # Misma forma que produce os.walk sobre DOCTRINA_DIR (absoluto): así el upsert reemplaza
    # la fila que dejó una indexación completa en vez de duplicarla.
    filepath = os.path.abspath(filepath)

    if not _has_doctrina_db(db_path):
        index_all_doctrina(doctrina_dir=doctrina_dir, db_path=db_path)

    instituciones = parse_doctrina_file(filepath)

    conn = init_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM doctrina_instituciones WHERE filepath = ?;", (filepath,))
        previas = [r[0] for r in cursor.fetchall()]
        cursor.executemany("DELETE FROM doctrina_fts WHERE rowid = ?;", [(i,) for i in previas])
        cursor.execute("DELETE FROM doctrina_instituciones WHERE filepath = ?;", (filepath,))

        for inst in instituciones:
            _insertar_institucion(cursor, inst)

        cursor.execute("SELECT COUNT(*) FROM doctrina_instituciones;")
        total = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    _invalidar_cache_lectura(db_path)

    return {"indexadas": len(instituciones), "reemplazadas": len(previas), "total": total}


def _normalize_area_filter(area: str) -> str:
    """Normaliza y mapea sinónimos de áreas jurídicas chilenas para concordancia amplia."""
    a = area.lower().strip()
    if "laboral" in a or "trabajo" in a:
        return "%Trabajo%"
    if "civil" in a:
        return "%Civil%"
    if "penal" in a:
        return "%Penal%"
    if "admin" in a:
        return "%Administrativo%"
    if "const" in a:
        return "%Constitucional%"
    if "proc" in a:
        return "%Procesal%"
    return f"%{area}%"


def _has_doctrina_db(db_path: Optional[str] = None) -> bool:
    """Verifica si la base de datos doctrina.db existe y tiene al menos un registro."""
    with _usar_lectura(db_path) as conn:
        return conn is not None


def _item_to_institucion_dict(it: Dict[str, Any]) -> Dict[str, Any]:
    definicion = it.get("definicion", "")
    operativa = it.get("operativa_procesal", "")
    contenido = definicion
    if operativa:
        contenido = f"{definicion}\n\n**Operativa Procesal Forense:**\n{operativa}"
    return {
        "id": it.get("id"),
        "area": it.get("area", "General"),
        "autor": it.get("autor", "Autor Desconocido"),
        "obra": it.get("obra", ""),
        "materia": it.get("materia", ""),
        "institucion": it.get("institucion", ""),
        "definicion": definicion,
        "contenido": contenido,
        "operativa_procesal": operativa,
        "concordancias": it.get("concordancias", ""),
        "fallo_rector": it.get("fallo_rector", ""),
        "filepath": it.get("archivo", ""),
        "tokens_aprox": it.get("tokens_aprox", 0),
        "cita_oficial": f"[Doctrina - {it.get('autor')}, {it.get('obra')}, Institución: {it.get('institucion')}]",
        "fuente_huggingface": it.get("ruta_hf", "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile")
    }


def _search_doctrina_catalogo(
    query: str,
    area: Optional[str] = None,
    autor: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Búsqueda de respaldo en el catálogo en memoria de instituciones_lite.jsonl."""
    try:
        from online_library_sync import _obtener_catalogo_instituciones, _normalizar_para_buscar, _PALABRAS_VACIAS
    except ImportError:
        return []

    items, indice = _obtener_catalogo_instituciones()
    if not items:
        return []

    clean_query = _normalizar_para_buscar(query).lower().strip()
    words = [w for w in re.findall(r"\b\w{3,}\b", clean_query) if w not in _PALABRAS_VACIAS]
    if not words:
        words = clean_query.split()

    from collections import Counter
    scores: Counter = Counter()

    for w in words:
        for idx in indice.get(w, []):
            it = items[idx]
            inst_norm = _normalizar_para_buscar(it.get("institucion", "")).lower()
            mat_norm = _normalizar_para_buscar(it.get("materia", "")).lower()
            aut_norm = _normalizar_para_buscar(it.get("autor", "")).lower()
            sc = 2
            if w in inst_norm:
                sc += 10
            if w in mat_norm:
                sc += 5
            if w in aut_norm:
                sc += 15
            if clean_query in inst_norm or clean_query in aut_norm:
                sc += 25
            scores[idx] += sc

    area_filter = area.lower().strip() if area else None
    autor_filter = autor.lower().strip() if autor else None

    results: List[Dict[str, Any]] = []
    vistos_inst = set()

    for idx, sc in scores.most_common(limit * 5):
        it = items[idx]
        it_area = it.get("area", "")
        it_autor = it.get("autor", "")
        it_inst = it.get("institucion", "")

        if area_filter and area_filter not in it_area.lower():
            continue
        if autor_filter and autor_filter not in it_autor.lower():
            continue

        if it_inst in vistos_inst:
            continue
        vistos_inst.add(it_inst)

        definicion = it.get("definicion", "")
        snippet = definicion[:300] + ("..." if len(definicion) > 300 else "")

        results.append({
            "id": it.get("id", idx + 1),
            "institucion": it_inst,
            "definicion": definicion,
            "snippet": snippet,
            "concordancias": it.get("concordancias", ""),
            "fallo_rector": it.get("fallo_rector", ""),
            "area": it_area,
            "autor": it_autor,
            "obra": it.get("obra", ""),
            "operativa_procesal": it.get("operativa_procesal", ""),
            "bm25_score": round(float(sc), 4),
            "cita_oficial": f"[Doctrina - {it_autor}, {it.get('obra')}, Institución: {it_inst}]",
            "fuente_huggingface": it.get("ruta_hf", "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile")
        })
        if len(results) >= limit:
            break

    return results


def _get_institucion_catalogo(
    nombre_o_termino: str,
    area: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Recupera la institución desde el catálogo en memoria de instituciones_lite.jsonl."""
    try:
        from online_library_sync import _obtener_catalogo_instituciones, _normalizar_para_buscar
    except ImportError:
        return None

    items, _ = _obtener_catalogo_instituciones()
    if not items:
        return None

    term_norm = _normalizar_para_buscar(nombre_o_termino).lower().strip()
    area_filter = area.lower().strip() if area else None

    # 1. Búsqueda exacta
    for it in items:
        it_area = it.get("area", "")
        if area_filter and area_filter not in it_area.lower():
            continue
        inst_norm = _normalizar_para_buscar(it.get("institucion", "")).lower().strip()
        if inst_norm == term_norm:
            return _item_to_institucion_dict(it)

    # 2. Búsqueda por contención
    candidatos = []
    for it in items:
        it_area = it.get("area", "")
        if area_filter and area_filter not in it_area.lower():
            continue
        inst_norm = _normalizar_para_buscar(it.get("institucion", "")).lower().strip()
        if term_norm in inst_norm:
            candidatos.append(it)

    if candidatos:
        def _sort_key(it: Dict[str, Any]) -> Tuple[int, int, str]:
            archivo = it.get("archivo", "").lower()
            penalizar = 1 if ("apuntes" in archivo or "academia_judicial" in archivo or "manuales" in archivo) else 0
            return (penalizar, len(it.get("institucion", "")), it.get("institucion", ""))

        candidatos.sort(key=_sort_key)
        return _item_to_institucion_dict(candidatos[0])

    # 3. Búsqueda en materia o autor
    for it in items:
        it_area = it.get("area", "")
        if area_filter and area_filter not in it_area.lower():
            continue
        mat_norm = _normalizar_para_buscar(it.get("materia", "")).lower()
        if term_norm in mat_norm:
            return _item_to_institucion_dict(it)

    return None


def search_doctrina(
    query: str,
    area: Optional[str] = None,
    autor: Optional[str] = None,
    limit: int = 5,
    db_path: Optional[str] = None,
    hibrido: bool = False,
) -> List[Dict[str, Any]]:
    """
    Busca doctrina dogmática chilena utilizando FTS5 con ranking BM25.
    Con `hibrido=True` fusiona BM25 con similitud vectorial (`fastembed` / `sqlite-vec` / NumPy)
    mediante Reciprocal Rank Fusion (RRF), 100 % local y sin envío de datos a la nube.
    Permite filtrar por área (Civil, Laboral, Penal, etc.) y por autor.
    Si la base de datos local no existe o no tiene registros, consulta
    el catálogo en memoria de instituciones_lite.jsonl.
    """
    if hibrido:
        return search_doctrina_hibrida(query=query, area=area, autor=autor, limit=limit, db_path=db_path)
    db_path = db_path or DB_PATH

    # Limpieza básica del query para FTS5 antes de abrir o crear la base
    clean_query = re.sub(r'[^\w\s"áéíóúÁÉÍÓÚñÑ]', ' ', query).strip()

    with _usar_lectura(db_path) as conn:
        if conn is None:
            if os.path.exists(DOCTRINA_DIR) and any(f.endswith(".md") for _, _, fs in os.walk(DOCTRINA_DIR) for f in fs):
                index_all_doctrina(db_path=db_path)
            else:
                return _search_doctrina_catalogo(query, area=area, autor=autor, limit=limit)

    with _usar_lectura(db_path) as conn:
        if conn is None or not clean_query:
            return []

        cursor = conn.cursor()

        # Construir tokens para MATCH FTS5
        words = clean_query.split()
        fts_query = " OR ".join([f'"{w}"' for w in words])

        params: List[Any] = []

        sql = """
        SELECT 
            rowid,
            institucion,
            definicion,
            snippet(doctrina_fts, 2, '【', '】', '...', 25) as snippet_contenido,
            concordancias,
            fallo_rector,
            area,
            autor,
            obra,
            operativa_procesal,
            bm25(doctrina_fts) as rank
        FROM doctrina_fts
        WHERE doctrina_fts MATCH ?
        """
        params.append(fts_query)

        if area:
            sql += " AND area LIKE ?"
            params.append(_normalize_area_filter(area))
        if autor:
            sql += " AND autor LIKE ?"
            params.append(f"%{autor}%")

        sql += """
        ORDER BY
            CASE
                WHEN autor != 'Autor Desconocido' AND TRIM(COALESCE(definicion, '')) != '' THEN 0
                WHEN autor != 'Autor Desconocido' THEN 1
                ELSE 2
            END ASC,
            rank ASC
        LIMIT ?
        """
        params.append(limit)

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback a búsqueda LIKE en la tabla relacional si la sintaxis FTS falla
            like_sql = """
            SELECT 
                id, institucion, definicion, SUBSTR(contenido, 1, 300) as snippet_contenido,
                concordancias, fallo_rector, area, autor, obra, operativa_procesal, 0 as rank
            FROM doctrina_instituciones
            WHERE (institucion LIKE ? OR contenido LIKE ? OR definicion LIKE ? OR operativa_procesal LIKE ?)
            """
            like_p: List[Any] = [f"%{clean_query}%", f"%{clean_query}%", f"%{clean_query}%", f"%{clean_query}%"]
            if area:
                like_sql += " AND area LIKE ?"
                like_p.append(f"%{area}%")
            if autor:
                like_sql += " AND autor LIKE ?"
                like_p.append(f"%{autor}%")
            like_sql += " LIMIT ?"
            like_p.append(limit)
            cursor.execute(like_sql, like_p)
            rows = cursor.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "institucion": r[1],
            "definicion": r[2],
            "snippet": r[3],
            "concordancias": r[4],
            "fallo_rector": r[5],
            "area": r[6],
            "autor": r[7],
            "obra": r[8],
            "operativa_procesal": r[9] if len(r) > 9 else "",
            "bm25_score": round(float(r[10]), 4) if len(r) > 10 else 0.0,
            "cita_oficial": f"[Doctrina - {r[7]}, {r[8]}, Institución: {r[1]}]",
            "fuente_huggingface": "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile"
        })

    if not results:
        results = _search_doctrina_catalogo(query, area=area, autor=autor, limit=limit)

    return results


def get_institucion(
    nombre_o_termino: str,
    area: Optional[str] = None,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Recupera la ficha doctrinal completa y detallada de una institución jurídica específica.
    """
    db_path = db_path or DB_PATH
    with _usar_lectura(db_path) as conn:
        if conn is None:
            if os.path.exists(DOCTRINA_DIR) and any(f.endswith(".md") for _, _, fs in os.walk(DOCTRINA_DIR) for f in fs):
                index_all_doctrina(db_path=db_path)
            else:
                return _get_institucion_catalogo(nombre_o_termino, area=area)

    with _usar_lectura(db_path) as conn:
        if conn is None:
            return _get_institucion_catalogo(nombre_o_termino, area=area)
        cursor = conn.cursor()

        sql = """
        SELECT id, area, autor, obra, materia, institucion, definicion, contenido, operativa_procesal, concordancias, fallo_rector, filepath, tokens_aprox
        FROM doctrina_instituciones
        WHERE institucion LIKE ?
        """
        params = [f"%{nombre_o_termino}%"]

        if area:
            sql += " AND area LIKE ?"
            params.append(_normalize_area_filter(area))

        # Sin ORDER BY, el orden lo decidía el recorrido de archivos, que cambia entre plataformas (por
        # eso el CI fallaba sólo en Windows) y que, con el corpus ampliado, devolvía la sección de un
        # documento convertido en vez del tratado. Regla: primero la doctrina canónica, después el
        # nombre más limpio y alfabético — así la búsqueda devuelve lo mismo en cualquier plataforma.
        sql += (
            " ORDER BY"
            "   CASE WHEN filepath LIKE '%apuntes_orrego%' OR filepath LIKE '%academia_judicial%'"
            "             OR filepath LIKE '%manuales%' THEN 1 ELSE 0 END,"
            "   LENGTH(institucion) ASC, institucion ASC"
            " LIMIT 1;"
        )
        cursor.execute(sql, params)
        row = cursor.fetchone()

    if not row:
        # Intento de búsqueda en FTS fuera del contexto previo de lectura si no hubo match directo en título
        matches = search_doctrina(nombre_o_termino, area=area, limit=1, db_path=db_path)
        if matches:
            best_id = matches[0]["id"]
            with _usar_lectura(db_path) as conn:
                if conn is not None:
                    row = conn.cursor().execute("""
                    SELECT id, area, autor, obra, materia, institucion, definicion, contenido, operativa_procesal, concordancias, fallo_rector, filepath, tokens_aprox
                    FROM doctrina_instituciones WHERE id = ?
                    """, (best_id,)).fetchone()

    if not row:
        return _get_institucion_catalogo(nombre_o_termino, area=area)

    return {
        "id": row[0],
        "area": row[1],
        "autor": row[2],
        "obra": row[3],
        "materia": row[4],
        "institucion": row[5],
        "definicion": row[6],
        "contenido": row[7],
        "operativa_procesal": row[8],
        "concordancias": row[9],
        "fallo_rector": row[10],
        "filepath": row[11],
        "tokens_aprox": row[12],
        "cita_oficial": f"[Doctrina - {row[2]}, {row[3]}, Institución: {row[5]}]",
        "fuente_huggingface": "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile"
    }


def list_obras(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista las obras y tratados indexados con sus autores, áreas y cantidad de instituciones."""
    db_path = db_path or DB_PATH
    with _usar_lectura(db_path) as conn:
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT area, autor, obra, COUNT(*) as num_instituciones, SUM(tokens_aprox) as total_tokens
            FROM doctrina_instituciones
            GROUP BY area, autor, obra
            ORDER BY area ASC, autor ASC;
            """)
            rows = cursor.fetchall()
            if rows:
                return [
                    {
                        "area": r[0],
                        "autor": r[1],
                        "obra": r[2],
                        "num_instituciones": r[3],
                        "tokens_aprox": r[4]
                    }
                    for r in rows
                ]

    # Fallback al catálogo en memoria de instituciones_lite.jsonl
    try:
        from online_library_sync import _obtener_catalogo_instituciones
        items, _ = _obtener_catalogo_instituciones()
    except Exception:
        items = []

    if not items:
        return []

    from collections import defaultdict
    obras_map: Dict[Tuple[str, str, str], Dict[str, Any]] = defaultdict(lambda: {"count": 0, "tokens": 0})
    for it in items:
        area = it.get("area", "General")
        autor = it.get("autor", "Autor Desconocido")
        obra = it.get("obra", "Tratado General")
        obras_map[(area, autor, obra)]["count"] += 1
        obras_map[(area, autor, obra)]["tokens"] += it.get("tokens_aprox", 0)

    res = []
    for (area, autor, obra), stats in sorted(obras_map.items()):
        res.append({
            "area": area,
            "autor": autor,
            "obra": obra,
            "num_instituciones": stats["count"],
            "tokens_aprox": stats["tokens"]
        })
    return res


def indexar_doctrina_vectorial(
    db_path: Optional[str] = None,
    use_fastembed: Optional[bool] = None,
    batch_size: int = 256,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Construye un índice vectorial local dentro de `doctrina.db` (`doctrina_vectores` y, si
    `sqlite-vec` está instalado, tabla virtual `doctrina_vec0`) usando `vector_engine.SemanticEmbeddingEngine`
    (`fastembed` ONNX multilingüe cuando está habilitado, o proyección léxica determinista 100 % offline).
    """
    import time
    import numpy as np
    from vector_engine import SemanticEmbeddingEngine, _cargar_sqlite_vec

    inicio = time.perf_counter()
    db_path = db_path or DB_PATH
    if not _has_doctrina_db(db_path):
        index_all_doctrina(db_path=db_path)

    engine = SemanticEmbeddingEngine(use_fastembed=use_fastembed)
    con = init_db(db_path)
    vec0_ok = _cargar_sqlite_vec(con)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS doctrina_vectores (
            inst_id INTEGER PRIMARY KEY,
            dim INTEGER NOT NULL,
            backend TEXT NOT NULL,
            embedding BLOB NOT NULL
        );
        """
    )
    cur.execute("DELETE FROM doctrina_vectores;")

    sql_src = (
        "SELECT id, area, autor, obra, institucion, definicion, operativa_procesal "
        "FROM doctrina_instituciones ORDER BY id"
    )
    if max_rows is not None and max_rows > 0:
        sql_src += f" LIMIT {int(max_rows)}"
    filas = cur.execute(sql_src).fetchall()

    dim = int(engine.dim)
    vec0_creada = False
    if vec0_ok and filas:
        try:
            cur.execute("DROP TABLE IF EXISTS doctrina_vec0;")
            cur.execute(f"CREATE VIRTUAL TABLE doctrina_vec0 USING vec0(embedding float[{dim}]);")
            vec0_creada = True
        except sqlite3.Error:
            vec0_creada = False

    total = 0
    for i in range(0, len(filas), max(1, int(batch_size))):
        lote = filas[i: i + batch_size]
        textos = [
            f"{r[4] or ''}. {r[5] or ''} {r[6] or ''} ({r[1] or ''}, {r[2] or ''})".strip()[:800]
            for r in lote
        ]
        matriz = np.asarray(engine.encode_batch(textos), dtype=np.float32)
        if matriz.ndim == 2 and matriz.shape[1] != dim:
            dim = int(matriz.shape[1])
            if vec0_creada:
                cur.execute("DROP TABLE IF EXISTS doctrina_vec0;")
                cur.execute(f"CREATE VIRTUAL TABLE doctrina_vec0 USING vec0(embedding float[{dim}]);")
        for row_meta, vec in zip(lote, matriz, strict=True):
            inst_id = int(row_meta[0])
            blob = vec.astype(np.float32).tobytes()
            cur.execute(
                "INSERT OR REPLACE INTO doctrina_vectores (inst_id, dim, backend, embedding) VALUES (?, ?, ?, ?);",
                (inst_id, dim, str(engine.backend), blob),
            )
            if vec0_creada:
                cur.execute("INSERT INTO doctrina_vec0 (rowid, embedding) VALUES (?, ?);", (inst_id, blob))
            total += 1

    con.commit()
    con.close()
    _invalidar_cache_lectura(db_path)
    return {
        "indexadas": total,
        "dim": dim,
        "backend": str(engine.backend),
        "sqlite_vec_activo": vec0_creada,
        "segundos": round(time.perf_counter() - inicio, 3),
        "db_path": db_path,
    }


def search_doctrina_hibrida(
    query: str,
    area: Optional[str] = None,
    autor: Optional[str] = None,
    limit: int = 5,
    db_path: Optional[str] = None,
    use_fastembed: Optional[bool] = None,
    k_rrf: int = 60,
) -> List[Dict[str, Any]]:
    """
    Búsqueda híbrida de doctrina chilena: combina FTS5 BM25 con similitud vectorial coseno
    (`doctrina_vectores` / `sqlite-vec` si está indexado, o re-ranking semántico al vuelo sobre
    candidatos BM25) mediante Reciprocal Rank Fusion (RRF). 100 % local y soberana.
    """
    import numpy as np
    from vector_engine import SemanticEmbeddingEngine, _cargar_sqlite_vec

    db_path = db_path or DB_PATH
    # 1. Recuperación léxica BM25 (amplia para permitir reordenamiento RRF)
    bm25_candidatos = search_doctrina(
        query=query,
        area=area,
        autor=autor,
        limit=max(20, int(limit) * 4),
        db_path=db_path,
        hibrido=False,
    )
    engine = SemanticEmbeddingEngine(use_fastembed=use_fastembed)
    q_vec = np.asarray(engine.encode(query), dtype=np.float32)

    sem_ranking: List[Tuple[int, float]] = []
    por_id: Dict[int, Dict[str, Any]] = {int(d["id"]): dict(d) for d in bm25_candidatos if d.get("id") is not None}

    # 2. Recuperación vectorial si `doctrina_vectores` existe en `doctrina.db`
    if _has_doctrina_db(db_path):
        con = init_db(db_path)
        vec0_ok = _cargar_sqlite_vec(con)
        cur = con.cursor()
        tiene_tabla = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='doctrina_vectores';"
        ).fetchone()
        if tiene_tabla:
            # Preferir KNN nativo `sqlite-vec` si no hay filtros y `doctrina_vec0` está disponible
            uso_vec0 = False
            if vec0_ok and not area and not autor:
                tiene_v0 = cur.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='doctrina_vec0';"
                ).fetchone()
                if tiene_v0:
                    try:
                        top_knn = cur.execute(
                            "SELECT rowid, distance FROM doctrina_vec0 WHERE embedding MATCH ? ORDER BY distance LIMIT ?;",
                            (q_vec.tobytes(), max(20, int(limit) * 4)),
                        ).fetchall()
                        sem_ranking = [(int(r[0]), max(0.0, 1.0 - float(r[1]))) for r in top_knn]
                        uso_vec0 = bool(sem_ranking)
                    except sqlite3.Error:
                        uso_vec0 = False
            if not uso_vec0:
                sql_v = (
                    "SELECT v.inst_id, v.embedding FROM doctrina_vectores v "
                    "JOIN doctrina_instituciones d ON d.id = v.inst_id WHERE 1=1"
                )
                v_params: List[Any] = []
                if area:
                    sql_v += " AND d.area LIKE ?"
                    v_params.append(_normalize_area_filter(area))
                if autor:
                    sql_v += " AND d.autor LIKE ?"
                    v_params.append(f"%{autor}%")
                filas_v = cur.execute(sql_v, v_params).fetchall()
                ids_v: List[int] = []
                vecs_v: List[np.ndarray] = []
                for iid, blob in filas_v:
                    arr = np.frombuffer(blob, dtype=np.float32)
                    if arr.shape == q_vec.shape:
                        ids_v.append(int(iid))
                        vecs_v.append(arr)
                if vecs_v:
                    mat = np.vstack(vecs_v)
                    sims = mat @ q_vec
                    top_idx = np.argsort(-sims)[: max(20, int(limit) * 4)]
                    sem_ranking = [(ids_v[int(idx)], float(sims[int(idx)])) for idx in top_idx]

            # Hidratar fichas recuperadas solo por vía vectorial
            faltan_ids = [iid for iid, _ in sem_ranking if iid not in por_id]
            if faltan_ids:
                placeholders = ",".join("?" for _ in faltan_ids)
                for row in cur.execute(
                    f"SELECT id, institucion, definicion, SUBSTR(contenido, 1, 300), concordancias, "  # nosec B608
                    f"fallo_rector, area, autor, obra, operativa_procesal "
                    f"FROM doctrina_instituciones WHERE id IN ({placeholders});",
                    faltan_ids,
                ):
                    por_id[int(row[0])] = {
                        "id": int(row[0]),
                        "institucion": row[1],
                        "definicion": row[2],
                        "snippet": row[3],
                        "concordancias": row[4],
                        "fallo_rector": row[5],
                        "area": row[6],
                        "autor": row[7],
                        "obra": row[8],
                        "operativa_procesal": row[9] or "",
                        "bm25_score": 0.0,
                        "cita_oficial": f"[Doctrina - {row[7]}, {row[8]}, Institución: {row[1]}]",
                        "fuente_huggingface": "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile",
                    }
        con.close()

    # 3. Fallback sin tabla `doctrina_vectores`: re-ranking semántico al vuelo sobre candidatos BM25
    if not sem_ranking and bm25_candidatos:
        textos_c = [
            f"{d.get('institucion', '')}. {d.get('definicion', '')} {d.get('snippet', '')}".strip()[:600]
            for d in bm25_candidatos
        ]
        mat_c = np.asarray(engine.encode_batch(textos_c), dtype=np.float32)
        sims_c = mat_c @ q_vec
        pares = [
            (int(d["id"]), float(sims_c[idx]))
            for idx, d in enumerate(bm25_candidatos)
            if d.get("id") is not None
        ]
        pares.sort(key=lambda x: -x[1])
        sem_ranking = pares

    # 4. Fusión Reciprocal Rank Fusion (RRF)
    rrf_scores: Dict[int, float] = {}
    sem_map = {iid: sc for iid, sc in sem_ranking}
    for rank_idx, d in enumerate(bm25_candidatos, 1):
        if d.get("id") is None:
            continue
        iid = int(d["id"])
        rrf_scores[iid] = rrf_scores.get(iid, 0.0) + 1.0 / (k_rrf + rank_idx)
    for rank_idx, (iid, _sc) in enumerate(sem_ranking, 1):
        rrf_scores[iid] = rrf_scores.get(iid, 0.0) + 1.0 / (k_rrf + rank_idx)

    ordenados = sorted(rrf_scores.items(), key=lambda kv: (-kv[1], -sem_map.get(kv[0], 0.0), kv[0]))
    salida: List[Dict[str, Any]] = []
    for iid, rrf_sc in ordenados[: max(1, int(limit))]:
        item = por_id.get(iid)
        if not item:
            continue
        item = dict(item)
        item["rrf_score"] = round(rrf_sc, 5)
        item["semantic_score"] = round(float(sem_map.get(iid, 0.0)), 4)
        item["modo_busqueda"] = f"hibrido_rrf:{engine.backend}"
        salida.append(item)
    return salida


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        total = index_all_doctrina()
        print(f"✅ Indexación completada: {total} instituciones dogmáticas indexadas en {DB_PATH}")
    elif len(sys.argv) > 1 and sys.argv[1] == "index-vec":
        res_v = indexar_doctrina_vectorial()
        print(f"✅ Indexación vectorial completada: {res_v}")
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        obras = list_obras()
        print(f"📚 Obras Indexadas ({len(obras)}):")
        for o in obras:
            print(f" - [{o['area']}] {o['obra']} ({o['autor']}): {o['num_instituciones']} instituciones (~{o['tokens_aprox']} tokens)")
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        q = sys.argv[2]
        res = search_doctrina(q)
        print(f"🔎 Resultados para '{q}' ({len(res)}):")
        for r in res:
            print(f" • [{r['area']}] {r['institucion']} ({r['autor']})")
            print(f"   Snippet: {r['snippet']}")
            print(f"   Normas: {r['concordancias']}")
    elif len(sys.argv) > 2 and sys.argv[1] == "institucion":
        term = sys.argv[2]
        inst = get_institucion(term)
        if inst:
            print(f"🏛️ {inst['institucion']} ({inst['autor']} - {inst['area']})")
            print(f"Definición: {inst['definicion']}")
            if inst.get("operativa_procesal"):
                print(f"\n⚖️ Operativa Procesal Forense:\n{inst['operativa_procesal']}")
            print(f"Normas: {inst['concordancias']}")
            print(f"Fallo Rector: {inst['fallo_rector']}")
            print(f"\nContenido:\n{inst['contenido']}")
        else:
            print(f"❌ No se encontró institución para: {term}")
    else:
        print("Uso: python doctrina_connector.py [index | list | search <query> | institucion <nombre>]")
