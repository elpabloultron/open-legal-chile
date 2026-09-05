# Conectores Oficiales del Estado de Chile

Open Legal Chile integra **10 conectores oficiales** con fuentes primarias del ordenamiento jurídico chileno. Todos se consumen a través del servidor MCP (`mcp_server.py`) o de la CLI (`openlegal`), y cada resultado conserva su **procedencia oficial** (URL o identificador del organismo) para citación verificable conforme al estándar de [AGENTS.md](AGENTS.md).

## Tabla de Conectores y Herramientas MCP

| # | Conector | Módulo | Fuente | Herramienta(s) MCP |
|---|----------|--------|--------|--------------------|
| 1 | **BCN — Biblioteca del Congreso Nacional (Ley Chile)** | `bcn_connector.py` | `bcn.cl/leychile` (XML) | `bcn_get_codigo`, `bcn_get_ley` |
| 2 | **CGR — Contraloría General de la República** | `cgr_connector.py` | `contraloria.cl/apibusca` | `cgr_search_jurisprudencia`, `cgr_search_auditorias` |
| 3 | **DT — Dirección del Trabajo** | `dt_connector.py` | `dt.gob.cl` | `dt_search_doctrina` |
| 4 | **CNE — Comisión Nacional de Energía (Energía Abierta)** | `cne_connector.py` | `api.cne.cl` (JWT) | `cne_get_centrales_y_proyectos` |
| 5 | **Panel de Expertos de la Ley Eléctrica** | `panel_expertos_connector.py` | `panel.cl` | `panel_expertos_search` |
| 6 | **CMF — Comisión para el Mercado Financiero** | `cmf_connector.py` | `cmfchile.cl` | `cmf_search_normativa` |
| 7 | **SII — Servicio de Impuestos Internos** | `sii_connector.py` | `sii.cl` | `sii_search_circulares` |
| 8 | **SMA — Superintendencia del Medio Ambiente (SNIFA)** | `ambiental_connector.py` (clase `SMAClient`) | `snifa.sma.gob.cl` | `sma_search_sancionatorios` |
| 9 | **TDLC — Tribunal de Defensa de la Libre Competencia** | `tdlc_connector.py` | `tdlc.cl` | `tdlc_search_jurisprudencia` |
| 10 | **PJUD — Poder Judicial (CS/TC)** | `pjud_connector.py` | base local SQLite (`jurisprudencia_judicial.db`) | `pjud_search_jurisprudencia` |

Además, la herramienta forense `export_brief_ojv` (módulo `exporters.py`) genera escritos para la Oficina Judicial Virtual (Ley N° 20.886) en HTML, Markdown, texto plano y JSON.

## Estándar de un buen conector para Open Legal Chile

1. **Fuente primaria oficial** — datos provenientes del organismo estatal (API, índice abierto o XML oficial), nunca de repositorios no oficiales.
2. **Procedencia en cada resultado** — retornar identificador citable (N° de dictamen, rol, norma) y fecha de vigencia.
3. **Solo lectura** — herramientas de búsqueda y consulta; nada de escritura sobre sistemas del Estado.
4. **Degradación elegante** — ante fallo de red o ausencia de credenciales, retornar estructura vacía consistente o `{"error": ...}` sin romper la sesión.
5. **Caché local por directorio** — cada conector cachea en `<institucion>_cache/` para funcionamiento offline y ahorro de cuota.

## 🔑 Credenciales y Acceso a Datos Estatales

| Conector Oficial | ¿Requiere Clave / API Key? | Estado por Defecto |
|---|---|---|
| **BCN Ley Chile** | ❌ **No.** Consulta el XML oficial público sin clave ni registro. | 100% Libre y Operativo |
| **CGR Contraloría** | ❌ **No.** API de jurisprudencia administrativa abierta al público. | 100% Libre y Operativo |
| **DT Dirección del Trabajo** | ❌ **No.** Catálogo de dictámenes y doctrina laboral abierto. | 100% Libre y Operativo |
| **PJUD Corte Suprema / TC** | ❌ **No.** Base jurisprudencial indexada localmente. | 100% Libre y Operativo |
| **CMF Mercado Financiero** | ❌ **No.** Consulta web oficial de normas y circulares abierta. | 100% Libre y Operativo |
| **SII Tributario** | ❌ **No.** Índices de circulares e instrucciones públicas. | 100% Libre y Operativo |
| **SMA SNIFA Ambiental** | ❌ **No.** Sistema Nacional de Información de Fiscalización Ambiental abierto. | 100% Libre y Operativo |
| **TDLC Libre Competencia** | ❌ **No.** Sentencias públicas abiertas. | 100% Libre y Operativo |
| **Panel de Expertos** | ❌ **No.** Discrepancias y dictámenes del sector eléctrico abiertos. | 100% Libre y Operativo |
| **CNE Energía Abierta** | ❌ **No** para capacidad instalada y proyectos; opcional cuenta CNE para API privada. | 100% Libre y Operativo |

> 📌 **Aclaración clave sobre BCN Ley Chile:**
> **No necesitas pedir ni configurar ninguna API Key de la BCN.** Open Legal Chile utiliza la pasarela oficial de datos abiertos en XML de la Biblioteca del Congreso Nacional (`leychile.cl/Consulta/obtxml`), garantizando acceso irrestricto, libre y gratuito a todo el corpus normativo de la República de Chile.

## Cómo contribuir un conector nuevo

1. Crea `<institucion>_connector.py` con una clase cliente (`<Sigla>Client`) que implemente al menos un método `search_*(query, ...)`.
2. Registra la herramienta en el catálogo `TOOLS` de `mcp_server.py` y su despacho en `handle_tool_call`.
3. Agrega el cliente a `connectors/registry.py` (`search_all`) para que participe de la Búsqueda Jurídica Universal.
4. Documenta el conector en esta tabla y en `openlegal.manifest.json` (`dataConnectors`).
5. Agrega una prueba de integración en `tests/test_connectors.py` que verifique la estructura de datos retornada.
