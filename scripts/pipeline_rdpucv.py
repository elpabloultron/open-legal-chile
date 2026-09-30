#!/usr/bin/env python3
"""
pipeline_rdpucv.py — Orquestador integral para la ingesta, normalización,
enriquecimiento en LegalGraphify y subida a Hugging Face de la Revista de Derecho PUCV.

Flujo:
1. Cosecha metadatos OAI-PMH (66+ volúmenes, 1.097 artículos).
2. Descarga concurrente de PDFs con reintentos y tolerancia a fallos.
3. Extracción y conversión a Markdown canónico RAE/ASALE con Frontmatter YAML.
4. Reindexación SQLite FTS5 (doctrina.db).
5. Sincronización del Knowledge Graph LegalGraphify (O(1)).
6. Actualización de catálogos y subida a Hugging Face Hub (pablobenavidesj/doctrina-jurisprudencia-chile).
"""

import argparse
import os
import pathlib
import sys
import time

# Asegurar path raíz del proyecto
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from scripts.harvest_rdpucv import cosechar_catalogo_completo, MANIFEST_PATH
from scripts.download_rdpucv import cargar_catalogo, descargar_lote_concurrente
from scripts.convert_rdpucv_to_md import procesar_todos_articulos, OUTPUT_DIR
from online_library_sync import resolver_token_hf


def ejecutar_pipeline(
    hilos_descarga: int = 8,
    hilos_conversion: int = 6,
    subir_hf: bool = True,
    limite: int = 0,
    solo_descarga: bool = False,
    solo_conversion: bool = False,
):
    print("\n" + "=" * 70)
    print("🚀 INICIANDO PIPELINE INTEGRAL: REVISTA DE DERECHO PUCV (1977 - 2024)")
    print("=" * 70 + "\n")
    t_global = time.perf_counter()

    # PASO 1: Cosecha de metadatos OAI-PMH
    if not MANIFEST_PATH.exists() or MANIFEST_PATH.stat().st_size < 1000:
        print("[FASE 1/6] Cosechando catálogo OAI-PMH...")
        articulos = cosechar_catalogo_completo()
    else:
        print(f"[FASE 1/6] Catálogo preexistente detectado en {MANIFEST_PATH}")
        articulos = cargar_catalogo()
        print(f"  ✓ {len(articulos)} artículos en catálogo.")

    if limite > 0:
        articulos = articulos[:limite]
        print(f"  * Límite configurado: procesando {limite} artículos.")

    # PASO 2: Descarga de PDFs
    if not solo_conversion:
        print(f"\n[FASE 2/6] Descarga concurrente de PDFs ({hilos_descarga} hilos)...")
        descargar_lote_concurrente(articulos, hilos=hilos_descarga)
    else:
        print("\n[FASE 2/6] Omitiendo descarga (--solo-conversion activo).")

    if solo_descarga:
        print("\n[✓] Descarga finalizada. Deteniendo por bandera --solo-descarga.")
        return

    # PASO 3: Conversión a Markdown Canónico
    print(f"\n[FASE 3/6] Conversión a Markdown canónico token-optimizado ({hilos_conversion} hilos)...")
    procesar_todos_articulos(hilos=hilos_conversion, limite=limite)

    # PASO 4: Indexación SQLite FTS5
    print("\n[FASE 4/6] Actualizando índice SQLite FTS5 (doctrina.db)...")
    try:
        from doctrina_connector import index_all_doctrina
        total_fts = index_all_doctrina()
        print(f"  ✓ FTS5 actualizado: {total_fts} instituciones indexadas.")
    except Exception as e:
        print(f"  [!] Advertencia al indexar FTS5: {e}")

    # PASO 5: Knowledge Graph LegalGraphify (O(1))
    print("\n[FASE 5/6] Reconstruyendo LegalGraphify Knowledge Graph...")
    try:
        from legal_graphify import DEFAULT_GRAPH_PATH, LegalGraphifyEngine
        engine = LegalGraphifyEngine(doctrina_dir=str(ROOT_DIR / "doctrina"))
        engine.construir_grafo_desde_doctrina()
        engine.guardar_grafo_json(DEFAULT_GRAPH_PATH)
        nodos = engine.graph.number_of_nodes()
        aristas = engine.graph.number_of_edges()
        print(f"  ✓ LegalGraphify actualizado con éxito ({nodos} nodos, {aristas} aristas).")
    except Exception as e:
        print(f"  [!] Advertencia al actualizar LegalGraphify: {e}")

    # PASO 6: Subida a Hugging Face Dataset Hub
    if subir_hf:
        print("\n[FASE 6/6] Sincronizando y subiendo a Hugging Face Dataset Hub...")
        token = resolver_token_hf()
        if not token:
            print("  [!] ERROR: No se encontró token de Hugging Face en ~/.openlegal/hf_token ni en variables de entorno.")
            print("      No es posible realizar la subida a Hugging Face.")
            return

        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            repo_id = "pablobenavidesj/doctrina-jurisprudencia-chile"

            # 1. Regenerar catálogos
            print("  [*] Actualizando catálogo train_lite.jsonl...")
            from online_library_sync import OnlineLibrarySyncManager
            mgr = OnlineLibrarySyncManager()
            mgr.generar_dataset_train_jsonl()

            # 2. Subir carpeta de la revista
            print(f"  [*] Subiendo carpeta {OUTPUT_DIR} a {repo_id}...")
            api.upload_folder(
                repo_id=repo_id,
                folder_path=str(OUTPUT_DIR),
                path_in_repo="doctrina/revistas/rdpucv",
                commit_message="feat(doctrina): incorporar coleccion completa Revista de Derecho PUCV (1977-2024)",
                commit_description="Ingesta masiva de 66 volumenes de la Revista de Derecho PUCV con metadatos canonicales, citas legales y nodos de LegalGraphify.",
                repo_type="dataset",
            )
            print("  ✓ Carpeta doctrina/revistas/rdpucv/ subida a Hugging Face exitosamente.")

            # 3. Subir catálogo train_lite.jsonl actualizado
            cat_path = ROOT_DIR / "data" / "catalogo" / "train_lite.jsonl"
            if cat_path.exists():
                api.upload_file(
                    path_or_fileobj=str(cat_path),
                    path_in_repo="data/catalogo/train_lite.jsonl",
                    repo_id=repo_id,
                    repo_type="dataset",
                    commit_message="chore(catalogo): actualizar train_lite.jsonl con Revista de Derecho PUCV",
                )
                print("  ✓ train_lite.jsonl actualizado en Hugging Face.")

        except Exception as e:
            print(f"  [X] Error durante la subida a Hugging Face: {e}")
    else:
        print("\n[FASE 6/6] Subida a Hugging Face omitida (--no-upload activo).")

    dur_total = round(time.perf_counter() - t_global, 2)
    print("\n" + "=" * 70)
    print(f"🎉 PIPELINE COMPLETADO EXITOSAMENTE en {dur_total} s ({round(dur_total / 60, 2)} min)")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Pipeline maestro de ingesta de Revista de Derecho PUCV.")
    parser.add_argument("--hilos-descarga", type=int, default=8, help="Hilos para descarga de PDFs (default: 8).")
    parser.add_argument("--hilos-conversion", type=int, default=6, help="Hilos para conversión a Markdown (default: 6).")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos (0 = todos los 1.097).")
    parser.add_argument("--solo-descarga", action="store_true", help="Solo descargar PDFs.")
    parser.add_argument("--solo-conversion", action="store_true", help="Solo convertir PDFs existentes.")
    parser.add_argument("--no-upload", action="store_false", dest="subir_hf", help="No subir a Hugging Face.")
    args = parser.parse_args()

    ejecutar_pipeline(
        hilos_descarga=args.hilos_descarga,
        hilos_conversion=args.hilos_conversion,
        subir_hf=args.subir_hf,
        limite=args.limite,
        solo_descarga=args.solo_descarga,
        solo_conversion=args.solo_conversion,
    )


if __name__ == "__main__":
    main()
