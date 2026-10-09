#!/usr/bin/env python3
"""
Open Legal Chile — Web Scraper y Extractor Oficial de Jurisprudencia PJUD
Extrae sentencias de la Excma. Corte Suprema y Cortes de Apelaciones desde https://juris.pjud.cl

Soporta:
  - Búsqueda por texto libre, fechas, materias y salas.
  - Extracción de metadatos estructurados (Rol, Carátula, Sala, Ministros, Recurso, Resultado).
  - Extracción de texto íntegro de considerandos y resoluciones.
  - Descarga directa de sentencias en PDF oficial o Word (.docx) editable.
  - Exportación masiva a JSONL y almacenamiento local.

Uso:
  python scripts/cosechar_pjud_scrapper.py --corte cs --texto "unificacion de doctrina" --limite 5
  python scripts/cosechar_pjud_scrapper.py --corte ca --texto "despido injustificado" --descargar pdf
  python scripts/cosechar_pjud_scrapper.py --corte cs --rol "14076-2026" --descargar docx
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, List, Optional
import requests

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "pjud_descargas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


class PJUDScraper:
    """Scraper y extractor para el portal oficial de jurisprudencia judicial de Chile (juris.pjud.cl)."""

    URL_BASE = "https://juris.pjud.cl"
    URL_BUSQUEDA = f"{URL_BASE}/busqueda/buscar_sentencias"
    URL_IMPRIMIR = f"{URL_BASE}/busqueda/imprimir"

    BUSCADORES = {
        "cs": {"nombre": "Corte Suprema", "id": "528", "url": f"{URL_BASE}/busqueda?Corte_Suprema"},
        "ca": {"nombre": "Corte de Apelaciones", "id": "168", "url": f"{URL_BASE}/busqueda?Corte_de_Apelaciones"},
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9",
        })
        self._tokens: Dict[str, str] = {}

    def _obtener_token(self, tipo_corte: str) -> str:
        """Obtiene el token CSRF de la sesión para el buscador respectivo."""
        if tipo_corte in self._tokens:
            return self._tokens[tipo_corte]

        cfg = self.BUSCADORES.get(tipo_corte.lower(), self.BUSCADORES["cs"])
        r = self.session.get(cfg["url"], headers={"Accept": "text/html"}, timeout=20)
        r.raise_for_status()

        match = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
        if not match:
            raise RuntimeError(f"No se pudo extraer el token CSRF de {cfg['url']}")

        token = match.group(1)
        self._tokens[tipo_corte] = token
        return token

    def buscar(
        self,
        tipo_corte: str = "cs",
        texto: str = "",
        fec_desde: str = "",
        fec_hasta: str = "",
        limite: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta la búsqueda sobre el motor Solr/Laravel de juris.pjud.cl.
        Retorna la lista de documentos con metadatos y texto limpio.
        """
        tipo_corte = tipo_corte.lower()
        if tipo_corte not in self.BUSCADORES:
            raise ValueError("tipo_corte debe ser 'cs' (Corte Suprema) o 'ca' (Cortes de Apelaciones)")

        cfg = self.BUSCADORES[tipo_corte]
        token = self._obtener_token(tipo_corte)

        filtros = {
            "texto": texto,
            "tipo_norma": "", "codigo_norma": "", "numero_norma": "",
            "numero_articulo": "", "numero_inciso": "",
            "fec_desde": fec_desde, "fec_hasta": fec_hasta,
            "facetas_seleccionadas": [],
            "palabras": {"todas": "", "algunas": "", "excluir": "", "literal": "", "proximidad": "", "distancia": ""},
            "orden": "fecha_desc", "pagina": 1, "largo_pagina": limite,
        }

        payload = {
            "_token": token,
            "id_buscador": cfg["id"],
            "filtros": json.dumps(filtros, ensure_ascii=False),
            "numero_filas_paginacion": str(limite),
            "offset_paginacion": str(offset),
            "orden": "fecha_desc",
            "personalizacion": "",
        }

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": cfg["url"],
        }

        resp = self.session.post(self.URL_BUSQUEDA, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        raw_docs = data.get("response", {}).get("docs", [])

        sentencias = []
        for d in raw_docs:
            sentencias.append(self._normalizar_documento(d, tipo_corte))

        return sentencias

    def _normalizar_documento(self, d: Dict[str, Any], tipo_corte: str) -> Dict[str, Any]:
        """Normaliza los campos del Solr a una estructura limpia de Open Legal Chile."""
        doc_id = d.get("id") or d.get("sent__crr_documento_i")
        rol = d.get("rol_era_sup_s") or d.get("rol_era_ape_s") or ""
        era = d.get("era_sup_i") or d.get("era_corte_i") or ""
        fecha = (d.get("fec_sentencia_sup_dt") or d.get("fec_sentencia_ape_dt") or "")[:10]
        corte = "Corte Suprema" if tipo_corte == "cs" else (d.get("gls_corte_s") or "Corte de Apelaciones")
        sala = d.get("gls_sala_sup_s") or ""
        recurso = d.get("gls_tip_recurso_sup_s") or d.get("gls_tip_recurso_ape_s") or ""
        resultado = d.get("resultado_recurso_sup_s") or d.get("resultado_recurso_ape_s") or ""
        caratula = d.get("caratulado_s") or d.get("caratulado_anon_s") or ""
        ministros = d.get("sent__gls_int_firma_sup_s") or ""

        # Limpieza básica de HTML de texto_sentencia
        raw_texto = d.get("texto_sentencia") or ""
        clean_texto = re.sub(r"<br\s*/?>", "\n", raw_texto)
        clean_texto = re.sub(r"<[^>]+>", "", clean_texto)
        clean_texto = re.sub(r"[ \t]+", " ", clean_texto)
        clean_texto = re.sub(r"\n{3,}", "\n\n", clean_texto).strip()

        return {
            "id": doc_id,
            "documento_id": d.get("sent__crr_documento_i"),
            "tipo_corte": tipo_corte,
            "tribunal": corte,
            "sala": sala,
            "rol": rol,
            "era": era,
            "fecha": fecha,
            "caratula": caratula,
            "recurso": recurso,
            "resultado": resultado,
            "ministros": ministros,
            "texto_integral": clean_texto,
            "id_buscador": self.BUSCADORES[tipo_corte]["id"],
            "url_origen": f"{self.URL_BASE}/busqueda?{'Corte_Suprema' if tipo_corte == 'cs' else 'Corte_de_Apelaciones'}",
        }

    def descargar_documento(
        self,
        doc_id: Any,
        tipo_corte: str = "cs",
        formato: str = "pdf",
        ruta_destino: Optional[pathlib.Path] = None
    ) -> pathlib.Path:
        """
        Descarga el documento oficial generado por PJUD.
        Formatos soportados:
          - 'pdf' (opcion=0): Documento PDF oficial
          - 'docx' (opcion=4): Documento Word (.docx) editable
          - 'html' (opcion=1): HTML renderizado
        """
        tipo_corte = tipo_corte.lower()
        cfg = self.BUSCADORES.get(tipo_corte, self.BUSCADORES["cs"])
        token = self._obtener_token(tipo_corte)

        opciones = {"pdf": "0", "html": "1", "docx": "4"}
        opcion_cod = opciones.get(formato.lower(), "0")

        payload = {
            "_token": token,
            "id_buscador": cfg["id"],
            "id": str(doc_id),
            "opcion": opcion_cod,
        }

        headers = {
            "Referer": cfg["url"],
        }

        r = self.session.post(self.URL_IMPRIMIR, data=payload, headers=headers, timeout=40)
        r.raise_for_status()

        if not r.content:
            raise RuntimeError(f"El servidor PJUD devolvió 0 bytes para el documento {doc_id} en formato {formato}")

        if not ruta_destino:
            extension = "docx" if formato.lower() == "docx" else ("html" if formato.lower() == "html" else "pdf")
            nombre_archivo = f"sentencia_{tipo_corte}_{doc_id}.{extension}"
            ruta_destino = OUTPUT_DIR / nombre_archivo

        ruta_destino.write_bytes(r.content)
        return ruta_destino


def main():
    parser = argparse.ArgumentParser(description="Scraper oficial de jurisprudencia PJUD (Corte Suprema y Apelaciones)")
    parser.add_argument("--corte", choices=["cs", "ca", "ambos"], default="cs", help="Corte a consultar: cs (Suprema), ca (Apelaciones) o ambos")
    parser.add_argument("--texto", default="", help="Término o frase a buscar en la jurisprudencia")
    parser.add_argument("--rol", default="", help="Filtrar por Rol específico (ej. 14076-2026)")
    parser.add_argument("--desde", default="", help="Fecha desde (YYYY-MM-DD)")
    parser.add_argument("--hasta", default="", help="Fecha hasta (YYYY-MM-DD)")
    parser.add_argument("--limite", type=int, default=5, help="Cantidad máxima de sentencias a recuperar")
    parser.add_argument("--descargar", choices=["pdf", "docx", "ninguno"], default="ninguno", help="Descargar archivo oficial")
    parser.add_argument("--salida-jsonl", default="", help="Ruta para exportar los resultados en formato JSONL")

    args = parser.parse_args()

    scraper = PJUDScraper()
    cortes = ["cs", "ca"] if args.corte == "ambos" else [args.corte]

    termino_busqueda = args.rol if args.rol else args.texto
    todos_los_docs = []

    for c in cortes:
        print(f"\n[*] Consultando {scraper.BUSCADORES[c]['nombre']} en {scraper.BUSCADORES[c]['url']}...")
        docs = scraper.buscar(
            tipo_corte=c,
            texto=termino_busqueda,
            fec_desde=args.desde,
            fec_hasta=args.hasta,
            limite=args.limite,
        )
        print(f"[+] Se encontraron {len(docs)} sentencias:")
        for doc in docs:
            print(f"  · ID: {doc['id']} | Rol: {doc['rol']} | Fecha: {doc['fecha']} | Sala: {doc['sala']}")
            print(f"    Carátula: {doc['caratula'][:80]}")
            print(f"    Recurso: {doc['recurso']} -> Resultado: {doc['resultado']}")
            if doc['ministros']:
                print(f"    Ministros: {doc['ministros'][:70]}...")

            if args.descargar != "ninguno":
                print(f"    [->] Descargando {args.descargar.upper()}...")
                archivo_salida = scraper.descargar_documento(doc["id"], tipo_corte=c, formato=args.descargar)
                print(f"    [OK] Guardado en: {archivo_salida}")

            todos_los_docs.append(doc)

    if args.salida_jsonl:
        ruta_jsonl = pathlib.Path(args.salida_jsonl)
        ruta_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_jsonl, "w", encoding="utf-8") as f:
            for d in todos_los_docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"\n[V] Catálogo exportado con éxito a {ruta_jsonl} ({len(todos_los_docs)} registros)")


if __name__ == "__main__":
    main()
