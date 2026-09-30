#!/usr/bin/env python3
"""
Open Legal Chile — Script de Indexación Vectorial de Códigos y CPR
Construye la base codigos_vectorial.db procesando los Códigos y la Constitución
almacenados en bcn_cache/ o descargados vía BCN.
"""

from __future__ import annotations

import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from vector_engine import obtener_motor_vectorial


def main():
    print("=" * 80)
    print("      ⚖️  OPEN LEGAL CHILE — INDEXADOR VECTORIAL DE CÓDIGOS Y CPR  ⚖️")
    print("=" * 80)
    forzar = "--fuerza" in sys.argv or "-f" in sys.argv
    t0 = time.time()
    motor = obtener_motor_vectorial()
    print(f"Indexando cuerpos legales (forzar={forzar})...")
    resumen = motor.indexar_desde_bcn_cache(forzar=forzar)
    total = sum(resumen.values())
    duracion = time.time() - t0

    for cuerpo, cant in resumen.items():
        print(f"  ✅ {cuerpo:14} : {cant:5} artículos indexados")

    print("\n" + "=" * 80)
    print(f"✨ Total artículos indexados: {total} en {duracion:.2f} segundos.")
    print(f"📁 Base vectorial lista en: {motor.db_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
