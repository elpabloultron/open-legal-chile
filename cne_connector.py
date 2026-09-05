"""
Open Legal Chile — Conector Oficial Comisión Nacional de Energía (CNE / Energía Abierta)
Módulo para consultar datos regulatorios, capacidad instalada, generación eléctrica,
proyectos SEA, clientes libres/regulados y combustibles en el mercado energético chileno.
"""

import os
import sys
import json
import time
import gzip
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

from config import CNE_EMAIL, CNE_PASSWORD, safe_urlopen

CNE_BASE_URL = "https://api.cne.cl"
BASE_URL = "https://api.cne.cl/api/v1"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cne_cache")


class CNEClient:
    def __init__(self, email: str = CNE_EMAIL, password: str = CNE_PASSWORD, cache_dir: str = CACHE_DIR):
        self.email = email
        self.password = password
        self.cache_dir = cache_dir
        self.token = None
        self.token_expiry: float = 0.0
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, endpoint_key: str) -> str:
        return os.path.join(self.cache_dir, f"{endpoint_key}.json")

    def login(self) -> Optional[str]:
        """Autentica con la API de la CNE y obtiene un token JWT válido."""
        if not self.email or not self.password or self.email == "tu_correo@ejemplo.cl":
            return None

        if self.token and time.time() < (self.token_expiry - 300):
            return self.token

        token_cache_file = os.path.join(self.cache_dir, "auth_token.json")
        if os.path.exists(token_cache_file):
            try:
                with open(token_cache_file, "r", encoding="utf-8") as f:
                    cached_auth = json.load(f)
                    if cached_auth.get("token") and time.time() < cached_auth.get("expires_at", 0):
                        self.token = cached_auth["token"]
                        self.token_expiry = cached_auth["expires_at"]
                        return self.token
            except Exception:
                pass

        login_url = f"{CNE_BASE_URL}/api/login"
        payload = urllib.parse.urlencode({
            "email": self.email,
            "password": self.password
        }).encode("utf-8")

        req = urllib.request.Request(
            login_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "OpenLegalChile/1.0 (Derecho Energetico Chile)"
            }
        )

        try:
            with safe_urlopen(req, timeout=15) as resp:
                raw_resp = resp.read().decode("utf-8", errors="ignore")
                if raw_resp.strip():
                    data = json.loads(raw_resp)
                    self.token = data.get("token")
                    self.token_expiry = time.time() + 3600

                    with open(token_cache_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "token": self.token,
                            "expires_at": self.token_expiry
                        }, f)

                    return self.token
        except Exception:
            pass

        return None

    def _get(self, endpoint: str, cache_key: Optional[str] = None, use_cache: bool = True) -> Any:
        """Realiza una petición GET autenticada a la API de la CNE descomprimiendo gzip."""
        if cache_key:
            cache_file = self._get_cache_path(cache_key)
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass

        token = self.login()
        if not token:
            # Si no hay token y no hay caché, retornar estructura vacía consistente
            return []

        url = f"{CNE_BASE_URL}{endpoint}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "OpenLegalChile/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            }
        )

        try:
            with safe_urlopen(req, timeout=45) as resp:
                raw_bytes = resp.read()
                is_gzip = resp.headers.get("Content-Encoding") == "gzip" or raw_bytes[:2] == b'\x1f\x8b'
                if is_gzip:
                    content = gzip.decompress(raw_bytes).decode("utf-8", errors="ignore")
                else:
                    content = raw_bytes.decode("utf-8", errors="ignore")

                parsed = json.loads(content)
                # Extraer listado de datos si viene envuelto en objeto {success: true, data: [...]}
                data = parsed.get("data", parsed) if isinstance(parsed, dict) and "data" in parsed else parsed

                if cache_key:
                    cache_file = self._get_cache_path(cache_key)
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                return data
        except Exception:
            return []


    # =========================================================================
    # ENDPOINTS DE DERECHO ELÉCTRICO Y REGULATORIO (ENERGÍA ABIERTA)
    # =========================================================================

    def get_capacidad_instalada(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene la capacidad instalada de generación eléctrica (MW) por tecnología y sistema."""
        return self._get("/api/ea/capacidad/instaladagx", "capacidad_instalada", use_cache)

    def get_proyectos_sea(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene proyectos de energía en tramitación en el Sistema de Evaluación Ambiental (SEA)."""
        return self._get("/api/ea/proyectos/sea", "proyectos_sea", use_cache)

    def get_proyectos_en_construccion(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene el catastro de proyectos de generación y transmisión eléctrica en construcción."""
        return self._get("/api/ea/proyectosenconstrucciongx", "proyectos_construccion", use_cache)

    def get_generacion_bruta_mensual(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene la generación eléctrica bruta mensual (GWh) por central y empresa generadora."""
        return self._get("/api/ea/generacionbrutamensual", "generacion_bruta_mensual", use_cache)

    def get_clientes_libres(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene estadísticas de clientes libres (consumos > 500 kW / 5 MW para contratos PPA)."""
        return self._get("/api/ea/cantidad/clienteslibres", "clientes_libres", use_cache)

    def get_clientes_regulados(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene estadísticas de clientes sujetos a fijación de precios y tarifas de distribución."""
        return self._get("/api/ea/cantidad/clientesregulados", "clientes_regulados", use_cache)

    def get_generacion_distribuida(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene proyectos de Net Billing / Generación Distribuida (Ley 20.571 y Ley 21.118)."""
        return self._get("/api/ea/netbilling", "generacion_distribuida", use_cache)

    def get_precios_gas_natural(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene estadísticas de precios de gas natural para generación y distribución."""
        return self._get("/api/ea/precio/gasnatural", "precio_gas_natural", use_cache)

    def get_precios_glp(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene precios de Gas Licuado de Petróleo (GLP)."""
        return self._get("/api/ea/precio/glp", "precio_glp", use_cache)

    def get_factor_emision(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene el factor de emisión de gases de efecto invernadero del Sistema Eléctrico Nacional."""
        return self._get("/api/ea/factoremision", "factor_emision", use_cache)

    def get_estaciones_servicio(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene el catastro de estaciones de servicio de combustibles líquidos a nivel nacional."""
        return self._get("/api/v4/estaciones", "estaciones_servicio", use_cache)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda de texto en centrales generadoras y proyectos SEA de la CNE."""
        q_lower = query.lower().strip()
        results = []
        datasets = []
        try:
            datasets.append(self.get_capacidad_instalada())
        except Exception:
            pass
        try:
            datasets.append(self.get_proyectos_sea())
        except Exception:
            pass

        for dataset in datasets:
            if not isinstance(dataset, list):
                continue
            for item in dataset:
                if not isinstance(item, dict):
                    continue
                if q_lower in json.dumps(item, ensure_ascii=False).lower():
                    results.append(item)
                    if len(results) >= limit:
                        return results
        return results


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE DERECHO ENERGÉTICO
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — CNE Comisión Nacional de Energía")
    parser.add_argument("--capacidad", action="store_true", help="Consultar capacidad instalada de generación")
    parser.add_argument("--proyectos-sea", action="store_true", help="Consultar proyectos en el SEA")
    parser.add_argument("--proyectos-construccion", action="store_true", help="Consultar proyectos en construcción")
    parser.add_argument("--clientes", action="store_true", help="Consultar clientes libres y regulados")
    parser.add_argument("--netbilling", action="store_true", help="Consultar proyectos de generación distribuida")
    parser.add_argument("--estaciones", action="store_true", help="Consultar estaciones de servicio de combustible")
    args = parser.parse_args()

    client = CNEClient()

    if args.capacidad:
        print("\n⚡ Consultando Capacidad Instalada en el Sistema Eléctrico Nacional (CNE)...")
        data = client.get_capacidad_instalada()
        print(f"Total registros obtenidos: {len(data) if isinstance(data, list) else 'OK'}")
        if isinstance(data, list) and len(data) > 0:
            print("\nMuestra de centrales generadoras:")
            for item in data[:3]:
                print(f" - {item.get('central')} ({item.get('tipo_tecnologia', item.get('tecnologia', 'Central'))}): {item.get('potencia_bruta', item.get('potencia_neta', item.get('capacidad_mw', 'N/A')))} MW | Titular: {item.get('razon_social', item.get('propietario'))}")
    elif args.proyectos_sea:
        print("\n🌱 Consultando Proyectos Energéticos en Evaluación Ambiental (SEA / CNE)...")
        data = client.get_proyectos_sea()
        print(f"Total proyectos registrados en SEA: {len(data) if isinstance(data, list) else 'OK'}")
        if isinstance(data, list) and len(data) > 0:
            for item in data[:3]:
                print(f" - {item.get('nombre_proyecto', item.get('proyecto'))} | Inversión: US${item.get('inversion_mmusd', item.get('inversion', 'N/A'))} MM | Estado: {item.get('estado')}")
    elif args.proyectos_construccion:
        print("\n🏗️ Consultando Proyectos de Generación y Transmisión en Construcción...")
        data = client.get_proyectos_en_construccion()
        print(f"Total proyectos en construcción: {len(data) if isinstance(data, list) else 'OK'}")
        if isinstance(data, list) and len(data) > 0:
            for item in data[:3]:
                print(" -", item)
    elif args.clientes:
        print("\n🏢 Consultando Clientes Libres vs. Clientes Regulados (CNE)...")
        libres = client.get_clientes_libres()
        regulados = client.get_clientes_regulados()
        print(f"Total registros Clientes Libres: {len(libres) if isinstance(libres, list) else 'OK'}")
        print(f"Total registros Clientes Regulados: {len(regulados) if isinstance(regulados, list) else 'OK'}")
    elif args.netbilling:
        print("\n☀️ Consultando Generación Distribuida (Ley 20.571 / Net Billing)...")
        data = client.get_generacion_distribuida()
        print(f"Total registros Net Billing: {len(data) if isinstance(data, list) else 'OK'}")
    elif args.estaciones:
        print("\n⛽ Consultando Estaciones de Servicio (CNE)...")
        data = client.get_estaciones_servicio()
        print(f"Total estaciones registradas: {len(data) if isinstance(data, list) else 'OK'}")
    else:
        print("Uso: python cne_connector.py [--capacidad | --proyectos-sea | --proyectos-construccion | --clientes | --netbilling | --estaciones]")
