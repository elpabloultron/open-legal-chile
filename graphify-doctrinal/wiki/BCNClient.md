# BCNClient

> 31 nodes · cohesion 0.12

## Key Concepts

- **BCNClient** (27 connections) — `bcn_connector.py`
- **Any** (10 connections)
- **._fetch_xml()** (8 connections) — `bcn_connector.py`
- **.get_ley()** (8 connections) — `bcn_connector.py`
- **.get_norma()** (7 connections) — `bcn_connector.py`
- **._parse_norma_xml()** (7 connections) — `bcn_connector.py`
- **._get_cache_path()** (6 connections) — `bcn_connector.py`
- **.get_codigo_historico()** (6 connections) — `bcn_connector.py`
- **.get_ley_historica()** (6 connections) — `bcn_connector.py`
- **test_bcn_busqueda_avisa.py** (5 connections) — `tests/test_bcn_busqueda_avisa.py`
- **.get_articulo_ley()** (4 connections) — `bcn_connector.py`
- **.get_codigo()** (4 connections) — `bcn_connector.py`
- **.search()** (4 connections) — `bcn_connector.py`
- **test_bcn_parser.py** (4 connections) — `tests/test_bcn_parser.py`
- **test_lo_que_si_resuelve_no_lleva_aviso()** (3 connections) — `tests/test_bcn_busqueda_avisa.py`
- **test_concepto_que_no_cubre_avisa_en_vez_de_venir_vacio()** (2 connections) — `tests/test_bcn_busqueda_avisa.py`
- **test_parse_norma_xml()** (2 connections) — `tests/test_bcn_parser.py`
- **test_bcn_ley_chile()** (2 connections) — `tests/test_connectors.py`
- **.__init__()** (1 connections) — `bcn_connector.py`
- **Obtiene una ley chilena por su número oficial (ej. 21643).** (1 connections) — `bcn_connector.py`
- **Obtiene una norma chilena por su ID interno de BCN (ej. Códigos de la…** (1 connections) — `bcn_connector.py`
- **Obtiene un Código de la República (civil, trabajo, cpc, cpp, penal, comercio,…** (1 connections) — `bcn_connector.py`
- **Obtiene un artículo específico de una ley (ej. Ley 21643, Art. 1).** (1 connections) — `bcn_connector.py`
- **Obtiene una ley chilena en una versión temporal histórica específica (YYYY-MM-…** (1 connections) — `bcn_connector.py`
- **Obtiene un Código de la República en una versión temporal histórica específica…** (1 connections) — `bcn_connector.py`
- *... and 6 more nodes in this community*

## Relationships

- [os](os.md) (6 shared connections)
- [test_connectors.py](test_connectors.py.md) (4 shared connections)
- [case_intake.py](case_intake.py.md) (2 shared connections)
- [mcp_server.py](mcp_server.py.md) (2 shared connections)

## Source Files

- `bcn_connector.py`
- `tests/test_bcn_busqueda_avisa.py`
- `tests/test_bcn_parser.py`
- `tests/test_connectors.py`

## Audit Trail

- EXTRACTED: 70 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*