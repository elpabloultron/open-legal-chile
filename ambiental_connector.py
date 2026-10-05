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
import pathlib
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional
from config import pedir_http, registrar_tiempo, safe_urlopen

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
        t0 = time.perf_counter()
        try:
            raw = pedir_http(url, "POST",
                             headers={"Content-Type": "application/x-www-form-urlencoded",
                                      "Accept": "application/json"},
                             cuerpo=data_bytes, timeout=25).decode("utf-8", errors="ignore")
        finally:
            registrar_tiempo("snifa.red", time.perf_counter() - t0)
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
        t0 = time.perf_counter()

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
            registrar_tiempo("snifa.cache", time.perf_counter() - t0)
            return data
        try:
            return self._consultar_snifa(nombre, expediente, categoria, limit, cache_file)
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise

    def descargar_expediente_documento(self, doc_url: str, expediente: str = "doc") -> Optional[str]:
        """Descarga el PDF oficial de un documento o resolución del expediente SNIFA."""
        if not doc_url:
            return None
        clean_exp = re.sub(r'[^A-Za-z0-9_\-]+', '_', str(expediente)).strip('_') or "doc"
        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"snifa_{clean_exp}.pdf"

        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        try:
            req = urllib.request.Request(doc_url, headers={'User-Agent': 'OpenLegalChile/1.0 (Derecho Ambiental Chile)'})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

    def get_sancionatorio_integral(self, expediente_o_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un expediente sancionatorio SNIFA con ficha oficial y estructuración canónica."""
        q = str(expediente_o_id).strip()
        res = self.search_sancionatorios(expediente=q)
        match_item = None
        if res.get("resultados"):
            match_item = res["resultados"][0]

        if not match_item:
            res_nom = self.search_sancionatorios(nombre=q)
            if res_nom.get("resultados"):
                match_item = res_nom["resultados"][0]

        if not match_item:
            return {"error": f"Procedimiento sancionatorio '{expediente_o_id}' no encontrado en SNIFA."}

        exp = match_item.get("expediente", q)
        titular = match_item.get("titular", "")
        unidad = match_item.get("unidadFiscalizable", "")
        cat = match_item.get("categoria", "")
        materia = f"{titular} — {unidad} ({cat})"
        texto_resumen = f"Expediente SNIFA {exp}: Procedimiento sancionatorio ambiental contra {titular} por infracciones en unidad fiscalizable {unidad} ({cat}). Región: {match_item.get('region', '')}. Estado procesal: {match_item.get('estado', '')}."

        doc = {
            "organismo": "SMA",
            "tipo_acto": "Sancionatorio",
            "identificador": exp,
            "numero": exp,
            "fecha": "",
            "materia": materia,
            "titular": titular,
            "unidad": unidad,
            "categoria": cat,
            "region": match_item.get("region", ""),
            "estado": match_item.get("estado", ""),
            "texto": texto_resumen,
            "texto_integral": texto_resumen,
            "link_oficial": match_item.get("fichaUrl", ""),
            "fuentes_legales": ["Ley 19.300", "Ley 20.417", "DS 40/2012"],
        }

        return doc

    def procesar_y_graficar_sma(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pipeline unificado para procedimientos sancionatorios de la SMA (SNIFA)."""
        from resolucion_administrativa2md import convertir_lote_dictamenes
        from resoluciones_parser import ResolucionesParserEngine
        from legal_graphify import LegalGraphifyEngine

        docs_procesar = []
        for item in ids_o_docs:
            if isinstance(item, str):
                doc_obj = self.get_sancionatorio_integral(item, descargar_formato=descargar_formato)
                docs_procesar.append(doc_obj)
            elif isinstance(item, dict):
                docs_procesar.append(item)

        rutas_md = []
        if convertir_a_md:
            try:
                rutas_md = [str(p) for p in convertir_lote_dictamenes(docs_procesar)]
                for i, r_path in enumerate(rutas_md):
                    if i < len(docs_procesar):
                        docs_procesar[i]["ruta_md"] = r_path
            except Exception:
                pass

        info_grafo = {}
        try:
            graph_engine = LegalGraphifyEngine()
            insumos = rutas_md if rutas_md else docs_procesar
            info_grafo = graph_engine.ingerir_lote_dictamenes(insumos, guardar_disco=False)
        except Exception as e:
            info_grafo = {"error": f"Error integrando con LegalGraphify: {str(e)}"}

        parser_engine = ResolucionesParserEngine()
        analisis = parser_engine.analizar_lote_resoluciones(docs_procesar, tema_relevante=tema_relevante)

        return {
            "organismo": "SMA",
            "total_sancionatorios": len(docs_procesar),
            "tema_relevante": tema_relevante or "General",
            "citas_destacadas": analisis.get("citas_destacadas", []),
            "grafo_impacto": {
                "nodos_nuevos": info_grafo.get("nodos_nuevos_totales", 0),
                "enlaces_nuevos": info_grafo.get("enlaces_nuevos_totales", 0),
                "grafo_total": info_grafo.get("grafo", {})
            },
            "archivos_generados": {
                "markdown": rutas_md,
                "descargas_oficiales": [d.get("archivo_descargado") for d in docs_procesar if d.get("archivo_descargado")]
            },
            "detalle_sancionatorios": analisis.get("documentos", [])
        }


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
