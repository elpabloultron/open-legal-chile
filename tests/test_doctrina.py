"""
Open Legal Chile — Suite de Pruebas Unitarias para Doctrina Jurídica Canónica
Cubre:
1. Parser dogmático y extracción de metadatos (doctrina_connector.py y scripts/doctrina_parser.py)
2. Motor de Indexación SQLite FTS5 y BM25
3. Búsqueda y filtrado por área y tratadista
4. Recuperación de fichas institucionales completas
5. Herramientas MCP (doctrina_search, doctrina_get_institucion, doctrina_list_obras)
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from doctrina_connector import (
    init_db,
    parse_doctrina_file,
    index_all_doctrina,
    search_doctrina,
    get_institucion,
    list_obras,
    DB_PATH,
    DOCTRINA_DIR
)
from scripts.doctrina_parser import clean_and_optimize_markdown, calculate_token_compression
from mcp_server import handle_tool_call, TOOLS


# ==============================================================================
# 1. PRUEBAS: PARSER DOGMÁTICO Y EXTRACCIÓN DE METADATOS
# ==============================================================================

def test_parse_sample_doctrina_file(tmp_path):
    """Verifica que el parser extraiga autor, área, instituciones y concordancias correctamente."""
    sample_md = tmp_path / "prueba_doctrina.md"
    sample_md.write_text("""# TRATADO DE PRUEBA DOGMÁTICA
**Tratadista:** Jurista Ilustre | **Área:** Derecho Civil | **Materia:** Teoría General
> 💡 *Base Doctrinal Canónica de Alta Densidad.*

---

## 🏛️ Enriquecimiento sin Causa
**Definición Canónica:**  
Atribución patrimonial sin justificación jurídica legítima que impone la obligación de restituir.

**Requisitos Copulativos:**
1. Enriquecimiento de un patrimonio.
2. Empobrecimiento correlativo de otro.
3. Falta de causa legítima.

**Concordancias Legales:** `[BCN - Código Civil, Art. 1437]` `[BCN - Código Civil, Art. 2295]`  
**Criterio Jurisprudencial Rector:** `[CS - Rol N° 1.234-2021, Fecha: 10-05-2022]`
""", encoding="utf-8")

    instituciones = parse_doctrina_file(str(sample_md))
    assert len(instituciones) == 1
    inst = instituciones[0]
    assert inst["area"] == "Derecho Civil"
    assert inst["autor"] == "Jurista Ilustre"
    assert inst["institucion"] == "Enriquecimiento sin Causa"
    assert "Atribución patrimonial" in inst["definicion"]
    assert "Art. 1437" in inst["concordancias"]
    assert "Rol N° 1.234-2021" in inst["fallo_rector"]
    assert inst["tokens_aprox"] > 10


def test_doctrina_parser_cleaner():
    """Verifica la limpieza de ruido editorial y cálculo de métricas de compresión."""
    raw_text = """
    Página 123
    TRATADO DE DERECHO CIVIL
    Editorial Jurídica de Chile
    
    El concepto de nulidad absoluta en el Código Civil.
    
    Página 124
    """
    clean_text = clean_and_optimize_markdown(raw_text)
    assert "Página 123" not in clean_text
    assert "Editorial Jurídica de Chile" not in clean_text
    assert "nulidad absoluta" in clean_text

    stats = calculate_token_compression(raw_text, clean_text)
    assert stats["tokens_originales"] >= stats["tokens_optimizados"]
    assert stats["ahorro_porcentual"] >= 0


# ==============================================================================
# 2. PRUEBAS: INDEXACIÓN Y BÚSQUEDA FTS5 (BM25)
# ==============================================================================

@pytest.fixture
def temp_doctrina_db(tmp_path):
    """Crea una base de datos SQLite FTS5 aislada para pruebas unitarias."""
    db_file = tmp_path / "doctrina_test.db"
    # Indexar el directorio oficial de doctrina del proyecto en esta DB temporal
    total = index_all_doctrina(doctrina_dir=DOCTRINA_DIR, db_path=str(db_file))
    assert total >= 30
    return str(db_file)


def test_search_doctrina_bm25(temp_doctrina_db):
    """Verifica la búsqueda por relevancia FTS5 BM25 en materias civiles, penales y laborales."""
    # Buscar responsabilidad extracontractual
    res_civil = search_doctrina("culpa presunta hecho ajeno", area="Civil", db_path=temp_doctrina_db)
    assert len(res_civil) > 0
    assert any("Barros" in r["autor"] or "Ramos" in r["autor"] for r in res_civil)
    assert res_civil[0]["concordancias"] != ""

    # Buscar en penal
    res_penal = search_doctrina("legítima defensa agresión", area="Penal", db_path=temp_doctrina_db)
    assert len(res_penal) > 0
    assert "Cury" in res_penal[0]["autor"]

    # Buscar en laboral
    res_laboral = search_doctrina("tutela laboral indicios", area="Laboral", db_path=temp_doctrina_db)
    assert len(res_laboral) > 0
    assert "Gamonal" in res_laboral[0]["autor"]


def test_search_doctrina_by_autor(temp_doctrina_db):
    """Verifica el filtro por autor tratadista."""
    res = search_doctrina("recurso", autor="Maturana", db_path=temp_doctrina_db)
    assert len(res) > 0
    assert "Maturana" in res[0]["autor"]


def test_get_institucion_exact_and_fuzzy(temp_doctrina_db):
    """Verifica la recuperación exacta y aproximada de fichas institucionales."""
    # Caso 1: Búsqueda exacta de institución
    inst = get_institucion("Recurso de Protección", db_path=temp_doctrina_db)
    assert inst is not None
    assert "Recurso de Protección" in inst["institucion"]
    assert "Art. 20" in inst["concordancias"]
    assert "Cea Egaña" in inst["autor"]

    # Caso 2: Búsqueda aproximada / FTS
    inst_aprox = get_institucion("falta de servicio", area="Administrativo", db_path=temp_doctrina_db)
    assert inst_aprox is not None
    assert "Falta de Servicio" in inst_aprox["institucion"]
    assert "Bermúdez" in inst_aprox["autor"]

    # Caso 3: Búsqueda inexistente
    inexistente = get_institucion("institucion_inexistente_xyz_999", db_path=temp_doctrina_db)
    assert inexistente is None


def test_list_obras(temp_doctrina_db):
    """Verifica el listado consolidado de obras indexadas."""
    obras = list_obras(db_path=temp_doctrina_db)
    assert len(obras) >= 7
    areas = {o["area"] for o in obras}
    assert "Derecho Civil" in areas
    assert "Derecho Penal" in areas
    assert any("Trabajo" in a for a in areas)
    assert "Derecho Administrativo" in areas
    assert "Derecho Procesal" in areas
    assert "Derecho Constitucional" in areas


# ==============================================================================
# 3. PRUEBAS: INTEGRACIÓN EN EL SERVIDOR MCP (mcp_server.py)
# ==============================================================================

def test_mcp_tools_registration():
    """Verifica que las herramientas de doctrina estén debidamente expuestas en TOOLS."""
    tool_names = [t["name"] for t in TOOLS]
    assert "doctrina_search" in tool_names
    assert "doctrina_get_institucion" in tool_names
    assert "doctrina_list_obras" in tool_names
    assert len(TOOLS) == 36


def test_mcp_doctrina_search_call():
    """Verifica la invocación de doctrina_search vía el dispatcher de mcp_server."""
    res = handle_tool_call("doctrina_search", {"query": "clausula penal deudor", "area": "Civil"})
    assert "resultados" in res
    assert len(res["resultados"]) > 0
    primer_res = res["resultados"][0]
    assert "institucion" in primer_res
    assert "concordancias" in primer_res


def test_mcp_doctrina_get_institucion_call():
    """Verifica la invocación de doctrina_get_institucion vía el dispatcher de mcp_server."""
    res = handle_tool_call("doctrina_get_institucion", {"nombre": "Prescripción Extracontractual"})
    assert "error" not in res
    assert "Barros" in res["autor"]
    assert "2332" in res["concordancias"]


def test_mcp_doctrina_list_obras_call():
    """Verifica la invocación de doctrina_list_obras vía el dispatcher de mcp_server."""
    res = handle_tool_call("doctrina_list_obras", {})
    assert "obras_indexadas" in res
    assert len(res["obras_indexadas"]) >= 7


def test_mcp_doctrina_error_handling():
    """Verifica el manejo correcto de errores y parámetros faltantes."""
    # Sin query en search
    err_search = handle_tool_call("doctrina_search", {})
    assert "error" in err_search

    # Sin nombre en get_institucion
    err_inst = handle_tool_call("doctrina_get_institucion", {})
    assert "error" in err_inst

    # Institución inexistente
    err_not_found = handle_tool_call("doctrina_get_institucion", {"nombre": "termino_inexistente_12345"})
    assert "error" in err_not_found
