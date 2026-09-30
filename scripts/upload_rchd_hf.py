#!/usr/bin/env python3
"""
upload_rchd_hf.py — Sube la colección completa de la Revista Chilena de Derecho (RChD)
y los catálogos regenerados a Hugging Face Hub (pablobenavidesj/doctrina-jurisprudencia-chile).
"""

from __future__ import annotations

import pathlib
import sys
import time

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from online_library_sync import resolver_token_hf

REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
RCHD_DIR = ROOT_DIR / "doctrina" / "revistas" / "rchd"


def subir_coleccion_rchd():
    print("\n" + "=" * 70)
    print("🚀 SUBIENDO REVISTA CHILENA DE DERECHO (RChD) A HUGGING FACE")
    print("=" * 70 + "\n")
    t0 = time.perf_counter()

    token = resolver_token_hf()
    if not token:
        print("[!] ERROR FATAL: No se encontró token de Hugging Face.")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("[!] ERROR: huggingface_hub no está instalado.")
        sys.exit(1)

    api = HfApi(token=token)

    archivos_md = list(RCHD_DIR.glob("**/*.md"))
    print(f"[*] Total de artículos Markdown a subir: {len(archivos_md)}")

    # 1. Subir carpeta completa de RChD
    print(f"[*] Subiendo carpeta {RCHD_DIR} a {REPO_ID}:doctrina/revistas/rchd ...")
    api.upload_folder(
        repo_id=REPO_ID,
        folder_path=str(RCHD_DIR),
        path_in_repo="doctrina/revistas/rchd",
        commit_message=f"feat(doctrina): incorporar coleccion completa Revista Chilena de Derecho ({len(archivos_md)} articulos)",
        commit_description="Ingesta masiva de la Revista Chilena de Derecho (Facultad de Derecho UC / SciELO CONICYT, ISSN 0718-3437, 2006-2026) con metadatos canonicales, citas legales y nodos de LegalGraphify.",
        repo_type="dataset",
    )
    print("  ✓ Carpeta doctrina/revistas/rchd/ subida exitosamente.")

    # 2. Subir catálogos y artefactos actualizados
    archivos_a_subir = [
        (ROOT_DIR / "data" / "catalogo" / "train_lite.jsonl", "data/catalogo/train_lite.jsonl", "chore(catalogo): actualizar train_lite.jsonl con coleccion RChD"),
        (ROOT_DIR / "data" / "catalogo" / "instituciones_lite.jsonl", "data/catalogo/instituciones_lite.jsonl", "chore(catalogo): actualizar instituciones_lite.jsonl con RChD"),
        (ROOT_DIR / "data" / "catalogo" / "indice_citas.jsonl", "data/catalogo/indice_citas.jsonl", "chore(catalogo): actualizar indice_citas.jsonl con RChD"),
        (ROOT_DIR / "data" / "catalogo" / "indice_agentes.json", "data/catalogo/indice_agentes.json", "chore(catalogo): actualizar indice_agentes.json con RChD"),
        (ROOT_DIR / "llms.txt", "llms.txt", "chore: actualizar llms.txt con estadisticas de RChD"),
        (ROOT_DIR / "doctrina" / "revistas" / "README.md", "doctrina/revistas/README.md", "docs: documentar coleccion RChD en README de revistas"),
    ]

    for local_p, repo_p, msg in archivos_a_subir:
        if local_p.exists():
            print(f"[*] Subiendo {local_p.name} a {repo_p}...")
            api.upload_file(
                path_or_fileobj=str(local_p),
                path_in_repo=repo_p,
                repo_id=REPO_ID,
                repo_type="dataset",
                commit_message=msg,
            )
            print(f"  ✓ {local_p.name} subido exitosamente.")

    dur = round(time.perf_counter() - t0, 1)
    print("\n" + "=" * 70)
    print(f"🎉 SUBIDA A HUGGING FACE COMPLETADA EXITOSAMENTE en {dur} s ({round(dur / 60, 2)} min)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    subir_coleccion_rchd()
