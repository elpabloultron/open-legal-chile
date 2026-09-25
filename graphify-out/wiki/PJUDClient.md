# PJUDClient

> 17 nodes · cohesion 0.15

## Key Concepts

- **PJUDClient** (14 connections) — `pjud_connector.py`
- **test_pjud.py** (9 connections) — `tests/test_pjud.py`
- **.search_jurisprudencia()** (4 connections) — `pjud_connector.py`
- **.add_sentencia()** (3 connections) — `pjud_connector.py`
- **._init_db()** (3 connections) — `pjud_connector.py`
- **Any** (3 connections)
- **_strip_accents()** (3 connections) — `pjud_connector.py`
- **.__init__()** (2 connections) — `pjud_connector.py`
- **test_mcp_pjud_tool()** (2 connections) — `tests/test_pjud.py`
- **test_pjud_search_confianza_legitima()** (2 connections) — `tests/test_pjud.py`
- **test_pjud_search_sala_laboral()** (2 connections) — `tests/test_pjud.py`
- **test_pjud_search_tc()** (2 connections) — `tests/test_pjud.py`
- **Inicializa y sincroniza la base de datos local de jurisprudencia judicial.** (1 connections) — `pjud_connector.py`
- **Busca sentencias judiciales de la Corte Suprema, Cortes de Apelaciones y TC por…** (1 connections) — `pjud_connector.py`
- **Permite indexar nuevas sentencias judiciales.** (1 connections) — `pjud_connector.py`
- **Elimina tildes y diacríticos para búsqueda insensible a acentos.** (1 connections) — `pjud_connector.py`
- **Pruebas de jurisprudencia judicial y Tribunal Constitucional (PJUD / CS / TC).** (1 connections) — `tests/test_pjud.py`

## Relationships

- [os](os.md) (5 shared connections)
- [test_connectors.py](test_connectors.py.md) (2 shared connections)
- [mcp_server.py](mcp_server.py.md) (2 shared connections)
- [handle_tool_call](handle_tool_call.md) (2 shared connections)
- [case_intake.py](case_intake.py.md) (1 shared connections)

## Source Files

- `pjud_connector.py`
- `tests/test_pjud.py`

## Audit Trail

- EXTRACTED: 32 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*