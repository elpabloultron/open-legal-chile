"""
Open Legal Chile — Conector Oficial Contraloría General de la República (CGR)
Módulo para consultar, indexar y buscar Jurisprudencia Administrativa, Dictámenes,
Instructivos y Auditorías vinculantes de la Contraloría General de la República de Chile.
"""

import os
import sys
import re
import html
import json
import hashlib
import datetime
import pathlib
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import cache_fresco, leer_json_si_se_puede, safe_urlopen

BASE_URL = "https://www.contraloria.cl/apibusca"
PORTAL = "https://www.contraloria.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cgr_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60  # la jurisprudencia de la CGR cambia lento: un mes
# v2: identificador citable, texto íntegro y página 0. Las copias de la versión anterior no se leen.
_VERSION_CACHE = "v2"
_POR_PAGINA = 20
_TIPO_ACTO = {"dictamenes": "Dictamen", "auditoria": "Auditoría", "instructivos": "Instructivo"}
# Código de dictamen ya normalizado (_codigo_normalizado): «E311060N23», «049495N12», «D289», «OF131056N26»,
# «49495/2009» o «E311060-23». Grupo 1: el número con su serie (sin ceros a la izquierda); grupo 2: el año.
_RE_ID_DICTAMEN = re.compile(r"^0*([A-Z]{0,3}\d+)(?:[N/\-](\d{4}|\d{2}))?$")
# Páginas que se revisan para resolver un código: con año (filtrado en la API) y sin año.
_PAGINAS_CON_ANIO = 3
_PAGINAS_SIN_ANIO = 5


def _texto(valor: Any) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _codigo_normalizado(doc_id: str) -> str:
    """El código como lo escriben las personas → forma compacta: «Dictamen N° 49.495, de 2012» →
    «49495/2012»; «Nº E311060 de 2023» → «E311060/2023»; «e311060n23» → «E311060N23»."""
    t = str(doc_id or "").upper()
    t = re.sub(r"\bDICT[AÁ]MEN(ES)?\b", " ", t)
    t = re.sub(r"\bN\s*[°º]|\bNRO\b\.?|\bNO\.", " ", t)
    t = re.sub(r"(?<=\d)\.(?=\d{3}(?!\d))", "", t)                  # punto de miles: 49.495 → 49495
    t = re.sub(r"\s*,?\s*\bDE(?:L\s+A[ÑN]O)?\s+(\d{4})\b", r"/\1", t)  # «, de 2012» → «/2012»
    return re.sub(r"\s+", "", t)


def _anio_completo(anio: str) -> str:
    """«09» → «2009», «92» → «1992» (la CGR emite dictámenes desde mediados del siglo XX)."""
    if len(anio) == 4:
        return anio
    return f"20{anio}" if int(anio) <= datetime.date.today().year % 100 else f"19{anio}"


def _en_lista(doc: Dict[str, Any]) -> Dict[str, Any]:
    """En una lista de resultados va lo que resume el acto, no el texto íntegro.

    Veinte dictámenes completos (un instructivo pasa de 100.000 caracteres) desbordan la salida de una
    herramienta MCP, y lo que se cita de una lista es la materia. El texto íntegro se pide por el
    código (get_dictamen / doc_id).
    """
    resumen = doc.get("conclusiones") or doc.get("objetivo") or doc.get("materia") or ""
    return {**doc, "texto": resumen, "texto_integral": resumen}


def _limpiar_html(crudo: str) -> str:
    """Texto plano del HTML que publica la CGR (respaldo cuando falta documento_completo)."""
    if not crudo:
        return ""
    limpio = re.sub(r"<br\s*/?>", "\n", crudo)
    limpio = re.sub(r"<[^>]+>", " ", limpio)
    limpio = html.unescape(limpio)
    limpio = re.sub(r"[ \t]+", " ", limpio)
    limpio = re.sub(r" *\n *", "\n", limpio)
    return re.sub(r"\n{3,}", "\n\n", limpio).strip()


def _numero_citable(doc_id: str) -> str:
    """«E311060N23» → «E311060»; «049495N12» → «49495»: el N° con el que se cita, sin el año."""
    return re.sub(r"N\d{2}$", "", doc_id).lstrip("0") or doc_id


def _normalizar_hit(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Un registro del índice de la CGR en el formato de la suite.

    El identificador citable es `doc_id` («E311060N23», con su año), no `numeric_doc_id` («E311060»,
    o «I» en todos los instructivos). En auditorías es `número` («622/2026»). El texto íntegro viaja
    en `documento_completo` dentro de la propia respuesta de búsqueda.
    """
    src = item.get("_source") or {}
    tipo = src.get("_tipo") or source
    if tipo == "auditoria":
        doc_id = (_texto(src.get("número")) or _texto(src.get("numero"))
                  or _texto(src.get("numeric_doc_id")) or str(item.get("_id") or ""))
        numero = doc_id
        destinatario = _texto(src.get("servicio_")) or _limpiar_html(src.get("destinatarios") or "")
    else:
        doc_id = _texto(src.get("doc_id")) or _texto(src.get("numeric_doc_id")) or str(item.get("_id") or "")
        numero = _numero_citable(doc_id)
        destinatario = _limpiar_html(src.get("destinatarios") or "") or _texto(src.get("organismo"))
    fecha = _texto(src.get("fecha_documento") or src.get("fecha"))[:10]
    anio = _texto(str(src.get("year_doc_id") or "")) or fecha[:4]
    tipo_acto = _TIPO_ACTO.get(tipo, "Dictamen")
    objetivo = _texto(src.get("objetivo"))
    conclusiones = _texto(src.get("conclusiones"))
    materia = _texto(src.get("materia")) or _texto(src.get("resena")) or _texto(src.get("descriptores"))
    nombre = _texto(src.get("nombre") or src.get("title") or src.get("titulo"))
    if not nombre and numero:
        nombre = f"{tipo_acto} {numero}"
    texto = (_texto(src.get("documento_completo"))
             or _limpiar_html(src.get("documento_completo_raw") or src.get("documento") or src.get("documento_raw") or "")
             or _texto(src.get("texto_completo") or src.get("texto") or src.get("resumen"))
             or conclusiones or objetivo or materia)

    pdf_url = _texto(src.get("pdf"))
    if pdf_url and not pdf_url.startswith("http"):
        pdf_url = f"{PORTAL}{pdf_url}"
    url_html = ""
    if tipo != "auditoria" and re.search(r"N\d{2}$", doc_id):
        # El lector oficial y el PDF firmado se piden por el código con año; en auditorías esa ruta
        # da 404 y el enlace es el `pdf` que trae el propio registro.
        url_html = f"{PORTAL}/pdfbuscador/{tipo}/{doc_id}/html"
        pdf_url = pdf_url or f"{PORTAL}/pdfbuscador/{tipo}/{doc_id}/pdf"

    return {
        "docId": doc_id,
        "numero": numero,
        "anio": anio,
        "organismo": "CGR",
        "tipo_acto": tipo_acto,
        "nombre": nombre,
        "fecha": fecha,
        "materia": materia or nombre,
        "descriptores": _texto(src.get("descriptores")),
        "fuentes_legales": _texto(src.get("fuentes_legales")),
        "objetivo": objetivo,
        "conclusiones": conclusiones,
        "organismo_destinatario": destinatario,
        "texto": texto,
        "texto_integral": texto,
        "pdfUrl": pdf_url,
        "urlHtml": url_html,
        "url": url_html or pdf_url,
        "link_oficial": pdf_url or url_html,
    }


class CGRClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def search_jurisprudencia(self, query: str, source: str = "dictamenes", page: int = 0, exact: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """Busca en el Sistema de Jurisprudencia de la Contraloría General de la República.

        La API cuenta las páginas desde 0 y entrega 20 documentos por página: con `page=1` una
        consulta acotada respondía `total` mayor que cero y `resultados` vacío (issue #1). Cada
        resultado trae su resumen; el texto íntegro de un dictamen se pide con get_dictamen.
        """
        datos = self._buscar(query, source=source, page=page, exact=exact, use_cache=use_cache)
        return {**datos, "resultados": [_en_lista(d) for d in datos.get("resultados", [])]}

    def _buscar(self, query: str, source: str = "dictamenes", page: int = 0, exact: bool = False,
                use_cache: bool = True, anio: str = "") -> Dict[str, Any]:
        """Una página de la búsqueda, con el texto íntegro de cada resultado (va a la caché así).

        `anio` filtra en la API por año del dictamen: sin él, un dictamen muy citado queda detrás
        de los posteriores que lo citan, en la última página.
        """
        # La consulta va en el nombre del archivo saneada (sin «/» ni nada que cambie la ruta) y con
        # un hash de la consulta exacta: «85700/2016» y «85700 2016» son búsquedas distintas.
        clean_q = re.sub(r"[^\w-]+", "_", query.strip().lower()).strip("_")[:60] or "vacia"
        huella = hashlib.sha256(json.dumps([source, exact, query, anio]).encode("utf-8")).hexdigest()[:12]
        cache_key = f"{_VERSION_CACHE}_{source}_{'exacta' if exact else 'libre'}_{clean_q}_{huella}_p{page}"
        cache_file = self._get_cache_path(cache_key)

        data = leer_json_si_se_puede(cache_file) if use_cache else None
        if data is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return data

        url = f"{BASE_URL}/search/{source}"
        date_name = "fecha_promulgación" if source == "legislacion" else "fecha_documento"

        payload = {
            "search": query,
            "exact_search": exact,
            "options": [{"type": "force_obj", "field": "year_doc_id", "value": anio}] if anio else {},
            "order": "desc",
            "date_name": date_name,
            "source": source,
            "page": page
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OpenLegalChile/1.0 (Derecho Administrativo Chile)"
            }
        )

        try:
            with safe_urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise
        res_json = json.loads(raw)

        hits = res_json.get("hits", {})
        total_val = hits.get("total", {})
        total_count = total_val.get("value", 0) if isinstance(total_val, dict) else total_val
        raw_items = hits.get("hits", [])

        output_data = {
            "query": query,
            "source": source,
            "total": total_count,
            "page": page,
            "resultados": [_normalizar_hit(item, source) for item in raw_items]
        }

        # Escritura atómica: con varios procesos (xdist, varios clientes) nadie lee una copia a medias.
        temporal = f"{cache_file}.{os.getpid()}.tmp"
        try:
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            os.replace(temporal, cache_file)
        except OSError:  # una copia que no se pudo guardar (Windows con el archivo abierto) no es un error
            try:
                os.remove(temporal)
            except OSError:
                pass

        return output_data

    def descargar_pdf_oficial(self, doc_id: str, year: str = "") -> Optional[str]:
        """Descarga el PDF oficial firmado del dictamen desde el servidor de la Contraloría."""
        clean_id = str(doc_id).strip()
        y_2d = year[-2:] if year else "24"
        if re.search(r"N\d{2}$", clean_id):   # ya trae el año («E311060N23»)
            codigo_pdf = clean_id
        else:
            codigo_pdf = f"{clean_id}N{y_2d}"

        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"dictamen_cgr_{clean_id}.pdf"

        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        url = f"https://www.contraloria.cl/pdfbuscador/dictamenes/{codigo_pdf}/pdf"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OpenLegalChile/1.0 (Derecho Administrativo Chile)"})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

    def _resolver_dictamen(self, doc_id: str) -> Dict[str, Any]:
        """El dictamen cuyo identificador es exactamente el pedido, o un error con los candidatos.

        La búsqueda de la CGR es de texto libre (`exact_search` no filtra): pedir «E311060N23»
        devuelve primero «0E6541N25». Quedarse con el primer resultado entregaba otro dictamen, y
        una cita equivocada en silencio es peor que un «no encontrado» (issue #1). Un número sin año
        que calza con varios dictámenes («49495»: N09 y N12) también es un error: se pide el año.

        Los resultados vienen del más nuevo al más antiguo, así que un dictamen muy citado
        (85.700/2016) queda detrás de los que lo citan: con año se filtra por año en la API y se
        revisan hasta 3 páginas; sin año, hasta 5, y si no se alcanzó a ver todo no se da por único.
        """
        buscado = _codigo_normalizado(doc_id)
        if not buscado:
            return {"error": "Falta el código del dictamen (p. ej. «E311060N23» o «49495/2009»).", "candidatos": []}
        partes = _RE_ID_DICTAMEN.match(buscado)
        numero = partes.group(1) if partes else ""
        anio = _anio_completo(partes.group(2)) if partes and partes.group(2) else ""
        vistos: Dict[str, Dict[str, Any]] = {}

        def coincidencias() -> List[Dict[str, Any]]:
            exactos = [d for clave, d in vistos.items() if clave.upper() == buscado]
            if exactos or not partes:
                return exactos
            return [d for d in vistos.values()
                    if d.get("numero", "").upper() == numero and (not anio or d.get("anio") == anio)]

        def recorrer(consulta: str, paginas: int, filtro_anio: str = "") -> bool:
            """Lee hasta `paginas` páginas; True si alcanzó a ver todos los resultados."""
            for pagina in range(paginas):
                datos = self._buscar(consulta, source="dictamenes", page=pagina, anio=filtro_anio)
                hits = datos.get("resultados", [])
                for doc in hits:
                    vistos.setdefault(doc.get("docId", ""), doc)
                if (pagina + 1) * _POR_PAGINA >= int(datos.get("total") or 0) or len(hits) < _POR_PAGINA:
                    return True
                if anio and coincidencias():
                    return True
            return False

        recorrer(buscado, 1)   # el código tal como viene: si trae año, casi siempre está en la primera página
        completo = True
        if not (anio and len(coincidencias()) == 1) and partes:
            completo = recorrer(numero, _PAGINAS_CON_ANIO if anio else _PAGINAS_SIN_ANIO, filtro_anio=anio)
        hallados = sorted(coincidencias(), key=lambda d: d.get("docId", ""))
        if len(hallados) == 1 and (anio or completo or hallados[0].get("docId", "").upper() == buscado):
            return hallados[0]
        if hallados:
            if len(hallados) == 1:
                motivo = (f"sin año no se puede asegurar que {hallados[0]['docId']} sea el único dictamen con ese "
                          "número: la búsqueda tiene más resultados de los que se revisaron")
            else:
                mas = "" if completo else " (y puede haber otros)"
                motivo = f"corresponde a {len(hallados)} dictámenes de la CGR{mas}"
            return {"error": f"El identificador {doc_id} {motivo}: indique el año (p. ej. «E311060N23» o «49495/2009»).",
                    "candidatos": [d["docId"] for d in hallados]}
        if anio:
            # Con ese año no existe: se muestran los de ese número en otros años, si los hay.
            recorrer(numero, 1)
            mismo_numero = sorted(d["docId"] for d in vistos.values() if d.get("numero", "").upper() == numero)
            if mismo_numero:
                return {"error": f"Dictamen {doc_id} no encontrado: ese número existe con otro año.",
                        "candidatos": mismo_numero[:5]}
        donde = "en la base de la CGR" if completo else "en los resultados revisados de la búsqueda; indique el año"
        return {"error": f"Dictamen {doc_id} no encontrado con ese identificador {donde}.",
                "candidatos": [clave for clave in vistos if clave][:5]}

    def get_dictamen_integral(self, doc_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene el texto completo, metadatos y PDF oficial de un dictamen específico."""
        doc = self._resolver_dictamen(doc_id)
        if doc.get("error"):
            return doc

        if descargar_formato and descargar_formato.lower() == "pdf":
            ruta_pdf = self.descargar_pdf_oficial(doc.get("docId", ""), year=doc.get("fecha", "")[:4])
            if ruta_pdf:
                doc["archivo_descargado"] = ruta_pdf
                doc["formato_descargado"] = "pdf"

        return doc

    def get_dictamen(self, doc_id: str) -> Dict[str, Any]:
        """Obtiene el texto de un dictamen (mantiene compatibilidad hacia atrás)."""
        return self.get_dictamen_integral(doc_id)

    def get_dictamenes_lote(self, doc_ids: List[str], descargar_formato: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene una lista de dictámenes en lote."""
        docs = []
        for did in doc_ids:
            docs.append(self.get_dictamen_integral(did, descargar_formato=descargar_formato))
        return docs

    def procesar_y_graficar_dictamenes(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pipeline unificado para dictámenes de Contraloría:
        1. Resuelve documentos (busca texto íntegro).
        2. Convierte a Markdown Canónico (dictamen2md).
        3. Ingesta en LegalGraphify.
        4. Desglosa y rankea consideraciones con ResolucionesParserEngine.
        """
        from resolucion_administrativa2md import convertir_lote_dictamenes
        from resoluciones_parser import ResolucionesParserEngine
        from legal_graphify import LegalGraphifyEngine

        docs_procesar = []
        no_encontrados = []
        for item in ids_o_docs:
            if isinstance(item, str):
                doc_obj = self.get_dictamen_integral(item, descargar_formato=descargar_formato)
                if doc_obj.get("error"):   # no se convierte ni se grafica un error como si fuera un dictamen
                    no_encontrados.append({"id": item, **doc_obj})
                    continue
                docs_procesar.append(doc_obj)
            elif isinstance(item, dict):
                docs_procesar.append(item)

        # Conversión a Markdown Canónico
        rutas_md = []
        if convertir_a_md:
            try:
                rutas_md = [str(p) for p in convertir_lote_dictamenes(docs_procesar)]
                for i, r_path in enumerate(rutas_md):
                    if i < len(docs_procesar):
                        docs_procesar[i]["ruta_md"] = r_path
            except Exception:
                pass

        # Ingesta en LegalGraphify
        info_grafo = {}
        try:
            graph_engine = LegalGraphifyEngine()
            insumos = rutas_md if rutas_md else docs_procesar
            info_grafo = graph_engine.ingerir_lote_dictamenes(insumos, guardar_disco=False)
        except Exception as e:
            info_grafo = {"error": f"Error integrando con LegalGraphify: {str(e)}"}

        # Análisis y citación canónica
        parser_engine = ResolucionesParserEngine()
        analisis = parser_engine.analizar_lote_resoluciones(docs_procesar, tema_relevante=tema_relevante)

        return {
            "organismo": "CGR",
            "total_dictamenes": len(docs_procesar),
            "no_encontrados": no_encontrados,
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
            "detalle_dictamenes": analisis.get("documentos", [])
        }

    def search_instructivos(self, query: str, page: int = 0) -> Dict[str, Any]:
        """Busca en los Instructivos y Circulares generales de la CGR."""
        return self.search_jurisprudencia(query, source="instructivos", page=page)

    def search_auditorias(self, query: str, page: int = 0) -> Dict[str, Any]:
        """Busca en los Informes Finales de Auditoría de la CGR."""
        return self.search_jurisprudencia(query, source="auditoria", page=page)


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE JURISPRUDENCIA CGR
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Contraloría General de la República (CGR)")
    parser.add_argument("--buscar", type=str, help="Término de búsqueda o materia (ej. 'confianza legitima' o 'compras publicas')")
    parser.add_argument("--id", type=str, help="Código de Dictamen (ej. E311060N23, D286N26 o 49495/2009)")
    parser.add_argument("--instructivos", type=str, help="Buscar en Instructivos de la CGR")
    parser.add_argument("--auditorias", type=str, help="Buscar en Informes de Auditoría de la CGR")
    args = parser.parse_args()

    client = CGRClient()

    if args.id:
        print(f"\n🏛️ Consultando Dictamen CGR N° {args.id}...")
        data = client.get_dictamen(args.id)
        if data and isinstance(data, dict) and not data.get("error"):
            print(f"\n[Dictamen CGR N° {data.get('numero')} ({data.get('anio') or 's/f'})]")
            print(f"📌 Materia / Criterio:\n{data.get('materia')}")
            if data.get("texto"):
                print(f"\n📜 Texto:\n{str(data.get('texto'))[:500]}...")
            if data.get("url"):
                print(f"\n🔗 {data.get('url')}")
        else:
            print(f"❌ {(data or {}).get('error', 'Dictamen no encontrado o error en respuesta.')}")
            if (data or {}).get("candidatos"):
                print(f"   Candidatos: {', '.join(data['candidatos'])}")
    elif args.instructivos:
        print(f"\n📜 Buscando Instructivos CGR: '{args.instructivos}'...")
        res = client.search_instructivos(args.instructivos)
        print(f"Total encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Instructivo N° {item.get('numero') or item.get('docId')} ({item.get('anio') or item.get('fecha')})")
            print(f"  📌 {item.get('materia')[:200]}...")
    elif args.auditorias:
        print(f"\n🔍 Buscando Informes de Auditoría CGR: '{args.auditorias}'...")
        res = client.search_auditorias(args.auditorias)
        print(f"Total encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Informe N° {item.get('docId')} ({item.get('fecha')})")
            print(f"  📌 {item.get('materia')[:200]}...")
    elif args.buscar or len(sys.argv) == 1:
        q = args.buscar or "compras publicas"
        print(f"\n🏛️ Buscando Dictámenes en la Contraloría: '{q}'...")
        res = client.search_jurisprudencia(q)
        print(f"Total Dictámenes encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Dictamen CGR N° {item.get('numero') or item.get('docId')} ({item.get('anio') or item.get('fecha')})")
            print(f"  📌 Materia: {item.get('materia')}")
