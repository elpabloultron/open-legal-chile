# DTClient

> 15 nodes · cohesion 0.20

## Key Concepts

- **DTClient** (16 connections) — `dt_connector.py`
- **.get_index_ordinarios()** (7 connections) — `dt_connector.py`
- **.search_dictamenes()** (7 connections) — `dt_connector.py`
- **.get_dictamen_content()** (6 connections) — `dt_connector.py`
- **_aviso()** (5 connections) — `dt_connector.py`
- **Any** (4 connections)
- **_coincide()** (3 connections) — `dt_connector.py`
- **._get_cache_path()** (3 connections) — `dt_connector.py`
- **test_dt_laboral()** (2 connections) — `tests/test_connectors.py`
- **.__init__()** (1 connections) — `dt_connector.py`
- **Descarga y parsea el contenido completo, materias y doctrina de un dictamen de…** (1 connections) — `dt_connector.py`
- **Busca dictámenes y ordinarios de la DT por número o por tema. La búsqueda por…** (1 connections) — `dt_connector.py`
- **Un vacío se explica: una lista vacía y muda se lee como «no existe», que es…** (1 connections) — `dt_connector.py`
- **Coincidencia por palabra completa: buscar «acta» no debe encontrar «contacto».** (1 connections) — `dt_connector.py`
- **Descarga e indexa el listado maestro de Ordinarios y Dictámenes de la DT.** (1 connections) — `dt_connector.py`

## Relationships

- [os](os.md) (7 shared connections)
- [test_connectors.py](test_connectors.py.md) (4 shared connections)
- [test_conectores_materia.py](test_conectores_materia.py.md) (4 shared connections)
- [mcp_server.py](mcp_server.py.md) (2 shared connections)

## Source Files

- `dt_connector.py`
- `tests/test_connectors.py`

## Audit Trail

- EXTRACTED: 37 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*