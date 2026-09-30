#!/usr/bin/env python3
"""
Open Legal Chile — Script de Caché Warming (Pre-calentamiento de Caché)
Pre-descarga y parsea en local los 10 cuerpos legales (9 Códigos de la República y la CPR),
leyes de alta frecuencia y jurisprudencia rectora de la Corte Suprema y TC.
Garantiza consultas en 0 ms sin depender de la conectividad en vivo con BCN o PJUD.
"""

from __future__ import annotations

import sys
import os
import time
from typing import Dict, Any, List

# Asegurar path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bcn_connector import BCNClient, CODIGOS_REPUBLICA, LEYES_FRECUENTES
from pjud_connector import PJUDClient


def calentar_codigos(bcn: BCNClient, verbose: bool = True) -> Dict[str, Any]:
    """Pre-descarga y cachea los Códigos de la República y la CPR."""
    if verbose:
        print("\n[1/3] 📜 Pre-calentando Códigos de la República y Constitución...")
    resultados = {}
    for clave, meta in CODIGOS_REPUBLICA.items():
        inicio = time.time()
        try:
            res = bcn.get_codigo(clave)
            duracion = time.time() - inicio
            total_arts = len(res.get("articulos", {}))
            resultados[clave] = {"estado": "ok", "articulos": total_arts, "tiempo_s": round(duracion, 2)}
            if verbose:
                print(f"  ✅ {clave:14} : {total_arts:5} arts ({duracion:.2f}s) — {meta['nombre']}")
        except Exception as e:
            resultados[clave] = {"estado": "error", "error": str(e)}
            if verbose:
                print(f"  ❌ {clave:14} : Error: {e}")
    return resultados


def calentar_leyes_frecuentes(bcn: BCNClient, verbose: bool = True) -> Dict[str, Any]:
    """Pre-descarga y cachea leyes de alta demanda práctica."""
    if verbose:
        print("\n[2/3] ⚖️  Pre-calentando Leyes Frecuentes...")
    resultados = {}
    for alias, numero in LEYES_FRECUENTES.items():
        inicio = time.time()
        try:
            res = bcn.get_ley(numero)
            duracion = time.time() - inicio
            total_est = res.get("totalEstructuras", 0)
            resultados[alias] = {"estado": "ok", "numero": numero, "estructuras": total_est, "tiempo_s": round(duracion, 2)}
            if verbose:
                print(f"  ✅ Ley N° {numero:<6} ({alias:18}) : {total_est:4} est ({duracion:.2f}s) — {res.get('titulo', '')[:50]}...")
        except Exception as e:
            resultados[alias] = {"estado": "error", "error": str(e)}
            if verbose:
                print(f"  ❌ Ley N° {numero} ({alias}) : Error: {e}")
    return resultados


def calentar_jurisprudencia(pjud: PJUDClient, verbose: bool = True) -> Dict[str, Any]:
    """Pre-calienta jurisprudencia unificada y sentencias rectoras."""
    if verbose:
        print("\n[3/3] 🏛️  Pre-calentando Jurisprudencia Rectora (CS / TC)...")
    consultas_clave = [
        "despido injustificado necesidades de la empresa",
        "tutela laboral indicios vulneracion derechos fundamentales",
        "confianza legitima contrata renovaciones sucesivas",
        "recurso de proteccion derecho de propiedad agua potable",
        "inaplicabilidad por inconstitucionalidad",
    ]
    resultados = {}
    for q in consultas_clave:
        inicio = time.time()
        try:
            res = pjud.search_jurisprudencia(q, limit=5)
            duracion = time.time() - inicio
            total = len(res) if isinstance(res, list) else 0
            resultados[q] = {"estado": "ok", "total": total, "tiempo_s": round(duracion, 2)}
            if verbose:
                print(f"  ✅ '{q[:40]}...' : {total} fallos ({duracion:.2f}s)")
        except Exception as e:
            resultados[q] = {"estado": "error", "error": str(e)}
            if verbose:
                print(f"  ❌ '{q[:40]}...' : Error: {e}")
    return resultados


def ejecutar_cache_warming(verbose: bool = True) -> Dict[str, Any]:
    """Ejecuta el pipeline completo de pre-calentamiento de caché."""
    print("=" * 80)
    print("      ⚖️  OPEN LEGAL CHILE — CACHÉ WARMING PIPELINE (SOBERANO & OFFLINE)  ⚖️")
    print("=" * 80)
    t_inicio = time.time()

    bcn = BCNClient()
    pjud = PJUDClient()

    codigos = calentar_codigos(bcn, verbose=verbose)
    leyes = calentar_leyes_frecuentes(bcn, verbose=verbose)
    juris = calentar_jurisprudencia(pjud, verbose=verbose)

    t_total = time.time() - t_inicio
    print("\n" + "=" * 80)
    print(f"✨ Caché warming completado en {t_total:.2f} segundos.")
    print("=" * 80)

    return {
        "tiempo_total_s": round(t_total, 2),
        "codigos": codigos,
        "leyes": leyes,
        "jurisprudencia": juris,
    }


if __name__ == "__main__":
    ejecutar_cache_warming()
