"""
Open Legal Chile — Conector Oficial Biblioteca del Congreso Nacional (BCN Ley Chile)
Módulo para consultar, descargar, cachear e indexar leyes, decretos y códigos de la República de Chile.
"""

import os
import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from config import BCN_API_KEY

BCN_API_BASE = "https://www.bcn.cl/leychile/api/v1"
BCN_XML_BASE = "https://www.leychile.cl/Consulta/obtxml"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "bcn_cache")

CODIGOS_REPUBLICA = {
    "civil": {"idNorma": 172986, "nombre": "Código Civil de Chile"},
    "trabajo": {"idNorma": 207436, "nombre": "Código del Trabajo (DFL 1 de 2003)"},
    "cpc": {"idNorma": 22740, "nombre": "Código de Procedimiento Civil"},
    "cpp": {"idNorma": 176595, "nombre": "Código Procesal Penal"},
    "penal": {"idNorma": 1984, "nombre": "Código Penal de Chile"},
    "comercio": {"idNorma": 1974, "nombre": "Código de Comercio"},
    "tributario": {"idNorma": 6368, "nombre": "Código Tributario (DL 830)"},
    "aguas": {"idNorma": 5605, "nombre": "Código de Aguas (DFL 1122)"},
    "mineria": {"idNorma": 29668, "nombre": "Código de Minería (Ley 18.248)"}
}

LEYES_FRECUENTES = {
    "karin": 21643,
    "40horas": 21561,
    "datos": 19628,
    "consumidor": 19496,
    "sa": 18046,
    "arriendo": 18101,
    "devolveme": 21461,
    "tramitacion_digital": 20886,
    "delitos_economicos": 21595,
    "empresas_en_un_dia": 20659
}


class BCNClient:
    def __init__(self, api_key: str = BCN_API_KEY, cache_dir: str = CACHE_DIR):
        self.api_key = api_key
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key_type: str, key_val: Any) -> str:
        return os.path.join(self.cache_dir, f"{key_type}_{key_val}.json")

    def _fetch_xml(self, params: Dict[str, Any]) -> str:
        """Obtiene XML desde el servicio web de la BCN."""
        query_str = urllib.parse.urlencode(params)
        url = f"{BCN_XML_BASE}?{query_str}"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (https://github.com/open-legal-chile)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='ignore')

    def _parse_norma_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parsea el XML de una norma chilena a estructura de datos limpia."""
        root = ET.fromstring(xml_content)
        # Limpiar namespaces
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        norma_id = root.attrib.get('normaId', '')
        fecha_version = root.attrib.get('fechaVersion', '')
        derogado = root.attrib.get('derogado', 'no')

        # Buscar título en Metadatos o Identificador o Encabezado
        titulo = ""
        t_elem = root.find('.//Metadatos/TituloNorma')
        if t_elem is None:
            t_elem = root.find('.//TituloNorma')
        if t_elem is None:
            t_elem = root.find('.//Identificador/TituloNorma')
        if t_elem is not None and t_elem.text:
            titulo = t_elem.text.strip()

        # Buscar organismo
        organismo = ""
        o_elem = root.find('.//Identificador/Organismos/Organismo')
        if o_elem is None:
            o_elem = root.find('.//Organismo')
        if o_elem is not None and o_elem.text:
            organismo = o_elem.text.strip()

        # Buscar número oficial
        numero = ""
        n_elem = root.find('.//Identificador/TiposNumeros/TipoNumero/Numero')
        if n_elem is None:
            n_elem = root.find('.//Numero')
        if n_elem is not None and n_elem.text:
            numero = n_elem.text.strip()

        # Extraer articulado y estructuras funcionales
        estructuras = []
        articulos_map = {}

        for node in root.findall('.//EstructuraFuncional'):
            tipo = node.attrib.get('tipoParte', '')
            id_parte = node.attrib.get('idParte', '')
            texto_elem = node.find('Texto')
            texto = texto_elem.text.strip() if (texto_elem is not None and texto_elem.text) else ""

            item = {
                "tipoParte": tipo,
                "idParte": id_parte,
                "texto": texto
            }
            estructuras.append(item)

            # Detectar número de artículo
            match = re.search(r'(?:Art[íi]culo|Art\.)\s*([0-9]+(?:\s*(?:bis|ter|quater|quinquies|sexies|septies|octies))?|primero|segundo|tercero|cuarto|quinto)', texto, re.IGNORECASE)
            if match:
                art_num = match.group(1).lower().strip()
                articulos_map[art_num] = texto

        return {
            "normaId": norma_id,
            "numero": numero,
            "titulo": titulo,
            "organismo": organismo,
            "fechaVersion": fecha_version,
            "derogado": derogado,
            "totalEstructuras": len(estructuras),
            "articulos": articulos_map,
            "estructuras": estructuras
        }


    def get_ley(self, id_ley: int, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene una ley chilena por su número oficial (ej. 21643)."""
        cache_file = self._get_cache_path("ley", id_ley)
        if use_cache and os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        xml_data = self._fetch_xml({"opt": 7, "idLey": id_ley})
        norma_data = self._parse_norma_xml(xml_data)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(norma_data, f, ensure_ascii=False, indent=2)

        return norma_data

    def get_norma(self, id_norma: int, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene una norma chilena por su ID interno de BCN (ej. Códigos de la República)."""
        cache_file = self._get_cache_path("norma", id_norma)
        if use_cache and os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        xml_data = self._fetch_xml({"opt": 7, "idNorma": id_norma})
        norma_data = self._parse_norma_xml(xml_data)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(norma_data, f, ensure_ascii=False, indent=2)

        return norma_data

    def get_codigo(self, codigo_nombre: str, articulo: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un Código de la República (civil, trabajo, cpc, cpp, penal, comercio, tributario)."""
        c_key = codigo_nombre.lower().strip()
        if c_key not in CODIGOS_REPUBLICA:
            raise ValueError(f"Código '{codigo_nombre}' no reconocido. Opciones: {list(CODIGOS_REPUBLICA.keys())}")

        id_norma = CODIGOS_REPUBLICA[c_key]["idNorma"]
        data = self.get_norma(id_norma)

        if articulo:
            art_str = str(articulo).lower().strip()
            # Buscar en el mapa de artículos
            if art_str in data["articulos"]:
                return {
                    "codigo": CODIGOS_REPUBLICA[c_key]["nombre"],
                    "articulo": articulo,
                    "texto": data["articulos"][art_str],
                    "fechaVersion": data["fechaVersion"]
                }
            # Búsqueda difusa en el articulado
            for k, text in data["articulos"].items():
                if k.startswith(art_str) or f"artículo {art_str}" in text.lower() or f"artículo {art_str}.-" in text.lower():
                    return {
                        "codigo": CODIGOS_REPUBLICA[c_key]["nombre"],
                        "articulo": k,
                        "texto": text,
                        "fechaVersion": data["fechaVersion"]
                    }
            return {
                "codigo": CODIGOS_REPUBLICA[c_key]["nombre"],
                "articulo": articulo,
                "error": f"Artículo {articulo} no encontrado en el texto vigente."
            }

        return data

    def get_articulo_ley(self, id_ley: int, articulo: str) -> Dict[str, Any]:
        """Obtiene un artículo específico de una ley (ej. Ley 21643, Art. 1)."""
        data = self.get_ley(id_ley)
        art_str = str(articulo).lower().strip()

        if art_str in data["articulos"]:
            return {
                "ley": id_ley,
                "titulo": data["titulo"],
                "articulo": articulo,
                "texto": data["articulos"][art_str],
                "fechaVersion": data["fechaVersion"]
            }

        for k, text in data["articulos"].items():
            if k.startswith(art_str) or f"artículo {art_str}" in text.lower():
                return {
                    "ley": id_ley,
                    "titulo": data["titulo"],
                    "articulo": k,
                    "texto": text,
                    "fechaVersion": data["fechaVersion"]
                }

        return {
            "ley": id_ley,
            "articulo": articulo,
            "error": f"Artículo {articulo} no encontrado en la Ley {id_ley}."
        }


# ==============================================================================
# CLI DE CONSULTA RÁPIDA
# ==============================================================================
if __name__ == "__main__":
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Conector CLI Open Legal Chile - BCN Ley Chile")
    parser.add_argument("--ley", type=int, help="Número de Ley (ej. 21643)")
    parser.add_argument("--codigo", type=str, help="Nombre del Código (civil, trabajo, cpc, cpp, penal, comercio)")
    parser.add_argument("--art", type=str, help="Número de Artículo (ej. 1545, 161, 254)")
    args = parser.parse_args()

    client = BCNClient()

    if args.codigo:
        print(f"\n🏛️ Consultando {args.codigo.upper()}...")
        res = client.get_codigo(args.codigo, args.art)
        if args.art:
            print(f"\n[Artículo {args.art} — {res.get('codigo')}]")
            print(res.get('texto', res.get('error')))
            print(f"\n📅 Fecha Versión Vigente: {res.get('fechaVersion')}")
        else:
            print(f"Norma: {res.get('titulo')} | Total Artículos: {len(res.get('articulos', {}))}")
    elif args.ley:
        print(f"\n📜 Consultando Ley N° {args.ley}...")
        if args.art:
            res = client.get_articulo_ley(args.ley, args.art)
            print(f"\n[Ley {args.ley} — Art. {args.art}]")
            print(res.get('texto', res.get('error')))
        else:
            res = client.get_ley(args.ley)
            print(f"Ley N° {args.ley}: {res.get('titulo')}")
            print(f"Total Estructuras: {res.get('totalEstructuras')} | Versión: {res.get('fechaVersion')}")
    else:
        print("Uso: python bcn_connector.py --codigo [civil|trabajo|cpc] --art [numero]")
        print("     python bcn_connector.py --ley [numero] [--art [numero]]")
