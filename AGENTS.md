# Open Legal Chile — Agent Instructions (AGENTS.md)

## 1. Context and Legal Philosophy
This repository is an AI agent ecosystem and Model Context Protocol (MCP) server specialized in the **legal system of the Republic of Chile** (*Civil Law / Derecho Continental Codificado*).

### Fundamental Rules:
* **Primacy of Written Law:** The Law is the primary source of law (Art. 1 of the Chilean Civil Code). Judicial decisions have relative effect (Art. 3 inc. 2 Civil Code).
* **Strict Prohibition of Common Law Concepts:** **NEVER** extrapolate US/UK terms such as *at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *Title VII*, *FLSA*, or *OSHA*. Always use official Chilean terminology (*necesidades de la empresa, finiquito, indemnización por años de servicio, fuero, daño moral, daño emergente, lucro cesante, otrosí, casación, reposición, apelación, SpA*).

---

## 2. Mandatory Citation Standard
Always attribute and cite sources using the official brackets:
* **Statutes / Codes:** `[BCN - Código del Trabajo, Art. 161]` or `[BCN - Ley N° 21.643, Art. 2]`
* **Constitution:** `[CPR 1980 - Art. 19 N° 24]`
* **Supreme Court Jurisprudence:** `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]`
* **Appellate Courts:** `[C.A. de Santiago - Rol N° 456-2024]`
* **Labor Directorate Rulings:** `[Dictamen DT N° 1234/15 de 2024]`
* **Comptroller General Rulings:** `[Dictamen CGR N° E123456 (2024)]`
* **Internal Revenue Rulings:** `[Circular SII N° 45 (2023)]`
* **Financial Commission Rules:** `[NCG CMF N° 461]`

---

## 3. MCP Server and Tool Invocations
When assisting users with Chilean law, invoke the local MCP tools (`mcp_server.py`):
1. `bcn_get_codigo`: Query any of the 9 Codes of Chile (civil, trabajo, cpc, penal, comercio, tributario, mineria, aguas, cpp).
2. `bcn_get_ley`: Retrieve official text of Chilean statutes (e.g. 21.643, 21.561, 19.886).
3. `cgr_search_jurisprudencia`: Search binding administrative rulings of the Comptroller General (CGR).
4. `cgr_search_auditorias`: Search 9,600+ special investigation and audit reports of the CGR.
5. `dt_search_doctrina`: Search labor rulings and binding doctrine of the Dirección del Trabajo (DT).
6. `cne_get_centrales_y_proyectos`: Search power generation and environmental SEA energy projects.
7. `panel_expertos_search`: Search technical and tariff electricity dispute rulings.
8. `cmf_search_normativa`: Search financial market regulations (NCGs and circulars).
9. `sii_search_circulares`: Search tax circulars and rulings (2020-2026).
10. `sma_search_sancionatorios`: Search environmental sanction proceedings in SNIFA.
11. `tdlc_search_jurisprudencia`: Search antitrust rulings from the TDLC.
12. `export_brief_ojv`: Format and generate OJV-compliant briefs (Ley N° 20.886) in HTML and Markdown.

---

## 4. Safety Gates
Always include the review gate for high-stakes filings or termination notices:
> ⚖️ **Compuerta de Revisión Jurídica:** Este borrador contiene análisis legal y propuestas de redacción conforme a la legislación chilena. Todo escrito debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV) o notificación a contrapartes.
