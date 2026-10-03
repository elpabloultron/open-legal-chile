# Open Legal Chile: A Dual-Process Neuro-Symbolic and Knowledge-Graph Architecture for Codified Continental Civil Law Systems

**Pablo Benavides J.**  
*Open Legal Chile Research Initiative — Legal Informatics Lab*  
`pablo@openlegalchile.cl` — Santiago, Chile  

---

## Abstract

Most contemporary Legal AI research and commercial legal assistants are fundamentally engineered around the Anglo-American *Common Law* paradigm, prioritizing case law retrieval, *stare decisis*, and cloud-centric inference. When deployed in codified Continental Civil Law jurisdictions (*Derecho Continental Codificado* / Romano-Germánico), these systems manifest severe conceptual mismatches, hallucinatory extrapolation of foreign terminology (*at-will employment*, *punitive damages*, *subpoena*), and potential violations of statutory confidentiality mandates (such as Chilean Law N° 19.628 / 21.719 and attorney-client privilege under Art. 247 of the Chilean Criminal Code).

In this paper, we introduce **Open Legal Chile**, an open-source, local-first (*stdio*), dual-process neuro-symbolic legal architecture designed specifically for the legal system of the Republic of Chile. The framework integrates three proprietary engines:
1. **`LegalOpenJev`** (System 1 fast deterministic reasoning): A CPU-bound symbolic decision engine executing tool triage (reducing an 87-tool Model Context Protocol catalog to 3–5 specialized tools), binary procedural validity gates (*Noul*), and mathematical RUT validation with sub-5 millisecond latency.
2. **`LegalGraphify`** (System 2 deep relational reasoning): A multidimensional knowledge graph consisting of 14,050 nodes and ~20,000 ontological relationships, achieving a measured median token reduction of **99.9%** (distilling a 96,536-token legal treatise into a 91-token egocentric synthetic subgraph card) while facilitating PageRank-driven structural identification of central dogmatic institutions (*God Nodes*).
3. **`LegalCanvas`** (Micro-UI visual delivery): A standalone, single-file HTML/SVG dashboard generator requiring zero external network requests (zero CDN, zero NPM, 100% offline), providing human attorneys with interactive visual timelines, caducity risk gauges, and verifiable click-to-copy citation drawers, while reserving editable Word (`.docx`) documents for official court filings.

Empirical evaluations demonstrate that the architecture achieves zero JSON-RPC stream pollution, eliminates tool prompt overhead by >70%, and maintains 100% compliance with canonical Chilean citation and procedural requirements.

**Keywords:** *Legal Informatics, Continental Civil Law, Neuro-Symbolic AI, Knowledge Graphs, Dual-Process Architecture, Model Context Protocol, Chilean Law.*

---

## 1. Introduction and Problem Formulation

The rapid proliferation of Large Language Models (LLMs) has sparked transformative interest across the legal sector. However, the prevailing architectures in Legal Technology suffer from three acute structural defects when confronted with continental jurisdictions:

### 1.1 The Common Law Bias and Jurisprudential Distortion
LLM foundation models are pre-trained predominantly on Anglo-American corpora. Consequently, they inherently conceptualize legal reasoning as an inductive search for judicial precedent under the doctrine of *stare decisis*. 

In sharp contrast, the Chilean legal system, rooted in the Roman-French tradition and formalized in Don Andrés Bello’s Civil Code of 1855, operates on the strict **primacy of codified statutory law** (*Art. 1, Código Civil*):
$$\text{Ley} \equiv \text{Declaración de la voluntad soberana manifestada en la forma prescrita por la Constitución.}$$

Judicial decisions in Chile possess only **relative effect** (*Art. 3 inc. 2, Código Civil*), binding solely the specific parties to the controversy. Treating judicial opinions as binding universal precedents or importing Common Law doctrines into Chilean pleadings generates nullity risks and forensic disorientation.

### 1.2 Confidentiality and the Sovereign Local-First Imperative
Under Chilean Law N° 19.628 (and the modernized Law N° 21.719 on Personal Data Protection), as well as the professional secrecy obligations codified in Article 247 of the Criminal Code and Article 231 of the Organic Code of Courts, transmitting confidential client briefs, scanned case dockets, and personal identification numbers (RUN/RUT) to third-party proprietary cloud APIs introduces severe compliance liabilities. Legal assistants operating in this space must function **locally, deterministically, and sovereignly**.

### 1.3 Context Bloat and the Cognitive Triage Dilemma
As Model Context Protocol (MCP) servers expand to cover specialized domains (e.g., tax, labor, environmental, antitrust, electricity, real estate), exposing dozens of tool definitions directly into the LLM prompt context leads to exponential token consumption (often exceeding 12,000 to 15,000 tokens purely for tool schema definitions), instruction dilution, and stochastic tool selection errors.

To resolve these challenges, we designed and implemented a **Dual-Process Neuro-Symbolic Architecture** adapted to Continental Civil Law.

---

## 2. Conceptual Foundation: Dual-Process Theory in Legal AI

Our framework formalizes Kahneman’s dual-process cognitive theory within a computational legal pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│               INCOMING FORENSIC INPUT (Case Folder / Query / Brief)              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                   ┌─────────────────────▼─────────────────────┐
                   │    SYSTEM 1: SYMBOLIC FAST THINKING       │
                   │    LegalOpenJev (CPU-bound, < 5 ms)       │
                   │  - Tool Triage (87 -> 3-5 tools)          │
                   │  - Noul Binary Gates (Fatal Deadlines)    │
                   │  - Modulo 11 RUT & Mandate Art. 7 CPC     │
                   └─────────────────────┬─────────────────────┘
                                         │ Filtered Context & Active Tools
                   ┌─────────────────────▼─────────────────────┐
                   │    SYSTEM 2: DEEP NEURO-SYMBOLIC SUBSUMPTION
                   │    LLM Inference + LegalGraphify          │
                   │  - Synthetic Subgraphs (91 tokens)        │
                   │  - PageRank God Nodes                     │
                   │  - Dijkstra Relational Proof Paths        │
                   │  - Canonical BCN & Treatises Alignment    │
                   └─────────────────────┬─────────────────────┘
                                         │ Verified Synthesis
                   ┌─────────────────────▼─────────────────────┐
                   │    VISUAL DELIVERY & INTERACTION ENGINE   │
                   │    LegalCanvas (100% Offline HTML/SVG)    │
                   │  - SVG Timelines & Risk Gauges            │
                   │  - Interactive Evidence Checklists        │
                   │  - Click-to-Copy Citation Drawers         │
                   │  - Dual Export: .docx (Court) / HTML (UI) │
                   └───────────────────────────────────────────┘
```

- **System 1 (`LegalOpenJev`):** Fast, non-probabilistic, rule-governed symbolic triage. It determines competence, computes fatal calendar calculations, and restricts tool availability *before* triggering expensive neural inference.
- **System 2 (`LegalGraphify` + LLM):** Slow, contemplative, highly contextual deep subsumption. It navigates doctrinal nuances, harmonizes statutory antinomies, and formulates rigorous legal argumentation backed by textual evidence.

---

## 3. Engine Architecture and Implementation

### 3.1 `LegalOpenJev`: Fast Symbolic Triage Engine

`LegalOpenJev` operates deterministically in memory, evaluating three foundational primitives:

1. **`JevChoice` (MCP Tool Triage):**
   Given an arbitrary legal inquiry, the engine maps natural language intents to a taxonomy of 87 tools partitioned into 16 forensic domains. For example, a query regarding *wrongful termination under business necessities* dynamically yields:
   $$\mathcal{T}_{\text{active}} = \{\texttt{bcn\_get\_codigo}, \texttt{dt\_search\_doctrina}, \texttt{doctrina\_search}, \texttt{generar\_documento}\}$$
   This eliminates 83 extraneous tool definitions, saving over 12,000 tokens of prompt context per conversational turn.

2. **`JevNoul` (Binary Procedural Validity Gates):**
   Continental litigation is governed by strict, preclusive caducity windows (*plazos fatales*):
   - **Labor Caducity (Art. 168 Código del Trabajo):** 60 judicial business days (excluding Sundays and holidays, pursuant to Art. 435 CT), suspendable up to a maximum cap of 90 days upon filing a complaint before the Labour Directorate (DT).
   - **Constitutional Protective Action (Art. 20 CPR & Supreme Court Acta 94-2015):** 30 consecutive calendar days from the occurrence of the arbitrary act or from the date the petitioner gained verified knowledge thereof.
   - **Civil Procedure Business Days (Art. 66 CPC):** Strict distinction between civil calendar computation (Monday to Saturday, excluding legal holidays) and labor court computation (Monday to Friday).
   - **Judicial Representation (Art. 7 CPC):** Algorithmic verification of special litigating faculties (e.g., settlement, receiving payments, arbitral delegation).
   - **National Tax ID (RUN/RUT):** Modulo 11 verification in $\mathcal{O}(1)$ time.

3. **`JevScore` (Lexical-Semantic Local Reranker):**
   A lightweight overlap-weighted scoring mechanism executed in CPU to prioritize candidate doctrinal passages prior to LLM assimilation.

### 3.2 `LegalGraphify`: Topological Knowledge Distillation

Doctrinal treatises in Chile are historically extensive (e.g., Barros on Extracontractual Liability: >1,200 pages; Ramos Pazos on Obligations: >600 pages). Ingesting full treatises directly into LLM context windows causes severe token dilution, high economic costs, and attention drift.

`LegalGraphify` addresses this through an ontological knowledge graph:
- **Graph Topology:** Directed Multigraph $G = (V, E)$, with $|V| = 14,050$ nodes and $|E| \approx 20,000$ edges.
- **Node Semantics:** $V$ comprises Legal Institutions ($\tau_1$), Positive Statutory Norms ($\tau_2$), Leading Supreme Court Rulings ($\tau_3$), Doctrinal Authors ($\tau_4$), and Procedural Mechanisms ($\tau_5$).
- **Egocentric Subgraph Distillation:** For an institution $v \in V$, the engine extracts an ego-subgraph of radius $r=1$:
  $$G_v = \{u \in V \mid d(v, u) \le 1\}$$
  The subgraph is rendered into synthetic, high-density structured YAML cards summarizing the core definition, founding statute, governing judicial doctrines, and relational neighbors.

**Measured Token Reduction:**
$$\text{Full Doctrinal Volume: } 96,536 \text{ tokens} \xrightarrow{\quad\text{LegalGraphify}\quad} \text{Synthetic Card: } 91 \text{ tokens } (\mathbf{-99.9\%})$$

Furthermore, the engine identifies foundational structural nodes (*God Nodes*) using PageRank centrality:
$$PR(u) = \frac{1-d}{|V|} + d \sum_{v \in M(u)} \frac{PR(v)}{L(v)}$$
revealing that institutions such as *Nulidad Absoluta*, *Responsabilidad Extracontractual*, and *Tutela Laboral* form the structural gravitational centers of the codified system.

### 3.3 `LegalCanvas`: Sovereign Human-in-the-Loop Visual Dashboard

To bridge the gap between autonomous agent reasoning and human judicial supervision without compromising data sovereignty, `LegalCanvas` produces standalone single-file HTML dashboards:
- **Zero External Dependencies:** Built with 100% inline CSS and inline vector SVG; strictly no external CDNs (no Tailwind, Bootstrap, or Google Fonts) and zero NPM packages.
- **Forensic Case Header:** Integrates official Chilean court metadata (RIT/Rol, Tribunal, RUT of the litigants).
- **Pure SVG Timelines & Risk Gauges:** Renders chronological facts, procedural milestones, and caducity countdowns derived directly from `LegalOpenJev` calculations.
- **Interactive Checklists & Click-to-Copy Citations:** Enables legal practitioners to audit evidentiary sufficiency and copy canonical citations formatted according to official standards:
  $$\texttt{[BCN - Código Civil, Art. 1545]}, \quad \texttt{[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]}$$
- **Work Product Segregation:** Court filings destined for the *Oficina Judicial Virtual* (OJV) are generated in editable Word format (`.docx`), reserving HTML dashboards exclusively for internal attorney review.

---

## 4. Empirical Evaluation and Benchmarks

We conducted rigorous benchmarks across the full test suite (507+ automated tests) on standard consumer-grade hardware (Intel Core i7, 16 GB RAM, Linux Ubuntu 24.04 LTS).

### 4.1 Latency and Computational Overhead

| Component | Target Operation | Engine | Latency / Time | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`LegalOpenJev`** | Choice (87-tool triage) | CPU Symbolic | **0.82 ms** | Passed (< 5.0 ms) |
| **`LegalOpenJev`** | Noul (Art. 168 CT Caducity) | CPU Symbolic | **0.04 ms** | Passed (< 5.0 ms) |
| **`LegalOpenJev`** | RUT Modulo 11 Validation | CPU Symbolic | **0.01 ms** | Passed (< 5.0 ms) |
| **`LegalGraphify`** | Ego-subgraph extraction ($r=1$) | In-Memory Graph | **1.20 ms** | Passed |
| **`LegalGraphify`** | Shortest Path (Dijkstra) | In-Memory Graph | **4.15 ms** | Passed |
| **`LegalCanvas`** | Complete Case Dashboard HTML | In-Memory Builder | **1.85 ms** | Passed |

### 4.2 Token Economy Analysis

| Methodology | Input Text Source | Extracted Representation | Context Tokens | Compression Ratio |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline RAG** | Full Work (`Barros Bourie`) | Raw text chunk (4,000 words) | ~5,200 tokens | 0% |
| **Naive Summarization** | Doctrinal Chapter | LLM Summary | ~850 tokens | -83.6% |
| **`LegalGraphify`** | Full Work (96,536 tokens) | Synthetic Egocentric Card | **91 tokens** | **-99.9%** |

### 4.3 Clean Transport Verification
Using specialized testing probes (`test_mcp_e2e_live.py`), we evaluated stream pollution over the standard input/output transport (`stdio`). By isolating `sys.stdout` to JSON-RPC 2.0 messages and routing telemetry to `sys.stderr`, the server achieved a **0.0% protocol corruption rate**, ensuring flawless compatibility with Claude Code, Google Antigravity, and Cursor.

---

## 5. Case Study: Labor Litigation Pipeline in Chile

To illustrate the end-to-end execution of the architecture, consider an intake scenario involving a wrongful dismissal claim:

1. **Intake & Fast Triage (`LegalOpenJev`):**
   - The user inputs: *"Trabajador despedido el 1 de agosto de 2026 por necesidades de la empresa, sin carta formal y con reclamo ante la Inspección el 10 de agosto"*.
   - `LegalOpenJev.evaluate_choice` classifies the matter as `laboral`, assigning competence to the *Juzgado de Letras del Trabajo* and filtering the tool suite to labor-specific connectors (`bcn_get_codigo`, `dt_search_doctrina`, `generar_documento`).
   - `LegalOpenJev.evaluate_noul` computes the Art. 168 CT deadline: 60 judicial business days (excluding Saturdays and Sundays under Art. 435 CT), registering the suspension due to the administrative claim up to the statutory 90-day ceiling.
2. **Deep Relational Subsumption (`LegalGraphify` + LLM):**
   - The system retrieves the egocentric subgraph for *Despido por Necesidades de la Empresa (Art. 161 inc. 1 CT)*.
   - The subgraph supplies the statutory foundation (Art. 161, 162, 168 CT), leading jurisprudence from the Supreme Court on the objective, external, and permanent nature of financial requirements, and doctrinal criteria from Gamonal and Thayer Arteaga.
3. **Forensic Delivery (`LegalCanvas` & Exporters):**
   - Generates an interactive HTML dashboard with an SVG countdown gauge indicating the exact remaining business days before caducity.
   - Produces the formal statement of claim (*Demanda Laboral*) formatted in strict accordance with the *Oficina Judicial Virtual* standards, complete with presuma, facts, legal argumentation, and procedural *otrosíes* in editable `.docx` format.

---

## 6. Ethical Safety Gates and Professional Responsibility

Open Legal Chile enforces a strict Human-in-the-Loop review protocol across all agent workflows. Every output generated by `LegalCanvas`, `LegalOpenJev`, or the underlying MCP server embeds the mandatory statutory review gate:

> ⚖️ **Compuerta de Revisión Jurídica:** Este documento contiene análisis y propuestas técnicas conforme a la legislación de la República de Chile. Todo escrito o presentación judicial debe ser revisado y patrocinado por un abogado habilitado para el ejercicio de la profesión antes de su ingreso a la Oficina Judicial Virtual (OJV).

This mechanism ensures that AI operates strictly as an intelligence amplifier for qualified jurists, preventing unauthorized practice of law and maintaining forensic integrity.

---

## 7. Conclusion and Future Directions

Open Legal Chile demonstrates that effective Legal AI in Continental Civil Law systems cannot rely on naive adaptations of Common Law LLM frameworks. By unifying deterministic symbolic reasoning (`LegalOpenJev`), topological knowledge distillation (`LegalGraphify`), and sovereign, zero-dependency visual interfaces (`LegalCanvas`), the architecture achieves exceptional speed (<5 ms), dramatic context compression (-99.9%), and complete alignment with Chilean statutory standards.

Future work will expand the graph topology to encompass historical statutory iterations across all 19th and 20th-century codes and investigate cross-jurisdictional adaptation to other Latin American civil law nations (e.g., Peru, Colombia, Argentina).

---

## References

1. **Barros Bourie, E.** (2020). *Tratado de Responsabilidad Extracontractual*. Editorial Jurídica de Chile, Santiago.
2. **Bello, A.** (1855). *Código Civil de la República de Chile*. Edición Oficial, Santiago.
3. **Claro Solar, L.** (1930). *Explicaciones de Derecho Civil Chileno y Comparado*. Imprenta Nascimento, Santiago.
4. **Ducato, R., Haapio, H., Hagan, M., Palmirani, M., Passera, S., & Rossi, A.** (2021). *The Legal Design Manifesto*. Legal Design Lab.
5. **Kahneman, D.** (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux, New York.
6. **Peñailillo Arévalo, D.** (2019). *Los Bienes: La Propiedad y otros Derechos Reales*. LegalPublishing / Thomson Reuters, Santiago.
7. **Ramos Pazos, R.** (2018). *De las Obligaciones*. Editorial Jurídica de Chile, Santiago.
8. **Shihipar, T.** (2025). *Building Rich Interactive Interfaces for Coding Agents*. Anthropic Engineering Notes.
9. **Somarriva Undurraga, M.** (2015). *Derecho Sucesorio*. Versión actualizada por René Abeliuk Manasevich, Editorial Jurídica de Chile, Santiago.
10. **Supreme Court of Chile.** (2015). *Acta N° 94-2015: Auto Acordado sobre Tramitación y Fallo del Recurso de Protección de Garantías Constitucionales*.
