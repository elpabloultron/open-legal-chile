#!/usr/bin/env python3
"""
Open Legal Chile — Pipeline de Ingesta Masiva y Grounding de Citas.

Procesa lotes masivos de documentos jurídicos (PDF, DOCX, TXT, MD) o directorios completos:
1. Normaliza ortotipografía RAE/ASALE y estandariza citas chilenas (BCN/CS/CPR).
2. Genera Markdown canónico token-optimizado en doctrina/<área>/.
3. Realiza sincronización unificada al finalizar el lote (evitando sobrecarga por archivo):
   - Re-indexación FTS5 en doctrina.db.
   - Reconstrucción del Knowledge Graph de LegalGraphify (O(1) inverted index).
   - Generación de catálogos ligeros (data/catalogo/instituciones_lite.jsonl, train_lite.jsonl).
   - Invalidación de caché en memoria de online_library_sync.
4. Emite reporte forense con métricas de compresión de tokens, instituciones y nodos.

Uso CLI:
    python scripts/ingestar_lote_masivo.py --origen /ruta/documentos --area laboral --autor "Sergio Gamonal"
    python scripts/ingestar_lote_masivo.py --origen /ruta/archivo.pdf --area civil --dry-run
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from doc2md_ingestor import DOCTRINA_DIR, ingestar_documento_doctrinal
from online_library_sync import invalidar_cache_catalogo


def procesar_lote(
    archivos: List[pathlib.Path],
    area: str = "civil",
    tratadista: str = "",
    obra: str = "",
    materia: str = "",
    destino_dir: Optional[str | pathlib.Path] = None,
    actualizar_grafo: bool = True,
    actualizar_fts: bool = True,
    dry_run: bool = False,
    verbose: bool = True,
    actualizar_catalogo: bool = True,
) -> Dict[str, Any]:
    """
    Procesa una lista de archivos jurídicos de manera secuencial o por lote,
    ejecutando la sincronización de FTS5 y LegalGraphify una sola vez al terminar.
    """
    t_inicio = time.perf_counter()
    procesados = []
    fallidos = []
    tokens_orig_total = 0
    tokens_md_total = 0
    total_instituciones = 0

    if verbose:
        print(f"[*] Iniciando ingesta de lote: {len(archivos)} archivo(s) detectados.")

    for i, p in enumerate(archivos, start=1):
        if not p.is_file():
            continue

        if dry_run:
            if verbose:
                print(f"  [DRY-RUN] ({i}/{len(archivos)}) Evaluando {p.name} [{area}]")
            procesados.append({"archivo": str(p), "status": "simulado"})
            continue

        if verbose:
            print(f"  [+] ({i}/{len(archivos)}) Ingestando: {p.name} ...", end=" ", flush=True)

        try:
            target_path = str(pathlib.Path(destino_dir) / f"{p.stem}.md") if destino_dir else None
            # Procesar documento sin actualizar FTS ni grafo por cada archivo individual
            res = ingestar_documento_doctrinal(
                file_path=str(p),
                area=area,
                tratadista=tratadista,
                obra=obra,
                materia=materia,
                target_path=target_path,
                actualizar_grafo=False,
                actualizar_fts=False,
            )
            tokens_orig_total += res.get("tokens_original", 0)
            tokens_md_total += res.get("tokens_markdown", 0)
            total_instituciones += res.get("instituciones_detectadas", 0)
            procesados.append(res)
            if verbose:
                ahorro = res.get("ahorro_tokens_pct", 0)
                print(f"OK ({res.get('instituciones_detectadas', 0)} inst., -{ahorro}% tokens)")
        except Exception as e:
            fallidos.append({"archivo": str(p), "error": str(e)})
            if verbose:
                print(f"ERROR: {e}")

    # Sincronización consolidada post-lote
    fts_ok = False
    grafo_ok = False
    catalogo_ok = False
    nodos_grafo = 0
    aristas_grafo = 0

    if not dry_run and procesados:
        if verbose:
            print("[*] Sincronizando índices y catálogos consolidados...")

        # 1. Indexar FTS5
        if actualizar_fts:
            try:
                from doctrina_connector import index_all_doctrina
                total_fts = index_all_doctrina()
                fts_ok = True
                if verbose:
                    print(f"  ✓ FTS5 doctrina.db actualizado ({total_fts} instituciones indexadas)")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error al indexar FTS5: {e}")

        # 2. Reconstruir LegalGraphify Knowledge Graph con motor O(1)
        if actualizar_grafo:
            try:
                from legal_graphify import DEFAULT_GRAPH_PATH, LegalGraphifyEngine
                engine = LegalGraphifyEngine(doctrina_dir=DOCTRINA_DIR)
                engine.construir_grafo_desde_doctrina()
                engine.guardar_grafo_json(DEFAULT_GRAPH_PATH)
                nodos_grafo = engine.graph.number_of_nodes()
                aristas_grafo = engine.graph.number_of_edges()
                grafo_ok = True
                if verbose:
                    print(f"  ✓ LegalGraphify actualizado ({nodos_grafo} nodos, {aristas_grafo} aristas)")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error al actualizar Knowledge Graph: {e}")

        # 3. Regenerar catálogos ligeros e invalidar caché. Reescribe data/catalogo/ del repositorio:
        # un lote en una carpeta temporal (las pruebas) lo apaga con actualizar_catalogo=False.
        if actualizar_catalogo:
            try:
                from online_library_sync import OnlineLibrarySyncManager
                mgr = OnlineLibrarySyncManager()
                mgr.generar_dataset_train_jsonl()

                try:
                    from scripts.optimizar_catalogo_hf import generar_indice_citas, generar_lite
                    generar_lite()
                    generar_indice_citas()
                except Exception:
                    pass

                invalidar_cache_catalogo()
                catalogo_ok = True
                if verbose:
                    print("  ✓ Catálogos y caché en memoria refrescados.")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error al refrescar catálogos: {e}")

    duracion = round(time.perf_counter() - t_inicio, 2)
    ahorro_total_pct = (
        round(((tokens_orig_total - tokens_md_total) / tokens_orig_total) * 100, 1)
        if tokens_orig_total > 0
        else 0.0
    )

    reporte = {
        "total_archivos": len(archivos),
        "exitosos": len(procesados),
        "fallidos": len(fallidos),
        "detalles_fallidos": fallidos,
        "instituciones_detectadas": total_instituciones,
        "tokens_originales": tokens_orig_total,
        "tokens_markdown": tokens_md_total,
        "tokens_ahorrados": tokens_orig_total - tokens_md_total,
        "ahorro_tokens_pct": ahorro_total_pct,
        "fts_actualizado": fts_ok,
        "grafo_actualizado": grafo_ok,
        "catalogo_actualizado": catalogo_ok,
        "nodos_grafo": nodos_grafo,
        "aristas_grafo": aristas_grafo,
        "duracion_segundos": duracion,
        "dry_run": dry_run,
    }

    if verbose:
        print("\n" + "=" * 60)
        print("  REPORTE DE INGESTA MASIVA — OPEN LEGAL CHILE")
        print("=" * 60)
        print(f"  Archivos procesados: {len(procesados)} / {len(archivos)}")
        print(f"  Instituciones incorporadas: {total_instituciones}")
        print(f"  Compresión de tokens: {tokens_orig_total:,} → {tokens_md_total:,} (-{ahorro_total_pct}%)")
        print(f"  Grafo LegalGraphify: {nodos_grafo} nodos, {aristas_grafo} aristas")
        print(f"  Tiempo transcurrido: {duracion} s")
        print("=" * 60 + "\n")

    return reporte


def ingestar_directorio(
    directorio: str | pathlib.Path,
    area: str = "civil",
    tratadista: str = "",
    obra: str = "",
    materia: str = "",
    destino_dir: Optional[str | pathlib.Path] = None,
    patron: str = "*",
    recursivo: bool = True,
    actualizar_grafo: bool = True,
    actualizar_fts: bool = True,
    dry_run: bool = False,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Escanea un directorio buscando archivos compatibles (.pdf, .docx, .txt, .md)
    y los procesa en lote mediante procesar_lote.
    """
    dir_path = pathlib.Path(directorio).resolve()
    if not dir_path.exists():
        raise FileNotFoundError(f"El directorio o ruta '{dir_path}' no existe.")

    if dir_path.is_file():
        archivos = [dir_path]
    else:
        extensiones = {".pdf", ".docx", ".txt", ".md"}
        archivos = []
        scanner = dir_path.rglob("*") if recursivo else dir_path.glob("*")
        for item in sorted(scanner):
            if item.is_file() and item.suffix.lower() in extensiones:
                if patron != "*" and not fnmatch.fnmatch(item.name, patron):
                    continue
                # Evitar re-ingestar archivos ya en el directorio canónico doctrina/ si se apunta a la raíz
                if "doctrina" in item.parts and item.suffix.lower() == ".md":
                    continue
                archivos.append(item)

    return procesar_lote(
        archivos=archivos,
        area=area,
        tratadista=tratadista,
        obra=obra,
        materia=materia,
        destino_dir=destino_dir,
        actualizar_grafo=actualizar_grafo,
        actualizar_fts=actualizar_fts,
        dry_run=dry_run,
        verbose=verbose,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open Legal Chile — Pipeline de Ingesta Masiva y Grounding de Citas."
    )
    parser.add_argument("--origen", required=True, help="Directorio o archivo a ingestar (.pdf, .docx, .txt, .md).")
    parser.add_argument("--destino", default=None, help="Directorio destino personalizado para archivos Markdown generados.")
    parser.add_argument("--area", default="civil", choices=["civil", "laboral", "penal", "procesal", "constitucional", "administrativo", "comercial"], help="Área del derecho.")
    parser.add_argument("--autor", "--tratadista", default="", dest="tratadista", help="Nombre del autor o tratadista.")
    parser.add_argument("--obra", default="", help="Título de la obra o manual.")
    parser.add_argument("--materia", default="", help="Materia dogmática específica.")
    parser.add_argument("--patron", default="*", help="Filtro glob para nombres de archivo (ej. '*.docx').")
    parser.add_argument("--no-recursivo", action="store_false", dest="recursivo", help="No buscar en subdirectorios.")
    parser.add_argument("--no-grafo", action="store_false", dest="actualizar_grafo", help="Omitir reconstrucción del Knowledge Graph.")
    parser.add_argument("--no-fts", "--sin-fts", action="store_false", dest="actualizar_fts", help="Omitir reindexación SQLite FTS5.")
    parser.add_argument("--dry-run", action="store_true", help="Simular ingesta sin escribir archivos ni modificar bases de datos.")

    args = parser.parse_args()

    try:
        reporte = ingestar_directorio(
            directorio=args.origen,
            area=args.area,
            tratadista=args.tratadista,
            obra=args.obra,
            materia=args.materia,
            patron=args.patron,
            recursivo=args.recursivo,
            actualizar_grafo=args.actualizar_grafo,
            actualizar_fts=args.actualizar_fts,
            dry_run=args.dry_run,
            verbose=True,
        )
        return 0 if reporte["fallidos"] == 0 else 1
    except Exception as e:
        print(f"[!] Error crítico en pipeline de ingesta: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
