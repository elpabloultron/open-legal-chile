"""
Open Legal Chile — Conector Oficial Derecho Ambiental (SMA / SNIFA / Tribunales Ambientales)
Módulo para consultar, indexar y buscar Procedimientos Sancionatorios Ambientales,
Infracciones a RCAs, Programas de Cumplimiento (PDC) y Resoluciones de la Superintendencia del Medio Ambiente.
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

BASE_URL = "https://snifa.sma.gob.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "ambiental_cache")
# Los expedientes del SNIFA cambian de estado con el tiempo: la copia local se revalida a la
# semana (vencida, se intenta refrescar; sin red, se entrega marcada).
_TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60


class SMAClient:
    """Cliente oficial de la Superintendencia del Medio Ambiente (SMA / SNIFA)."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def _cache_fresco(self, cache_file: str, ttl: float = _TTL_CACHE_SEGUNDOS) -> bool:
        """¿La copia local existe y está dentro del TTL? (el mtime es la fecha de consulta)."""
        return os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < ttl

    def _consultar_snifa(self, nombre: str, expediente: str, categoria: str, limit: int,
                         cache_file: str) -> Dict[str, Any]:
        """Consulta el grid público del SNIFA y deja la copia local al día."""
        url = f"{BASE_URL}/Sancionatorio/ObtenerResultadosGrid"
        payload = {
            "draw": 1,
            "start": 0,
            "length": limit,
            "nombre": nombre,
            "expediente": expediente,
            "categoria": categoria,
            "ddlRegion": "",
            "ddlComuna": ""
        }

        data_bytes = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": "OpenLegalChile/1.0 (Derecho Ambiental Chile)"
            }
        )

        with safe_urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            res_json = json.loads(raw)
            total = res_json.get("recordsTotal", 0)
            rows = res_json.get("data", [])

            results = []
            for r in rows:
                cleaned = [re.sub(r'<[^>]+>', '', str(c)).strip() for c in r]
                btn_html = str(r[-1]) if len(r) > 0 else ""
                link_m = re.search(r'href=["\']([^"\']+)["\']', btn_html)
                link = link_m.group(1) if link_m else ""
                ficha_id = link.split("/")[-1] if link else ""

                results.append({
                    "id": ficha_id,
                    "expediente": cleaned[1] if len(cleaned) > 1 else "",
                    "unidadFiscalizable": cleaned[2] if len(cleaned) > 2 else "",
                    "titular": cleaned[3] if len(cleaned) > 3 else "",
                    "categoria": cleaned[4] if len(cleaned) > 4 else "",
                    "region": cleaned[5] if len(cleaned) > 5 else "",
                    "estado": cleaned[6] if len(cleaned) > 6 else "",
                    "fichaUrl": f"{BASE_URL}{link}" if link else ""
                })

            output = {
                "total": total,
                "resultados": results
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            return output

    def search_sancionatorios(self, nombre: str = "", expediente: str = "", categoria: str = "", limit: int = 15, use_cache: bool = True) -> Dict[str, Any]:
        """Busca procedimientos sancionatorios ambientales en la base oficial SNIFA de la SMA.

        La copia local caduca a la semana: vencida, se intenta refrescar; si la red falla,
        se entrega la copia vencida marcada con `copia_local_vencida` (degradación honesta).
        """
        clean_key = f"sanc_{nombre}_{expediente}_{categoria}_{limit}".replace(" ", "_").lower()
        cache_file = self._get_cache_path(clean_key)

        data = None
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = None
            except Exception:  # noqa: BLE001 — una copia ilegible no es una copia
                data = None

        if data is not None and self._cache_fresco(cache_file):
            return data
        try:
            return self._consultar_snifa(nombre, expediente, categoria, limit, cache_file)
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise


# Alias de compatibilidad hacia atrás (nomenclatura histórica)
AmbientalClient = SMAClient


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE DERECHO AMBIENTAL (SMA)
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Derecho Ambiental (SMA / SNIFA)")
    parser.add_argument("--buscar", type=str, help="Nombre del titular o proyecto (ej. 'Minera', 'AquaChile', 'AES')")
    parser.add_argument("--expediente", type=str, help="Rol de expediente sancionatorio (ej. 'D-160-2026')")
    parser.add_argument("--ultimos", action="store_true", help="Mostrar últimos sancionatorios ingresados en la SMA")
    args = parser.parse_args()

    client = SMAClient()

    if args.expediente:
        print(f"\n🌱 Consultando Expediente Sancionatorio: '{args.expediente}'...")
        res = client.search_sancionatorios(expediente=args.expediente)
        print(f"Resultados encontrados: {len(res.get('resultados', []))}")
        for item in res.get("resultados", []):
            print(f"\n[Expediente: {item.get('expediente')}] | Estado: {item.get('estado')}")
            print(f"  🏢 Titular: {item.get('titular')}")
            print(f"  🏭 Unidad: {item.get('unidadFiscalizable')} ({item.get('categoria')})")
            print(f"  📍 Región: {item.get('region')}")
            print(f"  🔗 Ficha SNIFA: {item.get('fichaUrl')}")
    elif args.buscar:
        print(f"\n🌱 Buscando en Sancionatorios SMA por titular/proyecto: '{args.buscar}'...")
        res = client.search_sancionatorios(nombre=args.buscar)
        print(f"Total registros: {res.get('total')} | Muestra ({len(res.get('resultados', []))}):")
        for item in res.get("resultados", []):
            print(f"\n - [{item.get('expediente')}] {item.get('titular')} -> {item.get('unidadFiscalizable')}")
            print(f"   Estado: {item.get('estado')} | Región: {item.get('region')}")
            print(f"   Ficha: {item.get('fichaUrl')}")
    else:
        print("\n🌱 Consultando Últimos Sancionatorios Ambientales en SNIFA (SMA)...")
        res = client.search_sancionatorios(limit=5)
        print(f"Total histórico sancionatorios SMA: {res.get('total')}")
        print("\nMuestra de expedientes recientes:")
        for item in res.get("resultados", []):
            print(f" - [{item.get('expediente')}] {item.get('titular')} ({item.get('categoria')}) -> {item.get('estado')}")
