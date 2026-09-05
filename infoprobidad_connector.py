"""
Open Legal Chile — Conector Oficial de InfoProbidad (CGR / CPLT)
Permite extraer, estructurar y auditar las Declaraciones de Intereses y Patrimonio (DIP)
de autoridades públicas, ministros, parlamentarios, alcaldes y directivos del Estado.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional


class InfoProbidadClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        })

    def get_declaracion(self, query_or_url: str) -> Dict[str, Any]:
        """
        Descarga y parsea exhaustivamente una declaración de InfoProbidad.
        Acepta una URL completa o un ID numérico / hash.
        """
        if not query_or_url or not isinstance(query_or_url, str) or not query_or_url.strip():
            return {"error": "Debe especificar una URL o identificador válido de la declaración."}

        html, ident = self._download_html(query_or_url.strip())
        if not html:
            return {"error": f"No se pudo descargar la declaración para: {query_or_url}"}

        return self._parse_html(html, ident)

    def parse_html_string(self, html: str, ident: str = "offline") -> Dict[str, Any]:
        """Parsea directamente un contenido HTML de declaración (útil para caché, pruebas o análisis local)."""
        if not html or not isinstance(html, str):
            return {"error": "Contenido HTML vacío o inválido."}
        return self._parse_html(html, ident)

    def _download_html(self, entrada: str) -> tuple[str, str]:
        entrada = entrada.strip()
        if entrada.startswith("http://") or entrada.startswith("https://"):
            try:
                resp = self.session.get(entrada, timeout=25)
                if resp.status_code == 200 and len(resp.text) > 3000:
                    m = re.search(r'(?:ID=|declaracion=|IDCargo=)([a-zA-Z0-9]+)', entrada)
                    return resp.text, m.group(1) if m else "web"
            except Exception:
                pass

        match_hash = re.search(r'\b([a-fA-F0-9]{32})\b', entrada)
        urls = []
        if match_hash:
            h = match_hash.group(1)
            urls.extend([
                f"https://www.infoprobidad.cl/Declaracion/BuscarDeclaracion?declaracion={h}",
                f"https://www.infoprobidad.cl/Declaracion/BuscarDeclaracion?IDCargo={h}",
            ])
        else:
            match_num = re.search(r'\b(\d+)\b', entrada)
            if match_num:
                n = match_num.group(1)
                urls.extend([
                    f"https://www.infoprobidad.cl/Declaracion/Declaracion?ID={n}",
                    f"https://www.infoprobidad.cl/Declaracion/BuscarDeclaracion?ID={n}",
                ])

        for u in urls:
            try:
                resp = self.session.get(u, timeout=25)
                if resp.status_code == 200 and len(resp.text) > 3000 and "Declaración no disponible" not in resp.text:
                    return resp.text, entrada
            except Exception:
                pass

        # Intento fallback si es alfanumérico simple
        try:
            resp = self.session.get(f"https://www.infoprobidad.cl/Declaracion/Declaracion?ID={entrada}", timeout=25)
            if resp.status_code == 200 and len(resp.text) > 3000 and "Declaración no disponible" not in resp.text:
                return resp.text, entrada
        except Exception:
            pass

        return "", entrada

    def _parse_html(self, html: str, ident: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        h1 = soup.find('h1')
        nombre = h1.get_text(strip=True) if h1 else "Declarante Desconocido"

        # Extraer metadatos generales (cargo, institución, fecha, etc.)
        metadatos = {}
        for dl in soup.find_all(['dl', 'div']):
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            if dts and dds and len(dts) == len(dds):
                for dt_el, dd_el in zip(dts, dds, strict=False):
                    k = dt_el.get_text(strip=True).rstrip(':')
                    v = dd_el.get_text(strip=True)
                    if k and v and len(k) < 60:
                        metadatos[k] = v

        # Extraer campos clave por selectores o texto
        for strong in soup.find_all(['strong', 'label']):
            st_text = strong.get_text(strip=True).rstrip(':')
            next_sib = strong.next_sibling
            if next_sib and isinstance(next_sib, str) and next_sib.strip():
                val = next_sib.strip().lstrip(':').strip()
                if st_text and val and st_text not in metadatos and len(st_text) < 50:
                    metadatos[st_text] = val

        secciones = {}
        # Parsear todas las tablas y títulos
        for table in soup.find_all('table'):
            prev = table.find_previous(['h2', 'h3', 'h4', 'h5', 'caption', 'strong'])
            sec_title = prev.get_text(strip=True) if prev else "Tabla"

            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows = []
            for tr in table.find_all('tr'):
                tds = [td.get_text(strip=True) for td in tr.find_all('td')]
                if tds:
                    if headers and len(headers) == len(tds):
                        rows.append(dict(zip(headers, tds, strict=False)))
                    else:
                        rows.append(tds)
            if rows:
                if sec_title not in secciones:
                    secciones[sec_title] = []
                secciones[sec_title].extend(rows)

        return {
            "identificador": ident,
            "declarante": nombre,
            "metadatos": metadatos,
            "total_secciones": len(secciones),
            "secciones": secciones
        }


if __name__ == "__main__":
    import sys
    client = InfoProbidadClient()
    if len(sys.argv) > 1:
        res = client.get_declaracion(sys.argv[1])
        print(f"Declarante: {res.get('declarante')}")
        print(f"Secciones: {list(res.get('secciones', {}).keys())}")
    else:
        print("Uso: python infoprobidad_connector.py <URL_o_ID>")
