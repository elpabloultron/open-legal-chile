# NotebookLMConnector

> 20 nodes · cohesion 0.15

## Key Concepts

- **NotebookLMConnector** (14 connections) — `notebooklm_connector.py`
- **._run_nlm()** (7 connections) — `notebooklm_connector.py`
- **Any** (6 connections)
- **.create_notebook()** (5 connections) — `notebooklm_connector.py`
- **._extract_json()** (5 connections) — `notebooklm_connector.py`
- **.list_notebooks()** (5 connections) — `notebooklm_connector.py`
- **.add_source()** (4 connections) — `notebooklm_connector.py`
- **.is_available()** (3 connections) — `notebooklm_connector.py`
- **test_notebooklm_availability()** (3 connections) — `tests/test_new_tools.py`
- **test_notebooklm_extract_json_resilience()** (3 connections) — `tests/test_new_tools.py`
- **test_notebooklm_input_validations()** (3 connections) — `tests/test_new_tools.py`
- **.__init__()** (1 connections) — `notebooklm_connector.py`
- **Agrega un archivo local (PDF, Markdown, texto) como fuente en un cuaderno.** (1 connections) — `notebooklm_connector.py`
- **Verifica si el binario de la CLI nlm está disponible en el sistema.** (1 connections) — `notebooklm_connector.py`
- **Extrae de forma tolerante un bloque JSON de la salida de la CLI (omitiendo…** (1 connections) — `notebooklm_connector.py`
- **Lista los cuadernos activos en la cuenta de NotebookLM con sus metadatos…** (1 connections) — `notebooklm_connector.py`
- **Crea un nuevo cuaderno de investigación en NotebookLM y retorna su ID y URL.** (1 connections) — `notebooklm_connector.py`
- **Verifica detección de la CLI nlm en el sistema.** (1 connections) — `tests/test_new_tools.py`
- **Verifica que el extractor de JSON tolere avisos de actualización o banners de…** (1 connections) — `tests/test_new_tools.py`
- **Verifica validación de argumentos vacíos en llamadas de NotebookLM.** (1 connections) — `tests/test_new_tools.py`

## Relationships

- [handle_tool_call](handle_tool_call.md) (4 shared connections)
- [🔌 4. Catálogo Exhaustivo de Herramientas MCP (74 Herramientas Oficiales)](🔌_4._Catálogo_Exhaustivo_de_Herramientas_MCP_74_Herramientas_Oficiales.md) (3 shared connections)
- [mcp_server.py](mcp_server.py.md) (1 shared connections)
- [os](os.md) (1 shared connections)

## Source Files

- `notebooklm_connector.py`
- `tests/test_new_tools.py`

## Audit Trail

- EXTRACTED: 38 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*