"""
Open Legal Chile — Conector y Motor de Búsqueda Doctrinal (Doctrina Jurídica Canónica Chilena)
Indexa y consulta tratados dogmáticos y manuales de derecho chileno estructurados en Markdown
de alta densidad de tokens, con búsqueda FTS5 (BM25) y concordancias legales/jurisprudenciales.
"""

import os
import sys
import re
import sqlite3
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DB_PATH = os.path.join(BASE_DIR, "doctrina.db")


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Inicializa la base de datos SQLite con tablas relacionales y FTS5."""
    conn = sqlite3.connect(db_path)
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
        concordancias TEXT,
        fallo_rector TEXT,
        filepath TEXT,
        tokens_aprox INTEGER
    );
    """)

    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS doctrina_fts USING fts5(
        institucion,
        definicion,
        contenido,
        concordancias,
        fallo_rector,
        area UNINDEXED,
        autor UNINDEXED,
        obra UNINDEXED,
        tokenize='unicode61'
    );
    """)

    conn.commit()
    return conn


def parse_doctrina_file(filepath: str) -> List[Dict[str, Any]]:
    """Parsea un archivo Markdown de doctrina token-optimized en fichas dogmáticas individuales."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Extraer metadatos de cabecera
    obra_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    obra = obra_match.group(1).strip() if obra_match else os.path.basename(filepath)

    meta_match = re.search(
        r"\*\*Tratadistas?:\*\*\s*([^|]+)\|\s*\*\*Área:\*\*\s*([^|]+)\|\s*\*\*Materia:\*\*\s*(.+)$",
        text,
        re.MULTILINE
    )
    if meta_match:
        autor = meta_match.group(1).strip()
        area = meta_match.group(2).strip()
        materia = meta_match.group(3).strip()
    else:
        autor = "Autor Desconocido"
        area = "General"
        materia = ""

    # Dividir por secciones '## 🏛️ ' o '## '
    secciones = re.split(r"\n##\s+(?:🏛️\s*)?", text)
    instituciones = []

    for sec in secciones[1:]:  # Omitir cabecera
        lines = sec.strip().split("\n")
        if not lines:
            continue
        titulo = lines[0].strip()
        cuerpo = "\n".join(lines[1:]).strip()

        # Extraer Definición Canónica
        def_match = re.search(
            r"\*\*Definición Canónica(?:\s*\([^)]+\))?:\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|\n\*|\Z)",
            cuerpo,
            re.DOTALL
        )
        definicion = def_match.group(1).strip() if def_match else ""

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
            "concordancias": concordancias,
            "fallo_rector": fallo_rector,
            "filepath": filepath,
            "tokens_aprox": tokens_aprox
        })

    return instituciones


def index_all_doctrina(doctrina_dir: str = DOCTRINA_DIR, db_path: str = DB_PATH) -> int:
    """Escanea el directorio de doctrina e indexa todos los archivos Markdown en SQLite FTS5."""
    if not os.path.exists(doctrina_dir):
        return 0

    conn = init_db(db_path)
    cursor = conn.cursor()

    # Limpiar tablas previas para reconstrucción limpia
    cursor.execute("DELETE FROM doctrina_instituciones;")
    cursor.execute("DELETE FROM doctrina_fts;")

    total_instituciones = 0

    for root, dirs, files in os.walk(doctrina_dir):
        # Excluir carpetas de trabajo en crudo
        if "doctrina_raw" in root:
            continue
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                filepath = os.path.join(root, f)
                try:
                    instituciones = parse_doctrina_file(filepath)
                    for inst in instituciones:
                        cursor.execute("""
                        INSERT INTO doctrina_instituciones 
                        (area, autor, obra, materia, institucion, definicion, contenido, concordancias, fallo_rector, filepath, tokens_aprox)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            inst["area"], inst["autor"], inst["obra"], inst["materia"],
                            inst["institucion"], inst["definicion"], inst["contenido"],
                            inst["concordancias"], inst["fallo_rector"], inst["filepath"],
                            inst["tokens_aprox"]
                        ))
                        rowid = cursor.lastrowid

                        cursor.execute("""
                        INSERT INTO doctrina_fts 
                        (rowid, institucion, definicion, contenido, concordancias, fallo_rector, area, autor, obra)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            rowid, inst["institucion"], inst["definicion"], inst["contenido"],
                            inst["concordancias"], inst["fallo_rector"], inst["area"],
                            inst["autor"], inst["obra"]
                        ))
                        total_instituciones += 1
                except Exception as e:
                    print(f"Error procesando {filepath}: {e}", file=sys.stderr)

    conn.commit()
    conn.close()
    return total_instituciones


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


def search_doctrina(
    query: str,
    area: Optional[str] = None,
    autor: Optional[str] = None,
    limit: int = 5,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Busca doctrina dogmática chilena utilizando FTS5 con ranking BM25.
    Permite filtrar por área (Civil, Laboral, Penal, etc.) y por autor.
    """
    if not os.path.exists(db_path):
        index_all_doctrina(db_path=db_path)

    conn = init_db(db_path)
    cursor = conn.cursor()

    # Limpieza básica del query para FTS5
    clean_query = re.sub(r'[^\w\s"áéíóúÁÉÍÓÚñÑ]', ' ', query).strip()
    if not clean_query:
        conn.close()
        return []

    # Construir tokens para MATCH FTS5
    words = clean_query.split()
    fts_query = " OR ".join([f'"{w}"' for w in words])

    filters = []
    params = []

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

    sql += " ORDER BY rank ASC LIMIT ?"
    params.append(limit)

    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        # Fallback a búsqueda LIKE en la tabla relacional si la sintaxis FTS falla
        like_sql = """
        SELECT 
            id, institucion, definicion, SUBSTR(contenido, 1, 300) as snippet_contenido,
            concordancias, fallo_rector, area, autor, obra, 0 as rank
        FROM doctrina_instituciones
        WHERE (institucion LIKE ? OR contenido LIKE ? OR definicion LIKE ?)
        """
        like_p = [f"%{clean_query}%", f"%{clean_query}%", f"%{clean_query}%"]
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
            "bm25_score": round(float(r[9]), 4) if len(r) > 9 else 0.0
        })

    conn.close()
    return results


def get_institucion(
    nombre_o_termino: str,
    area: Optional[str] = None,
    db_path: str = DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    Recupera la ficha doctrinal completa y detallada de una institución jurídica específica.
    """
    if not os.path.exists(db_path):
        index_all_doctrina(db_path=db_path)

    conn = init_db(db_path)
    cursor = conn.cursor()

    sql = """
    SELECT id, area, autor, obra, materia, institucion, definicion, contenido, concordancias, fallo_rector, filepath, tokens_aprox
    FROM doctrina_instituciones
    WHERE institucion LIKE ?
    """
    params = [f"%{nombre_o_termino}%"]

    if area:
        sql += " AND area LIKE ?"
        params.append(_normalize_area_filter(area))

    sql += " LIMIT 1;"
    cursor.execute(sql, params)
    row = cursor.fetchone()

    if not row:
        # Intento de búsqueda en FTS si no hubo match directo en título
        matches = search_doctrina(nombre_o_termino, area=area, limit=1, db_path=db_path)
        if matches:
            best_id = matches[0]["id"]
            cursor.execute("""
            SELECT id, area, autor, obra, materia, institucion, definicion, contenido, concordancias, fallo_rector, filepath, tokens_aprox
            FROM doctrina_instituciones WHERE id = ?
            """, (best_id,))
            row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "area": row[1],
        "autor": row[2],
        "obra": row[3],
        "materia": row[4],
        "institucion": row[5],
        "definicion": row[6],
        "contenido": row[7],
        "concordancias": row[8],
        "fallo_rector": row[9],
        "filepath": row[10],
        "tokens_aprox": row[11]
    }


def list_obras(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Lista las obras y tratados indexados con sus autores, áreas y cantidad de instituciones."""
    if not os.path.exists(db_path):
        index_all_doctrina(db_path=db_path)

    conn = init_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT area, autor, obra, COUNT(*) as num_instituciones, SUM(tokens_aprox) as total_tokens
    FROM doctrina_instituciones
    GROUP BY area, autor, obra
    ORDER BY area ASC, autor ASC;
    """)
    rows = cursor.fetchall()
    conn.close()

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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        total = index_all_doctrina()
        print(f"✅ Indexación completada: {total} instituciones dogmáticas indexadas en {DB_PATH}")
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
            print(f"Normas: {inst['concordancias']}")
            print(f"Fallo Rector: {inst['fallo_rector']}")
            print(f"\nContenido:\n{inst['contenido']}")
        else:
            print(f"❌ No se encontró institución para: {term}")
    else:
        print("Uso: python doctrina_connector.py [index | list | search <query> | institucion <nombre>]")
