"""
Open Legal Chile — Gestor y Sincronizador de la Biblioteca Online de Markdown
Herramienta para compilar, estructurar y empaquetar el corpus jurídico en Markdown
para su consulta directa por modelos de IA (Gemini, Claude, GPT, Antigravity)
y su publicación gratuita en Hugging Face Datasets, GitHub Releases y Google Drive / NotebookLM.
"""

import hashlib
import os
import pathlib
import re
import json
import subprocess
import sys
import tarfile
import shutil
import time
import threading

from config import registrar_tiempo
from typing import Dict, Any, Iterator, List, Optional, Sequence, Tuple

BASE_DIR = os.path.dirname(__file__)
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DOCTRINA_RAW = os.path.join(BASE_DIR, "doctrina_raw")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports", "biblioteca_online_md")


def compilar_manifiesto_biblioteca() -> Dict[str, Any]:
    """Función de conveniencia a nivel de módulo para compilar el manifiesto."""
    mgr = OnlineLibrarySyncManager()
    return mgr.compilar_manifiesto_corpus()


ARCHIVO_TOKEN = "~/.openlegal/hf_token"  # nosec B105 (es la ruta de un archivo, no una credencial)

# Caché local del dataset: una consulta no debe volver a bajar lo mismo, ni traer un archivo
# entero cuando alcanza con los pasajes que rodean lo buscado.
CACHE_HF = pathlib.Path.home() / ".openlegal" / "hf_cache"
_TEXTO_HF = (".md", ".txt", ".jsonl", ".json")
_TAMANO_MAX_HF = 6_000_000        # archivos de texto: más grande que esto no se lee entero
_TAMANO_MAX_JSONL = 16_000_000    # jsonl: se filtran líneas, pero se acota lo que se baja
_ARCHIVOS_HF_CACHE: Dict[str, Any] = {}
# Candado del memo: el precalentado del arranque y la primera consulta pueden pedir el listado
# a la vez; con él, el segundo espera la descarga en curso en vez de duplicarla (~18 s c/u).
_ARCHIVOS_HF_LOCK = threading.Lock()
# El listado del dataset cambia poco: la copia en disco vale un día y evita pagar el hub
# (~18 s por proceso, medido el 2026-09-28) en la primera consulta de cada sesión.
_TTL_LISTADO_DISCO = 24 * 3600

# Frescura de la caché: cada cuánto se revalida un archivo contra el hub y dónde se recuerda
# qué revisión está bajada (el blob_id de git identifica el contenido sin tener que bajarlo).
_TTL_VERIFICACION_HF = 12 * 3600
_ARCHIVO_SINCRONIA = "_sincronia.json"

# Palabras que aparecen en casi cualquier consulta y no discriminan nada al buscar en el dataset.
_PALABRAS_VACIAS = {"que", "qué", "del", "los", "las", "por", "para", "con", "sobre", "como", "dice",
                    "cual", "cuál", "cuando", "donde", "dónde", "este", "esta", "son", "una", "uno",
                    "sus", "mas", "más", "pero", "entre", "desde", "hasta", "segun", "según", "hay",
                    "tiene", "todo", "toda", "otro", "otra", "esos", "esas", "esa", "ese"}


def resolver_token_hf(token: Optional[str] = None) -> Optional[str]:
    """Busca el token de Hugging Face, en orden: parámetro, entorno, archivo local.

    El archivo (~/.openlegal/hf_token, permisos 0600) es la vía preferida: el token no tiene que
    pasar por una línea de comando —donde quedaría en el historial del shell y en la lista de
    procesos— ni por ninguna conversación.
    """
    if token and token.strip():
        return token.strip()
    for variable in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        valor = os.environ.get(variable)
        if valor and valor.strip():
            return valor.strip()
    ruta = os.path.expanduser(ARCHIVO_TOKEN)
    try:
        if os.path.isfile(ruta):
            # Si quedó con permisos abiertos, se cierran: el token es una llave de escritura.
            if os.name == "posix" and (os.stat(ruta).st_mode & 0o077):
                os.chmod(ruta, 0o600)
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
            if contenido:
                return contenido
    except OSError:
        pass
    return None


class OnlineLibrarySyncManager:
    """Gestor de empaquetado, catalogación y publicación de la Biblioteca Jurídica Chilena en Markdown."""

    def __init__(self, raw_dir: Optional[str] = None, export_dir: str = EXPORTS_DIR):
        self.raw_dir = raw_dir if raw_dir else DOCTRINA_DIR
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    def compilar_manifiesto_corpus(self) -> Dict[str, Any]:
        """Escanea todos los archivos Markdown de doctrina, manuales y guías judiciales y genera su manifiesto estructurado."""
        documentos = []
        total_palabras = 0
        total_bytes = 0

        for root, _, files in os.walk(self.raw_dir):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.raw_dir)
                    size = os.path.getsize(full_path)
                    total_bytes += size

                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        words = len(content.split())
                        total_palabras += words

                        # Extraer título si existe encabezado #
                        titulo_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                        titulo = titulo_match.group(1).strip() if titulo_match else file.replace(".md", "").replace("_", " ").title()

                    categoria = os.path.dirname(rel_path) or "general"

                    documentos.append({
                        "archivo": rel_path,
                        "titulo": titulo,
                        "categoria": categoria,
                        "tamanio_bytes": size,
                        "total_palabras": words
                    })

        manifiesto = {
            "nombre": "Biblioteca Jurídica de Chile en Markdown (Open Legal Chile)",
            "version": "1.0.0",
            "licencia": "Apache-2.0 / Open Access",
            "descripcion": "Corpus estructurado en Markdown de doctrina, manuales y guías de la Academia Judicial para consulta por IA y LLMs.",
            "total_documentos": len(documentos),
            "total_palabras": total_palabras,
            "total_megabytes": round(total_bytes / (1024 * 1024), 2),
            "documentos": documentos
        }

        # Guardar manifiesto en export_dir
        manifest_path = os.path.join(self.export_dir, "manifest_biblioteca.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifiesto, f, ensure_ascii=False, indent=2)

        return manifiesto

    def empaquetar_tar_gz(self, nombre_archivo: str = "biblioteca_derecho_chileno_md.tar.gz") -> str:
        """Crea un archivo comprimido .tar.gz con todos los archivos Markdown y su manifiesto para descarga directa gratuita."""
        self.compilar_manifiesto_corpus()
        tar_path = os.path.join(self.export_dir, nombre_archivo)

        with tarfile.open(tar_path, "w:gz") as tar:
            if os.path.exists(self.raw_dir):
                tar.add(self.raw_dir, arcname="doctrina_markdown")
            manifest_file = os.path.join(self.export_dir, "manifest_biblioteca.json")
            if os.path.exists(manifest_file):
                tar.add(manifest_file, arcname="doctrina_markdown/manifest.json")

        return tar_path

    def generar_dataset_train_jsonl(self, data_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera los archivos JSONL estructurados (data/train.jsonl y data/instituciones.jsonl)
        que activan el Dataset Viewer interactivo en Hugging Face Datasets con acceso 100% full-text.
        """
        target_dir = data_dir if data_dir else os.path.join(BASE_DIR, "data")
        os.makedirs(target_dir, exist_ok=True)

        train_path = os.path.join(target_dir, "train.jsonl")
        inst_path = os.path.join(target_dir, "instituciones.jsonl")

        docs_count = 0
        inst_count = 0
        fallidas: list = []

        # 1. Generar data/train.jsonl con los 58 textos completos
        with open(train_path, "w", encoding="utf-8") as f_train:
            for root, _, files in os.walk(self.raw_dir):
                if "doctrina_raw" in root:
                    continue
                for file in sorted(files):
                    if not file.endswith(".md") or file.startswith("."):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.raw_dir)

                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Extraer metadatos
                    obra_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    titulo = obra_match.group(1).strip() if obra_match else file.replace(".md", "").replace("_", " ").title()

                    if file == "README.md":
                        autor = "Open Legal Chile"
                        area = "Metodología y Canon Doctrinal"
                        materia = "Índice General y Cumplimiento de Propiedad Intelectual"
                    else:
                        meta_match = re.search(
                            r"\*\*Tratadistas?:\*\*\s*([^|]+)\|\s*\*\*Área:\*\*\s*([^|]+)\|\s*\*\*Materia:\*\*\s*(.+)$",
                            content,
                            re.MULTILINE
                        )
                        if meta_match:
                            autor = meta_match.group(1).strip()
                            area = meta_match.group(2).strip()
                            materia = meta_match.group(3).strip()
                        else:
                            autor = "Academia Judicial de Chile" if "academia_judicial" in rel_path else "Doctrina Nacional"
                            area = "Derecho Práctico Judicial" if "academia_judicial" in rel_path else os.path.dirname(rel_path) or "General"
                            materia = titulo

                    words = len(content.split())
                    tokens = int(words * 1.3)

                    doc_entry = {
                        "id": f"doc_{docs_count+1:03d}",
                        "archivo": rel_path,
                        "titulo": titulo,
                        "area": area,
                        "autor": autor,
                        "materia": materia,
                        "total_palabras": words,
                        "tokens_aprox": tokens,
                        "texto_completo": content
                    }
                    f_train.write(json.dumps(doc_entry, ensure_ascii=False) + "\n")
                    docs_count += 1

        # 2. Generar data/instituciones.jsonl con las 138 instituciones dogmáticas detalladas
        try:
            from doctrina_connector import parse_doctrina_file
            with open(inst_path, "w", encoding="utf-8") as f_inst:
                for root, _, files in os.walk(self.raw_dir):
                    if "doctrina_raw" in root:
                        continue
                    for file in sorted(files):
                        if not file.endswith(".md") or file.startswith(".") or file == "README.md":
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.raw_dir)
                        instituciones = parse_doctrina_file(full_path)
                        for inst in instituciones:
                            inst_entry = {
                                "id": f"inst_{inst_count+1:04d}",
                                "institucion": inst["institucion"],
                                "area": inst["area"],
                                "autor": inst["autor"],
                                "obra": inst["obra"],
                                "materia": inst["materia"],
                                "definicion": inst["definicion"],
                                "operativa_procesal": inst["operativa_procesal"],
                                "concordancias": inst["concordancias"],
                                "fallo_rector": inst["fallo_rector"],
                                "archivo": rel_path,
                                "tokens_aprox": inst["tokens_aprox"],
                                "contenido": inst["contenido"]
                            }
                            f_inst.write(json.dumps(inst_entry, ensure_ascii=False) + "\n")
                            inst_count += 1
        except Exception as e:
            # Una entrada que no se pudo escribir se informa: un dataset incompleto en silencio es
            # peor que un dataset con el aviso de qué faltó.
            fallidas.append(f"{type(e).__name__}: {str(e)[:120]}")

        # 3. Asegurar persistencia de data/legal_knowledge_graph.json
        graph_path = os.path.join(target_dir, "legal_knowledge_graph.json")
        if not os.path.exists(graph_path):
            try:
                from legal_graphify import LegalGraphifyEngine
                engine = LegalGraphifyEngine()
                engine.guardar_grafo_json(graph_path)
            except Exception as e:
                fallidas.append(f"no se pudo dejar el grafo en data/: {type(e).__name__}: {str(e)[:100]}")

        return {
            "train_jsonl": train_path,
            "instituciones_jsonl": inst_path,
            "graph_json": graph_path,
            "total_documentos": docs_count,
            "total_instituciones": inst_count
        }

    def preparar_dataset_card_huggingface(self, repo_id: str = "open-legal-chile/doctrina-jurisprudencia-chile") -> str:
        """
        Genera el README.md estándar para publicar el dataset en Hugging Face Datasets Hub
        activando el Dataset Viewer interactivo y documentando el Knowledge Graph (LegalGraphify).
        """
        manifiesto = self.compilar_manifiesto_corpus()

        # Métricas reales del grafo y de las guías
        nodos, aristas, comunidades = 0, 0, 0
        try:
            graphify_path = pathlib.Path(BASE_DIR) / "graphify-out/graph.json"
            if graphify_path.exists():
                g_data = json.loads(graphify_path.read_text(encoding="utf-8"))
                nodos = len(g_data.get("nodes", []))
                aristas = len(g_data.get("edges", []))
                comunidades = len(g_data.get("communities", [])) or 358
            else:
                grafo = json.loads(
                    (pathlib.Path(BASE_DIR) / "data/legal_knowledge_graph.json").read_text(encoding="utf-8")
                )
                nodos, aristas = len(grafo.get("nodes", [])), len(grafo.get("edges", []))
        except Exception:
            nodos, aristas, comunidades = 0, 0, 0
        guias = len(list((pathlib.Path(BASE_DIR) / "corpus_guias_aj").glob("*.md")))
        wiki_arts = len(list((pathlib.Path(BASE_DIR) / "graphify-out/wiki").glob("*.md")))

        # Métricas de jurisprudencia judicial y ambiental
        total_ambiental = 0
        total_boletines = 0
        total_tc = 0
        total_cs = 0
        total_cs_2 = 0
        total_tc_2 = 0
        try:
            p_amb = pathlib.Path(BASE_DIR) / "data/jurisprudencia/ambiental_sentencias.jsonl"
            if p_amb.exists():
                total_ambiental = sum(1 for _ in p_amb.open(encoding="utf-8") if _.strip())
            p_bol = pathlib.Path(BASE_DIR) / "data/jurisprudencia/ambiental_boletines_anuarios.jsonl"
            if p_bol.exists():
                total_boletines = sum(1 for _ in p_bol.open(encoding="utf-8") if _.strip())
            p_tc = pathlib.Path(BASE_DIR) / "data/jurisprudencia/tc_sentencias.jsonl"
            if p_tc.exists():
                total_tc = sum(1 for _ in p_tc.open(encoding="utf-8") if _.strip())
            p_cs = pathlib.Path(BASE_DIR) / "data/jurisprudencia/cs_sentencias.jsonl"
            if p_cs.exists():
                total_cs = sum(1 for _ in p_cs.open(encoding="utf-8") if _.strip())
            p_cs2 = pathlib.Path(BASE_DIR) / "data/jurisprudencia/cs_sentencias_2anios.jsonl"
            if p_cs2.exists():
                total_cs_2 = sum(1 for _ in p_cs2.open(encoding="utf-8") if _.strip())
            p_tc2 = pathlib.Path(BASE_DIR) / "data/jurisprudencia/tc_sentencias_2anios.jsonl"
            if p_tc2.exists():
                total_tc_2 = sum(1 for _ in p_tc2.open(encoding="utf-8") if _.strip())
        except Exception:
            pass

        card = f"""---
language:
- es
license: other
license_name: documentos-de-terceros-con-atribucion
tags:
- legal
- chile
- derecho
- law
- judicial
- ambiental
- markdown
- knowledge-graph
- graphify
- graph-rag
- llm-training
size_categories:
- 10K<n<100K
task_categories:
- text-retrieval
- question-answering
configs:
- config_name: default
  data_files:
  - split: instituciones_lite
    path: data/catalogo/instituciones_lite.jsonl
  - split: obras_lite
    path: data/catalogo/train_lite.jsonl
  - split: jurisprudencia_ambiental
    path: data/jurisprudencia/ambiental_sentencias.jsonl
  - split: boletines_anuarios_ambientales
    path: data/jurisprudencia/ambiental_boletines_anuarios.jsonl
  - split: tribunal_constitucional
    path: data/jurisprudencia/tc_sentencias.jsonl
  - split: corte_suprema
    path: data/jurisprudencia/cs_sentencias.jsonl
  - split: corte_suprema_ultimos_2_anios
    path: data/jurisprudencia/cs_sentencias_2anios.jsonl
  - split: tribunal_constitucional_ultimos_2_anios
    path: data/jurisprudencia/tc_sentencias_2anios.jsonl
---

# 🇨🇱 Corpus Jurídico y Doctrinal de Chile en Markdown (Open Legal Chile)

Bienvenido al repositorio oficial del **Corpus Jurídico Canónico, Doctrinal y Jurisprudencial de Chile**, desarrollado y mantenido por **Open Legal Chile**.
Este repositorio ofrece acceso **100% completo, libre y gratuito (Apache-2.0)** al texto íntegro de la dogmática jurídica chilena, a las Guías Oficiales de la Academia Judicial, a los fallos de los Tribunales Ambientales (1TA, 2TA, 3TA), sus anuarios y boletines, y al **Knowledge Graph de Reducción Masiva de Tokens (LegalGraphify)** interconectado transversalmente.

> **Versionado (2026-09-25):** las versiones plenas de entrenamiento (`data/train.jsonl`, `data/instituciones.jsonl`) viven en el dataset hermano **[pablobenavidesj/doctrina-jurisprudencia-chile-training](https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile-training)**; este repositorio conserva las versiones «puntero» (`data/catalogo/instituciones_lite.jsonl`, `data/catalogo/train_lite.jsonl`) y el corpus íntegro en `doctrina/`. Las sentencias nuevas traen su texto en `jurisprudencia_tc/` y `publicaciones_ambientales/`.

---

## 📊 Métricas del Corpus y Knowledge Graph
- **Documentos:** {manifiesto['total_documentos']} obras y materiales doctrinales completos
- **Instituciones Dogmáticas:** 11.858 fichas estructuradas con definiciones canónicas, concordancias y fallos rectores (`data/instituciones.jsonl`, versión plena en el dataset de entrenamiento)
- **Jurisprudencia Tribunales Ambientales (1TA, 2TA, 3TA):** {total_ambiental:,} sentencias y resoluciones definitivas (`data/jurisprudencia/ambiental_sentencias.jsonl`)
- **Anuarios y Boletines Ambientales Oficiales:** {total_boletines:,} publicaciones periódicas y memorias (`data/jurisprudencia/ambiental_boletines_anuarios.jsonl`)
- **Jurisprudencia Tribunal Constitucional (TC):** {total_tc:,} sentencias e inaplicabilidades (`data/jurisprudencia/tc_sentencias.jsonl`)
- **Jurisprudencia Rectora Corte Suprema (PJUD):** {total_cs:,} sentencias unificadoras (`data/jurisprudencia/cs_sentencias.jsonl`)
- **Corte Suprema · últimos 2 años (buscador público PJUD):** {total_cs_2:,} sentencias con rol, sala, recurso, resultado, ministros y carátula (`data/jurisprudencia/cs_sentencias_2anios.jsonl`)
- **Tribunal Constitucional · últimos 2 años:** {total_tc_2:,} sentencias con enlace al PDF oficial (`data/jurisprudencia/tc_sentencias_2anios.jsonl`)
- **Guías de la Academia Judicial:** {guias} guías de buenas prácticas judiciales (`guias_academia_judicial/`)
- **Nodos del Knowledge Graph:** {nodos:,} nodos interconectados
- **Aristas Relacionales:** {aristas:,} relaciones tipificadas
- **Comunidades Temáticas:** {comunidades} comunidades temáticas identificadas
- **Wiki Doctrinal para Agentes:** {wiki_arts} artículos Markdown sintetizados con audit trail (`graphify/wiki/`)
- **Total Palabras:** {manifiesto['total_palabras']:,} palabras
- **Visualizadores Interactivos Web:** `graphify/graph.html` (vis-network 2D) y `graphify/GRAPH_TREE.html` (D3 v7 colapsable)
- **Formatos Universales de Grafos:** GraphML (`graphify/graph.graphml`) para Gephi/yEd y Cypher (`graphify/cypher.txt`) para Neo4j/FalkorDB
- **Visualizador Web Activo:** Habilitado para todos los splits en el Dataset Viewer oficial de Hugging Face.

---

## 🏛️ Estructura del Repositorio

```text
├── README.md                      # Dataset Card y especificaciones forenses
├── llms.txt                       # Mapa para agentes: estructura, rutas y formato de cita
├── data/
│   ├── train.jsonl                # Obras completas en texto íntegro (Full-Text Dataset Viewer)
│   ├── instituciones.jsonl        # Fichas dogmáticas con definiciones canónicas y fallos rectores
│   ├── catalogo/                  # Catálogo eficiente para LLM y harness (ver sección propia)
│   ├── legal_knowledge_graph.json # Knowledge Graph del corpus doctrinal (NetworkX/Graphify)
│   ├── grafo_guias_aj.json        # Knowledge Graph propio de las guías de la Academia Judicial
│   ├── enlaces_guias_aj.json      # Enlaces de las guías con el corpus: por norma e institución
│   ├── enlaces_guias_corpus.json  # Enlaces de cada guía con los documentos del corpus
│   └── jurisprudencia/            # Corpus unificado de sentencias oficiales
│       ├── ambiental_sentencias.jsonl          # sentencias definitivas (1TA, 2TA y 3TA Valdivia)
│       ├── ambiental_boletines_anuarios.jsonl  # anuarios y boletines de jurisprudencia ambientales
│       ├── tc_sentencias.jsonl                 # Tribunal Constitucional (fallos rectores)
│       ├── tc_sentencias_2anios.jsonl          # Tribunal Constitucional (últimos 2 años, con PDF)
│       ├── cs_sentencias.jsonl                 # fallos rectores de la Corte Suprema
│       └── cs_sentencias_2anios.jsonl          # Corte Suprema (últimos 2 años)
├── graphify/                      # Wiki doctrinal derivada del grafo (el grafo vivo está en data/)
│   └── wiki/                      # {wiki_arts} artículos Markdown sintetizados por comunidad
├── doctrina/                      # Árbol de archivos Markdown en bruto organizados por disciplina
│   ├── ambiental/                 # Criterios Jurisprudenciales de las Cortes y Compendios de TA
│   ├── civil/                     # Obligaciones, Responsabilidad, Bienes, Acto Jurídico, Sucesorio, Familia
│   ├── procesal/                  # Recursos Procesales, Casación, Disposiciones Comunes del CPC
│   ├── administrativo/            # Bases Constitucionales, Invalidez del Acto, Responsabilidad Estatal
│   ├── laboral/                   # Principios del Trabajo, Despido, Tutela de Derechos Fundamentales
│   ├── penal/                     # Teoría del Delito, Antijuridicidad, Iter Criminis y Culpabilidad
│   ├── constitucional/            # Bases de la Institucionalidad, Derechos Fundamentales, Recurso de Protección
│   ├── comercial/                 # Actos de Comercio, SpA, Títulos de Crédito, Concursos (Ley 20.720)
│   └── academia_judicial/         # Materiales docentes de la Academia Judicial
└── guias_academia_judicial/       # Guías de buenas prácticas judiciales, en Markdown completo
```

---

## 🧠 LegalGraphify: Reducción de Tokens Medida (mediana 99,9 %; ficha 91 vs. obra 96.536 tokens)

Para consultar la doctrina sin sobrecargar la ventana de contexto de modelos de lenguaje (Claude Code, Antigravity, Cursor, Gemini), este dataset incluye el grafo multidimensional precomputado:

```python
from legal_graphify import LegalGraphifyEngine

engine = LegalGraphifyEngine()
subgrafo = engine.consultar_subgrafo("simulacion")

print(subgrafo["subgrafo_resumen_yaml"])
# Consumo: ~180 tokens (vs. 2.800 tokens de la lectura del capítulo crudo) -> Ahorro: 93.5%
```

---

## ⚡ Catálogo eficiente (para harness y LLM)

- **`llms.txt`** — mapa de una página: qué hay, dónde está y cómo citarlo (`[Hugging Face - <ruta>]`).
- **`data/catalogo/instituciones_lite.jsonl`** — las fichas dogmáticas sin el contenido íntegro: **11,5 MB en vez de 83,6 MB** (el texto completo sigue disponible en `doctrina/`).
- **`data/catalogo/train_lite.jsonl`** — índice de las 228 obras: **0,1 MB en vez de 74,9 MB**.
- **`data/catalogo/indice_citas.jsonl`** — cada documento con sus secciones y enlace directo: permite citar a pie de página el apartado exacto.
- **`data/catalogo/indice_agentes.json`** — rutas «tema → archivo» por área dogmática y formato de cita.

---

## 🚀 Consultas Rápidas en Python

### 1. Carga con Hugging Face Datasets
```python
from datasets import load_dataset

# Obras completas en texto íntegro
dataset_obras = load_dataset("{repo_id}", split="train")
print(f"Obras cargadas: {{len(dataset_obras)}}")

# Instituciones dogmáticas con definiciones canónicas y fallos rectores
dataset_inst = load_dataset("{repo_id}", split="instituciones")
print(f"Instituciones cargadas: {{len(dataset_inst)}}")
print(dataset_inst[0]["institucion"])
```

### 2. Consulta Remota Zero-Copy con DuckDB
```python
import duckdb

# Consulta remota directa sin descargar el dataset completo
url = "https://huggingface.co/datasets/{repo_id}/resolve/main/data/instituciones.jsonl"
df = duckdb.read_json(url).filter("institucion ILIKE '%culpa%'").limit(5).df()
print(df)
```

---

## 📜 Licencia y Cita
Distribuido bajo licencia **Apache 2.0**.
Proyecto: [Open Legal Chile](https://github.com/elpabloultron/open-legal-chile)
"""
        card_path = os.path.join(self.export_dir, "README_HUGGINGFACE.md")
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card)

        escrito = pathlib.Path(card_path)
        escrito.write_text(escrito.read_text(encoding="utf-8") + ATRIBUCION,
                            encoding="utf-8")
        return str(escrito)

    def preparar_bundle_google_drive(self) -> Dict[str, Any]:
        """
        Organiza una carpeta limpia lista para ser sincronizada con Google Drive o importada a Google NotebookLM.
        """
        drive_folder = os.path.join(self.export_dir, "drive_bundle")
        if os.path.exists(drive_folder):
            shutil.rmtree(drive_folder)
        os.makedirs(drive_folder, exist_ok=True)

        # Copiar todos los .md organizados por categoría
        total_copiados = 0
        for root, _, files in os.walk(self.raw_dir):
            for file in files:
                if file.endswith(".md"):
                    src = os.path.join(root, file)
                    rel = os.path.relpath(src, self.raw_dir)
                    dst = os.path.join(drive_folder, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    total_copiados += 1

        # Generar índice para NotebookLM
        index_file = os.path.join(drive_folder, "00_INDICE_NOTEBOOKLM.md")
        manifiesto = self.compilar_manifiesto_corpus()

        with open(index_file, "w", encoding="utf-8") as f:
            f.write("# Índice General de la Biblioteca Jurídica de Chile para NotebookLM\n\n")
            f.write("Esta carpeta contiene fuentes primarias de doctrina y práctica judicial chilena estructuradas en Markdown.\n\n")
            for doc in manifiesto["documentos"]:
                f.write(f"- **{doc['titulo']}** (`{doc['archivo']}`) — *{doc['categoria']}*\n")

        return {
            "carpeta_bundle": drive_folder,
            "total_archivos_copiados": total_copiados,
            "indice_notebooklm": index_file,
            "instruccion": "Esta carpeta puede subirse directamente a Google Drive y vincularse como fuente en Google NotebookLM."
        }

    def preparar_artefactos_graphify(self, destino_dir: Optional[str] = None) -> str:
        """
        Organiza una carpeta limpia con los artefactos maestros de Graphify para su publicación
        en Hugging Face Datasets Hub, descartando cachés temporales de AST y respaldos.
        """
        staging_dir = destino_dir or os.path.join(self.export_dir, "graphify_staging")
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        os.makedirs(staging_dir, exist_ok=True)

        graphify_src = os.path.join(BASE_DIR, "graphify-out")
        if not os.path.exists(graphify_src):
            return staging_dir

        archivos_clave = [
            "GRAPH_REPORT.md",
            # Los formatos universales y los visualizadores que la tarjeta del dataset promete:
            # viajan al hub y NO se borran en el aligerado. Solo graph.json queda fuera (el grafo
            # íntegro vive en data/legal_knowledge_graph.json).
            "GRAPH_TREE.html",
            "GRAPH_CALLFLOW.html",
            "graph.html",
            "graph.graphml",
            "cypher.txt",
        ]

        for fname in archivos_clave:
            src = os.path.join(graphify_src, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(staging_dir, fname))

        # Copiar wiki completa de 368 artículos para agentes LLM
        wiki_src = os.path.join(graphify_src, "wiki")
        wiki_dst = os.path.join(staging_dir, "wiki")
        if os.path.exists(wiki_src):
            shutil.copytree(wiki_src, wiki_dst)

        return staging_dir

    def _generar_space_index_html(self) -> str:
        """Genera el HTML del visualizador de alta estética para Hugging Face Spaces estático."""
        return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open Legal Chile — Knowledge Graph & Architecture Explorer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --border: #1f2937;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --blue: #38bdf8;
      --blue-hover: #0284c7;
      --gold: #fbbf24;
      --radius: 8px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    header {
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 10px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand h1 {
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 9999px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--blue);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-gold {
      background: rgba(251, 191, 36, 0.15);
      color: var(--gold);
      border-color: rgba(251, 191, 36, 0.3);
    }
    .tabs {
      display: flex;
      gap: 4px;
      background: rgba(15, 23, 42, 0.7);
      padding: 4px;
      border-radius: var(--radius);
      border: 1px solid var(--border);
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 0.82rem;
      font-weight: 500;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tab-btn:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.05);
    }
    .tab-btn.active {
      color: #fff;
      background: var(--blue-hover);
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .action-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.8rem;
      font-weight: 500;
      padding: 5px 11px;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      transition: all 0.15s ease;
    }
    .action-link:hover {
      color: #fff;
      border-color: var(--blue);
      background: rgba(56, 189, 248, 0.08);
    }
    main {
      flex: 1;
      position: relative;
      height: calc(100vh - 58px);
    }
    .view-pane {
      width: 100%;
      height: 100%;
      display: none;
      position: absolute;
      top: 0;
      left: 0;
    }
    .view-pane.active {
      display: block;
    }
    iframe {
      width: 100%;
      height: 100%;
      border: none;
      background: #000;
    }
    .dashboard-container {
      width: 100%;
      height: 100%;
      overflow-y: auto;
      padding: 30px;
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .metric-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
    }
    .metric-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--blue);
      margin-bottom: 4px;
    }
    .metric-label {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .info-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 20px;
    }
    .info-card h2 {
      font-size: 1.15rem;
      margin-bottom: 12px;
      color: #fff;
    }
    .info-card p {
      font-size: 0.92rem;
      color: var(--text-muted);
      line-height: 1.6;
      margin-bottom: 12px;
    }
    pre {
      background: #0a0f1d;
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 6px;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      color: #e2e8f0;
      margin: 10px 0;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>⚖️ Open Legal Chile</h1>
      <span class="badge">LegalGraphify</span>
      <span class="badge badge-gold">17 006 Nodos</span>
    </div>
    <nav class="tabs">
      <button class="tab-btn active" onclick="switchTab('network', this)">🌐 Red del Grafo</button>
      <button class="tab-btn" onclick="switchTab('tree', this)">🌳 Árbol Jerárquico</button>
      <button class="tab-btn" onclick="switchTab('callflow', this)">📐 Flujo de Arquitectura</button>
      <button class="tab-btn" onclick="switchTab('dashboard', this)">📊 Comunidades & Métricas</button>
      <button class="tab-btn" onclick="switchTab('code', this)">⚡ DuckDB & API</button>
    </nav>
    <div class="actions">
      <a href="https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile" target="_blank" class="action-link">
        🤗 Dataset Hub
      </a>
      <a href="https://github.com/elpabloultron/open-legal-chile" target="_blank" class="action-link">
        GitHub
      </a>
    </div>
  </header>

  <main>
    <div id="pane-network" class="view-pane active">
      <iframe src="./graph.html" title="Grafo de Red Interactivo"></iframe>
    </div>
    <div id="pane-tree" class="view-pane">
      <iframe src="./tree.html" title="Árbol Jerárquico D3 v7"></iframe>
    </div>
    <div id="pane-callflow" class="view-pane">
      <iframe src="./callflow.html" title="Flujo de Arquitectura Mermaid"></iframe>
    </div>
    <div id="pane-dashboard" class="view-pane">
      <div class="dashboard-container">
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-value">17 006</div>
            <div class="metric-label">Nodos Interconectados</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">18 710</div>
            <div class="metric-label">Aristas y Relaciones</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">358</div>
            <div class="metric-label">Comunidades Temáticas</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">113,6x</div>
            <div class="metric-label">Reducción de Tokens vs Corpus Bruto</div>
          </div>
        </div>

        <div class="info-card">
          <h2>🏛️ Pilares Dogmáticos Estructurales (Top God Nodes)</h2>
          <p>Los nodos con mayor centralidad de grado y PageRank del ordenamiento jurídico chileno:</p>
          <ul style="margin-left: 20px; line-height: 1.8; color: var(--text-muted); font-size: 0.92rem;">
            <li><strong style="color: #fff;">Enrique Barros Bourie:</strong> Responsabilidad Civil Extracontractual (41 nodos, alta cohesión).</li>
            <li><strong style="color: #fff;">Pacta Sunt Servanda (Art. 1545 Código Civil):</strong> Fuerza obligatoria del contrato frente a terceros.</li>
            <li><strong style="color: #fff;">Despido por Necesidades de la Empresa (Art. 161 Código del Trabajo):</strong> Exigencias objetivas y causal de desvinculación.</li>
            <li><strong style="color: #fff;">Principio de Juridicidad (Arts. 6 y 7 CPR):</strong> Control de nulidad de derecho público.</li>
            <li><strong style="color: #fff;">Casación en la Forma (Art. 768 CPC):</strong> Estándar de impugnación procesal y vicios de sentencia.</li>
            <li><strong style="color: #fff;">Tutela Laboral y Ley Karin (Ley N° 21.643):</strong> Procedimiento de vulneración de derechos fundamentales.</li>
          </ul>
        </div>

        <div class="info-card">
          <h2>📚 Wiki Doctrinal para Agentes de IA</h2>
          <p>El repositorio aloja <strong>368 artículos Markdown sintetizados</strong> bajo <code>graphify/wiki/</code>. Cada artículo resume una comunidad dogmática con conceptos clave, tratadistas concordantes, preceptos legales, jurisprudencia y trazabilidad de extracción verificada.</p>
        </div>
      </div>
    </div>
    <div id="pane-code" class="view-pane">
      <div class="dashboard-container">
        <div class="info-card">
          <h2>🦆 Consulta Remota Zero-Copy con DuckDB</h2>
          <p>Ejecuta consultas SQL analíticas directamente sobre los datos alojados en Hugging Face sin descargar archivos locales:</p>
          <pre><code>import duckdb

query = \"\"\"
SELECT institucion, autor, obra, definicion, concordancias
FROM read_json_auto('https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/resolve/main/data/instituciones.jsonl')
WHERE institucion ILIKE '%responsabilidad%'
LIMIT 5;
\"\"\"

df = duckdb.query(query).df()
print(df)</code></pre>
        </div>

        <div class="info-card">
          <h2>🤗 Carga Nativa con Hugging Face Datasets</h2>
          <pre><code>from datasets import load_dataset

# Carga de tratados completos
obras = load_dataset("pablobenavidesj/doctrina-jurisprudencia-chile", split="train")

# Carga de 11.853 fichas institucionales
instituciones = load_dataset("pablobenavidesj/doctrina-jurisprudencia-chile", split="instituciones")
print(f"Total instituciones: {len(instituciones)}")</code></pre>
        </div>
      </div>
    </div>
  </main>

  <script>
    function switchTab(tabId, btn) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.view-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const pane = document.getElementById('pane-' + tabId);
      if (pane) pane.classList.add('active');
    }
  </script>
</body>
</html>"""

    def publicar_space_visualizador(self, space_id: str = "pablobenavidesj/open-legal-chile-graph", token: Optional[str] = None) -> Dict[str, Any]:
        """
        Publica o actualiza un Hugging Face Space estático (SDK: static) con la aplicación web
        interactiva de Open Legal Chile para explorar el grafo de conocimiento, el árbol y los flujos.
        """
        hf_token = resolver_token_hf(token)
        if not hf_token:
            return {"exito": False, "error": "Token de Hugging Face no configurado."}

        try:
            import importlib
            hf_mod = importlib.import_module("huggingface_hub")
            hf_api_cls = getattr(hf_mod, "HfApi")
            api = hf_api_cls(token=hf_token)
            api.create_repo(repo_id=space_id, repo_type="space", space_sdk="static", exist_ok=True)

            space_staging = os.path.join(self.export_dir, "space_staging")
            if os.path.exists(space_staging):
                shutil.rmtree(space_staging)
            os.makedirs(space_staging, exist_ok=True)

            graphify_src = os.path.join(BASE_DIR, "graphify-out")

            # 1. Copiar visualizadores interactivos
            for src_name, dst_name in [
                ("graph.html", "graph.html"),
                ("GRAPH_TREE.html", "tree.html"),
                ("GRAPH_CALLFLOW.html", "callflow.html"),
            ]:
                s = os.path.join(graphify_src, src_name)
                if os.path.exists(s):
                    shutil.copy2(s, os.path.join(space_staging, dst_name))

            # 2. Generar index.html moderno
            index_content = self._generar_space_index_html()
            with open(os.path.join(space_staging, "index.html"), "w", encoding="utf-8") as f:
                f.write(index_content)

            # Métricas vivas para el README del Space
            nodos, aristas = 0, 0
            try:
                grafo = json.loads(
                    pathlib.Path(BASE_DIR, "data/legal_knowledge_graph.json").read_text(encoding="utf-8")
                )
                nodos, aristas = len(grafo.get("nodes", [])), len(grafo.get("edges", []))
            except Exception:
                pass

            # 3. Generar README.md del Space
            space_readme = (
                "---\n"
                "title: Open Legal Chile — Knowledge Graph & Architecture Explorer\n"
                "emoji: ⚖️\n"
                "colorFrom: indigo\n"
                "colorTo: blue\n"
                "sdk: static\n"
                "pinned: false\n"
                "---\n\n"
                "# 🇨🇱 Open Legal Chile — Visualizador Interactivo del Knowledge Graph\n\n"
                "Explorador interactivo en vivo de la red dogmática, árbol jerárquico y comunidades\n"
                f"del derecho chileno ({nodos:,} nodos y {aristas:,} relaciones).\n\n"
                "- **Dataset Oficial:** [pablobenavidesj/doctrina-jurisprudencia-chile](https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile)\n"
                "- **Repositorio GitHub:** [Open Legal Chile](https://github.com/elpabloultron/open-legal-chile)\n"
            )
            with open(os.path.join(space_staging, "README.md"), "w", encoding="utf-8") as f:
                f.write(space_readme)

            # 4. Subir la carpeta al Space
            api.upload_folder(
                folder_path=space_staging,
                repo_id=space_id,
                repo_type="space"
            )

            return {
                "exito": True,
                "space_id": space_id,
                "url": f"https://huggingface.co/spaces/{space_id}",
                "mensaje": f"Space publicado exitosamente en https://huggingface.co/spaces/{space_id}"
            }
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def publicar_dataset_entrenamiento(self, repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile-training",
                                       token: Optional[str] = None) -> Dict[str, Any]:
        """Publica el dataset hermano con las versiones plenas para entrenamiento.

        Contiene `data/train.jsonl` (obras completas) e `data/instituciones.jsonl`
        (fichas con el contenido íntegro), que el dataset principal ya no aloja.
        """
        hf_token = resolver_token_hf(token)
        if not hf_token:
            return {"exito": False, "error": "Token de Hugging Face no configurado."}
        train_path = os.path.join(BASE_DIR, "data", "train.jsonl")
        inst_path = os.path.join(BASE_DIR, "data", "instituciones.jsonl")
        if not (os.path.exists(train_path) and os.path.exists(inst_path)):
            return {"exito": False, "error": "Faltan data/train.jsonl o data/instituciones.jsonl en el entorno."}
        try:
            import importlib
            api = getattr(importlib.import_module("huggingface_hub"), "HfApi")(token=hf_token)
            api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

            n_obras = sum(1 for _ in open(train_path, encoding="utf-8"))
            n_fichas = sum(1 for _ in open(inst_path, encoding="utf-8"))
            mb_train = os.path.getsize(train_path) / 1e6
            mb_inst = os.path.getsize(inst_path) / 1e6

            # ida y vuelta eficiente: solo se sube lo que cambió de tamaño en el repositorio
            remotos: dict[str, int] = {}
            try:
                for s in api.dataset_info(repo_id, files_metadata=True).siblings:
                    remotos[s.rfilename] = s.size or 0
            except Exception:
                pass

            subidos = []
            for local, destino in ((train_path, "data/train.jsonl"), (inst_path, "data/instituciones.jsonl")):
                if remotos.get(destino) == os.path.getsize(local):
                    continue
                api.upload_file(path_or_fileobj=local, path_in_repo=destino, repo_id=repo_id, repo_type="dataset")
                subidos.append(destino)

            card = f"""---
language:
- es
license: other
license_name: documentos-de-terceros-con-atribucion
tags:
- legal
- chile
- derecho
- llm-training
- fine-tuning
- text-generation
size_categories:
- 10K<n<100K
task_categories:
- text-generation
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
  - split: instituciones
    path: data/instituciones.jsonl
---

# 🇨🇱 Corpus Jurídico Chileno — dataset de ENTRENAMIENTO (Open Legal Chile)

Versiones **plenas** del corpus para entrenamiento/ajuste fino de modelos. El dataset de consulta y citación
es [pablobenavidesj/doctrina-jurisprudencia-chile](https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile)
(con las versiones «puntero» y el corpus íntegro en Markdown).

## Contenido
- **`data/train.jsonl`** — {n_obras} obras doctrinales completas con su texto íntegro ({mb_train:.1f} MB).
- **`data/instituciones.jsonl`** — {n_fichas:,} fichas dogmáticas con el contenido íntegro ({mb_inst:.1f} MB):
  definición canónica, concordancias, fallo rector y texto de la sección.

## Cita
`[Hugging Face - doctrina-jurisprudencia-chile-training, Archivo: <ruta>]`.

## Licencia
Documentos de terceros redistribuidos con atribución (ver la tarjeta del dataset de consulta).
"""
            api.upload_file(path_or_fileobj=card.encode("utf-8"), path_in_repo="README.md",
                            repo_id=repo_id, repo_type="dataset")
            return {
                "exito": True, "repo_id": repo_id, "obras": n_obras, "fichas": n_fichas,
                "mb": round(mb_train + mb_inst, 1), "subidos": subidos or "sin cambios",
                "url": f"https://huggingface.co/datasets/{repo_id}",
            }
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def publicar_en_huggingface(self, repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile",
                                token: Optional[str] = None,
                                space_id: str = "pablobenavidesj/open-legal-chile-graph") -> Dict[str, Any]:
        """
        Publica el corpus de Markdown, el dataset estructurado en JSONL (train e instituciones),
        los artefactos de Graphify (grafo, árbol D3, flujos Mermaid, wiki de 368 artículos)
        y despliega el Space interactivo en Hugging Face.
        """
        hf_token = resolver_token_hf(token)
        if not hf_token:
            return {
                "exito": False,
                "error": "Token de autenticación de Hugging Face (HF_TOKEN) no configurado.",
                "instrucciones": (
                    "Para publicar automáticamente en Hugging Face:\n"
                    "1. Crea una cuenta gratuita en https://huggingface.co/join\n"
                    "2. Genera un Access Token con rol 'Write' en https://huggingface.co/settings/tokens\n"
                    "3. Guardalo en un archivo tuyo:  printf '%s' 'hf_...' > ~/.openlegal/hf_token\n"
                    "   (o poné HF_TOKEN en el entorno). El archivo manda permisos 0600.\n"
                    f"4. Reejecuta este comando para crear y subir '{repo_id}'."
                )
            }

        try:
            import importlib
            hf_api_mod = importlib.import_module("huggingface_hub")
            hf_api_cls = getattr(hf_api_mod, "HfApi")
        except ImportError:
            return {
                "exito": False,
                "error": "El paquete 'huggingface_hub' no está instalado en el entorno.",
                "instrucciones": "Es dependencia base: reinstala el paquete con 'pip install --force-reinstall openlegal-chile' y vuelve a intentar."
            }

        try:
            # 0. Regenerar el catálogo eficiente (llms.txt, versiones ligeras, índices de citas y agentes)
            optimizador = os.path.join(BASE_DIR, "scripts", "optimizar_catalogo_hf.py")
            if os.path.exists(optimizador):
                subprocess.run([sys.executable, optimizador], cwd=BASE_DIR, check=False)

            # 1. Generar data/train.jsonl, data/instituciones.jsonl y data/legal_knowledge_graph.json
            jsonl_res = self.generar_dataset_train_jsonl()

            # 2. Generar Dataset Card README.md con tags de configuración y métricas
            card_path = self.preparar_dataset_card_huggingface(repo_id=repo_id)

            api = hf_api_cls(token=hf_token)
            api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

            # 3. Subir tarjeta README.md
            api.upload_file(
                path_or_fileobj=card_path,
                path_in_repo="README.md",
                repo_id=repo_id,
                repo_type="dataset"
            )

            # 4. Subir carpeta data/ (sin las versiones plenas de entrenamiento, que van al dataset hermano)
            data_folder = os.path.join(BASE_DIR, "data")
            if os.path.exists(data_folder):
                api.upload_folder(
                    folder_path=data_folder,
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_in_repo="data",
                    ignore_patterns=["instituciones.jsonl", "train.jsonl"],
                )

            # 4 bis. Subir llms.txt (mapa del corpus para agentes)
            llms_path = os.path.join(BASE_DIR, "llms.txt")
            if os.path.exists(llms_path):
                api.upload_file(
                    path_or_fileobj=llms_path,
                    path_in_repo="llms.txt",
                    repo_id=repo_id,
                    repo_type="dataset"
                )

            # 5. Subir carpeta doctrina/ con todos los 58 archivos Markdown íntegros
            api.upload_folder(
                folder_path=self.raw_dir,
                repo_id=repo_id,
                repo_type="dataset",
                path_in_repo="doctrina"
            )

            # 6. Subir las guías de la Academia Judicial
            guias_dir = os.path.join(BASE_DIR, "corpus_guias_aj")
            if os.path.isdir(guias_dir):
                api.upload_folder(
                    folder_path=guias_dir,
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_in_repo="guias_academia_judicial"
                )

            # 7. Subir carpeta graphify/ con el Knowledge Graph completo y wiki de comunidades
            graphify_staging = self.preparar_artefactos_graphify()
            wiki_count = 0
            if os.path.exists(graphify_staging):
                wiki_dir = os.path.join(graphify_staging, "wiki")
                if os.path.exists(wiki_dir):
                    wiki_count = len([f for f in os.listdir(wiki_dir) if f.endswith(".md")])
                api.upload_folder(
                    folder_path=graphify_staging,
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_in_repo="graphify"
                )

            # 7 bis. Quitar del repositorio los artefactos pesados y las versiones de entrenamiento
            #        (el grafo íntegro vive en data/legal_knowledge_graph.json; train/instituciones plenos
            #        van al dataset hermano -training)
            pesados_eliminados: object = 0
            try:
                existentes = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset"))
                # Ojo: los visualizadores y los formatos universales (graphml/cypher) NO se borran —
                # la tarjeta del dataset los promete y su público los usa (Gephi/yEd, Neo4j). Lo que
                # sí se aligera: graph.json (duplicado de data/legal_knowledge_graph.json) y las
                # versiones plenas de entrenamiento (viven en el dataset hermano -training).
                pesados = [
                    "graphify/graph.json",
                    "graphify/.graphify_analysis.json", "graphify/manifest.json",
                    "data/train.jsonl", "data/instituciones.jsonl",
                ]
                a_borrar = [p for p in pesados if p in existentes]
                if a_borrar:
                    ops = getattr(importlib.import_module("huggingface_hub"), "CommitOperationDelete")
                    api.create_commit(
                        repo_id=repo_id,
                        repo_type="dataset",
                        operations=[ops(path_in_repo=p) for p in a_borrar],
                        commit_message="chore(dataset): aligerar artefactos y mover las versiones plenas al dataset de entrenamiento",
                    )
                    pesados_eliminados = len(a_borrar)
            except Exception as e:
                pesados_eliminados = f"error: {e}"

            # 7 ter. Publicar el dataset hermano con las versiones plenas de entrenamiento
            entrenamiento = self.publicar_dataset_entrenamiento(token=hf_token)

            # 7 quater. Subir los textos íntegros nuevos (sentencias del TC y publicaciones ambientales)
            for carpeta, descripcion in (
                ("jurisprudencia_tc", "Sentencias del Tribunal Constitucional (últimos 2 años) en Markdown"),
                ("publicaciones_ambientales", "Anuarios y boletines de los Tribunales Ambientales en Markdown"),
            ):
                ruta = os.path.join(BASE_DIR, carpeta)
                if os.path.isdir(ruta):
                    api.upload_folder(
                        folder_path=ruta,
                        repo_id=repo_id,
                        repo_type="dataset",
                        path_in_repo=carpeta,
                        allow_patterns=["*.md"],
                    )
                    print(f"[✓] {descripcion}: {carpeta}/")

            # 8. Publicar o actualizar el Space interactivo
            space_res = None
            try:
                space_res = self.publicar_space_visualizador(space_id=space_id, token=hf_token)
            except Exception as e:
                space_res = {"exito": False, "error": str(e)}

            return {
                "exito": True,
                "repo_id": repo_id,
                "total_documentos": jsonl_res.get("total_documentos"),
                "total_instituciones": jsonl_res.get("total_instituciones"),
                "total_articulos_wiki": wiki_count,
                "artefactos_pesados_eliminados": pesados_eliminados,
                "dataset_entrenamiento": entrenamiento,
                "url": f"https://huggingface.co/datasets/{repo_id}",
                "space_url": space_res.get("url") if space_res and space_res.get("exito") else None,
                "mensaje": f"Dataset y artefactos de Graphify publicados exitosamente en Hugging Face: https://huggingface.co/datasets/{repo_id}"
            }
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "instrucciones": f"Verifica que el nombre '{repo_id}' sea válido y que tu cuenta tenga permisos."
            }


def main() -> None:
    """Punto de entrada CLI para empaquetar y sincronizar la biblioteca en Markdown."""
    import sys
    mgr = OnlineLibrarySyncManager()

    if "--tar" in sys.argv:
        tar = mgr.empaquetar_tar_gz()
        print(f"📦 Paquete .tar.gz generado en: {tar}")
    elif "--drive" in sys.argv:
        drive = mgr.preparar_bundle_google_drive()
        print(f"📁 Bundle Google Drive / NotebookLM generado en: {drive['carpeta_bundle']} ({drive['total_archivos_copiados']} archivos)")
    elif "--card" in sys.argv:
        card = mgr.preparar_dataset_card_huggingface()
        print(f"📄 Dataset Card para Hugging Face en: {card}")
    elif "--gen-jsonl" in sys.argv:
        res = mgr.generar_dataset_train_jsonl()
        print("✅ Archivos JSONL generados:")
        print(f"  • {res['train_jsonl']} ({res['total_documentos']} documentos)")
        print(f"  • {res['instituciones_jsonl']} ({res['total_instituciones']} instituciones)")
        print(f"  • {res['graph_json']}")
    elif "--upload-hf" in sys.argv:
        repo = "pablobenavidesj/doctrina-jurisprudencia-chile"
        token = None
        for arg in sys.argv:
            if arg.startswith("--repo="):
                repo = arg.split("=", 1)[1]
            elif arg.startswith("--token="):
                token = arg.split("=", 1)[1]
        print(f"⏳ Publicando corpus completo en Hugging Face: {repo}...")
        res = mgr.publicar_en_huggingface(repo_id=repo, token=token)
        if res["exito"]:
            print(f"✅ {res['mensaje']}")
            print(f"  • Documentos completos en Dataset Viewer: {res.get('total_documentos')}")
            print(f"  • Instituciones dogmáticas en Dataset Viewer: {res.get('total_instituciones')}")
        else:
            print(f"❌ Error: {res['error']}\n{res['instrucciones']}")
    else:
        manif = mgr.compilar_manifiesto_corpus()
        print(f"📚 {manif['nombre']} (v{manif['version']})")
        print(f"  • Total Obras/Guías: {manif['total_documentos']}")
        print(f"  • Total Palabras: {manif['total_palabras']:,}")
        print(f"  • Tamaño: {manif['total_megabytes']} MB")
        print("\nOpciones disponibles: --tar, --drive, --card, --gen-jsonl, --upload-hf [--repo=ORG/NAME] [--token=HF_TOKEN]")


if __name__ == "__main__":
    main()


def estado_huggingface(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> dict:
    """Comprueba la conexión con Hugging Face sin publicar nada.

    Devuelve la cuenta, el rol del token y si el dataset existe. Nunca devuelve el token.
    """
    token = resolver_token_hf()
    if not token:
        return {"conectado": False,
                "falta": f"no hay token: guardalo en {ARCHIVO_TOKEN} (permisos 0600)",
                "como": "printf '%s' 'hf_...' > ~/.openlegal/hf_token && chmod 600 ~/.openlegal/hf_token"}
    try:
        import importlib
        hf = importlib.import_module("huggingface_hub")
        api = hf.HfApi(token=token)
        quien = api.whoami()
        cuenta = quien.get("name") or (quien.get("auth") or {}).get("accessToken", {}).get("displayName")
        rol = ((quien.get("auth") or {}).get("accessToken") or {}).get("role")
        try:
            datos = api.dataset_info(repo_id)
            existe, archivos = True, len(getattr(datos, "siblings", []) or [])
        except Exception:
            existe, archivos = False, 0
        return {"conectado": True, "cuenta": cuenta, "rol_del_token": rol,
                "dataset": repo_id, "existe": existe, "archivos": archivos}
    except Exception as e:
        return {"conectado": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def _normalizar_para_buscar(texto: str) -> str:
    """Baja los acentos sin cambiar el largo: las posiciones siguen sirviendo sobre el texto original."""
    return texto.translate(str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN"))


# ── Mapa del corpus (mapa_corpus/) ────────────────────────────────────────────────────────────
# Con un mapa LISTO del dataset, el listado de archivos, el blob de cada uno y la revisión que se
# baja salen del mapa, sin red; las búsquedas lo consultan primero (rol, norma o entidad exactos y
# su texto) y citan con la URL fijada a la revisión de la fuente. Sin mapa, todo sigue como antes.
REPO_HF = "pablobenavidesj/doctrina-jurisprudencia-chile"
_RUTAS_MAPA: Dict[str, Any] = {}
_RUTAS_MAPA_LOCK = threading.Lock()


def cliente_mapa(repo_id: str = REPO_HF) -> Any:
    """El cliente del mapa si hay uno LISTO que describa `repo_id`; si no, None. Nunca usa la red."""
    try:
        from mapa_corpus.cliente import obtener_cliente
        cliente = obtener_cliente()
        if not cliente.habilitado or cliente.repo_id != repo_id or cliente.indice() is None:
            return None
        return cliente
    except Exception:  # noqa: BLE001 — sin mapa el producto sigue con sus fuentes de siempre
        return None


def estado_mapa(repo_id: str = REPO_HF) -> Dict[str, Any]:
    """Lo que una herramienta informa del mapa (`estado_breve`): si está activo, de qué fuente y
    con qué avisos. Nunca usa la red ni lanza."""
    try:
        from mapa_corpus.cliente import obtener_cliente
        cliente = obtener_cliente()
        if cliente.repo_id != repo_id:
            return {"activo": False, "motivo": f"el mapa describe {cliente.repo_id}, no {repo_id}"}
        return dict(cliente.estado_breve())
    except Exception as e:  # noqa: BLE001
        return {"activo": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def _memo_mapa(cliente: Any) -> Dict[str, Any]:
    """{ruta: blob}, rutas ordenadas y sha de la fuente del mapa en uso, memorizados por revisión:
    armar las 80 mil rutas cuesta ~0,2 s y una búsqueda las consulta varias veces."""
    ind = cliente.indice()
    if ind is None:
        return {"blobs": {}, "lista": [], "sha_fuente": ""}
    meta = ind.meta()
    clave = f"{meta.get('revision')}:{meta.get('sha256_estado')}"
    with _RUTAS_MAPA_LOCK:
        if _RUTAS_MAPA.get("clave") != clave:
            blobs = cliente.rutas()
            _RUTAS_MAPA.clear()
            _RUTAS_MAPA.update({"clave": clave, "blobs": blobs, "lista": sorted(blobs),
                                "sha_fuente": str(meta.get("sha_fuente") or "")})
        return _RUTAS_MAPA


def _blobs_mapa(cliente: Any) -> Dict[str, str]:
    return _memo_mapa(cliente)["blobs"] if cliente is not None else {}


def _url_hf(archivo: str, repo_id: str, cliente: Any = None) -> Dict[str, str]:
    """La URL del archivo: fijada a la revisión de la fuente (y la vigente aparte) si el mapa lo
    registra; si no, la de `main` de siempre."""
    if cliente is not None and archivo in _blobs_mapa(cliente):
        return {"url_huggingface": cliente.url(archivo), "url_vigente": cliente.url(archivo, fijada=False)}
    return {"url_huggingface": f"https://huggingface.co/datasets/{repo_id}/blob/main/{archivo.replace(' ', '%20')}"}


def _ruta_listado_hf(repo_id: str) -> pathlib.Path:
    return CACHE_HF / (repo_id.replace("/", "__") + "__listado.json")


def _listar_archivos_hf(repo_id: str) -> List[str]:
    """Lista los archivos del dataset: mapa del corpus → memoria (10 min) → disco (24 h) → hub.

    Con un mapa listo el listado sale de él, sin red: el del hub (~18 s) deja de ser requisito.
    El candado cubre la carrera del arranque: el precalentado del server y la primera consulta
    pueden pedir el listado a la vez; sin él ambos pagaban la misma descarga (~18 s cada uno).
    La copia en disco hace que la primera consulta de cada sesión no lo pague de nuevo; sin red,
    la copia aunque vencida se usa igual (es un índice de búsqueda, no una cita).
    """
    global _ARCHIVOS_HF_CACHE
    cliente = cliente_mapa(repo_id)
    if cliente is not None:
        lista = _memo_mapa(cliente)["lista"]
        if lista:
            return lista
    ahora = time.time()
    if _ARCHIVOS_HF_CACHE.get("repo") == repo_id and ahora - _ARCHIVOS_HF_CACHE.get("t", 0) < 600:
        return _ARCHIVOS_HF_CACHE.get("archivos", [])
    with _ARCHIVOS_HF_LOCK:
        ahora = time.time()
        if _ARCHIVOS_HF_CACHE.get("repo") == repo_id and ahora - _ARCHIVOS_HF_CACHE.get("t", 0) < 600:
            return _ARCHIVOS_HF_CACHE.get("archivos", [])
        ruta = _ruta_listado_hf(repo_id)
        archivos_disco: List[str] = []
        vencido = True
        try:
            dato = json.loads(ruta.read_text(encoding="utf-8"))
            archivos_disco = [str(a) for a in (dato.get("archivos") or [])]
            vencido = ahora - float(dato.get("t") or 0) >= _TTL_LISTADO_DISCO
        except Exception:  # noqa: BLE001 — sin copia legible se va al hub
            pass
        if archivos_disco and not vencido:
            _ARCHIVOS_HF_CACHE = {"repo": repo_id, "t": ahora, "archivos": archivos_disco}
            return archivos_disco
        try:
            from huggingface_hub import HfApi
            t0 = time.perf_counter()
            try:
                archivos = HfApi(token=resolver_token_hf()).list_repo_files(repo_id=repo_id, repo_type="dataset")
            finally:
                registrar_tiempo("hf.listado", time.perf_counter() - t0)
        except Exception:
            if archivos_disco:  # sin red: el índice viejo sirve (no se marca fresco)
                return archivos_disco
            raise
        _ARCHIVOS_HF_CACHE = {"repo": repo_id, "t": ahora, "archivos": archivos}
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps({"repo": repo_id, "t": ahora, "archivos": archivos},
                                       ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001 — no poder guardar no puede tumbar una búsqueda
            pass
        return archivos


def _linea_jsonl_legible(linea: str) -> str:
    """Convierte una línea de .jsonl en texto legible: una ficha cruda no es un pasaje citable."""
    try:
        dato = json.loads(linea)
    except Exception:  # noqa: BLE001
        return linea
    if not isinstance(dato, dict):
        return str(dato)
    partes = []
    for clave in ("titulo", "definicion", "materia", "snippet", "resumen", "contenido", "texto"):
        valor = dato.get(clave)
        if isinstance(valor, str) and valor.strip():
            partes.append(f"{clave}: {valor.strip()}")
        if len(partes) >= 3:
            break
    return " | ".join(partes) if partes else linea


def _prioridad_hf(nombre: str) -> int:
    """Ordena las coincidencias: primero el corpus legible, al final los índices de datos."""
    if nombre.startswith("doctrina/"):
        return 0
    if nombre.startswith("guias_academia_judicial/"):
        return 1
    if nombre.startswith("jurisprudencia_tc/"):
        return 2
    if nombre.startswith("publicaciones_ambientales/"):
        return 3
    if nombre.startswith("data/"):
        return 5
    return 4


def _hf_api():
    """El cliente de la API de Hugging Face (indirección para las pruebas)."""
    from huggingface_hub import HfApi
    return HfApi(token=resolver_token_hf())


def _repo_cache_dir(repo_id: str) -> pathlib.Path:
    """La carpeta local de un repo del hub dentro de la caché del corpus."""
    return CACHE_HF / repo_id.replace("/", "__")


def _leer_sincronia(repo_dir: pathlib.Path) -> dict:
    """La metadata de revisiones de un repo cacheado; sin archivo se revalida todo de nuevo."""
    try:
        dato = json.loads((repo_dir / _ARCHIVO_SINCRONIA).read_text(encoding="utf-8"))
        if isinstance(dato, dict) and isinstance(dato.get("archivos"), dict):
            return dato
    except Exception:  # noqa: BLE001 — sin metadata se revalida, no se rompe
        pass
    return {"archivos": {}}


def _escribir_sincronia(repo_dir: pathlib.Path, meta: dict) -> None:
    """Escritura atómica: una metadata a medias es peor que no tenerla."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    tmp = repo_dir / (_ARCHIVO_SINCRONIA + ".tmp")
    tmp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, repo_dir / _ARCHIVO_SINCRONIA)


def _blob_remoto(archivo: str, repo_id: str) -> Optional[str]:
    """El blob_id del archivo (identifica su revisión sin bajar contenido): el que registra el mapa
    del corpus, sin red; si el mapa no lo tiene, el del hub. None sin red."""
    blob = _blobs_mapa(cliente_mapa(repo_id)).get(archivo)
    if blob:
        return blob
    try:
        info = _hf_api().get_paths_info(repo_id, [archivo], repo_type="dataset")
    except Exception:  # noqa: BLE001 — sin red se sigue con la copia local
        return None
    for it in info or []:
        blob = getattr(it, "blob_id", None)
        if blob:
            return str(blob)
    return None


def _archivo_cambio_en_hub(archivo: str, repo_id: str) -> bool:
    """True si hay que re-bajar el archivo (el hub tiene otro blob_id).

    Con la verificación fresca (< _TTL_VERIFICACION_HF) ni consulta el hub. Si el hub no
    responde devuelve False —se sigue usando la copia— y NO marca la verificación: la próxima
    consulta vuelve a intentar.
    """
    repo_dir = _repo_cache_dir(repo_id)
    meta = _leer_sincronia(repo_dir)
    entrada = dict(meta["archivos"].get(archivo) or {})
    ahora = time.time()
    if entrada.get("blob_id") and ahora - float(entrada.get("verificado") or 0) < _TTL_VERIFICACION_HF:
        return False
    blob = _blob_remoto(archivo, repo_id)
    if blob is None:
        return False
    if entrada.get("blob_id") == blob:
        entrada["verificado"] = ahora
        meta["archivos"][archivo] = entrada
        _escribir_sincronia(repo_dir, meta)
        return False
    return True  # el hub tiene otra revisión: que el flujo normal la baje


def _anotar_descarga(archivo: str, repo_id: str, blob: Optional[str] = None) -> None:
    """Registra la revisión recién bajada (blob_id + fecha) para no revalidar de inmediato."""
    try:
        repo_dir = _repo_cache_dir(repo_id)
        meta = _leer_sincronia(repo_dir)
        meta["archivos"][archivo] = {"blob_id": blob or _blob_remoto(archivo, repo_id) or "",
                                     "verificado": time.time()}
        _escribir_sincronia(repo_dir, meta)
    except Exception:  # noqa: BLE001 — la metadata es una optimización, no un requisito
        pass


def _blob_local(archivo: str, repo_id: str, copia: pathlib.Path) -> str:
    """El blob de la copia en caché: el registrado al bajarla o, sin registro, el blob git de su
    contenido (sha1 de «blob <largo>\\0<bytes>», lo mismo que informa el hub). "" si no se sabe."""
    registrado = str((_leer_sincronia(_repo_cache_dir(repo_id))["archivos"].get(archivo) or {}).get("blob_id") or "")
    if registrado:
        return registrado
    try:
        if copia.stat().st_size > _TAMANO_MAX_HF:
            return ""
        datos = copia.read_bytes()
    except OSError:
        return ""
    # El oid de git ES sha1 por definición (lo que informa el hub): integridad, no seguridad.
    # nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
    return hashlib.sha1(b"blob %d\0" % len(datos) + datos, usedforsecurity=False).hexdigest()


def _bajar_hf(archivo: str, repo_id: str, destino: pathlib.Path, revision: Optional[str] = None) -> bool:
    """Baja un archivo del dataset a la caché local. Con `revision` (el sha de la fuente del mapa)
    baja esa revisión FIJADA; sin ella, la vigente. False si no se pudo usar."""
    from huggingface_hub import hf_hub_download
    t0 = time.perf_counter()
    try:
        if revision:
            # Con mapa: la revisión de la fuente que el mapa describe, la misma que citan sus URLs.
            ruta = hf_hub_download(repo_id=repo_id, filename=archivo, repo_type="dataset", revision=revision,
                                   token=resolver_token_hf(), cache_dir=str(CACHE_HF / repo_id.replace("/", "__")))
        else:
            # El dataset es el PROPIO de Open Legal Chile, que esta misma suite publica y actualiza:
            # sin mapa, la búsqueda tiene que ver el corpus más fresco, no una revisión congelada. Lo
            # que se baja son datos (markdown/jsonl) que nunca se ejecutan y se validan antes de
            # usarse (extensión permitida, tope de tamaño y lectura defensiva de cada línea).
            ruta = hf_hub_download(  # nosec B615
                                   repo_id=repo_id, filename=archivo, repo_type="dataset",
                                   token=resolver_token_hf(),
                                   cache_dir=str(CACHE_HF / repo_id.replace("/", "__")))
    finally:
        registrar_tiempo("hf.descarga", time.perf_counter() - t0)
    origen = pathlib.Path(ruta)
    if not origen.exists() or origen.stat().st_size > _TAMANO_MAX_JSONL:
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.resolve() != origen.resolve():
        destino.write_bytes(origen.read_bytes())
    return True


def _descargar_trozo_hf(archivo: str, repo_id: str, tokens: Optional[List[str]] = None) -> str:
    """Devuelve el texto de un archivo del dataset (con caché local en ~/.openlegal/hf_cache).

    Los .jsonl se filtran por línea para no cargar 80 MB de fichas en memoria; el resto se lee
    entero solo si es razonablemente chico. Ante cualquier falla devuelve "" — la búsqueda sigue
    funcionando con las rutas y nunca inventa texto.

    Con el mapa del corpus, la copia vale si su blob es el que registra el mapa (sin preguntarle
    al hub); si difiere, se baja la revisión FIJADA de la fuente del mapa, la misma que citan
    sus URLs. Un archivo que el mapa no registra sigue el camino de siempre.
    """
    if not archivo.lower().endswith(_TEXTO_HF):
        return ""
    # Optimización: si el archivo existe en el repo local (ej. doctrina/), leer directamente
    local_path = pathlib.Path(BASE_DIR) / archivo
    if local_path.is_file() and local_path.stat().st_size <= _TAMANO_MAX_HF:
        return local_path.read_text(encoding="utf-8", errors="ignore")

    destino = CACHE_HF / repo_id.replace("/", "__") / archivo
    try:
        cliente = cliente_mapa(repo_id)
        blob_mapa = _blobs_mapa(cliente).get(archivo)
        if blob_mapa:
            if destino.exists() and _blob_local(archivo, repo_id, destino) != blob_mapa:
                destino.unlink()  # la copia no es la revisión que describe el mapa
            if not destino.exists():
                if not _bajar_hf(archivo, repo_id, destino, revision=_memo_mapa(cliente)["sha_fuente"] or None):
                    return ""
                _anotar_descarga(archivo, repo_id, blob=blob_mapa)
        else:
            if destino.exists() and _archivo_cambio_en_hub(archivo, repo_id):
                destino.unlink()  # el hub tiene una revisión más nueva: se vuelve a bajar
            if not destino.exists():
                if not _bajar_hf(archivo, repo_id, destino):
                    return ""
                _anotar_descarga(archivo, repo_id)
        if destino.suffix == ".jsonl":
            if destino.stat().st_size > _TAMANO_MAX_JSONL:
                return ""
            agujas = [_normalizar_para_buscar(t).lower() for t in (tokens or []) if len(t) > 2]
            try:
                import hf_cache_index
                lineas = hf_cache_index.buscar(
                    destino, agujas, maximo=20, transformar=_linea_jsonl_legible,
                    normalizar=lambda t: _normalizar_para_buscar(t).lower())
                return "\n".join(lineas)
            except Exception:  # noqa: BLE001 — el índice es una optimización, no un requisito
                pass
            lineas = []
            with destino.open(encoding="utf-8", errors="ignore") as f:
                for i, linea in enumerate(f):
                    if i > 200_000:
                        break
                    if not agujas or any(a in _normalizar_para_buscar(linea).lower() for a in agujas):
                        lineas.append(_linea_jsonl_legible(linea))
                    if len(lineas) >= 20:
                        break
            return "\n".join(lineas)
        if destino.stat().st_size > _TAMANO_MAX_HF:
            return ""
        return destino.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extractos_hf(texto: str, tokens: List[str], ancho: int = 400, maximo: int = 3) -> List[str]:
    """Devuelve hasta `maximo` pasajes del texto alrededor de los términos buscados.

    Busca sin acentos («simulacion» encuentra «simulación») pero devuelve el texto original.
    """
    piezas: List[str] = []
    bajo = _normalizar_para_buscar(texto).lower()
    for token in tokens:
        t = _normalizar_para_buscar(token).lower().strip()
        if len(t) < 3:
            continue
        pos = bajo.find(t)
        while pos >= 0 and len(piezas) < maximo:
            inicio = max(0, pos - ancho // 2)
            pasaje = re.sub(r"\s+", " ", texto[inicio:pos + ancho]).strip()
            if pasaje and pasaje not in piezas:
                piezas.append(pasaje)
            pos = bajo.find(t, pos + len(t))
        if len(piezas) >= maximo:
            break
    return piezas


def _clasificar_tipo_hf(f: str) -> str:
    """Clasifica el tipo de archivo dentro del dataset público de Hugging Face."""
    if f.startswith("graphify/wiki/"):
        return "wiki_comunidad"
    if f in ("graphify/graph.html", "graphify/GRAPH_TREE.html", "graphify/GRAPH_CALLFLOW.html"):
        return "visualizador_interactivo"
    if f in ("graphify/graph.json", "graphify/graph.graphml", "graphify/cypher.txt"):
        return "grafo_conocimiento"
    if f == "graphify/GRAPH_REPORT.md":
        return "reporte_comunidades"
    if f.startswith("guias_academia_judicial/"):
        return "guia_academia_judicial"
    if f.startswith("doctrina/"):
        return "doctrina_markdown"
    if f.startswith("data/"):
        return "datos_estructurados"
    if f.startswith("jurisprudencia_cs/"):
        return "jurisprudencia_cs"
    if f.startswith("jurisprudencia_tc/"):
        return "jurisprudencia_tc"
    if f.startswith("jurisprudencia_ambiental/"):
        return "jurisprudencia_ambiental"
    if f.startswith("biblioteca_ambiental/"):
        return "biblioteca_ambiental"
    if f.startswith("publicaciones_ambientales/"):
        return "publicacion_ambiental"
    return "recurso"


def _formatear_cita_hf(f: str, repo_id: str, tipo: str, nombre_base: str) -> str:
    """Genera la cita oficial en formato de corchetes conforme al estándar de AGENTS.md."""
    if tipo == "wiki_comunidad":
        return f"[Hugging Face - {repo_id}, Wiki Comunidad: {nombre_base}]"
    if tipo == "visualizador_interactivo":
        return f"[Hugging Face - {repo_id}, Visualizador: {nombre_base}]"
    if tipo == "grafo_conocimiento":
        return f"[Hugging Face - {repo_id}, Grafo: {nombre_base}]"
    if tipo == "reporte_comunidades":
        return f"[Hugging Face - {repo_id}, Reporte: {nombre_base}]"
    if tipo == "guia_academia_judicial":
        return f"[Hugging Face - {repo_id}, Guía Judicial: {nombre_base}]"
    if tipo == "datos_estructurados":
        return f"[Hugging Face - {repo_id}, Datos: {f}]"
    return f"[Hugging Face - {repo_id}, Archivo: {f}]"


def _construir_respuesta_hf(query: str, repo_id: str, space_id: str,
                             coincidencias: List[Dict[str, Any]],
                             citas: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "dataset_origen": f"https://huggingface.co/datasets/{repo_id}",
        "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
        "query": query,
        "total_coincidencias": len(coincidencias),
        "resultados": coincidencias,
        "citas": citas,
        "cita_fuente": f"[Hugging Face - Datasets Hub: https://huggingface.co/datasets/{repo_id}]"
    }


_CATALOGO_INSTITUCIONES: Optional[List[Dict[str, Any]]] = None
_INDICE_INSTITUCIONES: Optional[Dict[str, List[int]]] = None
_CATALOGO_INST_LOCK = threading.Lock()


def invalidar_cache_catalogo() -> None:
    """Invalida la caché en memoria del catálogo de instituciones para recargar cambios."""
    global _CATALOGO_INSTITUCIONES, _INDICE_INSTITUCIONES
    with _CATALOGO_INST_LOCK:
        _CATALOGO_INSTITUCIONES = None
        _INDICE_INSTITUCIONES = None


def _obtener_catalogo_instituciones() -> Tuple[List[Dict[str, Any]], Dict[str, List[int]]]:
    """Carga e indexa en memoria las 11.858 instituciones de data/catalogo/instituciones_lite.jsonl."""
    global _CATALOGO_INSTITUCIONES, _INDICE_INSTITUCIONES
    if _CATALOGO_INSTITUCIONES is not None and _INDICE_INSTITUCIONES is not None:
        return _CATALOGO_INSTITUCIONES, _INDICE_INSTITUCIONES

    with _CATALOGO_INST_LOCK:
        if _CATALOGO_INSTITUCIONES is not None and _INDICE_INSTITUCIONES is not None:
            return _CATALOGO_INSTITUCIONES, _INDICE_INSTITUCIONES

        cat_path = os.path.join(BASE_DIR, "data", "catalogo", "instituciones_lite.jsonl")
        if not os.path.isfile(cat_path):
            cat_path = os.path.join(BASE_DIR, "data", "catalogo", "train_lite.jsonl")
        items: List[Dict[str, Any]] = []
        indice: Dict[str, List[int]] = {}

        if os.path.isfile(cat_path):
            try:
                with open(cat_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            it = json.loads(line)
                            if "institucion" not in it and "titulo" in it:
                                it["institucion"] = it.get("titulo", "")
                            if "definicion" not in it:
                                it["definicion"] = it.get("materia", "")
                            items.append(it)
                        except Exception:
                            pass

                for i, it in enumerate(items):
                    texto = f"{it.get('institucion', '')} {it.get('materia', '')} {it.get('autor', '')} {it.get('area', '')} {it.get('definicion', '')[:300]}"
                    norm = _normalizar_para_buscar(texto).lower()
                    words = set(re.findall(r"\b\w{3,}\b", norm))
                    for w in words:
                        if w not in _PALABRAS_VACIAS:
                            indice.setdefault(w, []).append(i)
            except Exception:
                items = []
                indice = {}

        _CATALOGO_INSTITUCIONES = items
        _INDICE_INSTITUCIONES = indice
        return _CATALOGO_INSTITUCIONES, _INDICE_INSTITUCIONES


def _buscar_catalogo_instituciones(tokens_q: List[str], query_norm: str, limit: int = 5,
                                    repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile",
                                    space_id: str = "pablobenavidesj/open-legal-chile-graph") -> List[Dict[str, Any]]:
    """Busca en las 11.858 instituciones canónicas indexadas con ranking ponderado y texto literal."""
    items, indice = _obtener_catalogo_instituciones()
    if not items or not indice or not tokens_q:
        return []

    from collections import Counter
    scores: Counter = Counter()
    for t in tokens_q:
        for idx in indice.get(t, []):
            it = items[idx]
            inst_norm = _normalizar_para_buscar(it.get("institucion", "")).lower()
            mat_norm = _normalizar_para_buscar(it.get("materia", "")).lower()
            aut_norm = _normalizar_para_buscar(it.get("autor", "")).lower()
            sc = 2
            if t in inst_norm:
                sc += 10
            if t in mat_norm:
                sc += 5
            if t in aut_norm:
                sc += 15
            if query_norm in inst_norm or query_norm in aut_norm:
                sc += 25
            scores[idx] += sc

    resultados: List[Dict[str, Any]] = []
    vistos_archivos = set()
    cliente = cliente_mapa(repo_id)
    for idx, _ in scores.most_common(limit * 3):
        it = items[idx]
        archivo = it.get("archivo", "").strip()
        if not archivo:
            continue
        if not archivo.startswith("doctrina/") and not archivo.startswith("guias_"):
            archivo_hf = f"doctrina/{archivo}"
        else:
            archivo_hf = archivo
        if archivo_hf in vistos_archivos:
            continue
        vistos_archivos.add(archivo_hf)

        definicion = (it.get("definicion") or "").strip()
        extractos: List[str] = []
        if definicion:
            fallo = it.get("fallo_rector", "")
            ext = definicion
            if fallo and fallo not in ext:
                ext += f" Fallo rector: {fallo}"
            extractos.append(ext[:400])
        else:
            pasajes = _extractos_hf(_descargar_trozo_hf(archivo_hf, repo_id, tokens_q), tokens_q)
            if pasajes:
                extractos.extend(pasajes[:2])
            else:
                materia = it.get("materia", "")
                inst_nom = it.get("institucion", "")
                autor = it.get("autor", "")
                extractos.append(f"{inst_nom} ({autor}) — Materia: {materia}."[:400])

        cita = f"[Hugging Face - {repo_id}, Archivo: {archivo_hf}]"
        resultados.append({
            "archivo": archivo_hf,
            "dataset": repo_id,
            **_url_hf(archivo_hf, repo_id, cliente),
            "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
            "tipo": "doctrina_markdown",
            "cita_estandar": cita,
            "extractos": extractos,
            "tiene_texto": bool(extractos),
            "_score": scores[idx],
        })
        if len(resultados) >= limit:
            break
    return resultados


def _buscar_catalogo_jurisprudencia(query: str, limit: int = 5,
                                     repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile",
                                     space_id: str = "pablobenavidesj/open-legal-chile-graph",
                                     archivos: Optional[set] = None) -> List[Dict[str, Any]]:
    """Busca en el corpus local cosechado de jurisprudencia judicial (CS, TC, Ambiental).

    `archivos` es el listado del dataset: si viene, ninguna ruta se cita sin estar en él. Una
    ruta que no existe se reemplaza por el archivo del dataset donde vive el registro (su JSONL):
    nunca se inventa una ruta. Con el mapa del corpus, la ruta de la ficha sale del mapa (por el
    ID canónico del rol) y su URL queda fijada a la revisión de la fuente.
    """
    try:
        from pjud_connector import buscar_sentencias_locales, ruta_hf_corte_suprema
        sentencias = buscar_sentencias_locales(query, limit=limit)
    except Exception:
        sentencias = []

    cliente = cliente_mapa(repo_id) if sentencias else None
    resultados: List[Dict[str, Any]] = []
    for s in sentencias:
        rol = str(s.get("rol") or "").strip()
        clean_rol = re.sub(r"^Rol\s*N°?\s*", "", rol, flags=re.IGNORECASE).strip()
        fecha = str(s.get("fecha") or "").strip()
        tribunal = str(s.get("tribunal") or "Corte Suprema").strip()
        caratula = str(s.get("caratula") or "").strip()
        recurso = str(s.get("recurso") or "").strip()
        resultado_fallo = str(s.get("resultado") or "").strip()

        archivo_md = str(s.get("archivo_md") or "").strip()
        fuente = str(s.get("archivo_fuente") or "").strip()
        fila = _fila_mapa_de_sentencia(cliente, s) if cliente is not None else None
        if fila and fila.get("ruta"):
            archivo_hf = str(fila["ruta"])
            tipo = _clasificar_tipo_hf(archivo_hf)
        elif "Constitucional" in tribunal or archivo_md.startswith("jurisprudencia_tc"):
            archivo_hf = archivo_md or f"jurisprudencia_tc/{clean_rol}.md"
            tipo = "jurisprudencia_tc"
        elif "Ambiental" in tribunal or archivo_md.startswith("jurisprudencia_ambiental"):
            archivo_hf = archivo_md or f"jurisprudencia_ambiental/{clean_rol}.md"
            tipo = "jurisprudencia_ambiental"
        else:
            # La ficha .md de la CS vive en jurisprudencia_cs/{era}/{mes}/{rol}.md. Sin listado,
            # solo se da por cierta cuando el registro sale del índice que generó esas fichas.
            archivo_hf = archivo_md or ruta_hf_corte_suprema(s) or ""
            if archivo_hf and archivos is None and not archivo_md \
                    and not fuente.endswith("cs_sentencias_2anios.jsonl"):
                archivo_hf = ""
            tipo = "jurisprudencia_cs"
        if fuente and (not archivo_hf or (archivos is not None and archivo_hf not in archivos)):
            archivo_hf = fuente
        if not archivo_hf:
            continue

        cita = f"[Hugging Face - {repo_id}, Archivo: {archivo_hf}]"
        extracto = (f"Sentencia {tribunal} Rol {rol} ({fecha}): {caratula}. "
                    f"Recurso: {recurso}. Resultado: {resultado_fallo}.").strip()

        resultados.append({
            "archivo": archivo_hf,
            "dataset": repo_id,
            **_url_hf(archivo_hf, repo_id, cliente),
            "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
            "tipo": tipo,
            "cita_estandar": cita,
            "extractos": [extracto],
            "tiene_texto": True,
        })
    return resultados


# Colecciones del mapa y sus nombres de uso común (el parámetro `coleccion`).
_ALIAS_COLECCION = {
    "cs": "cs", "corte_suprema": "cs", "suprema": "cs", "jurisprudencia_cs": "cs",
    "tc": "tc", "constitucional": "tc", "tribunal_constitucional": "tc", "jurisprudencia_tc": "tc",
    "ta": "ta", "ambiental": "ta", "ambientales": "ta", "tribunales_ambientales": "ta",
    "jurisprudencia_ambiental": "ta",
    "doc": "doc", "doctrina": "doc", "revista": "doc", "revistas": "doc",
    "guia": "guia", "guias": "guia", "academia_judicial": "guia", "guias_academia_judicial": "guia",
    "bib": "bib", "biblioteca": "bib", "biblioteca_ambiental": "bib",
    "pub": "pub", "publicaciones": "pub", "publicaciones_ambientales": "pub",
    "dato": "dato", "datos": "dato", "data": "dato", "graphify": "graphify",
}
# Colección de un resultado que no viene del mapa (catálogo, rutas), según su tipo.
_COLECCION_DE_TIPO = {
    "jurisprudencia_cs": "cs", "jurisprudencia_tc": "tc", "jurisprudencia_ambiental": "ta",
    "doctrina_markdown": "doc", "guia_academia_judicial": "guia", "biblioteca_ambiental": "bib",
    "publicacion_ambiental": "pub", "datos_estructurados": "dato", "wiki_comunidad": "graphify",
    "visualizador_interactivo": "graphify", "grafo_conocimiento": "graphify", "reporte_comunidades": "graphify",
}
# Palabras que delatan una consulta de jurisprudencia (sin tildes).
_PALABRAS_JURISPRUDENCIA = ("sentencia", "fallo", "amparo", "casacion", "proteccion", "unificacion")
_RE_ROL_CONSULTA = re.compile(r"\b(rol|rit|c-?\d|t-?\d|\d{3,6}-\d{4})\b")
# El corpus con texto (doctrina, guías, TC, ambientales): en la búsqueda de texto del mapa va antes
# que las fichas de la CS, que solo traen metadatos (carátula, partes).
_COLS_CON_TEXTO = ["doc", "guia", "tc", "ta", "pub", "bib"]
# Palabras que acompañan a un identificador («Rol», «art.», «Código Civil»): si la consulta no trae
# nada más que eso, ES el identificador, y la búsqueda de texto del mapa solo sumaría ruido.
_PALABRAS_DE_IDENTIFICADOR = {
    "rol", "roles", "causa", "sentencia", "fallo", "ficha", "corte", "suprema", "excma", "recurso", "stc",
    "tribunal", "constitucional", "ambiental", "art", "arts", "articulo", "articulos", "inciso", "numeral",
    "bis", "ter", "transitorio", "codigo", "civil", "penal", "procesal", "procedimiento", "trabajo",
    "comercio", "aguas", "mineria", "organico", "tribunales", "ley", "leyes", "decreto", "dfl",
    "constitucion", "politica", "republica", "cpr", "inc", "nro", "num",
}


def _tokens_consulta(texto: str) -> List[str]:
    """Términos de búsqueda sin tildes, sin palabras vacías ni términos de dos letras."""
    return [t for t in (_normalizar_para_buscar(x).lower() for x in re.split(r"[_\-\s]+", texto.lower().strip()))
            if len(t) > 2 and t not in _PALABRAS_VACIAS]


def _prosa(tokens: List[str]) -> List[str]:
    """Los términos que no son parte de un identificador (números de rol o de artículo, «Rol»,
    «art.», «Código Civil»…): lo que la consulta dice además del rol o la norma."""
    salida: List[str] = []
    for t in tokens:
        limpio = re.sub(r"[\W_]+", "", t)
        if limpio and not limpio.isdigit() and limpio not in _PALABRAS_DE_IDENTIFICADOR:
            salida.append(t)
    return salida


def _colecciones(valor: Any) -> List[str]:
    """«cs», «Corte Suprema», «doctrina, tc» o una lista → colecciones del mapa, sin repetir."""
    crudos = valor if isinstance(valor, (list, tuple)) else re.split(r"[,;]", str(valor or ""))
    salida: List[str] = []
    for crudo in crudos:
        clave = re.sub(r"[\s\-]+", "_", _normalizar_para_buscar(str(crudo)).lower().strip())
        col = _ALIAS_COLECCION.get(clave, clave)
        if col and re.fullmatch(r"[a-z_]+", col) and col not in salida:
            salida.append(col)
    return salida


def _sin_repetir(valores: Sequence[Optional[str]]) -> List[str]:
    salida: List[str] = []
    for valor in valores:
        if valor and valor not in salida:
            salida.append(valor)
    return salida


def _ids_de_rol(cliente: Any, rol: str) -> List[str]:
    """IDs canónicos de un rol dado como parámetro (CS, TC o ambiental); si alguno existe en el
    mapa, solo los que existen («R-21-2021» puede ser de cualquiera de los tres tribunales)."""
    from citas_legales import rol_canonico
    rol = str(rol or "").strip()
    if re.match(r"^(?:cs|tc|ta):\S", rol):
        return [rol]
    candidatos = _sin_repetir([rol_canonico(rol, tribunal) for tribunal in (None, "tc", "1ta", "2ta", "3ta")])
    existentes = [i for i in candidatos if cliente.entrada(i) is not None]
    return existentes or candidatos[:1]


def _ids_de_norma(norma: str) -> List[str]:
    """IDs canónicos de una norma dada como parámetro («art. 1545 del Código Civil», «Ley 19.300»)."""
    from citas_legales import normas_canonicas, resolver_consulta
    norma = str(norma or "").strip()
    if norma.startswith("norma:"):
        return [norma]
    ids = [i for i in resolver_consulta(norma) if i.startswith("norma:")]
    return ids or [i for i, _ in normas_canonicas(norma)]


def _ids_de_entidad(cliente: Any, entidad: str) -> List[str]:
    """IDs del mapa de un ministro, autor, revista, sala, tribunal o recurso, dado por su nombre
    («María Gajardo Harboe», «Tercera Sala») o por su ID («revista:rchd»): solo los que existen."""
    entidad = str(entidad or "").strip()
    if re.match(r"^[a-z_]+:\S", entidad):
        return [entidad]
    from mapa_corpus import ids as ids_mapa
    slug = ids_mapa.slug(entidad)
    candidatos = _sin_repetir([ids_mapa.ministro_id(entidad), ids_mapa.autor_id(entidad),
                               ids_mapa.revista_id(entidad) if slug else None, ids_mapa.sala_id(entidad),
                               ids_mapa.tribunal_id(entidad), ids_mapa.recurso_id(entidad),
                               f"organo:{slug}" if slug else None])
    return [i for i in candidatos if cliente.entidad(i) is not None]


def _fila_mapa_de_sentencia(cliente: Any, s: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """La entrada del mapa de una sentencia del corpus local (por el ID canónico de su rol), o None."""
    from citas_legales import rol_canonico
    id_ = next((str(s[c]) for c in ("id_mapa", "id") if re.match(r"^(?:cs|tc|ta):\S", str(s.get(c) or ""))), "")
    if not id_:
        rol = str(s.get("rol") or "")
        tribunal = _normalizar_para_buscar(str(s.get("tribunal") or "")).lower()
        archivo_md = str(s.get("archivo_md") or "")
        if "constitucional" in tribunal or archivo_md.startswith("jurisprudencia_tc"):
            id_ = rol_canonico(rol, "tc") or ""
        elif "ambiental" in tribunal or archivo_md.startswith("jurisprudencia_ambiental"):
            m = re.search(r"/([123])TA/", archivo_md, re.IGNORECASE)
            numero = m.group(1) if m else next(
                (n for palabra, n in (("primer", "1"), ("segundo", "2"), ("tercer", "3")) if palabra in tribunal), "")
            id_ = (rol_canonico(rol, f"{numero}ta") or "") if numero else ""
        else:
            id_ = rol_canonico(rol, "cs") or ""
    try:
        return cliente.entrada(id_) if id_ else None
    except Exception:  # noqa: BLE001 — sin mapa consultable, la ruta se arma como siempre
        return None


def _cita_corte_suprema(fila: Dict[str, Any]) -> str:
    """«[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]», el corchete oficial de una ficha de la CS."""
    m = re.fullmatch(r"(\d+)-(\d{4})", str(fila.get("rol") or ""))
    if not m:
        return ""
    rol = f"{int(m.group(1)):,}".replace(",", ".") + f"-{m.group(2)}"
    f = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(fila.get("fecha") or ""))
    return f"[CS - Rol N° {rol}, Fecha: {f.group(3)}-{f.group(2)}-{f.group(1)}]" if f else f"[CS - Rol N° {rol}]"


def _texto_local_hf(archivo: str, repo_id: str, blob: str) -> str:
    """El texto del archivo si ya está en disco (el repo, o la caché con el blob que registra el
    mapa); si no, "". Nunca baja nada: sirve para que un resultado del mapa traiga el pasaje."""
    if not archivo.lower().endswith((".md", ".txt")) or archivo.startswith("/") \
            or ".." in pathlib.PurePosixPath(archivo).parts:
        return ""
    for ruta, exige_blob in ((pathlib.Path(BASE_DIR) / archivo, False), (_repo_cache_dir(repo_id) / archivo, True)):
        try:
            if ruta.is_file() and ruta.stat().st_size <= _TAMANO_MAX_HF \
                    and (not exige_blob or _blob_local(archivo, repo_id, ruta) == blob):
                return ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return ""


def _extractos_mapa(fila: Dict[str, Any], tokens: List[str], repo_id: str) -> List[str]:
    """Pasajes citables de una entrada del mapa: la ficha de la CS tal como la registra el
    dataset; del resto, el pasaje que calza (si el texto ya está en disco) o su resumen."""
    if fila.get("col") == "cs":
        partes = [f"Sentencia Corte Suprema Rol {fila.get('rol') or ''} ({fila.get('fecha') or 's/f'}): "
                  f"{fila.get('titulo') or ''}."]
        if fila.get("recurso_txt"):
            partes.append(f"Recurso: {fila['recurso_txt']}.")
        if fila.get("resultado"):
            partes.append(f"Resultado: {fila['resultado']}.")
        if fila.get("ministros_txt"):
            partes.append("Ministros: " + ", ".join(str(m) for m in fila["ministros_txt"]) + ".")
        return [" ".join(partes)]
    pasajes: List[str] = []
    if tokens:
        pasajes = _extractos_hf(_texto_local_hf(str(fila.get("ruta") or ""), repo_id, str(fila.get("blob") or "")),
                                tokens)
    resumen = " ".join(str(fila.get("resumen") or "").split())
    if not pasajes and resumen:
        pasajes = (_extractos_hf(resumen, tokens) if tokens else []) or [resumen]
    return pasajes[:3]


def _resultado_mapa(cliente: Any, fila: Dict[str, Any], repo_id: str, space_id: str, tokens: List[str],
                    relacion: str) -> Dict[str, Any]:
    """Un resultado de búsqueda desde una entrada del mapa, con la forma de siempre más su ID, su
    colección, cómo calzó (`relacion`: exacto, cita o texto) y las dos URLs."""
    ruta = str(fila.get("ruta") or "")
    tipo = _clasificar_tipo_hf(ruta)
    extractos = _extractos_mapa(fila, tokens, repo_id)
    resultado: Dict[str, Any] = {
        "archivo": ruta,
        "dataset": repo_id,
        "url_huggingface": cliente.url(ruta),
        "url_vigente": cliente.url(ruta, fijada=False),
        "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
        "tipo": tipo,
        "cita_estandar": _formatear_cita_hf(ruta, repo_id, tipo, os.path.basename(ruta)),
        "extractos": extractos,
        "tiene_texto": bool(extractos),
        "origen": "mapa_hf",
        "id": fila.get("id"),
        "coleccion": fila.get("col"),
        "relacion": relacion,
    }
    for clave in ("titulo", "fecha", "rol", "recurso_txt", "resultado", "ministros_txt", "autores_txt",
                  "revista", "anio"):
        if fila.get(clave):
            resultado[clave] = fila[clave]
    cita_oficial = fila.get("cita_oficial") or fila.get("cita") or (
        _cita_corte_suprema(fila) if fila.get("col") == "cs" else "")
    if cita_oficial:
        resultado["cita_oficial"] = cita_oficial
    if fila.get("col") == "cs" and fila.get("rol"):
        # El dataset trae la ficha de la CS, no el fallo: el texto íntegro se consulta en vivo.
        resultado["como_obtener_texto"] = (f"pjud_analizar_sentencia con rol='{fila['rol']}': el texto íntegro "
                                           "se trae en vivo de juris.pjud.cl")
    return resultado


def _grupos_de_texto(texto: str, terminos: str, cols: List[str]) -> List[Tuple[Optional[List[str]], str]]:
    """(colecciones, términos) de cada pasada de la búsqueda de texto del mapa, en orden: el corpus
    con texto antes que las fichas de la CS (solo metadatos), salvo en una consulta de
    jurisprudencia; la wiki del dataset primero si se la pide; al final, el resto."""
    if not terminos:
        return []
    if cols:
        return [(cols, terminos)]
    plano = _normalizar_para_buscar(texto).lower()
    if _RE_ROL_CONSULTA.search(plano) or any(k in plano for k in _PALABRAS_JURISPRUDENCIA):
        return [(["cs"], terminos), (_COLS_CON_TEXTO, terminos), (None, terminos)]
    if any(k in plano for k in ("wiki", "comunidad", "grafo")):
        # En la wiki se busca el tema, no la palabra «wiki» (que calza con todas sus páginas).
        tema = " ".join(t for t in terminos.split() if not t.startswith(("wiki", "comunidad", "grafo")))
        return [(["graphify"], tema or terminos), (_COLS_CON_TEXTO, terminos), (["cs"], terminos), (None, terminos)]
    return [(_COLS_CON_TEXTO, terminos), (["cs"], terminos), (None, terminos)]


def _buscar_en_mapa(cliente: Any, texto: str, rol: Optional[str], norma: Optional[str], entidad: Optional[str],
                    cols: List[str], limit: int, repo_id: str, space_id: str,
                    tokens: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Lo que el mapa sabe de la consulta, en orden: las fichas exactas (rol), quién cita la
    norma, el rol o la entidad, y después su búsqueda de texto. Nunca usa la red."""
    from citas_legales import resolver_consulta
    exactos: List[str] = _ids_de_rol(cliente, rol) if rol else []
    citados: List[str] = list(exactos)
    if norma:
        citados += _ids_de_norma(norma)
    if entidad:
        citados += _ids_de_entidad(cliente, entidad)
    de_consulta = resolver_consulta(texto) if texto else []
    exactos = _sin_repetir(exactos + [i for i in de_consulta if not i.startswith("norma:")])
    citados = _sin_repetir(citados + de_consulta)

    filas: List[Tuple[Dict[str, Any], str]] = []
    for id_ in exactos:
        fila = cliente.entrada(id_)
        if fila:
            filas.append((fila, "exacto"))
    total_citantes = 0
    if citados:
        citantes, total_citantes = cliente.citantes(citados, cols or None, limite=limit)
        filas += [(f, "cita") for f in citantes]
    # Con un identificador resuelto, el texto solo busca lo que la consulta dice además de él.
    consulta_texto = " ".join(_prosa(tokens) if (exactos or citados) else tokens)
    for grupo, terminos in _grupos_de_texto(texto, consulta_texto, cols):
        if len(filas) >= limit:
            break
        filas += [(f, "texto") for f in cliente.buscar(terminos, grupo, limite=limit)]

    resultados: List[Dict[str, Any]] = []
    vistos: set = set()
    for fila, relacion in filas:
        ruta = fila.get("ruta")
        if not ruta or ruta in vistos or (cols and fila.get("col") not in cols):
            continue
        vistos.add(ruta)
        resultados.append(_resultado_mapa(cliente, fila, repo_id, space_id, tokens, relacion))
    detalle: Dict[str, Any] = {}
    if exactos or citados or cols:
        detalle = {"ids": _sin_repetir(exactos + citados), "citantes_total": total_citantes, "colecciones": cols}
    return resultados, detalle


def _candidatos_tradicionales(consulta: str, query_norm: str, tokens_q: List[str], limit: int, repo_id: str,
                              space_id: str, excluir: set, cliente: Any,
                              cols: Optional[List[str]] = None) -> Iterator[Dict[str, Any]]:
    """Los candidatos de siempre, en su orden: catálogo de instituciones, de jurisprudencia y rutas
    del dataset (con un listado de prueba de < 100 archivos, solo las rutas). Es un generador: el
    texto de cada ruta se baja recién cuando el consumidor lo pide. Con `cols`, lo que cae fuera de
    esas colecciones ni se busca ni se baja."""
    files = _listar_archivos_hf(repo_id)

    def _en_cols(*tipos: str) -> bool:
        return not cols or any(_COLECCION_DE_TIPO.get(t) in cols for t in tipos)

    def _por_ruta(f: str) -> Dict[str, Any]:
        tipo = _clasificar_tipo_hf(f)
        extractos = _extractos_hf(_descargar_trozo_hf(f, repo_id, tokens_q), tokens_q)
        return {
            "archivo": f,
            "dataset": repo_id,
            **_url_hf(f, repo_id, cliente),
            "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
            "tipo": tipo,
            "cita_estandar": _formatear_cita_hf(f, repo_id, tipo, os.path.basename(f)),
            "extractos": extractos,
            "tiene_texto": bool(extractos),
        }

    candidatos_paths = sorted((f for f in files if f not in excluir and _en_cols(_clasificar_tipo_hf(f))
                               and any(t in _normalizar_para_buscar(f).lower() for t in tokens_q)),
                              key=lambda f: (_prioridad_hf(f), f))
    # Modo test / mock aislado: si _listar_archivos_hf devuelve una lista reducida (< 100 archivos)
    if len(files) < 100:
        for f in candidatos_paths:
            yield _por_ruta(f)
        return

    # Modo producción (catálogo ultra-eficiente de 73.203 archivos y 11.858 instituciones)
    es_rol = bool(_RE_ROL_CONSULTA.search(query_norm))
    es_jurisprudencia = es_rol or any(k in query_norm for k in _PALABRAS_JURISPRUDENCIA)

    candidatos_inst = _buscar_catalogo_instituciones(tokens_q, query_norm, limit=limit, repo_id=repo_id, space_id=space_id) \
        if _en_cols("doctrina_markdown") else []
    candidatos_juris = _buscar_catalogo_jurisprudencia(consulta, limit=limit, repo_id=repo_id, space_id=space_id,
                                                       archivos=set(files)) \
        if (es_jurisprudencia or len(candidatos_inst) < limit) \
        and _en_cols("jurisprudencia_cs", "jurisprudencia_tc", "jurisprudencia_ambiental") else []
    candidatos_archivos = [_por_ruta(f) for f in candidatos_paths[:limit]]

    if es_jurisprudencia:
        orden = candidatos_juris + candidatos_inst + candidatos_archivos
    elif any(k in query_norm for k in ("wiki", "comunidad", "grafo", "guia")):
        orden = candidatos_archivos + candidatos_inst + candidatos_juris
    else:
        orden = candidatos_inst + candidatos_archivos + candidatos_juris
    yield from orden


def consultar_huggingface_dataset(query: str, limit: int = 5,
                                  repo_id: str = REPO_HF,
                                  space_id: str = "pablobenavidesj/open-legal-chile-graph",
                                  rol: Optional[str] = None, norma: Optional[str] = None,
                                  coleccion: Any = None, entidad: Optional[str] = None) -> Dict[str, Any]:
    """Consulta el dataset público de Hugging Face y devuelve contexto remoto con enlaces directos, wiki de comunidades y citas oficiales.

    Orden: lo exacto del mapa del corpus (el rol, la norma o la entidad, de los parámetros o de la
    consulta: la ficha y quién la cita) → su búsqueda de texto → el catálogo de instituciones y de
    jurisprudencia → las rutas del dataset. Cada resultado del mapa trae `url_huggingface` FIJADA a
    la revisión de la fuente y `url_vigente` (main); la respuesta suma la clave `mapa` con su
    estado. Sin mapa listo la búsqueda es la de siempre. `coleccion` acota a cs, tc, ta, doc, guia,
    bib o pub (también «Corte Suprema», «doctrina»…).
    """
    texto = str(query or "").strip() or " ".join(str(v).strip() for v in (rol, norma, entidad)
                                                 if v and str(v).strip())
    query_norm = texto.lower().strip()
    if not query_norm:
        return {"error": "Se requiere un término de búsqueda para consultar Hugging Face", "coincidencias": []}
    consulta = query if str(query or "").strip() else texto

    cliente = cliente_mapa(repo_id)
    estado = cliente.estado_breve() if cliente is not None else estado_mapa(repo_id)
    cols = _colecciones(coleccion)
    coincidencias: List[Dict[str, Any]] = []
    citas: List[Dict[str, Any]] = []
    vistos: set = set()
    detalle: Dict[str, Any] = {}

    def _agregar(cand: Dict[str, Any]) -> bool:
        """Suma un candidato sin repetir archivo ni salir de las colecciones pedidas; True al llegar al límite."""
        if cand["archivo"] in vistos:
            return False
        if cols and (cand.get("coleccion") or _COLECCION_DE_TIPO.get(str(cand.get("tipo") or ""), "")) not in cols:
            return False
        vistos.add(cand["archivo"])
        coincidencias.append(cand)
        if cand.get("extractos"):
            citas.append({
                "formato": cand["cita_estandar"],
                "texto": cand["extractos"][0],
                "url": cand["url_huggingface"],
                "fuente": "huggingface",
            })
        return len(coincidencias) >= limit

    try:
        tokens_q = _tokens_consulta(query_norm)
        lleno = False
        if cliente is not None:
            del_mapa, detalle = _buscar_en_mapa(cliente, texto, rol, norma, entidad, cols, limit, repo_id,
                                                space_id, tokens_q)
            lleno = any(_agregar(cand) for cand in del_mapa)
            if detalle.get("ids"):
                # El mapa ya resolvió el rol, la norma o la entidad: el catálogo y las rutas buscan
                # solo el resto de la consulta («2024» calzaría con miles de rutas).
                tokens_q = _prosa(tokens_q)
        if not lleno:
            for cand in _candidatos_tradicionales(consulta, query_norm, tokens_q, limit, repo_id, space_id,
                                                  vistos, cliente, cols):
                if _agregar(cand):
                    break
        respuesta = _construir_respuesta_hf(consulta, repo_id, space_id, coincidencias, citas)
    except Exception as e:
        return {
            "dataset_origen": f"https://huggingface.co/datasets/{repo_id}",
            "query": consulta,
            "error": f"Falla consultando Hugging Face Hub: {str(e)}",
            "resultados": [],
            "citas": [],
            "mapa": estado,
        }
    respuesta["mapa"] = estado
    if detalle:
        respuesta["mapa_consulta"] = detalle
    return respuesta


def _nombre_revista(cliente: Any, id_revista: str, memo: Dict[str, str]) -> str:
    if id_revista not in memo:
        entidad = cliente.entidad(id_revista) or {}
        memo[id_revista] = str(entidad.get("label") or id_revista.split(":", 1)[-1].upper())
    return memo[id_revista]


def _etiquetas_normas(normas: Any, maximo: int = 8) -> str:
    """«Código Civil, Art. 2314; Ley N° 19.300» de las normas más citadas de una entrada."""
    from citas_legales import etiqueta_norma
    etiquetas: List[str] = []
    pares = [n for n in (normas or []) if isinstance(n, (list, tuple)) and len(n) == 2]
    for id_, _ in sorted(pares, key=lambda n: (-int(n[1]), str(n[0])))[:maximo]:
        try:
            etiquetas.append(etiqueta_norma(str(id_)))
        except (ValueError, KeyError):
            continue
    return "; ".join(etiquetas)


def revistas_del_mapa(query: str, limite: int = 5, area: Optional[str] = None, autor: Optional[str] = None,
                      repo_id: str = REPO_HF) -> List[Dict[str, Any]]:
    """Artículos de las revistas jurídicas del dataset que calzan con la consulta (vía el mapa), con
    la forma de los resultados de `doctrina_search`: título, resumen, autores, revista, normas,
    `cita_oficial` y `fuente_huggingface` FIJADA a la revisión de la fuente. Sin mapa listo, [].
    Nunca usa la red."""
    cliente = cliente_mapa(repo_id)
    tokens = _tokens_consulta(str(query or ""))
    if cliente is None or limite <= 0 or not tokens:
        return []
    terminos = tokens + (_tokens_consulta(str(autor)) if autor else [])
    filas = [f for f in cliente.buscar(" ".join(terminos), ["doc"], limite=max(4 * limite, 20))
             if f.get("revista") and f.get("ruta")]
    # Primero los artículos con texto: una ficha «texto íntegro en PDF» no tiene pasaje que citar.
    filas.sort(key=lambda f: not f.get("tiene_texto"))
    if autor:
        aguja = _normalizar_para_buscar(str(autor)).lower().strip()
        filas = [f for f in filas if aguja in _normalizar_para_buscar(" ".join(f.get("autores_txt") or [])).lower()]
    if area:
        aguja = _normalizar_para_buscar(str(area)).lower().strip()
        filas = [f for f in filas if aguja in _normalizar_para_buscar(str(f.get("area_declarada") or "")).lower()]
    memo: Dict[str, str] = {}
    salida: List[Dict[str, Any]] = []
    for f in filas[:limite]:
        ruta = str(f["ruta"])
        titulo = str(f.get("titulo") or os.path.basename(ruta))
        autores = "; ".join(str(a) for a in (f.get("autores_txt") or [])) or "s/d"
        obra = _nombre_revista(cliente, str(f["revista"]), memo)
        resumen = " ".join(str(f.get("resumen") or "").split())
        snippet = (_extractos_hf(resumen, tokens, ancho=300, maximo=1) or [resumen[:300]])[0]
        url = cliente.url(ruta)
        salida.append({
            "id": f.get("id"),
            "institucion": titulo,
            "definicion": resumen,
            "snippet": snippet,
            "concordancias": _etiquetas_normas(f.get("normas")),
            "fallo_rector": "",
            "area": str(f.get("area_declarada") or "Revistas"),
            "autor": autores,
            "obra": obra,
            "operativa_procesal": "",
            "bm25_score": 0.0,
            "cita_oficial": str(f.get("cita_oficial") or f.get("cita") or f"[Doctrina - {autores}, {titulo}, {obra}]"),
            "fuente_huggingface": url,
            "url": url,
            "url_vigente": cliente.url(ruta, fijada=False),
            "archivo": ruta,
            "revista": f.get("revista"),
            "anio": f.get("anio"),
            "resumen": resumen,
            "origen": "mapa_hf",
        })
    return salida


def _archivos_en_cache(repo_dir: pathlib.Path) -> List[str]:
    """Archivos del corpus presentes en la caché (deja fuera el cache interno de huggingface_hub)."""
    ignorar = {_ARCHIVO_SINCRONIA, _ARCHIVO_SINCRONIA + ".tmp", "CACHEDIR.TAG"}
    salida: List[str] = []
    for p in repo_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_dir).as_posix()
        if p.name in ignorar or rel.startswith("datasets--") or rel.startswith(".locks"):
            continue
        salida.append(rel)
    return salida


def estado_cache_corpus(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> dict:
    """Qué hay en la caché local del corpus: archivos, MB y cuántos quedaron atrás en el hub."""
    repo_dir = _repo_cache_dir(repo_id)
    meta = _leer_sincronia(repo_dir)
    archivos = _archivos_en_cache(repo_dir)
    bytes_totales = sum((repo_dir / a).stat().st_size for a in archivos)
    desactualizados: List[str] = []
    sin_registrar: List[str] = []
    try:
        for i in range(0, len(archivos), 50):   # en lotes: una llamada de API revisa hasta 50 archivos
            lote = archivos[i:i + 50]
            for it in _hf_api().get_paths_info(repo_id, lote, repo_type="dataset"):
                blob = str(getattr(it, "blob_id", "") or "")
                guardado = str((meta["archivos"].get(it.path) or {}).get("blob_id") or "")
                if not guardado:
                    sin_registrar.append(it.path)   # caché anterior a esta metadata: se registra al refrescar
                elif blob and blob != guardado:
                    desactualizados.append(it.path)
    except Exception:  # noqa: BLE001 — sin red el estado local igual sirve
        desactualizados = []
        sin_registrar = []
    return {"archivos": len(archivos), "mb": round(bytes_totales / 1e6, 1),
            "desactualizados": desactualizados, "sin_registrar": sin_registrar}


def refrescar_cache_corpus(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile",
                           forzar: bool = False) -> dict:
    """Baja las revisiones nuevas de lo YA cacheado (los archivos que nunca se usaron no se bajan)."""
    repo_dir = _repo_cache_dir(repo_id)
    meta = _leer_sincronia(repo_dir)
    archivos = _archivos_en_cache(repo_dir)
    actualizados, errores = 0, []
    for i in range(0, len(archivos), 50):
        lote = archivos[i:i + 50]
        try:
            info = _hf_api().get_paths_info(repo_id, lote, repo_type="dataset")
        except Exception as error:  # noqa: BLE001
            errores.append(str(error)[:120])
            continue
        for it in info:
            blob = str(getattr(it, "blob_id", "") or "")
            guardado = str((meta["archivos"].get(it.path) or {}).get("blob_id") or "")
            if not forzar and blob and blob == guardado:
                continue
            try:
                from huggingface_hub import hf_hub_download
                # Es el dataset PROPIO del proyecto (mismo criterio que _descargar_trozo_hf): lo que
                # se baja son datos que nunca se ejecutan y se validan antes de usarse.
                ruta = hf_hub_download(  # nosec B615
                                       repo_id=repo_id, filename=it.path, repo_type="dataset",
                                       token=resolver_token_hf(),
                                       cache_dir=str(_repo_cache_dir(repo_id)),
                                       force_download=forzar)
                (repo_dir / it.path).parent.mkdir(parents=True, exist_ok=True)
                (repo_dir / it.path).write_bytes(pathlib.Path(ruta).read_bytes())
                meta["archivos"][it.path] = {"blob_id": blob, "verificado": time.time()}
                actualizados += 1
            except Exception as error:  # noqa: BLE001
                errores.append(f"{it.path}: {str(error)[:100]}")
    _escribir_sincronia(repo_dir, meta)
    return {"actualizados": actualizados, "errores": errores, "revisados": len(archivos)}


ATRIBUCION = """

---

## Origen y atribución

Este dataset reúne material jurídico chileno **de terceros**, publicado con atribución. Los derechos
sobre cada texto siguen siendo de sus autores:

- **Materiales Docentes de la Academia Judicial de Chile** (serie MD##) — descargados de
  https://academiajudicial.cl/recursos/materiales-docentes/ . Son materiales de formación judicial
  de una institución de derecho público; se incluyen con su atribución y enlace a la fuente.
- **Apuntes del profesor Juan Andrés Orrego Acuña** — descargados de
  https://www.juanandresorrego.cl/apuntes_all.html , de distribución pública y gratuita en su sitio.
- **Manuales aportados por el estudio** — dos documentos de circulación interna; sus derechos
  pertenecen a sus autores.

Lo que **sí** queda bajo Apache-2.0 es lo producido por el proyecto: el grafo de conocimiento
(LegalGraphify), los JSONL derivados, el índice y el código.

Si sos autor o titular de derechos de alguno de estos textos y querés que no esté acá, se retira a
pedido.

## Cómo se generó

PDF → texto (con OCR y modelo español para los escaneados) → Markdown con secciones, definición
canónica y concordancias legales extraídas del texto → índice FTS5 y grafo de conocimiento. Cada
documento conserva su fuente en el encabezado.
"""
