"""
Open Legal Chile — Suite de Pruebas Automatizadas para Nuevas Herramientas Forenses
Cubre:
1. ForensicOCREngine (forensic_ocr.py)
2. LegalDossierCompiler (pdf_dossier_compiler.py)
3. NotebookLMConnector (notebooklm_connector.py)
4. InfoProbidadClient (infoprobidad_connector.py)
5. LegalGraphBuilder / build_quick_graph (grafo_vinculos.py)
6. Integración en el Servidor MCP (mcp_server.py)
"""

import os
import sys
import tempfile
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pymupdf

from forensic_ocr import ForensicOCREngine
from pdf_dossier_compiler import LegalDossierCompiler
from notebooklm_connector import NotebookLMConnector
from infoprobidad_connector import InfoProbidadClient
from grafo_vinculos import LegalGraphBuilder, build_quick_graph
from mcp_server import handle_tool_call, TOOLS


# ==============================================================================
# 1. PRUEBAS: FORENSIC OCR ENGINE
# ==============================================================================

@pytest.fixture
def sample_native_pdf(tmp_path):
    """Crea un PDF sintético con texto judicial nativo para pruebas."""
    pdf_path = tmp_path / "sentencia_prueba.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    sample_text = (
        "CORTE SUPREMA DE JUSTICIA DE CHILE - ROL 12345-2025\n"
        "VISTOS Y CONSIDERANDO: Que la recurrente interpone recurso de protección "
        "fundado en la vulneración de las garantías constitucionales consagradas en el artículo 19 "
        "número 2 y número 24 de la Carta Fundamental de la República de Chile.\n"
        "SE RESUELVE: Acoger la acción deducida con expresa condenación en costas."
    )
    page.insert_textbox(pymupdf.Rect(50, 50, 545, 400), sample_text, fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_ocr_engine_native_extraction(sample_native_pdf):
    """Verifica extracción directa de texto digital en PDF."""
    engine = ForensicOCREngine()
    res = engine.extract_from_pdf(sample_native_pdf, start_page=1, end_page=1)
    assert "error" not in res
    assert res.get("total_pages_in_pdf") == 1
    assert res.get("processed_pages") == 1
    assert res.get("native_pages") == 1
    assert res.get("ocr_pages") == 0
    assert "CORTE SUPREMA" in res.get("full_text")
    assert "recurso de protección" in res.get("full_text")


def test_ocr_engine_force_ocr(sample_native_pdf):
    """Verifica la ejecución forzada del pipeline de OCR con PyMuPDF rendering."""
    engine = ForensicOCREngine()
    res = engine.extract_from_pdf(sample_native_pdf, start_page=1, end_page=1, force_ocr=True)
    assert "error" not in res
    assert res.get("ocr_pages") == 1
    assert res.get("native_pages") == 0
    assert len(res.get("pages")) == 1
    assert res["pages"][0]["method"] == "ocr"


def test_ocr_engine_invalid_inputs():
    """Verifica manejo robusto de rutas inexistentes y parámetros fuera de rango."""
    engine = ForensicOCREngine()
    # Archivo nulo o vacío
    res_none = engine.extract_from_pdf("")
    assert "error" in res_none

    # Archivo inexistente
    res_nonexistent = engine.extract_from_pdf("/tmp/archivo_inexistente_99999.pdf")
    assert "error" in res_nonexistent

    # Páginas fuera de rango
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_pdf = f.name
    doc = pymupdf.open()
    doc.new_page()
    doc.save(tmp_pdf)
    doc.close()

    try:
        res_overflow = engine.extract_from_pdf(tmp_pdf, start_page=10, end_page=12)
        assert "error" in res_overflow
        assert "excede el total" in res_overflow["error"]
    finally:
        if os.path.exists(tmp_pdf):
            os.unlink(tmp_pdf)


def test_mcp_ocr_tool(sample_native_pdf):
    """Verifica llamada a ocr_extract_pdf a través del dispatcher MCP."""
    res = handle_tool_call("ocr_extract_pdf", {
        "pdf_path": sample_native_pdf,
        "start_page": 1,
        "end_page": 1
    })
    assert isinstance(res, dict)
    assert "error" not in res
    assert res.get("total_pages_in_pdf") == 1


# ==============================================================================
# 2. PRUEBAS: LEGAL DOSSIER COMPILER
# ==============================================================================

@pytest.fixture
def sample_annex_files(tmp_path):
    """Genera anexos probatorios en PDF e imagen para compilar."""
    # Anexo PDF
    pdf_annex = tmp_path / "anexo_contrato.pdf"
    d = pymupdf.open()
    p = d.new_page(width=595, height=842)
    p.insert_textbox(pymupdf.Rect(50, 50, 500, 200), "ANEXO: CONTRATO DE PRESTACIÓN DE SERVICIOS", fontsize=14)
    d.save(str(pdf_annex))
    d.close()

    # Anexo Imagen PNG
    img_annex = tmp_path / "anexo_comprobante.png"
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 300, 200), 1)
    pix.clear_with(240)  # Fondo gris claro
    pix.save(str(img_annex))

    return str(pdf_annex), str(img_annex)


def test_dossier_compiler_basic(tmp_path):
    """Verifica compilación de escrito judicial en Markdown a PDF formal A4."""
    compiler = LegalDossierCompiler()
    out_pdf = tmp_path / "dossier_salida.pdf"
    md_content = (
        "# EN LO PRINCIPAL: DEMANDA CIVIL DE INDEMNIZACIÓN DE PERJUICIOS\n\n"
        "**S.J.L. EN LO CIVIL DE SANTIAGO (1°)**\n\n"
        "**JUAN PÉREZ GONZÁLEZ**, cédula de identidad N° 11.222.333-4, domiciliado en Santiago...\n\n"
        "## I. ANTECEDENTES DE HECHO\n"
        "1. Con fecha 1 de marzo de 2024, las partes suscribieron un contrato vinculante.\n\n"
        "## II. EL DERECHO\n"
        "Conforme a los artículos 1489 y 1545 del Código Civil, todo contrato legalmente celebrado es una ley para los contratantes."
    )

    res = compiler.compile(md_content, str(out_pdf))
    assert "error" not in res
    assert os.path.exists(str(out_pdf))
    assert res.get("total_pages") >= 1
    assert res.get("main_pages") >= 1
    assert res.get("annexes_count") == 0


def test_dossier_compiler_with_annexes(tmp_path, sample_annex_files):
    """Verifica ensamblaje de anexos probatorios (PDF e imagen) con separadores institucionales."""
    pdf_annex, img_annex = sample_annex_files
    compiler = LegalDossierCompiler()
    out_pdf = tmp_path / "expediente_completo.pdf"
    mobile_pdf = tmp_path / "preview_movil.pdf"

    md_content = "# ESCRITO PRINCIPAL: DENUNCIA ANTE MINISTERIO PÚBLICO\nRelación circunstanciada de los hechos."

    annexes = [
        {
            "num": "ANEXO N° 1",
            "title": "Contrato de Prestación de Servicios",
            "desc": "Instrumento privado suscrito ante Notario Público.",
            "path": pdf_annex
        },
        {
            "num": "ANEXO N° 2",
            "title": "Comprobante de Transferencia Bancaria",
            "desc": "Depósito acreditado en cuenta corriente institucional.",
            "path": img_annex
        }
    ]

    res = compiler.compile(
        markdown_content=md_content,
        output_pdf_path=str(out_pdf),
        annexes=annexes,
        mobile_preview_path=str(mobile_pdf)
    )

    assert "error" not in res
    assert os.path.exists(str(out_pdf))
    assert os.path.exists(str(mobile_pdf))
    assert res.get("annexes_count") == 2
    # El expediente final debe tener páginas principales + 2 separadores + 2 anexos
    assert res.get("total_pages") >= 5


def test_mcp_dossier_compiler_tool(tmp_path):
    """Verifica compilación a través del dispatcher MCP."""
    out_pdf = tmp_path / "mcp_dossier.pdf"
    res = handle_tool_call("compile_legal_dossier", {
        "markdown_content": "# Escrito Judicial Breve\nTexto de prueba.",
        "output_pdf_path": str(out_pdf)
    })
    assert isinstance(res, dict)
    assert "error" not in res
    assert os.path.exists(str(out_pdf))


# ==============================================================================
# 3. PRUEBAS: NOTEBOOKLM CONNECTOR
# ==============================================================================

def test_notebooklm_availability():
    """Verifica detección de la CLI nlm en el sistema."""
    nlm = NotebookLMConnector()
    # Si nlm está instalado, debe dar True
    available = nlm.is_available()
    assert isinstance(available, bool)


def test_notebooklm_extract_json_resilience():
    """Verifica que el extractor de JSON tolere avisos de actualización o banners de la CLI."""
    nlm = NotebookLMConnector()

    # Salida típica de nlm con aviso de versión
    raw_cli_output = (
        '[\n'
        '  {\n'
        '    "id": "adcb39f2-111c-4554-948a-0fed441a8428",\n'
        '    "title": "Investigación Universidad de Los Lagos",\n'
        '    "source_count": 2,\n'
        '    "updated_at": "2026-09-02T22:23:50Z"\n'
        '  }\n'
        ']\n\n'
        '🔔 Update available: 0.10.0 → 0.10.1. Run uv tool upgrade notebooklm-mcp-cli to update.\n'
    )

    extracted = nlm._extract_json(raw_cli_output)
    assert isinstance(extracted, list)
    assert len(extracted) == 1
    assert extracted[0]["id"] == "adcb39f2-111c-4554-948a-0fed441a8428"
    assert extracted[0]["title"] == "Investigación Universidad de Los Lagos"


def test_notebooklm_input_validations():
    """Verifica validación de argumentos vacíos en llamadas de NotebookLM."""
    nlm = NotebookLMConnector()
    assert "error" in nlm.create_notebook("")
    assert "error" in nlm.add_source("", "/tmp/test.pdf")
    assert "error" in nlm.query("", "pregunta")
    assert "error" in nlm.query("id_123", "")


def test_mcp_notebooklm_list_tool():
    """Verifica consulta de lista de cuadernos a través de la herramienta MCP."""
    res = handle_tool_call("notebooklm_list_notebooks", {})
    assert isinstance(res, dict)
    assert "cuadernos" in res
    assert isinstance(res["cuadernos"], list)


# ==============================================================================
# 4. PRUEBAS: INFOPROBIDAD CONNECTOR
# ==============================================================================

def test_infoprobidad_input_validation():
    """Verifica manejo de consultas vacías o inválidas."""
    client = InfoProbidadClient()
    res = client.get_declaracion("")
    assert "error" in res


def test_infoprobidad_parse_html_offline():
    """Verifica el parseo sintáctico de una declaración DIP mediante parse_html_string."""
    sample_html = """
    <html>
        <body>
            <h1>JUAN CARLOS MINISTRO DE ESTADO</h1>
            <dl>
                <dt>Institución:</dt>
                <dd>Ministerio de Obras Públicas</dd>
                <dt>Cargo:</dt>
                <dd>Subsecretario</dd>
                <dt>Fecha de Declaración:</dt>
                <dd>01/03/2026</dd>
            </dl>
            <h2>Bienes Inmuebles en Chile</h2>
            <table>
                <thead>
                    <tr><th>Comuna</th><th>Rol Avalúo</th><th>Avalúo Fiscal</th></tr>
                </thead>
                <tbody>
                    <tr><td>Las Condes</td><td>1234-56</td><td>$180.000.000</td></tr>
                    <tr><td>Providencia</td><td>7890-12</td><td>$95.000.000</td></tr>
                </tbody>
            </table>
            <h2>Vehículos Motorizados</h2>
            <table>
                <thead>
                    <tr><th>Tipo</th><th>Marca</th><th>Año</th><th>Avalúo</th></tr>
                </thead>
                <tbody>
                    <tr><td>Automóvil</td><td>Toyota</td><td>2022</td><td>$15.000.000</td></tr>
                </tbody>
            </table>
        </body>
    </html>
    """
    client = InfoProbidadClient()
    parsed = client.parse_html_string(sample_html, ident="123456")

    assert parsed.get("identificador") == "123456"
    assert "JUAN CARLOS" in parsed.get("declarante")
    assert parsed.get("total_secciones") >= 2
    assert "Bienes Inmuebles en Chile" in parsed.get("secciones")
    assert "Vehículos Motorizados" in parsed.get("secciones")

    inmuebles = parsed["secciones"]["Bienes Inmuebles en Chile"]
    assert len(inmuebles) == 2
    assert inmuebles[0].get("Comuna") == "Las Condes"
    assert inmuebles[0].get("Rol Avalúo") == "1234-56"

    metadatos = parsed.get("metadatos", {})
    assert metadatos.get("Institución") == "Ministerio de Obras Públicas"
    assert metadatos.get("Cargo") == "Subsecretario"


def test_mcp_infoprobidad_validation_tool():
    """Verifica manejo de errores por entrada vacía en la herramienta MCP."""
    res = handle_tool_call("infoprobidad_get_dip", {"query_or_url": ""})
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# 5. PRUEBAS: GRAFO DE VÍNCULOS
# ==============================================================================

def test_graph_builder_sanitization_and_mermaid():
    """Verifica sanitización de identificadores no alfanuméricos y numéricos."""
    builder = LegalGraphBuilder()

    # ID numérico (RUT o número)
    id1 = builder.add_node(76123456, "Inversiones Los Andes SpA", "sociedad")
    assert id1 == "id_76123456"

    # ID con caracteres especiales (puntos, guiones)
    id2 = builder.add_node("rut-11.222.333-4", "Representante Legal", "persona")
    assert "." not in id2 and "-" not in id2

    # Agregar arista con comillas y caracteres especiales
    builder.add_edge(id1, id2, 'Socio Fundador (100% "control")')

    graph_dict = builder.to_dict()
    assert graph_dict["total_nodes"] == 2
    assert graph_dict["total_edges"] == 1

    mermaid_code = builder.to_mermaid("Red de Prueba")
    assert "```mermaid" in mermaid_code
    assert "graph TD" in mermaid_code
    assert "classDef sociedad" in mermaid_code
    assert "classDef persona" in mermaid_code
    assert 'id_76123456["Inversiones Los Andes SpA"]' in mermaid_code
    assert "-->" in mermaid_code


def test_build_quick_graph_synonyms():
    """Verifica que build_quick_graph acepte sinónimos de campos ('origen', 'destino', 'rut')."""
    nodes = [
        {"rut": "99.888.777-K", "nombre": "Universidad Regional", "tipo": "organismo"},
        {"id": "fundacion_x", "label": "Fundación Desarrollo", "category": "sociedad"}
    ]
    edges = [
        {"origen": "99.888.777-K", "destino": "fundacion_x", "vinculo": "Convenio de Transferencia"}
    ]

    res = build_quick_graph(nodes, edges, title="Convenios Estatales")
    assert res["total_nodes"] == 2
    assert res["total_edges"] == 1
    assert "Convenio de Transferencia" in res["mermaid"]


def test_mcp_generar_grafo_tool():
    """Verifica la ejecución de generar_grafo_vinculos a través del dispatcher MCP."""
    nodes = [
        {"id": "minvu", "label": "MINVU Región de Los Lagos", "category": "organismo"},
        {"id": "ong1", "label": "Fundación Urbanismo Social", "category": "sociedad"}
    ]
    edges = [
        {"source": "minvu", "target": "ong1", "relation": "Convenio Asignación Directa"}
    ]
    res = handle_tool_call("generar_grafo_vinculos", {
        "nodes": nodes,
        "edges": edges,
        "title": "Red Caso Convenios"
    })
    assert isinstance(res, dict)
    assert res.get("total_nodes") == 2
    assert res.get("total_edges") == 1
    assert "mermaid" in res


# ==============================================================================
# 6. PRUEBAS: CATÁLOGO DEL SERVIDOR MCP
# ==============================================================================

def test_mcp_tools_catalog_complete():
    """Verifica que el catálogo TOOLS contenga las 24 herramientas oficiales registradas."""
    assert len(TOOLS) == 36
    tool_names = [t["name"] for t in TOOLS]

    expected_tools = [
        "bcn_get_codigo",
        "bcn_get_ley",
        "cgr_search_jurisprudencia",
        "cgr_search_auditorias",
        "dt_search_doctrina",
        "cne_get_centrales_y_proyectos",
        "panel_expertos_search",
        "cmf_search_normativa",
        "sii_search_circulares",
        "sma_search_sancionatorios",
        "tdlc_search_jurisprudencia",
        "pjud_search_jurisprudencia",
        "export_brief_ojv",
        "ocr_extract_pdf",
        "compile_legal_dossier",
        "infoprobidad_get_dip",
        "notebooklm_list_notebooks",
        "notebooklm_create_notebook",
        "notebooklm_add_source",
        "notebooklm_query",
        "generar_grafo_vinculos",
        "doctrina_search",
        "doctrina_get_institucion",
        "doctrina_list_obras"
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Herramienta '{tool}' falta en el catálogo TOOLS de mcp_server.py"


def test_mcp_unknown_tool():
    """Verifica que una herramienta no existente retorne un error controlado."""
    res = handle_tool_call("herramienta_fantasma", {})
    assert isinstance(res, dict)
    assert "error" in res
    assert "no encontrada" in res["error"]
