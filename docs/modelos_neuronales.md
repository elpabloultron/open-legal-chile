# Motores Neuronales Locales de Open Legal Chile (`v2.1.0`)

Open Legal Chile incorpora dos redes neuronales entrenadas directamente sobre el ordenamiento y la doctrina chilena, ejecutadas **100 % en local (`Zero Data Leak`)** en NumPy puro —sin requerir GPU, Internet ni librerías pesadas para inferencia— y empaquetadas de forma segura sin `pickle` (`allow_pickle=False`).

> **Regla de no-alucinación:** Tanto el reranking semántico como las predicciones de enlaces de `LegalGNN` generan hipótesis de búsqueda y cobertura estructural. Toda norma sugerida **debe** validarse con su texto literal vigente mediante `cita_texto` en BCN Ley Chile antes de incorporarla en un escrito judicial o informe.

---

## 1. Bi-Encoder Contrastivo + Reranker Neuronal Chileno (`neural_retriever.py`)

Entrenado con pérdida contrastiva **InfoNCE** + cabezal MLP monotónico pairwise de 10 rasgos jurídicos (`scripts/entrenar_embeddings_chile.py`) sobre `14 612` pares (`13 151` train / `1 461` held-out test) derivados de `doctrina_fichas.parquet`, aristas sustantivas de `grafo_aristas.parquet` y pares de sinonimia chilena (*autodespido ↔ Art. 171 CT, daño moral por rebote ↔ Art. 2329 CC, precario ↔ Art. 2195 CC, invalidación ↔ Art. 53 Ley N.° 19.880, Ley Karin ↔ Ley N.° 21.643, etc.*). El reranker usa *title-dropout* (`p = 0,5`) y pesos no negativos para priorizar coincidencia semántica, TF-IDF legal y sinonimia por sobre la repetición literal del título.

* **Artefacto empaquetado:** `data/modelos/chile_embed_v1.npz` (`2,740 MB`, 384 dimensiones L2-normalizadas compatibilizadas con `vector_engine.py` y `doctrina_connector.py`).
* **Desactivación / fallback opcional:** `OPENLEGAL_NEURAL_EMBEDDINGS=0` restaura la proyección léxica determinista.
* **Escalamiento GPU opcional (`ONNX`):** si se exporta un Transformer multilingüe/español fine-tuned con `scripts/entrenar_transformer_hf.py` hacia `~/.openlegal/models/embed_onnx` (o `OPENLEGAL_ONNX_EMBED_DIR`), el motor lo detecta y usa automáticamente vía `onnxruntime`.

### Resultados Held-Out (`1 461` consultas no vistas)

| Modelo / Etapa | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
| :--- | ---: | ---: | ---: | ---: |
| Baseline léxico (proyección 384-d) | 81,45 % | 90,14 % | 92,81 % | 0,8534 |
| **`ChileNeuralEmbed v1` (Bi-Encoder)** | **83,64 %** | **94,73 %** | **97,33 %** | **0,8858** |
| **`ChileNeuralRerank v1` (Top-20 → Top-1)** | **93,63 %** | — | — | **0,9548** |

---

## 2. `LegalGNN` Link Predictor (`legal_gnn.py`)

Red neuronal relacional sobre el subgrafo sustantivo limpio de `LegalGraphify` (`rango_norma_plausible = TRUE`, `es_sustantiva = TRUE`, grado sustantivo `>= 2`: **`31 600` nodos**, **`172 608` aristas relacionales únicas** en 3 familias: `norma`, `juris` y `estruct`).

* **División estricta sin fuga:** `85 %` train (`146 716` aristas) / `15 %` held-out test (`25 892` aristas). Las matrices normalizadas relacionales (2 saltos + 32 componentes espectrales SVD + embeddings de `ChileNeuralEmbedder`) se calculan exclusivamente sobre el subgrafo de entrenamiento.
* **Encoder / Decoder:** MLP relacional (`352 → 128 GELU → 64` L2-norm) + decoder **DistMult** entrenado con negativos balanceados (por grado y del mismo tipo de nodo) en `scripts/entrenar_gnn_chile.py`.
* **Artefacto empaquetado:** `data/modelos/legal_gnn_v1.npz` (**`2,979 MB`**, embeddings cuantizados `int8` + CSR de adyacencia existente para filtrar enlaces ya conocidos).
* **Peso total de modelos incluidos en el paquete:** **`5,719 MB`**.

### Resultados Held-Out (`2 000` aristas estratificadas, 1 positivo vs. 99 negativos del mismo tipo)

| Modelo | ROC-AUC | Hits@10 | Hits@20 | MRR |
| :--- | ---: | ---: | ---: | ---: |
| Baseline estructural (**Adamic-Adar**) | 0,6915 | 44,05 % | 56,90 % | 0,2544 |
| **`LegalGNN v1` (Held-Out)** | **0,8660** | **63,00 %** | **77,85 %** | **0,3540** |

### Puntos de Entrada MCP, CLI y Revisión Goldfish

* **Herramientas MCP (`114` totales):** `gnn_predecir_enlaces` y `gnn_auditar_brechas_escrito` (disponibles en perfiles `full`, `dogmatico` y `litigios`, y descubribles en `router`).
* **Enriquecimiento de `consulta_maestra`:** adjunta `hallazgos.sugerencias_gnn` cuando existen predicciones de alta confianza (`probabilidad >= 0,70`).
* **Sección consultiva en `critique_documento` (modo `goldfish`):** agrega sugerencias estructurales de cobertura normativa no bloqueantes (`Cobertura Normativa Sugerida`).
* **CLI:** `openlegal neural status`, `openlegal neural predict "Art. 2314 Código Civil"`, `openlegal neural gaps <borrador>`.

---

## 3. Scripts Opcionales de Reentrenamiento GPU

Cuando el usuario o investigador dispone de GPU con `torch` / `sentence-transformers` / `torch-geometric`:

```bash
# Fine-tuning Bi-Encoder Transformer con exportación ONNX cuantizada int8:
pip install sentence-transformers torch onnxruntime
python scripts/entrenar_transformer_hf.py --epochs 3

# Entrenamiento R-GCN en GPU con exportación directa al mismo esquema legal_gnn_v1.npz:
pip install torch torch-geometric
python scripts/entrenar_gnn_pyg_gpu.py --epochs 80
```
