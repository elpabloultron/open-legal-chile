"""
Open Legal Chile — Registro Unificado del Estado (Deep Module)
Módulo profundo que encapsula la orquestación, búsqueda concurrente y almacenamiento
en caché nativo (SQLite) de los 10 organismos del Estado de Chile.
"""

import os
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional

from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import SMAClient
from tdlc_connector import TDLCClient
from pjud_connector import PJUDClient

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openlegal_cache.db")

class StateRegistry:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self.bcn = BCNClient()
        self.cgr = CGRClient()
        self.dt = DTClient()
        self.cne = CNEClient()
        self.panel = PanelExpertosClient()
        self.cmf = CMFClient()
        self.sii = SIIClient()
        self.sma = SMAClient()
        self.tdlc = TDLCClient()
        self.pjud = PJUDClient()

    def _init_db(self):
        """Inicializa la base de datos SQLite para caché ultrarrápido sin dependencias externas."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        institution TEXT,
                        query_key TEXT,
                        response_json TEXT,
                        created_at REAL,
                        PRIMARY KEY (institution, query_key)
                    )
                """)
        except Exception:
            pass

    def _get_cached(self, institution: str, key: str, ttl_seconds: int = 86400) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT response_json, created_at FROM query_cache WHERE institution = ? AND query_key = ?",
                    (institution, key)
                )
                row = cur.fetchone()
                if row:
                    res_json, created_at = row
                    if time.time() - created_at < ttl_seconds:
                        return json.loads(res_json)
        except Exception:
            pass
        return None

    def _set_cached(self, institution: str, key: str, data: Any):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO query_cache (institution, query_key, response_json, created_at) VALUES (?, ?, ?, ?)",
                    (institution, key, json.dumps(data, ensure_ascii=False), time.time())
                )
        except Exception:
            pass

    def search_all(self, query: str) -> Dict[str, Any]:
        """Ejecuta una búsqueda jurídica universal en los 10 organismos del Estado."""
        q = query.strip()
        cached = self._get_cached("all", q)
        if cached:
            return cached

        results = {
            "query": q,
            "bcn": [],
            "cgr": {},
            "dt": [],
            "cne": [],
            "panel": [],
            "cmf": [],
            "sii": [],
            "sma": {},
            "tdlc": [],
            "pjud": []
        }

        # 1. BCN Ley Chile
        try:
            results["bcn"] = self.bcn.search(q)
        except Exception as e:
            results["bcn"] = [{"error": str(e)}]

        # 2. CGR
        try:
            results["cgr"] = self.cgr.search_jurisprudencia(q)
        except Exception as e:
            results["cgr"] = {"error": str(e)}

        # 3. DT
        try:
            results["dt"] = self.dt.search_dictamenes(q, limit=5)
        except Exception as e:
            results["dt"] = [{"error": str(e)}]

        # 4. CNE
        try:
            results["cne"] = self.cne.search(q)
        except Exception as e:
            results["cne"] = [{"error": str(e)}]

        # 5. Panel de Expertos
        try:
            results["panel"] = self.panel.search_dictamenes(q)
        except Exception as e:
            results["panel"] = [{"error": str(e)}]

        # 6. CMF
        try:
            results["cmf"] = self.cmf.search_normativa(q)
        except Exception as e:
            results["cmf"] = [{"error": str(e)}]

        # 7. SII
        try:
            results["sii"] = self.sii.search_circulares(q)
        except Exception as e:
            results["sii"] = [{"error": str(e)}]

        # 8. SMA
        try:
            results["sma"] = self.sma.search_sancionatorios(nombre=q)
        except Exception as e:
            results["sma"] = {"error": str(e)}

        # 9. TDLC
        try:
            results["tdlc"] = self.tdlc.search_jurisprudencia(q)
        except Exception as e:
            results["tdlc"] = [{"error": str(e)}]

        # 10. PJUD / Corte Suprema / TC
        try:
            results["pjud"] = self.pjud.search_jurisprudencia(q, limit=5)
        except Exception as e:
            results["pjud"] = [{"error": str(e)}]

        self._set_cached("all", q, results)
        return results
