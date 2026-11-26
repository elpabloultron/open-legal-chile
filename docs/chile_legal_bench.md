# ChileLegalBench v1.0 — Metodología y Benchmark Reproducible

**ChileLegalBench v1.0** amplía la evaluación de Open Legal Chile desde 8 casos RAG hacia **105 casos deterministas y 100 % reproducibles offline** distribuidos en 7 categorías clave del ordenamiento jurídico chileno:

| Categoría | N.° Casos | Módulo Evaluado | Criterio Objetivo |
| :--- | :---: | :--- | :--- |
| `vigencia_normativa` | 10 | `bcn_connector.evaluar_vigencia_norma` | Vacancia legal (Ley N.° 21.719 / Ley N.° 21.855 al 15-10-2027), vigencia y derogación. |
| `plazos_procesales` | 15 | `calculadoras_chile.calcular_plazo_procesal` | Feriados Chile, días hábiles judiciales Art. 66 CPC (lun-sáb), administrativos Art. 25 Ley N.° 19.880 (lun-vie), laboral + suspensión DT y corridos. |
| `calculadoras_cuantias` | 15 | `calculadoras_chile` | Finiquito CT (tope 11 años / 90 UF, AFC, recargos Art. 168), días-multa (Leyes N.° 21.595 / 20.393), alimentos UTM (Ley N.° 14.908) y conversión UF/UTM/UTA. |
| `validacion_formal_cbr` | 15 | `entes_publicos`, `cbr_titles`, `privacidad_anonimizar` | RUT Módulo 11, mandato judicial Art. 7 CPC, cadena CBR decenal (10 años) y anonimización reversible Ley N.° 21.719. |
| `triage_enrutamiento` | 15 | `legal_open_jev.LegalOpenJevEngine` | Clasificación de materia/fuero y recomendación de <= 5 herramientas MCP en CPU local. |
| `grounding_doctrina_grafo` | 20 | `doctrina_connector` + `legal_graphify` | Recuperación FTS5, fichas de instituciones, enlaces fijados a Hugging Face y subgrafos `LegalGraphify`. |
| `anti_alucinacion_common_law` | 15 | `critique.verificar_citas_escrito` | Bloqueo estricto de Common Law (*punitive damages, discovery, subpoena, grand jury, at-will*) y artículos fuera de rango legal. |

---

## Ejecución reproducible

```bash
# Ejecutar los 105 casos desde CLI o Python
.venv/bin/python evals/chile_legal_bench.py

# O vía CLI unificado exportando JSON y Markdown
openlegal bench --json-out /tmp/clb.json --md-out /tmp/clb.md
```

---

## Línea base observada (`v2.0.0`, 100 % offline)

| Categoría | Aprobados | Total | Tasa | Latencia p95 |
| :--- | :---: | :---: | :---: | :---: |
| `vigencia_normativa` | 10 | 10 | 100,00 % | 17,516 ms |
| `plazos_procesales` | 15 | 15 | 100,00 % | 0,064 ms |
| `calculadoras_cuantias` | 15 | 15 | 100,00 % | 0,060 ms |
| `validacion_formal_cbr` | 15 | 15 | 100,00 % | 0,586 ms |
| `triage_enrutamiento` | 15 | 15 | 100,00 % | 0,039 ms |
| `grounding_doctrina_grafo` | 20 | 20 | 100,00 % | 433,348 ms |
| `anti_alucinacion_common_law` | 15 | 15 | 100,00 % | 0,361 ms |
| **Total Global (`p50 = 0,028 ms`, `p95 = 403,835 ms`)** | **105** | **105** | **100,0 %** | **403,835 ms** |

