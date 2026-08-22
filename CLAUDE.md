# Open Legal Chile — Guía de Desarrollo para Asistentes y Agentes (CLAUDE.md)

Este repositorio es una suite de inteligencia jurídica y servidor Model Context Protocol (MCP) nativo especializado en el **ordenamiento jurídico de la República de Chile** (*Civil Law* / Derecho Continental Codificado).

## 1. Principios Jurídicos Innegociables
* **Primacía de la Ley Escrita:** La Ley es la fuente primordial (Art. 1 Código Civil). Las sentencias tienen efecto relativo (Art. 3 inc. 2 Código Civil).
* **Prohibición de Términos de Common Law:** NUNCA usar conceptos del derecho anglosajón (*at-will, punitive damages, discovery, subpoena, grand jury, Title VII, OSHA*). Usar terminología procesal y sustantiva chilena (*necesidades de la empresa, finiquito, indemnización por años de servicio, fuero, daño moral, daño emergente, lucro cesante, otrosí, casación, reposición, apelación, SpA*).
* **Estándar de Citación Obligatorio:** Citar con brackets oficiales:
  - Normas: `[BCN - Código del Trabajo, Art. 161]` o `[BCN - Ley N° 21.643, Art. 2]`
  - Constitución: `[CPR 1980 - Art. 19 N° 24]`
  - Jurisprudencia Judicial: `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]`
  - Jurisprudencia Administrativa: `[Dictamen DT N° 1234/15 de 2024]` o `[Dictamen CGR N° E123456 (2024)]`
  - Regulatorio: `[Circular SII N° 45 (2023)]` o `[NCG CMF N° 461]`

---

## 2. Arquitectura de Módulos y Conectores

```
open-legal-chile/
├── mcp_server.py             # Servidor MCP estándar JSON-RPC 2.0 (13 herramientas forenses)
├── openlegal.py              # Consola CLI interactiva y comandos unificados
├── chat_engine.py            # Motor de chat multi-proveedor (Gemini, Claude, DeepSeek, OpenAI, Ollama)
├── critique.py               # Motor de crítica forense en 5 dimensiones
├── exporters.py              # Generador de escritos OJV (Ley N° 20.886) en HTML y Markdown
├── config.py                 # Gestor centralizado de configuración y variables .env
├── domain/                   # Modelos de dominio tipificados (dataclasses)
├── connectors/               # Deep module de registro unificado con caché SQLite
│   ├── registry.py           # StateRegistry unificado
│   └── __init__.py
├── bcn_connector.py          # Conector BCN Ley Chile (9 Códigos y leyes)
├── cgr_connector.py          # Conector Contraloría (Dictámenes y auditorías)
├── dt_connector.py           # Conector Dirección del Trabajo (Doctrina laboral)
├── pjud_connector.py         # Conector Jurisprudencia Judicial (Corte Suprema y TC)
├── cne_connector.py          # Conector Comisión Nacional de Energía
├── panel_expertos_connector.py # Conector Panel de Expertos Ley Eléctrica
├── cmf_connector.py          # Conector Comisión para el Mercado Financiero
├── sii_connector.py          # Conector Servicio de Impuestos Internos
├── ambiental_connector.py    # Conector SMA / SNIFA Ambiental
├── tdlc_connector.py         # Conector Libre Competencia TDLC
├── evals/                    # Benchmark de evaluación jurídica chilena
└── tests/                    # Test suite automatizada con pytest
```

---

## 3. Comandos de Validación y Testing

```bash
# Ejecutar toda la suite de pruebas unitarias e integración
python -m pytest tests/ -v

# Probar servidor MCP sobre stdio
python mcp_server.py

# Iniciar CLI interactivo
python openlegal.py

# Ejecutar benchmark de evaluación jurídica
```
