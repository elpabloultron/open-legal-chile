#!/usr/bin/env python3
"""
ingestar_rducn.py — Ingesta de Revista de Derecho (Universidad Católica del Norte, Coquimbo).
Wrapper conveniente que invoca el motor central de ingestar_revistas_cientificas.py.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from scripts.ingestar_revistas_cientificas import REVISTAS, procesar_revista, regenerar_catalogos_ligeros


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta de Revista de Derecho (Coquimbo, UCN)")
    parser.add_argument("--skip-download", action="store_true", help="Omitir descarga si ya existen")
    parser.add_argument("--subir-hf", action="store_true", help="Subir a Hugging Face Hub al finalizar")
    parser.add_argument("--concurrencia", type=int, default=8, help="Hilos concurrentes para descarga")
    args = parser.parse_args()

    cfg = REVISTAS["rducn"]
    n = procesar_revista(cfg, skip_download=args.skip_download, subir_hf=args.subir_hf, concurrencia=args.concurrencia)
    if not args.skip_download and n > 0:
        regenerar_catalogos_ligeros(subir_hf=args.subir_hf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
