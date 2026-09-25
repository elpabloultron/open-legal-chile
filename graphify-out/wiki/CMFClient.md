# CMFClient

> 23 nodes · cohesion 0.13

## Key Concepts

- **CMFClient** (17 connections) — `cmf_connector.py`
- **.get_sanciones()** (8 connections) — `cmf_connector.py`
- **_parsear_sanciones_cmf()** (8 connections) — `cmf_connector.py`
- **.get_index_normas()** (6 connections) — `cmf_connector.py`
- **.search_sanciones()** (6 connections) — `cmf_connector.py`
- **Any** (6 connections)
- **_aviso()** (5 connections) — `cmf_connector.py`
- **.search_normativa()** (4 connections) — `cmf_connector.py`
- **._get_cache_path()** (3 connections) — `cmf_connector.py`
- **_coincide()** (3 connections) — `cmf_connector.py`
- **_texto_plano()** (3 connections) — `cmf_connector.py`
- **test_la_cmf_encuentra_por_materia()** (3 connections) — `tests/test_conectores_materia.py`
- **test_las_sanciones_del_cmf_se_extraen_de_la_tabla()** (2 connections) — `tests/test_conectores_materia.py`
- **test_cmf_valores()** (2 connections) — `tests/test_connectors.py`
- **.__init__()** (1 connections) — `cmf_connector.py`
- **Busca en el catálogo de normativa CMF por término, tipo (NCG, Circular,…** (1 connections) — `cmf_connector.py`
- **Indexa las resoluciones sancionatorias que la CMF publica por mercado. La…** (1 connections) — `cmf_connector.py`
- **Busca en el registro de sanciones de la CMF por número, entidad o materia.** (1 connections) — `cmf_connector.py`
- **HTML -> texto: sin etiquetas, sin entidades (&Oacute;), sin espacios repetidos.** (1 connections) — `cmf_connector.py`
- **Un vacío se explica: una lista vacía y muda se lee como «no existe», que es…** (1 connections) — `cmf_connector.py`
- **Coincidencia por palabra completa, no por trozo («banco» no debe encontrar…** (1 connections) — `cmf_connector.py`
- **Extrae N°, fecha, MATERIA y archivo de cada fila de la tabla de sanciones de la…** (1 connections) — `cmf_connector.py`
- **Descarga e indexa el listado de Resoluciones, NCG y Circulares de la CMF.** (1 connections) — `cmf_connector.py`

## Relationships

- [os](os.md) (8 shared connections)
- [test_conectores_materia.py](test_conectores_materia.py.md) (5 shared connections)
- [test_connectors.py](test_connectors.py.md) (4 shared connections)
- [mcp_server.py](mcp_server.py.md) (2 shared connections)

## Source Files

- `cmf_connector.py`
- `tests/test_conectores_materia.py`
- `tests/test_connectors.py`

## Audit Trail

- EXTRACTED: 51 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*