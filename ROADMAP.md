# 🗺️ Hoja de Ruta Oficial (ROADMAP 2026-2027)

> **Visión:** Posicionar a Open Legal Chile como la infraestructura soberana de código abierto de referencia para la inteligencia jurídica y el protocolo MCP en el Derecho Chileno (*Civil Law* Codificado).

---

## 📍 Q1-Q2 2026: Consolidación del Protocolo MCP
* [x] **10 Conectores Oficiales del Estado de Chile:** BCN Ley Chile, CGR, DT, CNE, Panel de Expertos, CMF, SII, SMA, TDLC y PJUD/CS/TC.
* [x] **Servidor MCP JSON-RPC 2.0:** Compatible con Antigravity, Claude Code, Cursor, OpenCode y Codex (87 herramientas).
* [x] **Conector PJUD / OJV:** Jurisprudencia de la Corte Suprema (unificación laboral, constitucional, civil) y Tribunal Constitucional con base local SQLite.
* [x] **Motor de Crítica Forense en 5 Dimensiones:** Auditoría de legalidad y doctrina con prompt auditor activo.
* [x] **CI/CD & Monitor de APIs Estatales:** Integración continua en GitHub Actions (Python 3.10–3.14).
* [x] **Publicación en PyPI:** Paquete oficial `pip install openlegal-chile` con workflow automatizado.
* [x] **Registro en Smithery:** Publicado oficialmente en [Smithery.ai](https://smithery.ai/servers/pablobenavidesjorquera/open-legal-chile) con las herramientas MCP catalogadas.

---

## 📍 Q3-Q4 2026: Espacios de Casos, Motor Vectorial y Rendimiento
* [x] **Catálogo de 18 habilidades jurídicas chilenas:** laboral, litigación, inmobiliario, administrativo, energía, ambiental, contratos, corporativo, forense, probidad, expedientes, investigación IA, grado, mesa, vigilante, clínica, propiedad-datos y dogmático.
* [x] **Espacio de Trabajo Local de Casos (`casos/<id_caso>/`):** Ingesta automática de antecedentes judiciales, conversión canónica a Markdown (RAE/ASALE y BCN), sincronización ontológica con subgrafos locales LegalGraphify y enriquecimiento con el dataset de Hugging Face.
* [x] **Motor Vectorial Local Integrado:** Embeddings densos locales y motor híbrido (Dense Similitud Coseno + Sparse FTS5 BM25 con Reciprocal Rank Fusion - RRF) para los 9 Códigos de la República y la Constitución Política en `codigos_vectorial.db`, 100 % local y offline ($0 costo de inferencia).
* [x] **Optimización de Rendimiento e Infraestructura:** Paralelización de suite de pruebas con `pytest-xdist` (<60s) y pipeline de pre-calentamiento programado de caché (`openlegal cache warm`).
* [ ] **Expansión a 100 Casos en *Chilean Legal Eval*:** Benchmark ampliado con derecho tributario y libre competencia.

---

## 📍 2027: Soberanía Forense y Profundidad Doctrinal Nacional
* [ ] **Peritaje Doctrinal y Jurisprudencial de Corte:** Análisis automático de líneas contradictorias de la Corte Suprema y criterios de unificación en recursos de nulidad y casación.
* [ ] **Extensión de Embeddings Locales a Doctrina Completa:** Cobertura de las 11.858 instituciones dogmáticas de `doctrina.db` con búsqueda híbrida vectorial local.
