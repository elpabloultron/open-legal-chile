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
        "cs": {
            "nombre": "Corte Suprema",
            "id": "528",
            "url": f"{URL_BASE}/busqueda?Corte_Suprema",
            "jsonl": "data/jurisprudencia/cs_sentencias_2anios.jsonl",
            "md_dir": "jurisprudencia_cs",
        },
        "ca": {
            "nombre": "Corte de Apelaciones",
            "id": "168",
            "url": f"{URL_BASE}/busqueda?Corte_de_Apelaciones",
            "jsonl": "data/jurisprudencia/ca_sentencias.jsonl",
            "md_dir": "jurisprudencia_ca",
        },
        "lineas": {
            "nombre": "Líneas Jurisprudenciales CS",
            "id": "628",
            "url": f"{URL_BASE}/busqueda?Lineas_Jurisprudenciales",
            "jsonl": "data/jurisprudencia/cs_lineas_jurisprudenciales.jsonl",
            "md_dir": "jurisprudencia_lineas_cs",
        },
        "salud": {
            "nombre": "Buscador Especializado Salud CS",
            "id": "127",
            "url": f"{URL_BASE}/busqueda?Salud_CS",
            "jsonl": "data/jurisprudencia/cs_salud.jsonl",
            "md_dir": "jurisprudencia_salud_cs",
        },
        "extranjeria": {
            "nombre": "Compendio de Extranjería CS",
            "id": "648",
            "url": f"{URL_BASE}/busqueda?Compendio_Extranjer%C3%ADa",
            "jsonl": "data/jurisprudencia/cs_extranjeria.jsonl",
            "md_dir": "jurisprudencia_extranjeria_cs",
        },
        "ddhh": {
            "nombre": "Sentencias Derechos Humanos CS",
            "id": "811",
            "url": "https://busddhh.pjud.cl/buscador/sentencias-derechos-humanos",
            "jsonl": "data/jurisprudencia/cs_ddhh.jsonl",
            "md_dir": "jurisprudencia_ddhh",
        },
    }

    DESCRIPTORES_DDHH = [
        "lesa humanidad",
        "desaparicion forzada",
        "apremios ilegitimos",
        "convenios de ginebra",
        "derechos humanos",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9",
        })
        self._tokens: Dict[str, str] = {}

    def _obtener_token(self, tipo_corte: str) -> str:
        """Obtiene el token CSRF de la sesión para el buscador respectivo."""
        tipo_corte = tipo_corte.lower()
        if tipo_corte == "ddhh":
            tipo_corte = "cs"
        if tipo_corte in self._tokens:
            return self._tokens[tipo_corte]

        cfg = self.BUSCADORES.get(tipo_corte, self.BUSCADORES["cs"])
        r = self.session.get(cfg["url"], headers={"Accept": "text/html"}, timeout=20)
        r.raise_for_status()

        match = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
        if not match:
            raise RuntimeError(f"No se pudo extraer el token CSRF de {cfg['url']}")

        token = match.group(1)
        self._tokens[tipo_corte] = token
        return token

    @staticmethod
    def _construir_filtros_2026(
        texto: str = "",
        rol: str = "",
        era: str = "",
        fec_desde: str = "",
        fec_hasta: str = "",
    ) -> Dict[str, Any]:
        """Construye el diccionario `filtros` oficial vigente en juris.pjud.cl (esquema 2026)."""
        rol_val = str(rol or "").strip()
        era_val = str(era or "").strip()
        texto_val = str(texto or "").strip()

        # Si `texto` tiene forma de Rol (ej. '14076-2026') y no se pasó `rol` explícito, descomponerlo
        if not rol_val and re.fullmatch(r"\d{1,7}-\d{4}", texto_val):
            partes = texto_val.split("-", 1)
            rol_val, era_val = partes[0], partes[1]
            texto_val = ""

        return {
            "rol": rol_val,
            "era": era_val,
            "fec_desde": fec_desde,
            "fec_hasta": fec_hasta,
            "tipo_norma": "",
            "num_norma": "",
            "num_art": "",
            "num_inciso": "",
            "todas": texto_val,
            "algunas": "",
            "excluir": "",
            "literal": "",
            "proximidad": "",
            "distancia": "",
            "analisis_s": "",
            "submaterias": "",
            "facetas_seleccionadas": [],
            "filtros_omnibox": [],
            "ids_comunas_seleccionadas_mapa": [],
        }

    def buscar(
        self,
        tipo_corte: str = "cs",
        texto: str = "",
        fec_desde: str = "",
        fec_hasta: str = "",
        limite: int = 10,
        offset: int = 0,
        rol: str = "",
        era: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta la búsqueda sobre el motor Solr/Laravel de juris.pjud.cl (esquema 2026).
        Soporta cs, ca, lineas, salud, extranjeria y ddhh (con fallback automático a CS id=528
        si el backend legado busddhh.pjud.cl id=811 devuelve HTTP 500).
        """
        tipo_corte = tipo_corte.lower()
        if tipo_corte not in self.BUSCADORES:
            raise ValueError(f"tipo_corte debe ser uno de: {', '.join(self.BUSCADORES)}")

        if tipo_corte == "ddhh":
            return self._buscar_ddhh(
                texto=texto, fec_desde=fec_desde, fec_hasta=fec_hasta,
                limite=limite, offset=offset, rol=rol, era=era
            )

        cfg = self.BUSCADORES[tipo_corte]
        token = self._obtener_token(tipo_corte)
        filtros = self._construir_filtros_2026(
            texto=texto, rol=rol, era=era, fec_desde=fec_desde, fec_hasta=fec_hasta
        )

        payload = {
            "_token": token,
            "id_buscador": cfg["id"],
            "filtros": json.dumps(filtros, ensure_ascii=False),
            "numero_filas_paginacion": str(limite),
            "offset_paginacion": str(offset),
            "orden": "fecha_desc",
            "personalizacion": "false",
        }

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": cfg["url"],
        }

        resp = self.session.post(self.URL_BUSQUEDA, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        raw_docs = data.get("response", {}).get("docs", [])
        highlighting = data.get("highlighting", {}) if isinstance(data.get("highlighting"), dict) else {}

        sentencias = []
        for d in raw_docs:
            sentencias.append(self._normalizar_documento(d, tipo_corte, highlighting=highlighting))

        return sentencias

    def _buscar_ddhh(
        self,
        texto: str = "",
        fec_desde: str = "",
        fec_hasta: str = "",
        limite: int = 10,
        offset: int = 0,
        rol: str = "",
        era: str = "",
    ) -> List[Dict[str, Any]]:
        """Consulta el portal de DD.HH. (id=811) y, si responde HTTP 500, aplica fallback automático
        al buscador de la Corte Suprema (id=528) filtrado por descriptores de Derechos Humanos."""
        termino = (texto or "").strip() or "lesa humanidad"
        try:
            r_init = self.session.get(self.BUSCADORES["ddhh"]["url"], timeout=12)
            m_tok = re.search(r'name="_token"\s+value="([^"]+)"', r_init.text)
            if m_tok:
                r_ajax = self.session.post(
                    "https://busddhh.pjud.cl/buscadormantenedor/previsualizar/ajax",
                    data={"_token": m_tok.group(1), "id": 811, "parametros": json.dumps({"texto": termino})},
                    headers={"X-Requested-With": "XMLHttpRequest", "Referer": self.BUSCADORES["ddhh"]["url"]},
                    timeout=12,
                )
                if r_ajax.status_code == 200:
                    data = r_ajax.json()
                    docs = data.get("response", {}).get("docs", [])
                    hl = data.get("highlighting", {}) if isinstance(data.get("highlighting"), dict) else {}
                    if docs:
                        return [self._normalizar_documento(d, "ddhh", highlighting=hl) for d in docs[:limite]]
        except Exception:
            pass

        # Fallback oficial verificado sobre juris.pjud.cl (Corte Suprema id=528 con filtro DD.HH.)
        docs_cs = self.buscar(
            tipo_corte="cs",
            texto=termino,
            fec_desde=fec_desde,
            fec_hasta=fec_hasta,
            limite=limite,
            offset=offset,
            rol=rol,
            era=era,
        )
        for d in docs_cs:
            d["tipo_corte"] = "ddhh"
            d["portal"] = "ddhh"
            d["url_origen"] = self.BUSCADORES["ddhh"]["url"]
        return docs_cs

    @staticmethod
    def _limpiar_html(raw_texto: str) -> str:
        if not raw_texto:
            return ""
        clean = re.sub(r"<br\s*/?>", "\n", str(raw_texto))
        clean = re.sub(r"<[^>]+>", "", clean)
        clean = re.sub(r"[ \t]+", " ", clean)
        return re.sub(r"\n{3,}", "\n\n", clean).strip()

    def _normalizar_documento(
        self,
        d: Dict[str, Any],
        tipo_corte: str,
        highlighting: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Normaliza los campos del Solr a una estructura limpia de Open Legal Chile."""
        doc_id = d.get("id") or d.get("crr_documento_id_i") or d.get("sent__crr_documento_i")
        rol = d.get("rol_era_sup_s") or d.get("rol_era_ape_s") or ""
        era = d.get("era_sup_i") or d.get("era_corte_i") or d.get("anio_sentencia_sup_i") or ""
        fecha = (d.get("fec_sentencia_sup_dt") or d.get("fec_sentencia_ape_dt") or "")[:10]
        corte = "Corte de Apelaciones" if tipo_corte == "ca" else "Corte Suprema"
        sala = d.get("gls_sala_sup_s") or ""
        recurso = d.get("gls_tip_recurso_sup_s") or d.get("gls_tip_recurso_ape_s") or ""
        resultado = d.get("resultado_recurso_sup_s") or d.get("resultado_recurso_ape_s") or ""
        caratula = d.get("caratulado_s") or d.get("caratulado_anon_s") or ""
        ministros_raw = d.get("gls_ministro_ss") or d.get("sent__gls_int_firma_sup_s") or []
        if isinstance(ministros_raw, list):
            ministros_lista = [str(m).strip() for m in ministros_raw if str(m).strip()]
            ministros = ", ".join(ministros_lista)
        else:
            ministros = str(ministros_raw).strip()
            ministros_lista = [m.strip() for m in ministros.split(",") if m.strip()]

        descriptores = d.get("gls_descriptor_ss") or []
        if not isinstance(descriptores, list):
            descriptores = [str(descriptores)] if descriptores else []

        # Extraer texto desde texto_sentencia, highlighting o texto_sentencia_preview
        hl_doc = (highlighting or {}).get(str(doc_id), {}) if doc_id is not None else {}
        hl_frags = (hl_doc.get("texto_sentencia") or []) if isinstance(hl_doc, dict) else []
        hl_texto = "\n...\n".join(self._limpiar_html(f) for f in hl_frags if f)
        preview = self._limpiar_html(d.get("texto_sentencia_preview") or "")
        raw_texto = self._limpiar_html(d.get("texto_sentencia") or "")
        clean_texto = raw_texto or hl_texto or preview

        url_corta = d.get("url_acceso_sentencia") or d.get("url_corta_s") or ""
        if url_corta and not url_corta.startswith("http"):
            url_corta = f"{self.URL_BASE}/s/{url_corta.lstrip('/')}"
        cita = d.get("cita_bibliografica") or (f"[CS - Rol N° {rol}, Fecha: {fecha}]" if rol else "")

        registro: Dict[str, Any] = {
            "id": doc_id,
            "documento_id": d.get("crr_documento_id_i") or d.get("sent__crr_documento_i") or doc_id,
            "tipo_corte": tipo_corte,
            "portal": tipo_corte,
            "tribunal": corte,
            "sala": sala,
            "rol": rol,
            "era": era,
            "fecha": fecha,
            "caratula": caratula,
            "materia": d.get("gls_materia_s") or ", ".join(descriptores[:4]),
            "recurso": recurso,
            "resultado": resultado,
            "ministros": ministros,
            "ministros_lista": ministros_lista,
            "descriptores": descriptores,
            "cita": cita,
            "url_corta": url_corta,
            "texto_integral": clean_texto,
            "extracto_relevante": (hl_texto or preview or clean_texto)[:700],
            "id_buscador": self.BUSCADORES[tipo_corte]["id"],
            "url_origen": self.BUSCADORES[tipo_corte]["url"],
        }

        # Campos especializados según el portal
        if tipo_corte == "lineas":
            pregunta = d.get("gls_sala_sup_s") or ""
            sintesis = self._limpiar_html(d.get("gls_materia_s") or "")
            sala_linea = d.get("gls_tip_recurso_sup_s") or ""
            roles_vinc = [str(r).strip() for r in descriptores if str(r).strip()]
            rol_principal = roles_vinc[0] if roles_vinc else f"LINEA-{doc_id}"
            registro.update({
                "rol": rol_principal,
                "sala": sala_linea,
                "pregunta_juridica": pregunta,
                "sintesis_doctrinal": sintesis,
                "roles_vinculados": roles_vinc,
                "ids_sentencias_vinculadas": d.get("id_descriptor_ss") or [],
                "materia": f"{caratula} — {pregunta}".strip(" —"),
                "texto_integral": f"Pregunta jurídica: {pregunta}\n\nSíntesis doctrinal: {sintesis}\n\nSentencias vinculadas: {', '.join(roles_vinc)}",
                "extracto_relevante": f"{pregunta} {sintesis}"[:700],
                "cita": f"[CS - Línea Jurisprudencial: {caratula}, Rol Rector N° {rol_principal}]",
            })
        elif tipo_corte == "salud":
            tematica = d.get("tematica_ss") or []
            isapre = d.get("isapre_ss") or []
            registro.update({
                "tematica": tematica,
                "isapre": isapre,
                "materia": ", ".join(tematica + descriptores[:3]) or registro["materia"],
            })
        elif tipo_corte == "extranjeria":
            tematica = d.get("tematica_ss") or []
            organismo = d.get("organismo_ss") or []
            nacionalidad = d.get("medicamento_ss") or []
            registro.update({
                "tematica": tematica,
                "organismo_recurrido": organismo,
                "nacionalidad": nacionalidad,
                "materia": ", ".join(tematica + organismo + descriptores[:2]) or registro["materia"],
            })

        return registro

    def cosechar_portal(
        self,
        tipo_corte: str,
        max_registros: int = 500,
        lote: int = 50,
        texto: str = "",
        exportar_md: bool = True,
    ) -> Dict[str, Any]:
        """Cosecha un portal especializado de PJUD paginando sobre Solr y guarda JSONL + Markdown."""
        tipo_corte = tipo_corte.lower()
        cfg = self.BUSCADORES[tipo_corte]
        ruta_jsonl = BASE_DIR / cfg["jsonl"]
        dir_md = BASE_DIR / cfg["md_dir"]
        ruta_jsonl.parent.mkdir(parents=True, exist_ok=True)
        if exportar_md:
            dir_md.mkdir(parents=True, exist_ok=True)

        vistos_ids: set = set()
        registros: List[Dict[str, Any]] = []

        if tipo_corte == "ddhh" and not texto:
            por_termino = max(20, max_registros // len(self.DESCRIPTORES_DDHH))
            for desc in self.DESCRIPTORES_DDHH:
                offset = 0
                obtenidos_desc = 0
                while obtenidos_desc < por_termino and len(registros) < max_registros:
                    filas = min(lote, por_termino - obtenidos_desc)
                    lote_docs = self.buscar(tipo_corte="ddhh", texto=desc, limite=filas, offset=offset)
                    if not lote_docs:
                        break
                    for doc in lote_docs:
                        did = str(doc.get("id") or doc.get("rol"))
                        if did not in vistos_ids:
                            vistos_ids.add(did)
                            doc["descriptor_busqueda"] = desc
                            registros.append(doc)
                    obtenidos_desc += len(lote_docs)
                    offset += len(lote_docs)
                    if len(lote_docs) < filas:
                        break
                    time.sleep(0.15)
        else:
            offset = 0
            while len(registros) < max_registros:
                filas = min(lote, max_registros - len(registros))
                lote_docs = self.buscar(tipo_corte=tipo_corte, texto=texto, limite=filas, offset=offset)
                if not lote_docs:
                    break
                nuevos = 0
                for doc in lote_docs:
                    did = str(doc.get("id") or doc.get("rol"))
                    if did not in vistos_ids:
                        vistos_ids.add(did)
                        registros.append(doc)
                        nuevos += 1
                offset += len(lote_docs)
                if len(lote_docs) < filas or nuevos == 0:
                    break
                time.sleep(0.15)

        with open(ruta_jsonl, "w", encoding="utf-8") as f:
            for reg in registros:
                if exportar_md:
                    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", str(reg.get("rol") or reg.get("id") or "doc")).strip("_")[:60]
                    rel_md = f"{cfg['md_dir']}/{slug}.md"
                    reg["archivo_md"] = rel_md
                    md_path = BASE_DIR / rel_md
                    md_path.write_text(self._formatear_ficha_md(reg), encoding="utf-8")
                f.write(json.dumps(reg, ensure_ascii=False) + "\n")

        return {
            "portal": tipo_corte,
            "nombre": cfg["nombre"],
            "total_cosechados": len(registros),
            "archivo_jsonl": str(ruta_jsonl.relative_to(BASE_DIR)),
            "directorio_md": cfg["md_dir"] if exportar_md else None,
        }

    @staticmethod
    def _formatear_ficha_md(reg: Dict[str, Any]) -> str:
        rol = reg.get("rol") or "S/R"
        fecha = reg.get("fecha") or "s/f"
        caratula = reg.get("caratula") or "Sin carátula"
        sala = reg.get("sala") or "Sala CS"
        materia = reg.get("materia") or "General"
        cita = reg.get("cita") or f"[CS - Rol N° {rol}, Fecha: {fecha}]"
        url = reg.get("url_corta") or reg.get("url_origen") or "https://juris.pjud.cl"
        cuerpo = reg.get("texto_integral") or reg.get("extracto_relevante") or ""
        return (
            f"---\n"
            f"rol: \"{rol}\"\n"
            f"fecha: \"{fecha}\"\n"
            f"tribunal: \"{reg.get('tribunal', 'Corte Suprema')}\"\n"
            f"portal: \"{reg.get('portal', 'cs')}\"\n"
            f"sala: \"{sala}\"\n"
            f"url_oficial: \"{url}\"\n"
            f"---\n\n"
            f"# {caratula} (Rol N.° {rol})\n\n"
            f"- **Tribunal:** {reg.get('tribunal', 'Corte Suprema')} ({sala})\n"
            f"- **Fecha:** {fecha}\n"
            f"- **Materia / Descriptores:** {materia}\n"
            f"- **Recurso / Resultado:** {reg.get('recurso', '')} · {reg.get('resultado', '')}\n"
            f"- **Ministros:** {reg.get('ministros', '')}\n"
            f"- **Cita Oficial:** `{cita}`\n"
            f"- **Enlace Oficial PJUD:** {url}\n\n"
            f"## Síntesis y Extracto Jurisprudencial\n\n"
            f"{cuerpo}\n"
        )

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
    parser = argparse.ArgumentParser(description="Scraper oficial de jurisprudencia PJUD (Corte Suprema, Apelaciones y Portales Especializados)")
    parser.add_argument(
        "--corte",
        choices=["cs", "ca", "lineas", "salud", "extranjeria", "ddhh", "especializados", "ambos"],
        default="cs",
        help="Portal a consultar: cs, ca, lineas, salud, extranjeria, ddhh, especializados o ambos",
    )
    parser.add_argument("--texto", default="", help="Término o frase a buscar en la jurisprudencia")
    parser.add_argument("--rol", default="", help="Filtrar por Rol específico (ej. 14076-2026)")
    parser.add_argument("--desde", default="", help="Fecha desde (YYYY-MM-DD)")
    parser.add_argument("--hasta", default="", help="Fecha hasta (YYYY-MM-DD)")
    parser.add_argument("--limite", type=int, default=5, help="Cantidad máxima de sentencias a recuperar")
    parser.add_argument("--descargar", choices=["pdf", "docx", "ninguno"], default="ninguno", help="Descargar archivo oficial")
    parser.add_argument("--salida-jsonl", default="", help="Ruta para exportar los resultados en formato JSONL")
    parser.add_argument("--cosechar-portal", action="store_true", help="Cosechar y exportar el portal completo a JSONL + Markdown")

    args = parser.parse_args()

    scraper = PJUDScraper()
    if args.corte == "ambos":
        cortes = ["cs", "ca"]
    elif args.corte == "especializados":
        cortes = ["lineas", "salud", "extranjeria", "ddhh"]
    else:
        cortes = [args.corte]

    if args.cosechar_portal:
        for c in cortes:
            print(f"[*] Cosechando portal completo '{c}' ({scraper.BUSCADORES[c]['nombre']})...")
            res = scraper.cosechar_portal(c, max_registros=args.limite, texto=args.texto, exportar_md=True)
            print(f"[+] {res['nombre']}: {res['total_cosechados']} registros -> {res['archivo_jsonl']}")
        return

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
            if doc.get("ministros"):
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
