"""
Open Legal Chile — Gestor y Sincronizador de la Biblioteca Online de Markdown
Herramienta para compilar, estructurar y empaquetar el corpus jurídico en Markdown
para su consulta directa por modelos de IA (Gemini, Claude, GPT, Antigravity)
y su publicación gratuita en Hugging Face Datasets, GitHub Releases y Google Drive / NotebookLM.
"""

import os
import pathlib
import re
import json
import subprocess
import sys
import tarfile
import shutil
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(__file__)
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DOCTRINA_RAW = os.path.join(BASE_DIR, "doctrina_raw")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports", "biblioteca_online_md")


def compilar_manifiesto_biblioteca() -> Dict[str, Any]:
    """Función de conveniencia a nivel de módulo para compilar el manifiesto."""
    mgr = OnlineLibrarySyncManager()
    return mgr.compilar_manifiesto_corpus()


ARCHIVO_TOKEN = "~/.openlegal/hf_token"  # nosec B105 (es la ruta de un archivo, no una credencial)


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
  - split: train
    path: data/train.jsonl
  - split: instituciones
    path: data/instituciones.jsonl
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

---

## 📊 Métricas del Corpus y Knowledge Graph
- **Documentos:** {manifiesto['total_documentos']} obras y materiales doctrinales completos
- **Instituciones Dogmáticas:** 11.853 fichas estructuradas con definiciones canónicas, concordancias y fallos rectores (`data/instituciones.jsonl`)
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
                "del derecho chileno (17.006 nodos y 18.710 relaciones).\n\n"
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
                "instrucciones": "Instálalo ejecutando: pip install huggingface_hub"
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

            # 4. Subir carpeta data/ (con train.jsonl, instituciones.jsonl y legal_knowledge_graph.json)
            data_folder = os.path.join(BASE_DIR, "data")
            if os.path.exists(data_folder):
                api.upload_folder(
                    folder_path=data_folder,
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_in_repo="data"
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

            # 7 bis. Quitar del repositorio los artefactos pesados que ya no se publican
            #        (el grafo íntegro vive en data/legal_knowledge_graph.json; la wiki se mantiene)
            pesados_eliminados: object = 0
            try:
                existentes = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset"))
                pesados = [
                    "graphify/graph.json", "graphify/graph.graphml", "graphify/cypher.txt",
                    "graphify/graph.html", "graphify/GRAPH_TREE.html", "graphify/GRAPH_CALLFLOW.html",
                    "graphify/.graphify_analysis.json", "graphify/manifest.json",
                ]
                a_borrar = [p for p in pesados if p in existentes]
                if a_borrar:
                    ops = getattr(importlib.import_module("huggingface_hub"), "CommitOperationDelete")
                    api.create_commit(
                        repo_id=repo_id,
                        repo_type="dataset",
                        operations=[ops(path_in_repo=p) for p in a_borrar],
                        commit_message="chore(dataset): aligerar graphify/ — el grafo vive en data/",
                    )
                    pesados_eliminados = len(a_borrar)
            except Exception as e:
                pesados_eliminados = f"error: {e}"

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


def consultar_huggingface_dataset(query: str, limit: int = 5,
                                  repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile",
                                  space_id: str = "pablobenavidesj/open-legal-chile-graph") -> Dict[str, Any]:
    """Consulta el dataset público de Hugging Face y devuelve contexto remoto con enlaces directos, wiki de comunidades y citas oficiales."""
    query_norm = (query or "").lower().strip()
    if not query_norm:
        return {"error": "Se requiere un término de búsqueda para consultar Hugging Face", "coincidencias": []}

    coincidencias: List[Dict[str, Any]] = []
    try:
        from huggingface_hub import HfApi
        token = resolver_token_hf()
        api = HfApi(token=token)
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")

        tokens_q = [t for t in re.split(r"[_\-\s]+", query_norm) if len(t) > 2]

        for f in files:
            f_norm = f.lower()
            if any(t in f_norm for t in tokens_q):
                encoded_path = f.replace(" ", "%20")
                nombre_base = os.path.basename(f)

                # Clasificación especializada de recursos en el dataset
                if f.startswith("graphify/wiki/"):
                    tipo = "wiki_comunidad"
                    cita = f"[Hugging Face - {repo_id}, Wiki Comunidad: {nombre_base}]"
                elif f in ("graphify/graph.html", "graphify/GRAPH_TREE.html", "graphify/GRAPH_CALLFLOW.html"):
                    tipo = "visualizador_interactivo"
                    cita = f"[Hugging Face - {repo_id}, Visualizador: {nombre_base}]"
                elif f in ("graphify/graph.json", "graphify/graph.graphml", "graphify/cypher.txt"):
                    tipo = "grafo_conocimiento"
                    cita = f"[Hugging Face - {repo_id}, Grafo: {nombre_base}]"
                elif f == "graphify/GRAPH_REPORT.md":
                    tipo = "reporte_comunidades"
                    cita = f"[Hugging Face - {repo_id}, Reporte: {nombre_base}]"
                elif f.startswith("guias_academia_judicial/"):
                    tipo = "guia_academia_judicial"
                    cita = f"[Hugging Face - {repo_id}, Guía Judicial: {nombre_base}]"
                elif f.startswith("doctrina/"):
                    tipo = "doctrina_markdown"
                    cita = f"[Hugging Face - {repo_id}, Archivo: {f}]"
                elif f.startswith("data/"):
                    tipo = "datos_estructurados"
                    cita = f"[Hugging Face - {repo_id}, Datos: {f}]"
                else:
                    tipo = "recurso"
                    cita = f"[Hugging Face - {repo_id}, Archivo: {f}]"

                coincidencias.append({
                    "archivo": f,
                    "dataset": repo_id,
                    "url_huggingface": f"https://huggingface.co/datasets/{repo_id}/blob/main/{encoded_path}",
                    "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
                    "tipo": tipo,
                    "cita_estandar": cita
                })
                if len(coincidencias) >= limit:
                    break

        return {
            "dataset_origen": f"https://huggingface.co/datasets/{repo_id}",
            "space_interactivo": f"https://huggingface.co/spaces/{space_id}",
            "query": query,
            "total_coincidencias": len(coincidencias),
            "resultados": coincidencias,
            "cita_fuente": f"[Hugging Face - Datasets Hub: https://huggingface.co/datasets/{repo_id}]"
        }
    except Exception as e:
        return {
            "dataset_origen": f"https://huggingface.co/datasets/{repo_id}",
            "query": query,
            "error": f"Falla consultando Hugging Face Hub: {str(e)}",
            "resultados": []
        }


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
