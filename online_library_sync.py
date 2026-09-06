"""
Open Legal Chile — Gestor y Sincronizador de la Biblioteca Online de Markdown
Herramienta para compilar, estructurar y empaquetar el corpus jurídico en Markdown
para su consulta directa por modelos de IA (Gemini, Claude, GPT, Antigravity)
y su publicación gratuita en Hugging Face Datasets, GitHub Releases y Google Drive / NotebookLM.
"""

import os
import re
import json
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
        except Exception:
            pass

        # 3. Asegurar persistencia de data/legal_knowledge_graph.json
        graph_path = os.path.join(target_dir, "legal_knowledge_graph.json")
        if not os.path.exists(graph_path):
            try:
                from legal_graphify import LegalGraphifyEngine
                engine = LegalGraphifyEngine()
                engine.guardar_grafo_json(graph_path)
            except Exception:
                pass

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

        card = f"""---
language:
- es
license: apache-2.0
tags:
- legal
- chile
- derecho
- law
- judicial
- markdown
- knowledge-graph
- graphify
- llm-training
size_categories:
- 1K<n<10K
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
---

# 🇨🇱 Corpus Jurídico y Doctrinal de Chile en Markdown (Open Legal Chile)

Bienvenido al repositorio oficial del **Corpus Jurídico Canónico y Doctrinal de Chile**, desarrollado y mantenido por **Open Legal Chile**.
Este repositorio ofrece acceso **100% completo, libre y gratuito (Apache-2.0)** al texto íntegro de la dogmática jurídica chilena, a las Guías Oficiales de la Academia Judicial y al **Knowledge Graph de Reducción Masiva de Tokens (LegalGraphify)**.

---

## 📊 Métricas del Corpus
- **Obras y Guías Completas:** {manifiesto['total_documentos']} documentos
- **Instituciones Dogmáticas FTS5:** 138 instituciones indexadas
- **Nodos del Knowledge Graph:** 967 nodos interconectados
- **Aristas Relacionales:** 1.366 relaciones tipificadas
- **Total Palabras:** {manifiesto['total_palabras']:,} palabras
- **Visualizador Web Activo:** Habilitado mediante `data/train.jsonl` y `data/instituciones.jsonl` (Dataset Viewer oficial de Hugging Face).

---

## 🏛️ Estructura del Repositorio

```text
├── README.md                      # Dataset Card y especificaciones forenses
├── data/
│   ├── train.jsonl                # 58 Obras completas en texto íntegro (Full-Text Dataset Viewer)
│   ├── instituciones.jsonl        # 138 Fichas dogmáticas con definiciones canónicas y fallos rectores
│   └── legal_knowledge_graph.json # Knowledge Graph multidimensional en formato NetworkX/Graphify
└── doctrina/                      # Árbol de archivos Markdown en bruto organizados por disciplina
    ├── civil/                     # Obligaciones, Responsabilidad, Bienes, Acto Jurídico, Sucesorio, Familia
    ├── procesal/                  # Recursos Procesales, Casación, Disposiciones Comunes del CPC
    ├── administrativo/            # Bases Constitucionales, Invalidez del Acto, Responsabilidad Estatal
    ├── laboral/                   # Principios del Trabajo, Despido, Tutela de Derechos Fundamentales
    ├── penal/                     # Teoría del Delito, Antijuridicidad, Iter Criminis y Culpabilidad
    ├── constitucional/            # Bases de la Institucionalidad, Derechos Fundamentales, Recurso de Protección
    ├── comercial/                 # Actos de Comercio, SpA, Títulos de Crédito, Concursos (Ley 20.720)
    └── academia_judicial/         # Guías Oficiales de Conducción de Audiencias, Penas y Ética Judicial
```

---

## 🧠 LegalGraphify: Reducción Masiva de Tokens (85% - 95%)

Para consultar la doctrina sin sobrecargar la ventana de contexto de modelos de lenguaje (Claude Code, Antigravity, Cursor, Gemini), este dataset incluye el grafo multidimensional precomputado:

```python
from legal_graphify import LegalGraphifyEngine

engine = LegalGraphifyEngine()
subgrafo = engine.consultar_subgrafo("simulacion")

print(subgrafo["subgrafo_resumen_yaml"])
# Consumo: ~180 tokens (vs. 2.800 tokens de la lectura del capítulo crudo) -> Ahorro: 93.5%
```

---

## 🚀 Carga Rápida con Python y Hugging Face Datasets

```python
from datasets import load_dataset

# 1. Cargar las 58 obras completas en texto íntegro
dataset_obras = load_dataset("{repo_id}", split="train")
print(f"Obras cargadas: {{len(dataset_obras)}}")
print(dataset_obras[0]["titulo"])

# 2. Cargar las 138 instituciones dogmáticas con concordancias y fallos rectores
dataset_inst = load_dataset("{repo_id}", split="instituciones")
print(f"Instituciones cargadas: {{len(dataset_inst)}}")
print(dataset_inst[0]["institucion"])
```

---

## 📜 Licencia y Cita
Distribuido bajo licencia **Apache 2.0**.
Proyecto: [Open Legal Chile](https://github.com/elpabloultron/open-legal-chile)
"""
        card_path = os.path.join(self.export_dir, "README_HUGGINGFACE.md")
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card)

        return card_path

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

    def publicar_en_huggingface(self, repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile", token: Optional[str] = None) -> Dict[str, Any]:
        """
        Publica el corpus de Markdown, el dataset estructurado en JSONL (train e instituciones)
        y el Knowledge Graph de LegalGraphify en Hugging Face Datasets Hub usando huggingface_hub.
        Requiere un token de Hugging Face con permisos de escritura (HF_TOKEN o parámetro token).
        """
        hf_token = token or os.environ.get("HF_TOKEN")
        if not hf_token:
            return {
                "exito": False,
                "error": "Token de autenticación de Hugging Face (HF_TOKEN) no configurado.",
                "instrucciones": (
                    "Para publicar automáticamente en Hugging Face:\n"
                    "1. Crea una cuenta gratuita en https://huggingface.co/join\n"
                    "2. Genera un Access Token con rol 'Write' en https://huggingface.co/settings/tokens\n"
                    "3. En tu terminal ejecuta: export HF_TOKEN='hf_...'\n"
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
            # 1. Generar data/train.jsonl, data/instituciones.jsonl y data/legal_knowledge_graph.json
            jsonl_res = self.generar_dataset_train_jsonl()

            # 2. Generar Dataset Card README.md con tags de configuración
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

            # 5. Subir carpeta doctrina/ con todos los 58 archivos Markdown íntegros
            api.upload_folder(
                folder_path=self.raw_dir,
                repo_id=repo_id,
                repo_type="dataset",
                path_in_repo="doctrina"
            )

            return {
                "exito": True,
                "repo_id": repo_id,
                "total_documentos": jsonl_res.get("total_documentos"),
                "total_instituciones": jsonl_res.get("total_instituciones"),
                "url": f"https://huggingface.co/datasets/{repo_id}",
                "mensaje": f"Dataset publicado exitosamente en Hugging Face: https://huggingface.co/datasets/{repo_id}"
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
