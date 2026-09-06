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

    def preparar_dataset_card_huggingface(self) -> str:
        """
        Genera el README.md estándar para publicar el dataset de texto completo en Hugging Face Datasets:
        repo: open-legal-chile/doctrina-jurisprudencia-chile (100% gratuito e ilimitado).
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
- llm-training
size_categories:
- 10K<n<100K
task_categories:
- text-retrieval
- question-answering
---

# 🇨🇱 Corpus Jurídico y Doctrinal de Chile en Markdown (Open Legal Chile)

Este repositorio contiene la biblioteca digital estructurada en **Markdown limpio** con manuales de derecho,
doctrina de los autores clásicos y las **Guías Oficiales de Buenas Prácticas Judiciales de la Academia Judicial de Chile**.

## 📊 Métricas del Corpus
- **Total Documentos:** {manifiesto['total_documentos']} obras/guías
- **Total Palabras:** {manifiesto['total_palabras']:,} palabras
- **Tamaño Total:** {manifiesto['total_megabytes']} MB
- **Formato:** Markdown (`.md`) con metadatos YAML frontmatter

## 🏛️ Contenido Incluido
1. **Academia Judicial de Chile:** Guías de conducción de audiencias (Penal, Laboral, Familia), Determinación de Penas, APJO y Ética Judicial.
2. **Doctrina General y Manuales:** Derecho Civil (Bienes, Obligaciones, Contratos), Derecho Procesal y Derecho Penal.
3. **Compendios Ambientales:** Criterios y compendios de los Tribunales Ambientales (1TA, 2TA, 3TA).

## 🚀 Uso Rápido con Python y Hugging Face Hub
```python
from datasets import load_dataset

# Carga directa del dataset de Derecho Chileno
dataset = load_dataset("open-legal-chile/doctrina-jurisprudencia-chile")
print(dataset)
```

## 📜 Licencia y Cita
Licencia Apache 2.0. Desarrollado por la iniciativa comunitaria Open Legal Chile.
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
