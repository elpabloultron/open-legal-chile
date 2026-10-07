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
├── mcp_server.py             # Servidor MCP JSON-RPC 2.0 sobre stdio: protocolo, perfiles y ensamblado (87 herramientas)
├── servidor/                 # Esquemas y despacho de las herramientas, un módulo por dominio
│   ├── conectores.py         # BCN, CGR, DT, CNE, Panel, CMF, SII, SMA, TDLC, PJUD
│   ├── corpus.py · forense.py · casos.py · ambiental.py · suite.py
├── openlegal.py              # CLI (openlegal mcp | doctor | instalar | integrar | …)
├── integraciones_harness.py  # Config MCP por harness (Claude Code/Desktop, Cursor, VS Code, Gemini, Codex, …)
├── diagnostico.py            # `openlegal doctor` / herramienta suite_doctor
├── recursos.py               # Ubica skills, agentes y AGENTS.md (repo o share/openlegal-chile instalado)
├── agents_runtime.py         # Runtime de agentes y exportación a subagentes de Claude Code
├── agents/                   # 19 agentes: *.json (fuente) y *.md (subagentes del plugin, generados)
├── .agents/skills/           # 18 skills (SKILL.md), compartidas por todos los harness
├── .claude-plugin/           # plugin.json (MCP por uvx + skills + agentes) y marketplace.json
├── gemini-extension.json     # Extensión de Gemini CLI
├── chat_engine.py · critique.py · exporters.py · config.py   # chat, crítica, escritos OJV, configuración y red
├── *_connector.py            # Conectores del Estado (BCN, CGR, DT, PJUD, CNE, Panel, CMF, SII, SMA, TDLC, …)
├── connectors/registry.py    # StateRegistry unificado con caché
├── domain/ · doctrina/ · data/   # modelos, corpus doctrinal y grafo LegalGraphify (viajan en el wheel)
├── graphify-doctrinal/      # grafo doctrinal de graphify: wiki y visualizadores que se publican en HF
├── graphify-out/            # grafo del CÓDIGO (local, no versionado; alcance en .graphifyignore)
├── scripts/                  # Ingestas, bump de versión, generador de agentes del plugin
├── evals/                    # Benchmark de evaluación jurídica chilena
└── tests/                    # Suite pytest (protocolo, esquemas portables, plugin, empaquetado, conectores…)
```

Al agregar o cambiar una herramienta: esquema y despacho en `servidor/<dominio>.py`, nombre en
`ORDEN_ORIGEN` de `mcp_server.py`. Al cambiar `agents/*.json`: `python scripts/generar_agentes_plugin.py`.
Al subir versión: `python scripts/bump_version.py <patch|minor|major>` (también actualiza el plugin
y la extensión de Gemini, que fijan la versión que lanza uvx).

---

## 3. Comandos de Validación y Testing

```bash
# Ejecutar toda la suite de pruebas unitarias e integración
python -m pytest tests/ -v

# Probar servidor MCP sobre stdio
python mcp_server.py

# Iniciar CLI interactivo
python openlegal.py

# Diagnóstico de la instalación
python openlegal.py doctor

# Plugin de Claude Code y extensión de Gemini
claude plugin validate .claude-plugin/plugin.json && claude plugin validate .claude-plugin/marketplace.json
python scripts/generar_agentes_plugin.py --check
npx -y @google/gemini-cli extensions validate .
```

## graphify (grafo del CÓDIGO, no del derecho)

`graphify-out/` es el grafo del código de la suite (módulos, herramientas MCP, conectores, pruebas)
que arma la CLI de terceros graphify. Es local y no se versiona: en las sesiones en la nube lo
instala y construye `.claude/hooks/graphify-sesion.sh` (~9 s, en segundo plano); en una máquina
propia, `uvx --from graphifyy==0.9.79 graphify update .`. Qué entra lo fija `.graphifyignore`.

No confundir con el grafo JURÍDICO (`data/legal_knowledge_graph.json`), que se consulta con las
herramientas MCP `graphify_*`, ni con `graphify-doctrinal/` (wiki y visualizadores que se publican
en Hugging Face). Una pregunta de derecho chileno sigue el protocolo de citas (`consulta_maestra`,
`cita_texto`): la CLI de graphify no sabe nada de normas.

Reglas:
- Pregunta sobre el código: si existe `graphify-out/graph.json`, primero `graphify query "<pregunta>"`;
  `graphify path "<A>" "<B>"` para relaciones y `graphify explain "<símbolo>"` para un nodo. Si no
  existe, se navega con Grep/Read.
- `graphify-out/GRAPH_REPORT.md`, solo para una revisión amplia de arquitectura.
- Después de modificar código, `graphify update .` (solo AST, sin costo de API; no ensucia git).
  Si se niega porque el grafo «se achicaría», es un `graphify-out/` de antes de `.graphifyignore`:
  borrarlo y volver a correr.
- No correr `graphify claude install` ni sus pares de Cursor/Antigravity: reescriben estas reglas.
