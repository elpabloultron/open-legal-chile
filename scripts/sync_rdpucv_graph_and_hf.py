#!/usr/bin/env python3
"""
sync_rdpucv_graph_and_hf.py — Sincronización post-ingesta de la Revista de Derecho PUCV:
1. Reconstruye el grafo multidimensional LegalGraphify (O(1)).
2. Reindexa la base SQLite FTS5 (doctrina.db).
3. Regenera los catálogos ligeros (train_lite.jsonl, instituciones_lite.jsonl).
4. Sube la colección completa a Hugging Face Hub (pablobenavidesj/doctrina-jurisprudencia-chile).
"""

import json
import os
import pathlib
import sys
import time

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from online_library_sync import resolver_token_hf

RDPUCV_DIR = ROOT_DIR / "doctrina" / "revistas" / "rdpucv"


def sincronizar_todo():
    print("\n" + "=" * 70)
    print("🧠 SINCRONIZACIÓN LEGALGRAPHIFY & SUBIDA A HUGGING FACE")
    print("=" * 70 + "\n")
    t0 = time.perf_counter()

    # Contar archivos generados
    archivos_md = list(RDPUCV_DIR.glob("**/*.md"))
    print(f"[*] Total de artículos Markdown en doctrina/revistas/rdpucv/: {len(archivos_md)}")

    # 1. Indexar FTS5
    print("\n[1/4] Reindexando SQLite FTS5 (doctrina.db)...")
    try:
        from doctrina_connector import index_all_doctrina
        total_fts = index_all_doctrina()
        print(f"  ✓ FTS5 actualizado con éxito: {total_fts} instituciones indexadas.")
    except Exception as e:
        print(f"  [!] Error indexando FTS5: {e}")

    # 2. Reconstruir Knowledge Graph LegalGraphify
    print("\n[2/4] Reconstruyendo Knowledge Graph LegalGraphify con motor O(1)...")
    try:
        from legal_graphify import DEFAULT_GRAPH_PATH, LegalGraphifyEngine
        engine = LegalGraphifyEngine(doctrina_dir=str(ROOT_DIR / "doctrina"))
        engine.construir_grafo_desde_doctrina()
        engine.guardar_grafo_json(DEFAULT_GRAPH_PATH)
        nodos = engine.graph.number_of_nodes()
        aristas = engine.graph.number_of_edges()
        print(f"  ✓ LegalGraphify actualizado: {nodos} nodos y {aristas} aristas.")
    except Exception as e:
        print(f"  [!] Error actualizando LegalGraphify: {e}")

    # 3. Regenerar catálogos ligeros para citación rápida
    print("\n[3/4] Regenerando catálogos de citación y búsqueda rápida...")
    try:
        from online_library_sync import OnlineLibrarySyncManager
        mgr = OnlineLibrarySyncManager()
        mgr.generar_dataset_train_jsonl()
        print("  ✓ train_lite.jsonl regenerado con éxito.")
    except Exception as e:
        print(f"  [!] Error generando catálogo: {e}")

    # 4. Subir a Hugging Face Hub
    print("\n[4/4] Subiendo colección a Hugging Face Hub...")
    token = resolver_token_hf()
    if not token:
        print("  [!] ERROR: Token de Hugging Face no encontrado. Sincronización remota omitida.")
        return

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        repo_id = "pablobenavidesj/doctrina-jurisprudencia-chile"

        print(f"  [*] Subiendo carpeta {RDPUCV_DIR} a {repo_id}...")
        api.upload_folder(
            repo_id=repo_id,
            folder_path=str(RDPUCV_DIR),
            path_in_repo="doctrina/revistas/rdpucv",
            commit_message=f"feat(doctrina): incorporar coleccion completa Revista de Derecho PUCV ({len(archivos_md)} articulos)",
            commit_description="Ingesta masiva de la Revista de Derecho de la Pontificia Universidad Católica de Valparaíso (Pro Jure / SciELO) con metadatos canonicales, citas legales y nodos de LegalGraphify.",
            repo_type="dataset",
        )
        print("  ✓ Carpeta doctrina/revistas/rdpucv/ subida exitosamente a Hugging Face.")

        cat_path = ROOT_DIR / "data" / "catalogo" / "train_lite.jsonl"
        if cat_path.exists():
            api.upload_file(
                path_or_fileobj=str(cat_path),
                path_in_repo="data/catalogo/train_lite.jsonl",
                repo_id=repo_id,
                repo_type="dataset",
                commit_message="chore(catalogo): actualizar train_lite.jsonl con coleccion RDPUCV",
            )
            print("  ✓ train_lite.jsonl actualizado en Hugging Face.")

    except Exception as e:
        print(f"  [X] Error durante la subida a Hugging Face: {e}")

    dur = round(time.perf_counter() - t0, 2)
    print("\n" + "=" * 70)
    print(f"✨ PROCESO FINALIZADO EN {dur} s ({round(dur / 60, 2)} min)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    sincronizar_todo()
