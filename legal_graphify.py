"""
Open Legal Chile — Motor LegalGraphify (Knowledge Graph Jurídico de Reducción de Tokens)
Construye un grafo de conocimiento multidimensional a partir de los 58 textos doctrinales,
manuales y guías de la Academia Judicial chilena.
Permite consultas hiper-densas de subgrafos con un ahorro mediano de 99,9 % de tokens para LLMs
(medición 2026-09-25 sobre 9.863 instituciones: ficha mediana 91 tokens vs. obra completa 96.536;
 el detalle y el script de medición
están en docs/medicion_tokens.md). Antes este docstring prometía 85%-95%: era falso, lo inflaba
un piso de 1200 tokens que se aplicaba al tamaño de cada obra.
Compatible con el esquema Node-Link de NetworkX y Graphify Labs.
"""

import os
import re
import sys
import json
import gzip
import hashlib
import functools
import itertools
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, Callable, Iterator, List, Optional, Set, Tuple, TypeVar, Union, cast

import networkx as nx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_GRAPH_PATH = os.path.join(DATA_DIR, "legal_knowledge_graph.json")
# El artefacto versionado tal como lo fija el repositorio: aunque una prueba reapunte
# DEFAULT_GRAPH_PATH, volcar la capa del mapa aquí sigue prohibido (ver guardar_grafo_json).
_GRAFO_VERSIONADO = DEFAULT_GRAPH_PATH

# ── Capa del mapa del corpus de Hugging Face (mapa_corpus/) ──────────────────────────────────
# Marca de los nodos y aristas que vienen del mapa (atributo `capa`). Lo curado no la lleva.
CAPA_MAPA = "mapa"
# Vecinos de la capa del mapa que entran al subgrafo por nodo y por salto: una norma como el
# Código Civil tiene miles (sus artículos y los documentos que la citan). Los vecinos curados
# entran siempre, así que la ficha de una institución curada no cambia con el mapa cargado.
TOPE_VECINOS_POR_SALTO = 30
# Elementos por lista en la ficha de un nodo del mapa (el total de cada lista va al lado).
TOPE_LISTA_FICHA = 8
# Fallos de la Corte Suprema que se materializan por consulta (el total se informa igual).
TOPE_FALLOS_CS = 10
# Nodos de un diagrama Mermaid: con más que esto el diagrama no se lee.
TOPE_NODOS_MERMAID = 60

# Tipos de nodo que trae el mapa: con qué clave los nombra la ficha, cómo se titulan en la
# explicación y si sus fallos de la Corte Suprema se traen del índice. Los 70 mil fallos de la CS
# no son nodos del grafo: se materializan por consulta (ver _vista_consulta).
_TIPOS_FICHA: Dict[str, Dict[str, Any]] = {
    "norma": {"clave": "norma", "titulo": "Norma", "fallos_cs": True},
    "ministro": {"clave": "ministro", "titulo": "Ministro", "fallos_cs": True},
    "sala": {"clave": "sala", "titulo": "Sala de la Corte Suprema", "fallos_cs": True},
    "recurso": {"clave": "recurso", "titulo": "Recurso", "fallos_cs": True},
    "tribunal": {"clave": "tribunal", "titulo": "Tribunal", "fallos_cs": False},
    "organo": {"clave": "organo", "titulo": "Órgano", "fallos_cs": False},
    "autor": {"clave": "autor", "titulo": "Autor", "fallos_cs": False},
    "revista": {"clave": "revista", "titulo": "Revista", "fallos_cs": False},
    "documento": {"clave": "documento", "titulo": "Documento", "fallos_cs": False},
    "guia": {"clave": "guia", "titulo": "Guía de la Academia Judicial", "fallos_cs": False},
    "estudio": {"clave": "estudio", "titulo": "Estudio ambiental", "fallos_cs": False},
    "publicacion": {"clave": "publicacion", "titulo": "Publicación ambiental", "fallos_cs": False},
    "sentencia_tc": {"clave": "sentencia_tc", "titulo": "Sentencia del Tribunal Constitucional", "fallos_cs": False},
    "sentencia_ta": {"clave": "sentencia_ta", "titulo": "Sentencia de un Tribunal Ambiental", "fallos_cs": False},
    "sentencia_cs": {"clave": "sentencia_cs", "titulo": "Fallo de la Corte Suprema", "fallos_cs": False},
}
# Colección de una entrada del mapa → tipo de nodo, para materializar una entrada que no es nodo.
_TIPO_DE_COLECCION = {"cs": "sentencia_cs", "tc": "sentencia_tc", "ta": "sentencia_ta", "doc": "documento",
                      "guia": "guia", "bib": "estudio", "pub": "publicacion"}
# Campo de una entrada → relación con que se materializa la arista hacia la entidad citada.
_RELACION_DE_CAMPO = {
    "ministros": "integrado_por", "sala": "resuelto_por", "tribunal": "resuelto_por",
    "recurso": "resuelve_recurso", "origen": "proviene_de", "redactor": "redactado_por",
    "normas": "cita_norma", "autores": "escrito_por", "revista": "publicado_en",
    "cita_cs": "cita_rol", "cita_tc": "cita_rol", "cita_ta": "cita_rol",
    "gestion_cs": "gestion_pendiente", "acumuladas": "acumula",
}
# Lista de la ficha según la relación y su sentido ("sale": del nodo al vecino; "entra": al revés).
# El orden de esta tabla es el orden de las listas en la ficha; lo que no figura va a vinculos_subgrafo.
_CLAVES_RELACION: Dict[Tuple[str, str], str] = {
    ("parte_de", "sale"): "parte_de",
    ("parte_de", "entra"): "articulos_y_numerales",
    ("resuelto_por", "sale"): "resuelto_por",
    ("resuelve_recurso", "sale"): "recurso",
    ("proviene_de", "sale"): "tribunal_de_origen",
    ("integrado_por", "sale"): "integrado_por",
    ("redactado_por", "sale"): "redactado_por",
    ("escrito_por", "sale"): "autores",
    ("publicado_en", "sale"): "revista",
    ("cita_norma", "sale"): "normas_citadas",
    ("cita_rol", "sale"): "roles_citados",
    ("gestion_pendiente", "sale"): "gestion_pendiente",
    ("acumula", "sale"): "acumula",
    ("integra_sala", "sale"): "salas",
    ("integra_sala", "entra"): "ministros",
    ("conoce_recurso", "sale"): "recursos",
    ("conoce_recurso", "entra"): "salas_que_lo_conocen",
    ("eleva_a", "sale"): "eleva_a",
    ("eleva_a", "entra"): "tribunales_de_origen",
    ("equivale_a", "sale"): "via_procesal",
    ("equivale_a", "entra"): "recursos_equivalentes",
    ("cita_norma", "entra"): "citada_por",
    ("cita_rol", "entra"): "citado_por",
    ("resuelto_por", "entra"): "sentencias",
    ("integrado_por", "entra"): "sentencias_que_integra",
    ("redactado_por", "entra"): "sentencias_que_redacta",
    ("escrito_por", "entra"): "obras",
    ("publicado_en", "entra"): "articulos",
    ("gestion_pendiente", "entra"): "requerimientos_tc",
    ("acumula", "entra"): "acumulada_en",
    ("mismo_documento", "sale"): "documento_oficial",
    ("mismo_documento", "entra"): "fichas_curadas",
    ("mismo_archivo", "sale"): "documento_oficial",
    ("mismo_archivo", "entra"): "fichas_curadas",
    ("refiere_a", "sale"): "fallo_del_corpus",
    ("refiere_a", "entra"): "fichas_curadas",
    ("fundamenta_en", "entra"): "instituciones",
    ("contenido_en", "entra"): "instituciones",
    ("analizado_por", "entra"): "instituciones",
    ("aplica_norma", "entra"): "aplicada_en",
}
_ORDEN_CLAVES = {clave: i for i, clave in enumerate(dict.fromkeys(_CLAVES_RELACION.values()))}
_TIPOS_NORMA = ("norma", "articulo_legal", "cuerpo_legal")
_TIPOS_SENTENCIA = ("sentencia_cs", "sentencia_tc", "sentencia_ta", "jurisprudencia", "jurisprudencia_tc",
                    "jurisprudencia_cs", "sentencia_judicial")
# Títulos que se quitan antes de buscar a una persona por su nombre («ministra María Gajardo Harboe»).
_RE_TRATAMIENTO = re.compile(r"^(?:(?:el|la)\s+)?(?:ministr[oa]|magistrad[oa]|juez[a]?|sr\.?|sra\.?|don|dona)\s+")
# Sentinela de _buscar_en_mapa: la consulta es un rol que el mapa no tiene (no seguir buscando).
_ROL_INEXISTENTE = "\x00rol-inexistente"

# Valor previo «no estaba» de un atributo curado que la capa del mapa pisó (para restaurarlo).
_AUSENTE = object()

_F = TypeVar("_F", bound=Callable[..., Any])


class GrafoConCapaMapaError(RuntimeError):
    """El grafo en memoria trae la capa del mapa: no se puede volcar al artefacto versionado."""


def _es_grafo_versionado(ruta: str) -> bool:
    """¿Es `ruta` el artefacto versionado del repositorio (o el que DEFAULT_GRAPH_PATH fija ahora)?"""
    destino = os.path.normcase(os.path.abspath(ruta))
    return destino in {os.path.normcase(os.path.abspath(p)) for p in (DEFAULT_GRAPH_PATH, _GRAFO_VERSIONADO)}


def _con_cerrojo(metodo: _F) -> _F:
    """Serializa con el RLock del motor las cargas y los cambios del grafo y de sus índices.

    Las consultas no lo toman: leen el grafo vigente, que la carga de la capa del mapa reemplaza
    de una sola vez (copia y cambio), así que nunca ven un grafo a medio armar. Cada llamada sube
    la versión del grafo, que invalida las cachés derivadas (la vista no dirigida de los caminos).
    """
    @functools.wraps(metodo)
    def envoltura(self: "LegalGraphifyEngine", *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            try:
                return metodo(self, *args, **kwargs)
            finally:
                self._version += 1
    return cast(_F, envoltura)


def _filas_gz(ruta: Path) -> Iterator[Dict[str, Any]]:
    """Filas de una partición del mapa (JSONL comprimido), leídas de a una: la de citas a normas
    tiene 113 mil filas y armarlas todas en una lista antes de usarlas costaba ~30 MB más."""
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                yield json.loads(linea)


def _copiar_digrafo(g: nx.DiGraph, sin_capa: bool = False) -> nx.DiGraph:
    """Copia de un DiGraph que conserva el orden de sucesores Y de predecesores.

    `nx.DiGraph.copy()` rehace los predecesores en el orden de los nodos de origen, y
    `_buscar_nodo_relevante` usa el primer predecesor: con una copia común, cargar el mapa podía
    cambiar a qué institución se resuelve una norma curada. Con `sin_capa` deja fuera los nodos y
    las aristas de la capa del mapa. Los atributos de lo curado se copian (diccionarios nuevos).
    """
    h = nx.DiGraph()
    h.graph.update(g.graph)
    for n, d in g._node.items():
        if sin_capa and d.get("capa") == CAPA_MAPA:
            continue
        h._node[n] = dict(d)
        h._succ[n] = {}
        h._pred[n] = {}
    for u, vecinos in g._succ.items():
        if u not in h._node:
            continue
        destino = h._succ[u]
        for v, d in vecinos.items():
            if v not in h._node or (sin_capa and d.get("capa") == CAPA_MAPA):
                continue
            destino[v] = d if d.get("capa") == CAPA_MAPA else dict(d)
    for v, vecinos in g._pred.items():
        if v not in h._node:
            continue
        origen = h._pred[v]
        for u in vecinos:
            datos = h._succ.get(u, {}).get(v)
            if datos is not None:
                origen[u] = datos
    return h


def _ids_de_consulta(query: str) -> List[str]:
    """IDs canónicos a los que apunta una consulta (`citas_legales.resolver_consulta`). Una
    consulta que es un solo rol con la palabra «rol» («Rol N° 4.321-2020») se resuelve también con
    `rol_canonico`: resolver_consulta no la reconoce cuando el «N°» va sin contexto de tribunal."""
    try:
        from citas_legales import resolver_consulta, rol_canonico
    except ImportError:  # pragma: no cover — viaja en el mismo paquete
        return []
    ids = resolver_consulta(query)
    if not ids and re.search(r"\brol\b", query, re.IGNORECASE):
        canonico = rol_canonico(query.strip())
        ids = [canonico] if canonico else []
    return ids


def _fecha_desc(fecha: str) -> Tuple[int, Tuple[int, ...]]:
    """Clave de orden para fechas ISO de la más reciente a la más antigua; sin fecha, al final."""
    return (0, tuple(-ord(c) for c in fecha)) if fecha else (1, ())


def _miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def cita_fallo_cs(fila: Dict[str, Any]) -> str:
    """Corchete oficial de un fallo de la Corte Suprema del mapa: «[CS - Rol N° 1.234-2023, Fecha:
    10-05-2023]». Sin fecha registrada, el corchete va sin ella (no se inventa)."""
    rol = str(fila.get("rol") or str(fila.get("id", "")).split(":", 1)[-1])
    m = re.fullmatch(r"(\d+)-(\d{4})", rol)
    rol_fmt = f"{_miles(int(m.group(1)))}-{m.group(2)}" if m else rol
    fecha = str(fila.get("fecha") or "")
    mf = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", fecha)
    return f"[CS - Rol N° {rol_fmt}, Fecha: {mf.group(3)}-{mf.group(2)}-{mf.group(1)}]" if mf else f"[CS - Rol N° {rol_fmt}]"


def _normalize_str(text: str) -> str:
    """Normaliza texto eliminando tildes y caracteres especiales para comparaciones seguras."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()


def _sanitize_id(text: str, prefix: str = "") -> str:
    """Genera un identificador alfanumérico limpio para grafos y diagramas."""
    norm = _normalize_str(text)
    clean = re.sub(r"[^a-z0-9]+", "_", norm).strip("_")
    if not clean:
        clean = "nodo"
    if clean[0].isdigit():
        clean = f"id_{clean}"
    if prefix:
        return f"{prefix}_{clean}"
    return clean


def extract_articulos_de_codigo(codigo_nombre: str, texto: str) -> nx.DiGraph:
    """
    Convierte el texto oficial de un código (p. ej. el que entrega el conector BCN) en un grafo
    de artículos: un nodo `cuerpo_legal` para el código y uno `articulo_legal` por artículo,
    unidos por la relación `pertenece_a`.

    Rescatado del paquete `legal-graphify` al cerrarlo (18-09-2026): era su única pieza que
    aportaba algo que este repositorio no tenía. Este repo ya saca artículos del texto
    doctrinal, pero no de un código descargado del BCN.

    Ojo con dos cosas. Primero, el reconocimiento de encabezados es por expresión regular:
    no entiende de reformas, derogaciones ni artículos con incisos complejos. Sirve para
    poblar el grafo con texto oficial, no para interpretarlo. Segundo, el patrón original
    del paquete no sobrevivía a una coma (su grupo intermedio excluía la puntuación, así que
    en un código real encontraba casi ningún artículo): aquí se corta el texto por encabezado
    de artículo, que es más tolerante y no inventa límites.
    """
    grafo = nx.DiGraph()
    codigo_id = _sanitize_id(codigo_nombre, "codigo")
    grafo.add_node(codigo_id, label=codigo_nombre, node_type="cuerpo_legal", community=2)

    inicio_articulo = re.compile(
        r"^(?=\s*(?:Art[íi]culo|Art\.)\s+\d+)", re.IGNORECASE | re.MULTILINE
    )
    encabezado_articulo = re.compile(
        r"^\s*(?:Art[íi]culo|Art\.)\s+(\d+(?:\s*(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|decies))?)\s*[\.\-:]?\s*",
        re.IGNORECASE,
    )

    for fragmento in inicio_articulo.split(texto):
        if not fragmento.strip():
            continue
        encabezado = encabezado_articulo.match(fragmento)
        if not encabezado:
            continue
        etiqueta = f"{codigo_nombre}, Art. {encabezado.group(1).strip()}"
        nodo_id = _sanitize_id(etiqueta, "norma")
        grafo.add_node(
            nodo_id,
            label=etiqueta,
            node_type="articulo_legal",
            texto=fragmento[encabezado.end():].strip()[:500],
            community=2,
        )
        grafo.add_edge(nodo_id, codigo_id, relation="pertenece_a")

    return grafo


class LegalGraphifyEngine:
    """
    Motor de Grafo de Conocimiento Jurídico Chileno (LegalGraphify).
    Extrae entidades dogmáticas, normas legales BCN, fallos rectores de la Corte Suprema,
    tratadistas y vías procesales desde los 58 manuales y tratados.
    """

    def __init__(self, doctrina_dir: str = DOCTRINA_DIR, usar_mapa: bool = False):
        self.doctrina_dir = doctrina_dir
        self.graph = nx.DiGraph()
        self.instituciones_index: Dict[str, str] = {}  # norm_name -> node_id
        self.normas_index: Dict[str, str] = {}         # norm_name -> node_id
        self._label_index: Dict[str, str] = {}         # norm_label -> node_id
        self._word_to_nodes: Dict[str, Set[str]] = defaultdict(set)     # word -> set(node_ids)
        self._def_word_to_nodes: Dict[str, Set[str]] = defaultdict(set) # def_word -> set(node_ids)
        self.is_built = False
        # Avisos de esta corrida, misma convención de la suite (avisar, no inventar).
        # Hoy lo usa la carga del grafo: si el artefacto publicado está corrupto o no
        # es Node-Link, se reconstruye desde doctrina/ — y quien consulta merece saberlo,
        # porque entonces la respuesta ya no viene del artefacto que creía estar usando.
        self.advertencias: List[str] = []
        # De dónde viene el grafo en memoria: "repo" (el artefacto curado más lo ingerido en esta
        # sesión) o "mapa" (con la capa del mapa del corpus superpuesta, ver cargar_capa_mapa).
        self.origen_grafo = "repo"
        # Con `usar_mapa`, la primera consulta que lo necesita sube la capa del mapa si el cliente
        # tiene una revisión lista (sin red y sin esperar). Lo usa el motor compartido del proceso;
        # un motor suelto (conectores, scripts, pruebas) se comporta como siempre.
        self.usar_mapa = usar_mapa
        # Cliente del mapa inyectable (pruebas); por defecto, el compartido del proceso.
        self.cliente_mapa: Any = None
        self._lock = threading.RLock()
        self._version = 0
        self._cache_no_dirigido: Optional[Tuple[Tuple[int, int, int, int], nx.Graph]] = None
        self._reiniciar_estado_mapa()

    def _reiniciar_estado_mapa(self) -> None:
        """Olvida la capa del mapa: el grafo en memoria vuelve a ser solo el del repositorio."""
        self.origen_grafo = "repo"
        self._capa: Dict[str, Any] = {}                 # firma y resumen de la capa cargada
        self._canon_a_curado: Dict[str, str] = {}       # ID canónico del mapa -> nodo curado que lo lleva
        self._alias_mapa: Dict[str, str] = {}           # ID curado legado -> ID canónico del mapa
        self._label_mapa: Dict[str, str] = {}           # etiqueta normalizada -> nodo de la capa
        self._previas_mapa: Dict[str, Dict[str, Any]] = {}  # atributos curados que la capa pisó
        self._roles_curados: Dict[str, str] = {}        # ID de rol (cs:/tc:/ta:) -> nodo curado de ese rol
        self._roles_curados_version = -1

    @_con_cerrojo
    def _actualizar_indice_invertido(self) -> None:
        """Construye índices invertidos en memoria O(1) para resolución ultra-rápida de nodos."""
        self._label_index.clear()
        self._word_to_nodes.clear()
        self._def_word_to_nodes.clear()
        for nid, d in self.graph.nodes(data=True):
            self._indexar_nodo(nid, d)

    def _indexar_nodo(self, nid: str, d: Dict[str, Any]) -> None:
        """Registra un nodo en los índices invertidos (etiqueta y palabras de la definición).

        Los nodos de la capa del mapa no entran: tienen su propio índice exacto (_label_mapa) y su
        búsqueda de texto (el FTS del mapa); mezclarlos aquí cambiaría a qué institución curada se
        resuelve una consulta en prosa."""
        if d.get("capa") == CAPA_MAPA:
            return
        lbl_norm = _normalize_str(d.get("label", ""))
        if lbl_norm:
            self._label_index[lbl_norm] = nid
            for w in re.findall(r"\b\w+\b", lbl_norm):
                if len(w) > 3:
                    self._word_to_nodes[w].add(nid)
        def_norm = _normalize_str(d.get("definicion", ""))
        if def_norm:
            for w in re.findall(r"\b\w+\b", def_norm):
                if len(w) > 3:
                    self._def_word_to_nodes[w].add(nid)

    def _parse_frontmatter(self, text: str) -> Tuple[Dict[str, str], str]:
        """Extrae metadatos frontmatter si existen."""
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                raw_meta = parts[1]
                body = parts[2]
                meta = {}
                for line in raw_meta.strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
                return meta, body
        return {}, text

    def _incorporar_archivo(self, filepath: str) -> Tuple[Set[str], int]:
        """
        Incorpora al grafo las entidades y relaciones de un archivo de doctrina.

        Es el cuerpo por archivo de construir_grafo_desde_doctrina, separado para que la ingesta
        de un documento pueda agregar solo ese archivo al grafo publicado. Devuelve los ids de los
        nodos que tocó (creados o actualizados) y la cantidad de secciones institucionales.
        """
        tocados: Set[str] = set()
        total_secciones = 0
        try:
            rel_path = os.path.relpath(filepath, BASE_DIR)
        except ValueError:
            # Windows: la carpeta y el repo pueden estar en discos distintos (C: y D:)
            # y relpath no cruza unidades. Se usa la ruta normalizada, que alcanza para
            # las comprobaciones por subcadena que vienen después.
            rel_path = filepath.replace(chr(92), '/')

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        frontmatter, body = self._parse_frontmatter(text)

        # Extraer título de obra y tratadista
        obra_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        obra = frontmatter.get("titulo") or (obra_match.group(1).strip() if obra_match else os.path.basename(filepath).replace(".md", ""))

        meta_match = re.search(
            r"\*\*Tratadistas?:\*\*\s*([^|]+)\|\s*\*\*Área:\*\*\s*([^|]+)\|\s*\*\*Materia:\*\*\s*(.+)$",
            body,
            re.MULTILINE
        )
        if meta_match:
            autor = meta_match.group(1).strip()
            area = meta_match.group(2).strip()
            materia = meta_match.group(3).strip()
        else:
            autor = frontmatter.get("autor", "Academia Judicial de Chile" if "academia_judicial" in rel_path else "Doctrina Nacional")
            area = frontmatter.get("materia", "Derecho Práctico Judicial" if "academia_judicial" in rel_path else "General")
            materia = frontmatter.get("titulo", "")

        # Registrar nodo de Autor
        autor_id = _sanitize_id(autor, "autor")
        tocados.add(autor_id)
        if not self.graph.has_node(autor_id):
            self.graph.add_node(
                autor_id,
                label=autor,
                node_type="autor",
                file_type="legal_author",
                source_file=rel_path,
                community=1
            )

        # Calcular tokens aproximados del archivo completo.
        # Sin piso a propósito: antes esto era max(1200, ...) y como 54 de los 58
        # archivos de doctrina están bajo ese umbral, el 93% de las instituciones
        # reportaba 1200 tokens sin importar su tamaño real (de 118 a 1612), lo que
        # inflaba el ahorro que se publica. El número debe ser el del archivo.
        tokens_archivo_total = max(1, int(len(text.split()) * 1.3))

        # Registrar nodo de Obra
        obra_id = _sanitize_id(obra, "obra")
        tocados.add(obra_id)
        if not self.graph.has_node(obra_id):
            self.graph.add_node(
                obra_id,
                label=obra,
                node_type="obra",
                file_type="legal_work",
                area=area,
                source_file=rel_path,
                tokens_archivo=tokens_archivo_total,
                community=1
            )
        self._agregar_arista(obra_id, autor_id, relation="escrito_por", weight=1.0)

        # Dividir por secciones
        secciones = re.split(r"\n##\s+(?:🏛️\s*)?", body)
        if len(secciones) <= 1:
            # Guía de la Academia Judicial sin múltiples secciones '## '
            secciones = [body]

        for sec in secciones:
            sec_clean = sec.strip()
            if not sec_clean or sec_clean.startswith("# ") or sec_clean.startswith("**Tratadista"):
                continue

            lines = sec_clean.split("\n")
            titulo = lines[0].strip().lstrip("#").strip()
            if not titulo or len(titulo) < 3:
                continue

            total_secciones += 1
            inst_id = _sanitize_id(titulo, "inst")
            tocados.add(inst_id)

            # Extraer Definición Canónica
            def_match = re.search(
                r"\*\*Definición Canónica(?:\s*\([^)]+\))?:\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|\n\*|\Z)",
                sec_clean,
                re.DOTALL
            )
            definicion = def_match.group(1).strip() if def_match else ""
            if not definicion and len(lines) > 1:
                # Extraer primera oración explicativa
                for line_item in lines[1:]:
                    l_str = line_item.strip()
                    if l_str and not l_str.startswith("**") and not l_str.startswith("#"):
                        definicion = l_str[:250] + ("..." if len(l_str) > 250 else "")
                        break

            # Extraer Operativa Procesal Forense
            proc_match = re.search(
                r"\*\*Operativa Procesal Forense:\*\*\s*\n*(.*?)(?=\n\n\*\*|\n\*\*Concordancias|\n\*\*Criterio|\n---\Z|\Z)",
                sec_clean,
                re.DOTALL
            )
            operativa_procesal = proc_match.group(1).strip() if proc_match else ""

            # Extraer Concordancias Legales
            concordancias_raw = []
            conc_header = re.search(r"\*\*Concordancias Legales:\*\*\s*(.+)", sec_clean)
            if conc_header:
                concordancias_raw.extend(re.findall(r"\[([^\]]+)\]", conc_header.group(1)))
            # Búsqueda adicional en texto
            concordancias_raw.extend(re.findall(r"\[(BCN\s*-\s*[^\]]+)\]", sec_clean))
            concordancias_raw.extend(re.findall(r"(?:Arts?\.?\s*\d+(?:\s*(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|decies))?(?:\s*(?:inc\.?\s*\d+|N°\s*\d+))*\s*(?:del\s*)?(?:CC|CPC|CPP|CP|COT|CT|CPR|Ley\s*\d+[\.\d]*))", sec_clean))

            # Extraer Criterio Jurisprudencial Rector
            jurisprudencia_raw = []
            fallo_header = re.search(r"\*\*Criterio Jurisprudencial Rector:\*\*\s*(.+)", sec_clean)
            if fallo_header:
                jurisprudencia_raw.extend(re.findall(r"\[([^\]]+)\]", fallo_header.group(1)))
            jurisprudencia_raw.extend(re.findall(r"\[((?:CS|STC|CA)\s*-\s*Rol\s*N°\s*[^\]]+)\]", sec_clean))
            jurisprudencia_raw.extend(re.findall(r"Rol\s*N°?\s*\d+[\.\d]*-\d{4}", sec_clean))

            # Calcular tokens aproximados de la sección y del archivo completo
            tokens_seccion = int(len(sec_clean.split()) * 1.3)

            # Registrar Nodo de Institución
            self.graph.add_node(
                inst_id,
                label=titulo,
                node_type="institucion",
                file_type="legal_doctrine",
                area=area,
                materia=materia,
                autor=autor,
                obra=obra,
                definicion=definicion,
                operativa_procesal=operativa_procesal,
                source_file=rel_path,
                tokens_seccion=tokens_seccion,
                tokens_completos=tokens_archivo_total,
                norm_label=_normalize_str(titulo),
                community=0
            )
            self.instituciones_index[_normalize_str(titulo)] = inst_id
            self.instituciones_index[_normalize_str(titulo.replace("🏛️", "").strip())] = inst_id

            # Conectar Institución -> Autor y Obra
            self._agregar_arista(inst_id, autor_id, relation="analizado_por", weight=1.0)
            self._agregar_arista(inst_id, obra_id, relation="contenido_en", weight=1.0)

            # Procesar y conectar Normas Legales
            normas_vistas: Set[str] = set()
            for norm_text in concordancias_raw:
                clean_norm = norm_text.replace("BCN -", "").strip(" `[]")
                if not clean_norm or clean_norm in normas_vistas or len(clean_norm) < 3:
                    continue
                normas_vistas.add(clean_norm)

                norm_id = _sanitize_id(clean_norm, "norma")
                tocados.add(norm_id)
                if not self.graph.has_node(norm_id):
                    self.graph.add_node(
                        norm_id,
                        label=clean_norm,
                        node_type="articulo_legal",
                        file_type="legal_norm",
                        source_file=rel_path,
                        norm_label=_normalize_str(clean_norm),
                        community=2
                    )
                    self.normas_index[_normalize_str(clean_norm)] = norm_id

                self._agregar_arista(inst_id, norm_id, relation="fundamenta_en", weight=1.0)

            # Procesar y conectar Jurisprudencia CS
            fallos_vistos: Set[str] = set()
            for f_text in jurisprudencia_raw:
                clean_f = f_text.strip(" `[]")
                if not clean_f or clean_f in fallos_vistos or len(clean_f) < 4:
                    continue
                fallos_vistos.add(clean_f)

                fallo_id = _sanitize_id(clean_f, "fallo")
                tocados.add(fallo_id)
                if not self.graph.has_node(fallo_id):
                    self.graph.add_node(
                        fallo_id,
                        label=clean_f,
                        node_type="jurisprudencia",
                        file_type="legal_ruling",
                        source_file=rel_path,
                        community=3
                    )
                self._agregar_arista(inst_id, fallo_id, relation="criterio_jurisprudencial", weight=1.0)

            # Extraer y conectar Vías Procesales
            if operativa_procesal:
                vias_detectadas = re.findall(
                    r"(?:demanda\s+ordinaria|accion\s+reivindicatoria|recurso\s+de\s+casacion|recurso\s+de\s+apelacion|recurso\s+de\s+proteccion|tutela\s+laboral|juicio\s+ejecutivo|juicio\s+sumario|excepcion\s+dilatoria|excepcion\s+perentoria|procedimiento\s+abreviado|audiencia\s+preparatoria|medida\s+precautoria|medida\s+cautelar)",
                    _normalize_str(operativa_procesal)
                )
                for via in set(vias_detectadas):
                    via_id = _sanitize_id(via, "via")
                    tocados.add(via_id)
                    via_label = via.title()
                    if not self.graph.has_node(via_id):
                        self.graph.add_node(
                            via_id,
                            label=via_label,
                            node_type="via_procesal",
                            file_type="legal_procedure",
                            source_file=rel_path,
                            community=4
                        )
                    self._agregar_arista(inst_id, via_id, relation="via_procesal", weight=1.0)

        return tocados, total_secciones

    def _agregar_arista(self, u: str, v: str, **atributos: Any) -> None:
        """`add_edge` que no actualiza en el lugar una arista de la capa del mapa.

        Los atributos de esas aristas son diccionarios compartidos entre muchas (ver
        cargar_capa_mapa): `add_edge` sobre una existente los actualiza en el lugar y cambiaría
        cientos de aristas a la vez. Si lo curado afirma la arista, pasa a ser curada y propia.
        Sin mapa es exactamente `add_edge`."""
        previa = self.graph.get_edge_data(u, v)
        if previa is not None and previa.get("capa") == CAPA_MAPA:
            self.graph.remove_edge(u, v)
        self.graph.add_edge(u, v, **atributos)

    @_con_cerrojo
    def construir_grafo_desde_doctrina(self) -> Dict[str, Any]:
        """
        Escanea el directorio de doctrina e indexa todas las entidades dogmáticas y relaciones.
        """
        self._reiniciar_estado_mapa()
        self.graph.clear()
        self.instituciones_index.clear()
        self.normas_index.clear()

        archivos_procesados = 0
        total_secciones = 0

        for root, _, files in os.walk(self.doctrina_dir):
            if "doctrina_raw" in root or "revistas" in root:
                continue
            for file in sorted(files):
                if not file.endswith(".md") or file.startswith("."):
                    continue
                if file == "README.md":
                    continue

                filepath = os.path.join(root, file)
                archivos_procesados += 1
                total_secciones += self._incorporar_archivo(filepath)[1]

        # Establecer conexiones cruzadas entre instituciones (co-ocurrencia y referencias dogmáticas)
        self._conectar_instituciones_cruzadas()

        # Detección de comunidades con Greedy Modularity
        self._detectar_comunidades()

        self.is_built = True
        self._actualizar_indice_invertido()

        # Un grafo vacío no es un detalle: significa que las cinco herramientas graphify_*
        # responderán "no encontrado" a todo. La causa más común es haber instalado el paquete
        # desde PyPI, donde NO viaja el corpus doctrinal (el paquete solo lleva los módulos).
        # Antes esto se callaba y el agente concluía que el tema no está en la doctrina.
        if self.graph.number_of_nodes() == 0:
            aviso = (
                f"El grafo quedó vacío: no se encontró doctrina en '{self.doctrina_dir}' ni un "
                f"artefacto en '{DEFAULT_GRAPH_PATH}'. Las consultas al grafo responderán "
                "'no encontrado' a cualquier tema. Si instalaste con pip desde PyPI, ten en cuenta "
                "que el corpus doctrinal NO viene dentro del paquete: clona el repositorio o "
                "sincroniza la biblioteca para tener doctrina que consultar."
            )
            if aviso not in self.advertencias:
                self.advertencias.append(aviso)

        stats = {
            "archivos_procesados": archivos_procesados,
            "total_secciones_instituciones": total_secciones,
            "total_nodos": self.graph.number_of_nodes(),
            "total_aristas": self.graph.number_of_edges(),
            "densidad_grafo": round(nx.density(self.graph), 4),
            "total_autores": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "autor"),
            "total_normas": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "articulo_legal"),
            "total_jurisprudencia": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "jurisprudencia"),
            "total_vias_procesales": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "via_procesal"),
        }
        return stats

    def _conectar_instituciones_cruzadas(self, solo: Optional[Set[str]] = None) -> None:
        """Enlaza instituciones jurídicas que comparten normas clave o se citan dogmáticamente.

        Con `solo`, crea únicamente los pares en que participa alguna de esas instituciones: es
        lo que necesita la ingesta incremental, sin volver a enlazar el resto del grafo.
        """
        # Enlace por normas compartidas
        norma_a_insts: Dict[str, List[str]] = {}
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") == "fundamenta_en":
                norma_a_insts.setdefault(v, []).append(u)

        for _norma_node, insts in norma_a_insts.items():
            if len(insts) > 1:
                for i in range(len(insts)):
                    for j in range(i + 1, min(len(insts), i + 4)):
                        if solo is not None and insts[i] not in solo and insts[j] not in solo:
                            continue
                        if not self.graph.has_edge(insts[i], insts[j]):
                            self.graph.add_edge(
                                insts[i],
                                insts[j],
                                relation="comparte_norma",
                                weight=0.8
                            )

    @_con_cerrojo
    def incorporar_archivo_doctrina(self, filepath: str) -> Dict[str, Any]:
        """
        Agrega al grafo ya cargado los nodos y aristas de un solo archivo de doctrina.

        Es la vía de la ingesta de un documento. construir_grafo_desde_doctrina recorre todo el
        corpus y recalcula la modularidad global (greedy_modularity_communities): medido el
        2026-10-07, 240 de sus 247 s por documento. Además partía de un grafo vacío, así que
        cada ingesta borraba del artefacto publicado los nodos que no vienen de doctrina/
        (jurisprudencia TC, publicaciones ambientales, órganos del Estado).

        Aquí no se recalcula la modularidad. Los nodos que ya existían conservan su comunidad
        y los nuevos toman la comunidad mayoritaria de sus vecinos ya existentes. Es una
        aproximación local: `python legal_graphify.py --build` recalcula todo.
        """
        previas = {nid: d.get("community") for nid, d in self.graph.nodes(data=True)}

        tocados, secciones = self._incorporar_archivo(filepath)
        instituciones = {n for n in tocados if self.graph.nodes[n].get("node_type") == "institucion"}
        self._conectar_instituciones_cruzadas(solo=instituciones)

        nuevos = tocados - previas.keys()
        for nid in tocados:
            if nid in previas:
                # add_node sobre una institución repetida pisa su comunidad con el valor por defecto
                self.graph.nodes[nid]["community"] = previas[nid]
        for nid in nuevos:
            votos = Counter(
                previas[v] for v in nx.all_neighbors(self.graph, nid)
                if previas.get(v) is not None
            )
            if votos:
                self.graph.nodes[nid]["community"] = votos.most_common(1)[0][0]

        for nid in tocados:
            self._indexar_nodo(nid, self.graph.nodes[nid])
        self.is_built = True

        return {
            "archivo": filepath,
            "secciones": secciones,
            "nodos_agregados": len(nuevos),
            "total_nodos": self.graph.number_of_nodes(),
            "total_aristas": self.graph.number_of_edges(),
        }

    def _detectar_comunidades(self) -> None:
        """Aplica detección de comunidades por modularidad voraz de Clauset-Newman-Moore."""
        try:
            undirected = self.graph.to_undirected()
            communities = nx.algorithms.community.greedy_modularity_communities(undirected)
            for idx, comm in enumerate(communities):
                for node_id in comm:
                    if self.graph.has_node(node_id):
                        self.graph.nodes[node_id]["community"] = idx
        except Exception:
            pass

    def _buscar_nodo_relevante(self, query: str) -> Optional[str]:
        """Encuentra el nodo central más representativo para la consulta."""
        q_norm = _normalize_str(query)
        palabras_q = set(q_norm.split())

        # 0. Coincidencia directa por ID exacto o normalizado
        if query in self.graph:
            return query
        if q_norm in self.graph:
            return q_norm

        # 1. Coincidencia exacta O(1) en instituciones (antes que el mapa: «Obligaciones Naturales
        # y Civiles (Art. 1470 CC)» es la institución curada, no la ficha del artículo 1470).
        if q_norm in self.instituciones_index:
            return self.instituciones_index[q_norm]

        # 1.2 Con la capa del mapa: alias e índice exacto (un rol o una norma citados como tales).
        # Un rol que el mapa no tiene puede seguir en el grafo curado (fallos antiguos citados en la
        # doctrina: «Rol N° 4.821-2019»), pero solo vale el nodo que ES ese rol: los pasos por
        # palabras sueltas («causa», «sentencia», «rol») y la búsqueda en el texto de la doctrina
        # (~12 s) devolverían una institución o un fallo cualquiera.
        if self.origen_grafo == CAPA_MAPA:
            en_mapa = self._buscar_en_mapa(query)
            if en_mapa == _ROL_INEXISTENTE:
                return self._nodo_curado_del_rol(_ids_de_consulta(query), q_norm)
            if en_mapa:
                return en_mapa

        # 1.5 Con la capa del mapa: nombre exacto de una entidad del mapa (un ministro, una sala,
        # una revista, una norma por su etiqueta), con o sin el tratamiento («ministra …»).
        if self.origen_grafo == CAPA_MAPA:
            for clave in dict.fromkeys((q_norm, _RE_TRATAMIENTO.sub("", q_norm))):
                if clave in self._label_mapa and self._label_mapa[clave] in self.graph:
                    return self._label_mapa[clave]

        # 2. Coincidencia en normas
        for name, nid in self.normas_index.items():
            if q_norm in name:
                return self._primer_predecesor(nid) or nid

        # 2.5 Coincidencia por contención o todas las palabras en instituciones canónicas
        # Prioriza la entidad dogmática con mayor grado y penaliza fragmentos no normalizados
        candidatos_sub: List[Tuple[int, int, str]] = []  # (-score, len(label), nid)
        palabras_q_list = [w for w in q_norm.split() if len(w) > 2]

        if len(q_norm) > 3:
            for name, nid in self.instituciones_index.items():
                if q_norm in name or (len(palabras_q_list) > 1 and all(w in name for w in palabras_q_list)):
                    if self.graph.has_node(nid):
                        deg = self._grado_curado(nid)
                        score = deg * 10
                        if q_norm in name:
                            score += 5
                        if name.startswith(("id_", "1", "2", "3", "4", "5", "6", "7", "8", "9", "pregunta", "parte ")):
                            score -= 50
                        candidatos_sub.append((-score, len(name), nid))

            if candidatos_sub:
                candidatos_sub.sort()
                return candidatos_sub[0][2]

            # Si no hubo coincidencia en instituciones, buscar en _label_index resolviendo vías a su institución
            if q_norm in self._label_index:
                nid = self._label_index[q_norm]
                if self.graph.nodes[nid].get("node_type") == "via_procesal":
                    primero = self._primer_predecesor(nid)
                    if primero:
                        return primero
                return nid

            for lbl_norm, nid in self._label_index.items():
                if q_norm in lbl_norm:
                    if self.graph.has_node(nid):
                        deg = self._grado_curado(nid)
                        score = deg * 10
                        target_nid = nid
                        if self.graph.nodes[nid].get("node_type") == "via_procesal":
                            primero = self._primer_predecesor(nid)
                            if primero:
                                target_nid = primero
                                deg = self._grado_curado(target_nid)
                                score = deg * 10
                        if lbl_norm.startswith(("id_", "1", "2", "3", "4", "5", "6", "7", "8", "9", "pregunta", "parte ")):
                            score -= 50
                        candidatos_sub.append((-score, len(lbl_norm), target_nid))

            if candidatos_sub:
                candidatos_sub.sort()
                return candidatos_sub[0][2]

        # 3. Puntuación ultra-rápida por solapamiento de palabras con índice invertido (O(K))
        if not self._word_to_nodes and self.graph.number_of_nodes() > 0:
            self._actualizar_indice_invertido()

        candidatos_score: Dict[str, int] = defaultdict(int)
        for w in palabras_q:
            if len(w) > 3:
                for nid in self._word_to_nodes.get(w, ()):
                    candidatos_score[nid] += 5
                for nid in self._def_word_to_nodes.get(w, ()):
                    candidatos_score[nid] += 2

        if candidatos_score:
            max_score = max(candidatos_score.values())
            # Desempate determinista: mayor grado y luego orden alfabético
            mejores = [nid for nid, sc in candidatos_score.items() if sc == max_score]
            mejores.sort(key=lambda nid: (-self._grado_curado(nid), nid))
            return mejores[0]

        # 4. Último recurso: el término puede no nombrar ningún nodo y, aun así, ser el
        # tema de una obra ('compraventa' aparece en 4 tratados sin ser el label de
        # ninguna institución). Se busca en el TEXTO del corpus y se avisa de dónde salió.
        return self._buscar_por_corpus(query)

    # ── Resolución con la capa del mapa ──────────────────────────────────────────────────────
    def _es_del_mapa(self, datos: Dict[str, Any]) -> bool:
        """Un nodo de la capa del mapa, o un nodo curado que lleva un ID canónico del mapa."""
        return datos.get("capa") == CAPA_MAPA or "id_mapa" in datos

    def _primer_predecesor(self, nid: str) -> Optional[str]:
        """El primer predecesor de un nodo (la institución que se funda en una norma, la que usa una
        vía). Sin mapa es `predecessors(nid)[0]`, como siempre; con la capa cargada se descartan
        los predecesores del mapa (documentos, recursos) y se prefiere una institución curada."""
        preds = list(self.graph.predecessors(nid))
        if self.origen_grafo == CAPA_MAPA:
            curados = [p for p in preds if self.graph.nodes[p].get("capa") != CAPA_MAPA]
            preds = [p for p in curados if self.graph.nodes[p].get("node_type") == "institucion"] or curados
        return preds[0] if preds else None

    def _grado_curado(self, nid: str) -> int:
        """Grado del nodo sin contar las aristas de la capa del mapa: ordena candidatos curados
        igual con o sin el mapa (una norma curada con 800 citas del mapa no le gana a una institución)."""
        if self.origen_grafo != CAPA_MAPA:
            return int(self.graph.degree(nid))
        g = self.graph
        return sum(1 for d in itertools.chain(g.succ[nid].values(), g.pred[nid].values())
                   if d.get("capa") != CAPA_MAPA)

    def _cliente_activo(self) -> Any:
        """El cliente del mapa si tiene una revisión lista, o None. Nunca usa la red."""
        cliente = self.cliente_mapa
        if cliente is None:
            try:
                from mapa_corpus.cliente import obtener_cliente
            except ImportError:
                return None
            cliente = obtener_cliente()
        try:
            if not cliente.habilitado or cliente.indice() is None:
                return None
        except Exception:  # noqa: BLE001 — una caché ilegible deja al grafo como sin mapa
            return None
        return cliente

    def _nodo_de_id(self, id_: str) -> Optional[str]:
        """Nodo del grafo que corresponde a un ID (canónico del mapa, legado curado o propio)."""
        if id_ in self.graph:
            return id_
        curado = self._canon_a_curado.get(id_)
        if curado and curado in self.graph:
            return curado
        canonico = self._alias_mapa.get(id_)
        if canonico and canonico != id_:
            if canonico in self.graph:
                return canonico
            curado = self._canon_a_curado.get(canonico)
            if curado and curado in self.graph:
                return curado
        return None

    def _buscar_en_mapa(self, query: str) -> Optional[str]:
        """Paso exacto con la capa del mapa: alias e IDs canónicos de `resolver_consulta`.

        Devuelve el nodo; el ID canónico de una entrada del índice que no es nodo (un fallo de la
        CS que nadie cita: se materializa en la vista de la consulta); `_ROL_INEXISTENTE` si la
        consulta es solo roles y ninguno está en el mapa; o None para seguir con el flujo común
        (prosa, o una norma que el mapa no registra)."""
        directo = self._nodo_de_id(query.strip())
        if directo:
            return directo
        ids = _ids_de_consulta(query)
        if not ids:
            return None
        cliente = self._cliente_activo()
        for id_ in ids:
            nodo = self._nodo_de_id(id_)
            if nodo:
                return nodo
            fila = cliente.entrada(id_) if cliente is not None else None
            if fila:
                nodo = self._nodo_de_id(str(fila.get("id") or ""))
                if nodo:
                    return nodo
                if fila.get("col") in _TIPO_DE_COLECCION:
                    return str(fila["id"])
        if all(i.startswith(("cs:", "tc:", "ta:")) for i in ids):
            return _ROL_INEXISTENTE
        return None

    def _nodo_curado_del_rol(self, ids: List[str], q_norm: str = "") -> Optional[str]:
        """El nodo curado cuya etiqueta es ese mismo rol («Rol N° 4.821-2019»), o None.

        Primero la etiqueta idéntica a la consulta (lo que daba el flujo sin mapa); si no, un índice
        rol → nodo armado una vez por versión del grafo con las etiquetas que nombran un rol, donde
        ante dos nodos del mismo rol gana el de jurisprudencia y, luego, el ID menor."""
        if self._roles_curados_version != self._version:
            if not self._label_index and self.graph.number_of_nodes() > 0:
                self._actualizar_indice_invertido()
            mejores: Dict[str, Tuple[int, str]] = {}
            for nid in set(self._label_index.values()):
                datos = self.graph.nodes[nid] if nid in self.graph else {}
                etiqueta = str(datos.get("label") or "")
                if not re.search(r"\b(?:rol|stc)\b", etiqueta, re.IGNORECASE):
                    continue
                prioridad = 0 if str(datos.get("node_type", "")).startswith("jurisprudencia") else 1
                for id_ in _ids_de_consulta(etiqueta):
                    if id_.startswith(("cs:", "tc:", "ta:")) and (prioridad, nid) < mejores.get(id_, (2, "")):
                        mejores[id_] = (prioridad, nid)
            self._roles_curados = {id_: nid for id_, (_, nid) in mejores.items()}
            self._roles_curados_version = self._version
        exacto = self._label_index.get(q_norm) if q_norm else None
        if exacto and exacto in self.graph and set(_ids_de_consulta(str(self.graph.nodes[exacto].get("label") or ""))) & set(ids):
            return exacto
        return next((self._roles_curados[i] for i in ids if i in self._roles_curados), None)

    def _buscar_por_texto_mapa(self, query: str) -> Optional[str]:
        """Último paso con la capa del mapa: búsqueda de texto (FTS) en las 80 mil entradas.
        Devuelve el nodo (o la entrada materializable) mejor ranqueado y deja el aviso de que la
        coincidencia es de texto."""
        cliente = self._cliente_activo()
        if cliente is None:
            return None
        filas = cliente.buscar(query, limite=10)
        for fila in filas:
            id_ = str(fila.get("id") or "")
            elegido = self._nodo_de_id(id_) or (id_ if fila.get("col") in _TIPO_DE_COLECCION else None)
            if not elegido:
                continue
            etiqueta = (self.graph.nodes[elegido].get("label") if elegido in self.graph else None) or fila.get("titulo") or elegido
            aviso = (
                f"'{query}' no es el nombre de ningún nodo del grafo, pero aparece en el texto de "
                f"{len(filas)} archivo(s) del mapa del corpus de Hugging Face: se resolvió al mejor "
                f"ranqueado ('{etiqueta}'). La coincidencia es de TEXTO, no de nombre: revisa el "
                "subgrafo antes de citarlo."
            )
            if aviso not in self.advertencias:
                self.advertencias.append(aviso)
            return elegido
        return None

    def _buscar_por_corpus(self, query: str) -> Optional[str]:
        """
        Resuelve una consulta que no calza con ningún nodo buscándola en el texto de las obras.
        Devuelve la institución mejor conectada entre las obras que la mencionan, y deja un
        aviso: la coincidencia es de texto, no de nombre. Preferible a responder "no encontrado"
        cuando el tema sí está en la doctrina. Con la capa del mapa cargada, si la doctrina local
        no lo tiene, se busca además en el texto indexado del mapa (FTS), con el mismo aviso.
        """
        elegido = self._buscar_por_corpus_doctrina(query)
        if elegido is None and self.origen_grafo == CAPA_MAPA and len(_normalize_str(query)) >= 4:
            elegido = self._buscar_por_texto_mapa(query)
        return elegido

    def _buscar_por_corpus_doctrina(self, query: str) -> Optional[str]:
        """El recorrido de siempre por el texto de doctrina/ (ver _buscar_por_corpus)."""
        q_norm = _normalize_str(query)
        if len(q_norm) < 4:
            return None

        archivos: List[str] = []
        for raiz, _, nombres in os.walk(self.doctrina_dir):
            for nombre in nombres:
                if not nombre.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(raiz, nombre), "r", encoding="utf-8", errors="ignore") as f:
                        if q_norm in _normalize_str(f.read()):
                            archivos.append(nombre)
                except OSError:
                    continue
        if not archivos:
            return None

        candidatos = [
            nid
            for nid, data in self.graph.nodes(data=True)
            if data.get("node_type") == "institucion"
            and os.path.basename(data.get("source_file", "")) in archivos
        ]
        if not candidatos:
            return None

        # Desempate explícito por etiqueta: `max` devuelve el primer máximo que encuentra, así
        # que sin ordenar antes, dos candidatos con el mismo grado podrían alternar entre
        # procesos. Hoy hay un máximo único, pero el orden no puede quedar al azar del hash.
        elegido = max(
            sorted(candidatos, key=lambda n: self.graph.nodes[n].get("label", n)),
            key=lambda n: self._grado_curado(n),
        )
        etiqueta = self.graph.nodes[elegido].get("label", elegido)
        aviso = (
            f"'{query}' no es el nombre de ninguna institución del grafo, pero aparece en el texto "
            f"de {len(archivos)} obra(s): se resolvió a la más conectada de ellas ('{etiqueta}'). "
            "La coincidencia es de TEXTO, no de nombre: revisa el subgrafo antes de citarlo. Si es "
            "un tema que consultas seguido, conviene que sea una institución del catálogo."
        )
        if aviso not in self.advertencias:
            self.advertencias.append(aviso)
        return elegido

    @_con_cerrojo
    def ingerir_codigo_bcn(self, codigo_nombre: str, texto: str) -> Dict[str, Any]:
        """
        Incorpora al grafo los artículos de un código cuyo texto oficial se obtuvo del BCN
        (por ejemplo `BCNClient.get_codigo(...)`). Los artículos que ya están no se
        duplican; los nuevos quedan disponibles para las consultas por norma.

        Si el texto no rindió ningún artículo, queda el aviso: una ingesta que no ingirió nada
        no puede reportarse como un éxito silencioso (es el error que ya cometió una vez el
        documento inexistente del paquete).
        """
        if not self.is_built:
            # Igual que en consultar_subgrafo: artefacto publicado primero, reconstrucción
            # desde doctrina solo como último recurso.
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        extraido = extract_articulos_de_codigo(codigo_nombre, texto)
        articulos = sum(
            1 for _, d in extraido.nodes(data=True) if d.get("node_type") == "articulo_legal"
        )
        if articulos == 0:
            # Un texto sin artículos no toca el grafo: agregar el nodo del código por agregarlo
            # dejaría basura ('Código Inventado') y daría la apariencia de una ingesta hecha.
            self.advertencias.append(
                f"El texto de '{codigo_nombre}' no rindió ningún artículo: no se incorporó nada al "
                "grafo. Revisa que sea el texto oficial del código (el conector BCN lo entrega así) "
                "y que los artículos vengan con su encabezado ('Art. 1234' o 'Artículo 1234')."
            )
            return {
                "codigo": codigo_nombre,
                "articulos_detectados": 0,
                "nodos_nuevos": 0,
                "enlaces_nuevos": 0,
                "grafo": {
                    "nodos": self.graph.number_of_nodes(),
                    "aristas": self.graph.number_of_edges(),
                },
                "advertencias": list(self.advertencias),
            }

        nodos_nuevos, enlaces_nuevos = 0, 0
        for nodo_id, datos in extraido.nodes(data=True):
            if not self.graph.has_node(nodo_id):
                self.graph.add_node(nodo_id, **datos)
                nodos_nuevos += 1
            if datos.get("node_type") == "articulo_legal":
                self.normas_index[_normalize_str(datos.get("label", ""))] = nodo_id
        for origen, destino, datos in extraido.edges(data=True):
            if not self.graph.has_edge(origen, destino):
                self.graph.add_edge(origen, destino, **datos)
                enlaces_nuevos += 1
        self.is_built = True

        return {
            "codigo": codigo_nombre,
            "articulos_detectados": articulos,
            "nodos_nuevos": nodos_nuevos,
            "enlaces_nuevos": enlaces_nuevos,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            },
            "advertencias": list(self.advertencias),
        }

    @_con_cerrojo
    def ingerir_sentencia_judicial(self, doc_o_path: Any) -> Dict[str, Any]:
        """
        Incorpora una sentencia judicial (o su archivo Markdown) al Knowledge Graph.
        Genera el nodo de la sentencia (`sentencia_judicial`), los nodos de considerandos clave,
        y enlaza la sentencia con artículos legales (BCN) y nodos dogmáticos existentes.
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        from sentencia2md import parsear_frontmatter_yaml, segmentar_secciones_sentencia

        # Si se pasa una ruta de archivo .md
        doc_dict: Dict[str, Any] = {}
        if isinstance(doc_o_path, (str, os.PathLike)) and str(doc_o_path).endswith(".md"):
            p = os.path.abspath(doc_o_path)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    cuerpo_md = f.read()
                meta, _ = parsear_frontmatter_yaml(cuerpo_md)
                doc_dict = dict(meta)
                sec = segmentar_secciones_sentencia(cuerpo_md)
                doc_dict["considerandos_lista"] = sec.get("considerandos", [])
                doc_dict["texto_integral"] = cuerpo_md
        elif isinstance(doc_o_path, dict):
            doc_dict = dict(doc_o_path)
        else:
            return {"error": "Formato de sentencia no soportado (se espera dict o ruta .md)"}

        rol = str(doc_dict.get("rol", "")).strip()
        tribunal = str(doc_dict.get("tribunal", "Corte Suprema")).strip()
        fecha = str(doc_dict.get("fecha", "")).strip()
        caratula = str(doc_dict.get("caratula", "")).strip()
        recurso = str(doc_dict.get("recurso", "")).strip()
        resultado = str(doc_dict.get("resultado", "")).strip()
        link_oficial = str(doc_dict.get("link_oficial") or doc_dict.get("url_origen") or doc_dict.get("link") or "").strip()

        if not rol:
            return {"error": "La sentencia no especifica Rol o identificador de causa"}

        sentencia_id = _sanitize_id(f"{tribunal}_{rol}", "sentencia")
        etiqueta_sentencia = f"[{tribunal} - Rol N° {rol}]"

        nodos_nuevos, enlaces_nuevos = 0, 0

        # 1. Agregar nodo de la sentencia
        if not self.graph.has_node(sentencia_id):
            self.graph.add_node(
                sentencia_id,
                label=etiqueta_sentencia,
                node_type="sentencia_judicial",
                rol=rol,
                tribunal=tribunal,
                fecha=fecha,
                caratula=caratula,
                recurso=recurso,
                resultado=resultado,
                link=link_oficial,
                community=3
            )
            nodos_nuevos += 1
            self._label_index[_normalize_str(etiqueta_sentencia)] = sentencia_id
            self._label_index[_normalize_str(f"rol {rol}")] = sentencia_id

        # 2. Considerandos
        cons_list = doc_dict.get("considerandos_lista")
        if not cons_list:
            texto_base = doc_dict.get("texto_integral") or doc_dict.get("texto_sentencia") or ""
            if texto_base:
                sec = segmentar_secciones_sentencia(texto_base)
                cons_list = sec.get("considerandos", [])

        if cons_list:
            for c in cons_list:
                num = str(c.get("numero", "")).strip()
                c_texto = c.get("texto", "")
                c_id = _sanitize_id(f"{sentencia_id}_cons_{num}", "cons")
                c_label = f"Considerando {num} (Rol {rol})"
                
                if not self.graph.has_node(c_id):
                    self.graph.add_node(
                        c_id,
                        label=c_label,
                        node_type="considerando_judicial",
                        numero=num,
                        tipo=c.get("tipo", "HECHO"),
                        texto=c_texto[:600],
                        community=3
                    )
                    nodos_nuevos += 1
                
                if not self.graph.has_edge(sentencia_id, c_id):
                    self.graph.add_edge(sentencia_id, c_id, relation="contiene_considerando")
                    enlaces_nuevos += 1

                # Enlazar normas del considerando si las hay
                for n_str in c.get("normas_citadas", []):
                    norma_norm = _normalize_str(n_str)
                    target_nid = self.normas_index.get(norma_norm)
                    if not target_nid:
                        # Si no existe, crear nodo liviano de norma
                        target_nid = _sanitize_id(n_str, "norma")
                        if not self.graph.has_node(target_nid):
                            self.graph.add_node(target_nid, label=n_str, node_type="articulo_legal", community=2)
                            nodos_nuevos += 1
                            self.normas_index[norma_norm] = target_nid
                    if not self.graph.has_edge(c_id, target_nid):
                        self.graph.add_edge(c_id, target_nid, relation="aplica_norma")
                        enlaces_nuevos += 1

        # 3. Vincular con instituciones dogmáticas detectadas en el texto
        texto_completo = doc_dict.get("texto_integral") or doc_dict.get("texto_sentencia") or ""
        texto_norm = _normalize_str(texto_completo)
        
        # Muestreo sobre las instituciones dogmáticas del índice
        for inst_norm, inst_nid in list(self.instituciones_index.items())[:500]:
            if len(inst_norm) > 4 and inst_norm in texto_norm:
                if not self.graph.has_edge(sentencia_id, inst_nid):
                    self.graph.add_edge(sentencia_id, inst_nid, relation="aplica_doctrina")
                    enlaces_nuevos += 1

        self.is_built = True

        return {
            "sentencia_id": sentencia_id,
            "rol": rol,
            "tribunal": tribunal,
            "nodos_nuevos": nodos_nuevos,
            "enlaces_nuevos": enlaces_nuevos,
            "total_considerandos": len(cons_list) if cons_list else 0,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            }
        }

    def ingerir_lote_sentencias(
        self,
        lista_sentencias: List[Any],
        guardar_disco: bool = False
    ) -> Dict[str, Any]:
        """Ingesta una lista de sentencias (rutas .md o diccionarios) en lote."""
        resultados = []
        nodos_totales, enlaces_totales = 0, 0
        for s in lista_sentencias:
            res = self.ingerir_sentencia_judicial(s)
            if "error" not in res:
                nodos_totales += res.get("nodos_nuevos", 0)
                enlaces_totales += res.get("enlaces_nuevos", 0)
            resultados.append(res)

        if guardar_disco and self.is_built:
            self.guardar_grafo_json()

        return {
            "total_sentencias": len(lista_sentencias),
            "nodos_nuevos_totales": nodos_totales,
            "enlaces_nuevos_totales": enlaces_totales,
            "detalles": resultados,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            }
        }

    @_con_cerrojo
    def ingerir_dictamen_administrativo(self, doc_o_path: Any) -> Dict[str, Any]:
        """
        Incorpora un dictamen o resolución administrativa (o su archivo Markdown) al Knowledge Graph.
        Genera el nodo del pronunciamiento administrativo (`dictamen_administrativo`), los nodos
        de criterios y consideraciones jurídicas, y enlaza con artículos legales (BCN) y doctrina canónica.
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        from resolucion_administrativa2md import parsear_frontmatter_yaml, segmentar_secciones_administrativas

        # Si se pasa una ruta de archivo .md
        doc_dict: Dict[str, Any] = {}
        if isinstance(doc_o_path, (str, os.PathLike)) and str(doc_o_path).endswith(".md"):
            p = os.path.abspath(doc_o_path)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    cuerpo_md = f.read()
                meta, _ = parsear_frontmatter_yaml(cuerpo_md)
                doc_dict = dict(meta)
                sec = segmentar_secciones_administrativas(cuerpo_md, organismo=str(doc_dict.get("organismo", "CGR")))
                doc_dict["consideraciones_lista"] = sec.get("consideraciones", [])
                doc_dict["texto_integral"] = cuerpo_md
        elif isinstance(doc_o_path, dict):
            doc_dict = dict(doc_o_path)
        else:
            return {"error": "Formato de pronunciamiento administrativo no soportado (se espera dict o ruta .md)"}

        organismo = str(doc_dict.get("organismo", "CGR")).strip().upper()
        tipo_acto = str(doc_dict.get("tipo_acto", "Dictamen")).strip()
        identificador = str(doc_dict.get("identificador") or doc_dict.get("numero") or doc_dict.get("docId") or "").strip()
        fecha = str(doc_dict.get("fecha", "")).strip()
        materia = str(doc_dict.get("materia", "")).strip()
        link_oficial = str(doc_dict.get("link_oficial") or doc_dict.get("url_oficial") or doc_dict.get("link") or doc_dict.get("url") or doc_dict.get("pdfUrl") or "").strip()

        if not identificador:
            return {"error": "El pronunciamiento no especifica número o identificador"}

        dictamen_id = _sanitize_id(f"{organismo}_{tipo_acto}_{identificador}", "dictamen")
        etiqueta_dictamen = f"[{organismo} - {tipo_acto} N° {identificador}]"

        nodos_nuevos, enlaces_nuevos = 0, 0

        # 1. Agregar nodo del dictamen/resolución
        if not self.graph.has_node(dictamen_id):
            self.graph.add_node(
                dictamen_id,
                label=etiqueta_dictamen,
                node_type="dictamen_administrativo",
                organismo=organismo,
                tipo_acto=tipo_acto,
                identificador=identificador,
                fecha=fecha,
                materia=materia,
                link=link_oficial,
                community=4
            )
            nodos_nuevos += 1
            self._label_index[_normalize_str(etiqueta_dictamen)] = dictamen_id
            self._label_index[_normalize_str(f"{organismo} {identificador}")] = dictamen_id

        # 2. Consideraciones y criterios
        cons_list = doc_dict.get("consideraciones_lista")
        if not cons_list:
            texto_base = doc_dict.get("texto_integral") or doc_dict.get("texto") or doc_dict.get("documento") or ""
            if texto_base:
                sec = segmentar_secciones_administrativas(texto_base, organismo=organismo)
                cons_list = sec.get("consideraciones", [])

        if cons_list:
            for c in cons_list:
                num = str(c.get("numero", "")).strip()
                c_texto = c.get("texto", "")
                c_id = _sanitize_id(f"{dictamen_id}_parr_{num}", "criterio")
                c_label = f"Párrafo {num} ({organismo} {identificador})"

                if not self.graph.has_node(c_id):
                    self.graph.add_node(
                        c_id,
                        label=c_label,
                        node_type="criterio_administrativo",
                        numero=num,
                        es_analisis_juridico=c.get("es_analisis_juridico", True),
                        texto=c_texto[:600],
                        community=4
                    )
                    nodos_nuevos += 1

                if not self.graph.has_edge(dictamen_id, c_id):
                    self.graph.add_edge(dictamen_id, c_id, relation="contiene_criterio")
                    enlaces_nuevos += 1

                # Enlazar normas citadas si las hay
                for n_str in c.get("normas_citadas", []):
                    norma_norm = _normalize_str(n_str)
                    target_nid = self.normas_index.get(norma_norm)
                    if not target_nid:
                        target_nid = _sanitize_id(n_str, "norma")
                        if not self.graph.has_node(target_nid):
                            self.graph.add_node(target_nid, label=n_str, node_type="articulo_legal", community=2)
                            nodos_nuevos += 1
                            self.normas_index[norma_norm] = target_nid
                    if not self.graph.has_edge(c_id, target_nid):
                        self.graph.add_edge(c_id, target_nid, relation="interpreta_norma")
                        enlaces_nuevos += 1

        # Enlazar fuentes legales generales del documento
        fuentes_doc = doc_dict.get("fuentes_legales") or doc_dict.get("marco_normativo") or []
        if isinstance(fuentes_doc, str):
            fuentes_doc = [f.strip() for f in fuentes_doc.split(",") if f.strip()]
        for n_str in fuentes_doc:
            norma_norm = _normalize_str(n_str)
            target_nid = self.normas_index.get(norma_norm)
            if not target_nid:
                target_nid = _sanitize_id(n_str, "norma")
                if not self.graph.has_node(target_nid):
                    self.graph.add_node(target_nid, label=n_str, node_type="articulo_legal", community=2)
                    nodos_nuevos += 1
                    self.normas_index[norma_norm] = target_nid
            if not self.graph.has_edge(dictamen_id, target_nid):
                self.graph.add_edge(dictamen_id, target_nid, relation="interpreta_norma")
                enlaces_nuevos += 1

        # 3. Vincular con instituciones dogmáticas detectadas en el texto
        texto_completo = doc_dict.get("texto_integral") or doc_dict.get("texto") or doc_dict.get("documento") or materia
        texto_norm = _normalize_str(texto_completo)

        for inst_norm, inst_nid in list(self.instituciones_index.items())[:500]:
            if len(inst_norm) > 4 and inst_norm in texto_norm:
                if not self.graph.has_edge(dictamen_id, inst_nid):
                    self.graph.add_edge(dictamen_id, inst_nid, relation="fija_doctrina_administrativa")
                    enlaces_nuevos += 1

        self.is_built = True

        return {
            "dictamen_id": dictamen_id,
            "organismo": organismo,
            "identificador": identificador,
            "nodos_nuevos": nodos_nuevos,
            "enlaces_nuevos": enlaces_nuevos,
            "total_criterios": len(cons_list) if cons_list else 0,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            }
        }

    def ingerir_lote_dictamenes(
        self,
        lista_dictamenes: List[Any],
        guardar_disco: bool = False
    ) -> Dict[str, Any]:
        """Ingesta una lista de dictámenes o resoluciones administrativas en lote."""
        resultados = []
        nodos_totales, enlaces_totales = 0, 0
        for d in lista_dictamenes:
            res = self.ingerir_dictamen_administrativo(d)
            if "error" not in res:
                nodos_totales += res.get("nodos_nuevos", 0)
                enlaces_totales += res.get("enlaces_nuevos", 0)
            resultados.append(res)

        if guardar_disco and self.is_built:
            self.guardar_grafo_json()

        return {
            "total_dictamenes": len(lista_dictamenes),
            "nodos_nuevos_totales": nodos_totales,
            "enlaces_nuevos_totales": enlaces_totales,
            "detalles": resultados,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            }
        }

    ingerir_lote_resoluciones = ingerir_lote_dictamenes

    def resumen_por_comunidades(self, top_n: int = 12, representativos: int = 4) -> Dict[str, Any]:
        """Resumen jerárquico: qué hay en cada comunidad, sin leer los nodos.

        Es la idea de GraphRAG (Edge et al., arXiv:2404.16130): el grafo se organiza en comunidades
        que se resumen, y se recupera el resumen de la comunidad en vez de recorrer los nodos. Para
        una pregunta de panorama («¿qué hay de laboral?») alcanza con esto, y cuesta cientos de
        tokens en lugar de miles. Las comunidades son las que detectó el motor al construir.
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()
        if self.graph.number_of_nodes() == 0:
            return {"error": "el grafo está vacío: no se cargó el corpus "
                             "(revisá data/legal_knowledge_graph.json)"}

        por_comunidad: Dict[Any, List[str]] = {}
        for nid, datos in self.graph.nodes(data=True):
            clave = datos.get("comunidad", datos.get("community", 0))
            por_comunidad.setdefault(clave, []).append(nid)

        carpetas = ("civil", "penal", "laboral", "familia", "procesal", "administrativo",
                    "constitucional", "comercial", "academia_judicial", "apuntes_orrego", "manuales")

        def area_de(nid: str) -> str:
            origen = str(self.graph.nodes[nid].get("source_file") or "")
            for parte in origen.replace("\\", "/").split("/"):
                if parte in carpetas:
                    return parte
            return "general"

        comunidades = []
        for numero, miembros in sorted(por_comunidad.items(), key=lambda kv: -len(kv[1]))[:top_n]:
            por_grado = sorted(((self.graph.degree(n), n) for n in miembros), reverse=True)
            conteo: Dict[str, int] = {}
            for _, n in por_grado[:max(20, len(por_grado) // 4)]:
                conteo[area_de(n)] = conteo.get(area_de(n), 0) + 1
            area_principal = max(conteo.items(), key=lambda kv: kv[1])[0] if conteo else "general"
            comunidades.append({
                "comunidad": numero,
                "tamano": len(miembros),
                "area_principal": area_principal,
                "representativos": [str(self.graph.nodes[n].get("label") or n)[:70]
                                    for _, n in por_grado[:representativos]],
            })

        resumen: Dict[str, Any] = {
            "comunidades_totales": len(por_comunidad),
            "nodos_totales": self.graph.number_of_nodes(),
            "comunidades": comunidades,
            "como_se_usa": ("Para un panorama, leer esto. Para el detalle de una institución, "
                            "consultar_subgrafo con su nombre."),
        }
        resumen["tokens_aproximados"] = len(json.dumps(resumen, ensure_ascii=False)) // 4
        return resumen

    def consultar_subgrafo(self, query: str, max_hops: int = 1) -> Dict[str, Any]:
        """
        Recupera el subgrafo conectado para una consulta jurídica y genera una ficha sintética
        hiper-densa (de ~50 a ~550 tokens según la institución, medido sobre el grafo completo)
        en lugar de inyectar textos completos de hasta ~1.600 tokens.
        """
        # Artefacto publicado primero (instantáneo); reconstruir desde doctrina es el último
        # recurso: en frío cuesta decenas de segundos.
        self._preparar_consulta()

        nodo_central = self._buscar_nodo_relevante(query)
        # Un nodo del mapa (o una entrada del índice que no es nodo) tiene su propia ficha, armada
        # sobre una vista de la consulta con los fallos de la CS materializados.
        consulta = self._consulta_mapa(nodo_central, max_hops)
        if consulta is not None and nodo_central:
            return self._resultado_mapa(nodo_central, consulta)
        if not nodo_central or not self.graph.has_node(nodo_central):
            return {
                "encontrado": False,
                "query": query,
                "mensaje": self._mensaje_no_encontrado(query),
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }

        central_data = self.graph.nodes[nodo_central]

        # Extraer ego-subgrafo (los vecinos de la capa del mapa, si está cargada, con tope por salto)
        sub_nodes = set(self._ego(self.graph, nodo_central, max_hops))

        # Clasificar vecinos
        normas = []
        jurisprudencia = []
        vias = []
        relaciones_conceptuales = []
        autor_obra = f"{central_data.get('autor', 'Doctrina')} — {central_data.get('obra', 'Tratado')}"

        for neighbor in sub_nodes:
            if neighbor == nodo_central:
                continue
            n_data = self.graph.nodes[neighbor]
            n_type = n_data.get("node_type")
            n_label = n_data.get("label", neighbor)

            # Obtener relación de arista
            rel = ""
            if self.graph.has_edge(nodo_central, neighbor):
                rel = self.graph[nodo_central][neighbor].get("relation", "conecta_con")
            elif self.graph.has_edge(neighbor, nodo_central):
                rel = self.graph[neighbor][nodo_central].get("relation", "afecta_a")

            if n_type == "articulo_legal":
                normas.append(n_label)
            elif n_type == "jurisprudencia":
                jurisprudencia.append(n_label)
            elif n_type == "via_procesal":
                vias.append(n_label)
            elif n_type == "institucion":
                relaciones_conceptuales.append(f"{rel} -> {n_label}")

        # Orden estable antes de recortar. Estas cuatro listas se armaban recorriendo un set, así
        # que su orden dependía de la semilla de hash del proceso: dos corridas de la MISMA
        # consulta devolvían fichas con artículos/criterios distintos y el tamaño variaba ±3
        # tokens (el ahorro publicado, ±1 pp). Para una herramienta cuyos números se citan en un
        # expediente, la misma consulta tiene que dar la misma respuesta siempre.
        normas.sort()
        jurisprudencia.sort()
        vias.sort()
        relaciones_conceptuales.sort()

        # Construir Ficha Sintética Hiper-Densa (Optimizada para Context Window)
        ficha_yaml = (
            f"institucion: \"{central_data.get('label')}\"\n"
            f"area: \"{central_data.get('area', 'Derecho')}\"\n"
            f"fuente_canonica: \"{autor_obra}\"\n"
            f"definicion: \"{central_data.get('definicion', 'No registrada')}\"\n"
            f"normas_positivas: {json.dumps(normas[:6], ensure_ascii=False)}\n"
            f"criterios_cs: {json.dumps(jurisprudencia[:3], ensure_ascii=False)}\n"
            f"operativa_procesal: \"{central_data.get('operativa_procesal', vias[0] if vias else 'Vía declarativa ordinaria')}\"\n"
            f"vinculos_subgrafo: {json.dumps(relaciones_conceptuales[:5], ensure_ascii=False)}"
        )

        tokens_subgrafo = int(len(ficha_yaml.split()) * 1.3)
        # Los nodos 'obra' guardan el tamaño de su texto en 'tokens_archivo' (no
        # en 'tokens_completos'); sin este fallback se usaba el default 2800 y se
        # reportaba un ahorro fabricado (~97%).
        tokens_completos = (
            central_data.get("tokens_completos")
            or central_data.get("tokens_archivo")
            or 2800
        )
        ahorro_tokens = max(0, tokens_completos - tokens_subgrafo)
        pct_ahorro = round((ahorro_tokens / max(1, tokens_completos)) * 100, 1)

        return {
            "encontrado": True,
            "nodo_id": nodo_central,
            "label": central_data.get("label"),
            "subgrafo_resumen_yaml": ficha_yaml,
            "metricas_tokens": {
                "tokens_subgrafo": tokens_subgrafo,
                "tokens_texto_completo": tokens_completos,
                "tokens_ahorrados": ahorro_tokens,
                "porcentaje_ahorro": pct_ahorro,
                "factor_reduccion": f"{round(tokens_completos / max(1, tokens_subgrafo), 1)}x"
            },
            "subgrafo_info": {
                "total_nodos_subgrafo": len(sub_nodes),
                "normas_conectadas": len(normas),
                "fallos_conectados": len(jurisprudencia),
                "vias_conectadas": len(vias)
            }
        }

    def calcular_ahorro_tokens(self, query: str) -> Dict[str, Any]:
        """Calcula el ahorro exacto de tokens al consultar el subgrafo en lugar de textos completos."""
        res = self.consultar_subgrafo(query)
        if not res.get("encontrado"):
            return {
                "query": query,
                "encontrado": False,
                "mensaje": res.get("mensaje")
            }
        return {
            "query": query,
            "encontrado": True,
            "institucion": res["label"],
            "metricas": res["metricas_tokens"],
            "ficha_optimizada": res["subgrafo_resumen_yaml"]
        }

    def exportar_subgrafo_mermaid(self, query: str, max_hops: int = 1) -> str:
        """Genera diagrama Mermaid interactivo centrado en el subgrafo de la consulta.

        Los nodos van con alias `n0..nk` (en el orden de sus IDs) y su etiqueta entre comillas: los
        IDs del mapa llevan «:» («norma:cc:1545», «cs:1234-2023») y Mermaid los rompe. Más de
        TOPE_NODOS_MERMAID nodos no se leen: se dejan los más cercanos al centro (lo curado antes
        que la capa del mapa) y el diagrama dice cuántos quedaron fuera.
        """
        # Mismo orden que consultar_subgrafo: artefacto publicado antes de reconstruir.
        self._preparar_consulta()

        nodo_central = self._buscar_nodo_relevante(query)
        consulta = self._consulta_mapa(nodo_central, max_hops)
        g = consulta["vista"] if consulta is not None else self.graph
        if not nodo_central or not g.has_node(nodo_central):
            return "```mermaid\ngraph TD\n    A[\"No se encontró nodo para la consulta\"]\n```"

        distancias = self._ego(g, nodo_central, max_hops, acotar_curados=consulta is not None)
        sub_nodes = sorted(distancias)
        # Alias y tope solo cuando el subgrafo trae la capa del mapa: un diagrama solo curado sale
        # idéntico al de siempre (sus IDs no rompen Mermaid).
        con_mapa = any(g.nodes[n].get("capa") == CAPA_MAPA or ":" in n for n in sub_nodes)
        omitidos = 0
        if con_mapa and len(sub_nodes) > TOPE_NODOS_MERMAID:
            prioridad = sorted(distancias, key=lambda n: (distancias[n], g.nodes[n].get("capa") == CAPA_MAPA, n))
            sub_nodes = sorted(prioridad[:TOPE_NODOS_MERMAID])
            omitidos = len(distancias) - len(sub_nodes)
        alias = {nid: (f"n{i}" if con_mapa else nid) for i, nid in enumerate(sub_nodes)}
        hay_mapa = any(g.nodes[n].get("capa") == CAPA_MAPA for n in sub_nodes)

        titulo = str(g.nodes[nodo_central].get("label", query)).replace("\n", " ")
        lines = [
            "```mermaid",
            "---",
            f"title: Subgrafo de Conocimiento Jurídico — {titulo}",
            "---",
            "graph TD",
            "    %% Clases estilizadas",
            "    classDef central fill:#1a237e,stroke:#3949ab,stroke-width:3px,color:#ffffff,font-weight:bold;",
            "    classDef institucion fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;",
            "    classDef norma fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;",
            "    classDef fallo fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c;",
            "    classDef via fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f;",
            "    classDef autor fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;",
        ]
        if hay_mapa:
            lines.append("    classDef mapa fill:#eceff1,stroke:#546e7a,stroke-width:1px,color:#263238;")
        lines.append("")

        # Nodos
        for nid in sub_nodes:
            data = g.nodes[nid]
            lbl = str(data.get("label", nid)).replace('"', "'").replace("\n", " ")
            if len(lbl) > 40:
                lbl = lbl[:37] + "..."
            ntype = data.get("node_type", "institucion")
            nodo = alias[nid]
            lines.append(f'    {nodo}["{lbl}"]')

            if nid == nodo_central:
                lines.append(f"    class {nodo} central;")
            elif ntype in ("institucion", "obra"):
                lines.append(f"    class {nodo} institucion;")
            elif ntype in ("articulo_legal", "norma"):
                lines.append(f"    class {nodo} norma;")
            elif ntype == "jurisprudencia" or (data.get("capa") == CAPA_MAPA and ntype in _TIPOS_SENTENCIA):
                lines.append(f"    class {nodo} fallo;")
            elif ntype == "via_procesal":
                lines.append(f"    class {nodo} via;")
            elif ntype == "autor":
                lines.append(f"    class {nodo} autor;")
            elif data.get("capa") == CAPA_MAPA:
                lines.append(f"    class {nodo} mapa;")

        lines.append("")

        # Aristas
        subgraph = g.subgraph(sub_nodes)
        for u, v, data in subgraph.edges(data=True):
            rel = data.get("relation", "")
            if rel:
                rel_clean = rel.replace("_", " ")
                lines.append(f"    {alias[u]} -->|{rel_clean}| {alias[v]}")
            else:
                lines.append(f"    {alias[u]} --> {alias[v]}")

        if omitidos:
            lines.append(f"    %% {omitidos} nodos más quedaron fuera del diagrama (tope de {TOPE_NODOS_MERMAID})")
        lines.append("```")
        return "\n".join(lines)

    def encontrar_camino(self, origen: str, destino: str, max_caminos: int = 3) -> Dict[str, Any]:
        """
        Calcula y traza los caminos relacionales mínimos entre dos conceptos, instituciones o normas.
        Permite a LLMs y abogados deducir cadenas de subsunción y argumentación dogmática.
        """
        self._preparar_consulta()

        nodo_a = self._buscar_nodo_relevante(origen)
        nodo_b = self._buscar_nodo_relevante(destino)

        if not nodo_a or not self.graph.has_node(nodo_a):
            return {
                "encontrado": False,
                "mensaje": f"No se encontró el nodo de origen '{origen}'.",
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }
        if not nodo_b or not self.graph.has_node(nodo_b):
            return {
                "encontrado": False,
                "mensaje": f"No se encontró el nodo de destino '{destino}'.",
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }

        # Vista no dirigida cacheada: copiar el grafo en cada consulta costaba un recorrido
        # completo (con la capa del mapa, ~180 mil aristas por llamada).
        undirected = self._no_dirigido()

        if not nx.has_path(undirected, nodo_a, nodo_b):
            return {
                "encontrado": False,
                "origen": self.graph.nodes[nodo_a].get("label", nodo_a),
                "destino": self.graph.nodes[nodo_b].get("label", nodo_b),
                "mensaje": f"No existe un camino relacional conexo entre '{origen}' y '{destino}'."
            }

        all_paths = []
        try:
            generator = nx.all_shortest_paths(undirected, source=nodo_a, target=nodo_b)
            for i, p in enumerate(generator):
                if i >= max_caminos:
                    break
                all_paths.append(p)
        except Exception:
            try:
                p = nx.shortest_path(undirected, source=nodo_a, target=nodo_b)
                all_paths.append(p)
            except Exception as e:
                return {"encontrado": False, "error": str(e)}

        caminos_formateados = []
        for path in all_paths:
            cadena_pasos = []
            for idx in range(len(path)):
                curr_node = path[idx]
                curr_data = self.graph.nodes[curr_node]
                curr_lbl = curr_data.get("label", curr_node)
                curr_type = curr_data.get("node_type", "nodo")

                if idx < len(path) - 1:
                    next_node = path[idx + 1]
                    rel_name = "conecta_con"
                    if self.graph.has_edge(curr_node, next_node):
                        rel_name = self.graph[curr_node][next_node].get("relation", "conecta_con")
                    elif self.graph.has_edge(next_node, curr_node):
                        rel_name = f"es_{self.graph[next_node][curr_node].get('relation', 'afectado_por')}_de"
                    cadena_pasos.append(f"[{curr_type}] {curr_lbl} ➔ --({rel_name})-->")
                else:
                    cadena_pasos.append(f"[{curr_type}] {curr_lbl}")

            caminos_formateados.append({
                "longitud_saltos": len(path) - 1,
                "nodos": [self.graph.nodes[n].get("label", n) for n in path],
                "trazado": " ".join(cadena_pasos)
            })

        return {
            "encontrado": True,
            "origen": self.graph.nodes[nodo_a].get("label", nodo_a),
            "destino": self.graph.nodes[nodo_b].get("label", nodo_b),
            "total_caminos_encontrados": len(caminos_formateados),
            "caminos": caminos_formateados
        }

    def explicar_institucion(self, query: str) -> Dict[str, Any]:
        """
        Genera un desglose explicativo 360° de una institución o concepto jurídico:
        antecedentes normativos, vías procesales, fallos de la Corte Suprema, autores y posición en el grafo.
        Un nodo del mapa (norma, ministro, sala, recurso, documento…) se explica con sus listas
        propias y los fallos de la Corte Suprema que lo citan, traídos del índice del mapa.
        """
        self._preparar_consulta()

        nodo = self._buscar_nodo_relevante(query)
        consulta = self._consulta_mapa(nodo, 1)
        if consulta is not None and nodo:
            return self._explicacion_mapa(nodo, consulta)
        if not nodo or not self.graph.has_node(nodo):
            return {
                "encontrado": False,
                "mensaje": f"No se encontró el nodo '{query}'.",
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }

        data = self.graph.nodes[nodo]
        out_edges = [(v, self.graph[nodo][v].get("relation", "")) for v in self.graph.successors(nodo)]

        normas = [self.graph.nodes[v].get("label", v) for v, r in out_edges if self.graph.nodes[v].get("node_type") == "articulo_legal"]
        fallos = [self.graph.nodes[v].get("label", v) for v, r in out_edges if self.graph.nodes[v].get("node_type") == "jurisprudencia"]
        vias = [self.graph.nodes[v].get("label", v) for v, r in out_edges if self.graph.nodes[v].get("node_type") == "via_procesal"]
        conceptos_relacionados = [self.graph.nodes[v].get("label", v) for v, r in out_edges if self.graph.nodes[v].get("node_type") == "institucion"]

        grado_in = self.graph.in_degree(nodo)
        grado_out = self.graph.out_degree(nodo)

        explicacion_texto = (
            f"# Explicación Dogmática 360°: {data.get('label')}\n\n"
            f"**Área:** {data.get('area', 'General')} | **Tratadista:** {data.get('autor', 'Doctrina')} | **Obra:** {data.get('obra', 'Tratado')}\n\n"
            f"### Definición Canónica\n{data.get('definicion', 'No registrada')}\n\n"
            f"### Operativa Procesal\n{data.get('operativa_procesal', 'Vía ordinaria declarativa')}\n\n"
            f"### Sustento Positivo (Normas BCN)\n" + ("\n".join([f"- {n}" for n in normas]) if normas else "- Sin normas directas vinculadas") + "\n\n"
            "### Jurisprudencia Rectora (Corte Suprema)\n" + ("\n".join([f"- {f}" for f in fallos]) if fallos else "- Criterio general aplicado por tribunales ordinarios") + "\n\n"
            "### Vías de Acción Judicial\n" + ("\n".join([f"- {v}" for v in vias]) if vias else "- Acción civil ordinaria") + "\n\n"
            "### Nexos Conceptuales\n" + ("\n".join([f"- {c}" for c in conceptos_relacionados]) if conceptos_relacionados else "- Nodo conceptual terminal")
        )

        return {
            "encontrado": True,
            "nodo_id": nodo,
            "label": data.get("label"),
            "tipo": data.get("node_type"),
            "comunidad": data.get("community"),
            "estadisticas_conexiones": {
                "grado_total": grado_in + grado_out,
                "normas_positivas": len(normas),
                "fallos_rector": len(fallos),
                "vias_procesales": len(vias),
                "conceptos_vecinos": len(conceptos_relacionados)
            },
            "explicacion_markdown": explicacion_texto
        }

    def analizar_impacto_normativo(self, objetivo: str) -> Dict[str, Any]:
        """
        Calcula el radio de afectación (Blast Radius) topológico cuando una norma legal,
        artículo o institución dogmática sufre una reforma legal o giro jurisprudencial.
        Para un nodo del mapa, los afectados se ordenan por peso y fecha, y se suman los fallos de
        la Corte Suprema que lo citan (del índice del mapa).
        """
        self._preparar_consulta()

        nodo = self._buscar_nodo_relevante(objetivo)
        consulta = self._consulta_mapa(nodo, 1)
        if consulta is not None and nodo:
            return self._impacto_mapa(nodo, consulta)
        if not nodo or not self.graph.has_node(nodo):
            return {
                "encontrado": False,
                "mensaje": f"No se encontró el nodo objetivo '{objetivo}' para el análisis de impacto.",
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }

        target_data = self.graph.nodes[nodo]
        target_label = target_data.get("label", nodo)

        afectados_directos = set(self.graph.predecessors(nodo))
        if not afectados_directos:
            afectados_directos = set(self.graph.successors(nodo))

        directos_info = []
        # Orden por etiqueta, no por recorrido del set: el payload recorta con [:15] y sin este
        # orden la misma consulta devolvía un conjunto distinto de afectados en cada proceso.
        for n in sorted(afectados_directos, key=lambda x: self.graph.nodes[x].get("label", x)):
            ndata = self.graph.nodes[n]
            directos_info.append({
                "id": n,
                "label": ndata.get("label", n),
                "tipo": ndata.get("node_type", "institucion"),
                "obra": ndata.get("obra", "")
            })

        afectados_cascada = set()
        for d in afectados_directos:
            for succ in self.graph.successors(d):
                if succ != nodo and succ not in afectados_directos:
                    afectados_cascada.add(succ)

        cascada_info = []
        for n in sorted(afectados_cascada, key=lambda x: self.graph.nodes[x].get("label", x)):
            ndata = self.graph.nodes[n]
            cascada_info.append({
                "id": n,
                "label": ndata.get("label", n),
                "tipo": ndata.get("node_type", "institucion")
            })

        total_afectados = len(afectados_directos) + len(afectados_cascada)
        nivel_impacto = "ALTO" if total_afectados >= 8 else ("MEDIO" if total_afectados >= 3 else "BAJO")

        return {
            "encontrado": True,
            "objetivo": target_label,
            "tipo_nodo": target_data.get("node_type"),
            "nivel_riesgo_impacto": nivel_impacto,
            "metricas_impacto": {
                "afectados_directos_grado_1": len(directos_info),
                "afectados_cascada_grado_2": len(cascada_info),
                "total_entidades_impactadas": total_afectados
            },
            "impacto_directo": directos_info[:15],
            "impacto_cascada": cascada_info[:15],
            "dictamen_sintetico": (
                f"Una reforma o variación en '{target_label}' genera un impacto {nivel_impacto}. "
                f"Afecta directamente a {len(directos_info)} instituciones/obras y repercute en cascada sobre "
                f"{len(cascada_info)} vías procesales y figuras jurídicas derivadas."
            )
        }

    def calcular_god_nodes(self, top_n: int = 10) -> Dict[str, Any]:
        """
        Identifica los pilares dogmáticos estructurales (God Nodes) del sistema jurídico
        mediante algoritmos de PageRank y centralidad de grado sobre el grafo dogmático.
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        ordenado_por = "pagerank"
        try:
            pagerank_scores = nx.pagerank(self.graph, alpha=0.85, max_iter=100)
        except Exception as exc:
            # Sin numpy y scipy, NetworkX no puede correr PageRank y aquí se cae a un simple
            # grado de conexión (y cada motor caía a uno distinto). El payload sigue llamando
            # 'pagerank' a ese número, así que tiene que quedar dicho — y el criterio de orden
            # también tiene que quedar dicho, porque no es el mismo: una etiqueta que miente es
            # peor que un fallback honesto.
            ordenado_por = "grado_conexiones"
            self.advertencias.append(
                f"PageRank no disponible ({type(exc).__name__}: {exc}); el ranking se calculó con el "
                "grado de conexión de cada nodo, que NO es PageRank. Instala numpy y scipy (extra "
                "'pagerank' del paquete) si necesitas el PageRank real."
            )
            pagerank_scores = {n: self.graph.degree(n) for n in self.graph.nodes()}

        degree_dict = dict(self.graph.degree())

        nodos_ordenados = sorted(
            pagerank_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        instituciones_top: List[Dict[str, Any]] = []
        normas_top: List[Dict[str, Any]] = []

        for nid, score in nodos_ordenados:
            ndata = self.graph.nodes[nid]
            ntype = ndata.get("node_type")
            lbl = ndata.get("label", nid)
            deg = degree_dict.get(nid, 0)

            entry = {
                "id": nid,
                "label": lbl,
                "tipo": ntype,
                "pagerank": round(score, 5),
                "grado_conexiones": deg,
                "comunidad": ndata.get("community", 0)
            }

            if ntype in ("institucion", "obra") and len(instituciones_top) < top_n:
                instituciones_top.append(entry)
            elif ntype == "articulo_legal" and len(normas_top) < top_n:
                normas_top.append(entry)

            if len(instituciones_top) >= top_n and len(normas_top) >= top_n:
                break

        return {
            "total_nodos_analizados": self.graph.number_of_nodes(),
            "total_aristas": self.graph.number_of_edges(),
            "ordenado_por": ordenado_por,
            "god_instituciones": instituciones_top,
            "god_normas": normas_top,
            "analisis": (
                f"Se han identificado las {len(instituciones_top)} instituciones dogmáticas y "
                f"{len(normas_top)} normas legales más centrales topológicamente, ordenadas por "
                + (
                    "PageRank (alpha=0.85)."
                    if ordenado_por == "pagerank"
                    else "grado de conexión, porque PageRank no estaba disponible (ver advertencias)."
                )
                + " Cada entrada trae ambas métricas a propósito: en este grafo el 83% de los nodos"
                " no tiene aristas de salida, así que PageRank y grado de conexión NO ordenan igual"
                " y conviene mirar las dos antes de llamar 'pilar' a una institución."
            )
        }

    @_con_cerrojo
    def guardar_grafo_json(self, filepath: str = DEFAULT_GRAPH_PATH) -> str:
        """Serializa el grafo en formato Node-Link JSON estándar de NetworkX / Graphify.

        Emite una única clave de aristas ("edges" con NetworkX >= 3.6). Duplicar la
        misma lista bajo "edges" y "links" no aportaba compatibilidad real (los
        lectores de este módulo aceptan cualquiera de las dos) y sí inflaba el
        archivo ~39%, además de permitir que ambas copias divergieran al editarse
        sólo una de ellas.

        Con la capa del mapa cargada (`origen_grafo != "repo"`) el artefacto versionado no se
        escribe: lanza GrafoConCapaMapaError. La capa vive en Hugging Face y se superpone en
        memoria; volcarla al repositorio duplicaría 30 mil nodos que quedarían desfasados con la
        próxima revisión del mapa. Otra ruta (un respaldo, graphify-out) sí se puede escribir.
        """
        if self.origen_grafo != "repo" and _es_grafo_versionado(filepath):
            raise GrafoConCapaMapaError(
                f"El grafo en memoria trae la capa del mapa del corpus (origen_grafo={self.origen_grafo!r}): "
                f"no se vuelca a {filepath}. Para guardar lo curado, carga el artefacto en un motor sin "
                "la capa (LegalGraphifyEngine().cargar_grafo_json()), incorpora ahí y guarda ese."
            )
        if not self.is_built:
            self.construir_grafo_desde_doctrina()

        directorio = os.path.dirname(filepath)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        try:
            data = nx.node_link_data(self.graph, edges="edges")
        except TypeError:
            # NetworkX < 3.6 serializa las aristas bajo "links" por defecto.
            data = nx.node_link_data(self.graph)

        if "edges" in data and "links" in data:
            data.pop("links")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    @_con_cerrojo
    def cargar_grafo_json(self, filepath: Optional[str] = None) -> bool:
        """Carga el grafo serializado desde un archivo JSON para consulta instantánea.

        Sin `filepath` usa DEFAULT_GRAPH_PATH — evaluado en la llamada, no al definir la clase,
        para que las pruebas (y cada runtime) puedan apuntar a otro artefacto. Reemplaza el
        grafo en memoria: si traía la capa del mapa, la capa se va (`origen_grafo` vuelve a
        "repo"); el motor compartido la vuelve a subir en la próxima consulta.
        """
        filepath = filepath or DEFAULT_GRAPH_PATH
        if not os.path.exists(filepath):
            # No es un error (primera corrida), pero tampoco puede quedar en silencio: el
            # consumidor tiene que poder distinguir "no hay artefacto todavía" de "el grafo
            # tiene datos y los estoy usando".
            aviso = (
                f"No existe el grafo en {filepath} (no hay nada cargado). Si el corpus sí está, "
                f"reconstrúyelo con construir_grafo_desde_doctrina(); si instalaste desde PyPI, el "
                "corpus doctrinal no viaja dentro del paquete."
            )
            if aviso not in self.advertencias:  # sin duplicar: cada consulta reintenta la carga
                self.advertencias.append(aviso)
            return False
        self.advertencias = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "edges" in data and "links" not in data:
                data["links"] = data["edges"]
            elif "links" in data and "edges" not in data:
                data["edges"] = data["links"]

            def _interpretar_con(edges_param: Optional[str]) -> Optional[nx.DiGraph]:
                """
                Interpreta el JSON con una convención de aristas concreta ('edges', 'links' o la
                que NetworkX traiga por defecto). Devuelve None si esa convención no calza, para
                probar la siguiente sin propagar el fallo.
                """
                try:
                    kwargs: Dict[str, Any] = {"directed": True}
                    if edges_param:
                        kwargs["edges"] = edges_param
                    return nx.node_link_graph(data, **kwargs)
                except Exception:
                    return None

            loaded_graph = None
            for edges_param in [None, "edges", "links"]:
                candidato = _interpretar_con(edges_param)
                if candidato is not None and candidato.number_of_nodes() > 0:
                    loaded_graph = nx.DiGraph(candidato) if not candidato.is_directed() else candidato
                    break

            if loaded_graph is None or loaded_graph.number_of_nodes() == 0:
                self.advertencias.append(
                    f"El grafo en {filepath} no tiene una estructura Node-Link utilizable: "
                    f"se reconstruyó desde {self.doctrina_dir}."
                )
                self.construir_grafo_desde_doctrina()
                return True

            self.graph = loaded_graph
            self._reiniciar_estado_mapa()
            self.instituciones_index.clear()
            self.normas_index.clear()
            for nid, d in self.graph.nodes(data=True):
                if d.get("node_type") == "institucion":
                    lbl = _normalize_str(d.get("label", ""))
                    self.instituciones_index[lbl] = nid
                elif d.get("node_type") == "articulo_legal":
                    lbl = _normalize_str(d.get("label", ""))
                    self.normas_index[lbl] = nid
            self.is_built = True
            self._actualizar_indice_invertido()
            return True
        except Exception as exc:
            self.advertencias.append(
                f"No se pudo leer {filepath} ({type(exc).__name__}: {exc}): "
                f"se reconstruyó el grafo desde {self.doctrina_dir}."
            )
            self.construir_grafo_desde_doctrina()
            return True

    # ── Capa del mapa del corpus de Hugging Face ─────────────────────────────────────────────
    def _preparar_consulta(self) -> None:
        """Lo que toda consulta necesita: el grafo cargado (artefacto publicado primero; reconstruir
        desde doctrina es el último recurso) y, en el motor compartido, la capa del mapa si el
        cliente tiene una revisión lista. Nunca usa la red ni espera una descarga."""
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()
        if self.usar_mapa:
            self.subir_capa_mapa()

    @staticmethod
    def _marca_directorio(carpeta: Path) -> Tuple[str, int, int]:
        """Marca barata de un mapa en disco (ruta, mtime y tamaño de estado.json): evita releer y
        hashear el estado en cada consulta para saber si la capa cargada sigue siendo la vigente."""
        try:
            st = (carpeta / "estado.json").stat()
            return (str(carpeta.resolve()), int(st.st_mtime_ns), int(st.st_size))
        except OSError:
            return (str(carpeta), 0, 0)

    def subir_capa_mapa(self) -> bool:
        """Sube (o renueva) la capa del mapa desde el cliente del mapa si tiene una revisión lista.

        Sin red y sin esperar: si otro hilo está cargando el grafo, la consulta sigue sin la capa y
        la toma la siguiente. Una carga que falló no se reintenta con el mismo mapa (queda el
        aviso). Devuelve si quedó la capa cargada."""
        cliente = self._cliente_activo()
        directorio = cliente.directorio() if cliente is not None else None
        if directorio is None:
            return self.origen_grafo == CAPA_MAPA
        marca = self._marca_directorio(Path(directorio))
        if marca == self._capa.get("marca") or marca == getattr(self, "_marca_fallida", None):
            return self.origen_grafo == CAPA_MAPA
        if not self._lock.acquire(blocking=False):
            return self.origen_grafo == CAPA_MAPA
        try:
            self.cargar_capa_mapa(directorio)
        except Exception as exc:  # noqa: BLE001 — sin la capa, el grafo curado sigue respondiendo
            self._marca_fallida = marca
            aviso = (f"No se pudo cargar la capa del mapa del corpus ({type(exc).__name__}: {exc}): el grafo "
                     "responde solo con lo curado del repositorio.")
            if aviso not in self.advertencias:
                self.advertencias.append(aviso)
        finally:
            self._lock.release()
        return self.origen_grafo == CAPA_MAPA

    @_con_cerrojo
    def cargar_capa_mapa(self, dir_mapa: Union[str, "os.PathLike[str]"]) -> Dict[str, Any]:
        """Superpone la capa conectora del mapa del corpus sobre el grafo curado ya cargado.

        `dir_mapa` es la carpeta de un mapa (`MapaCliente.directorio()` o la salida de
        `python -m mapa_corpus construir`); se leen sus particiones `grafo/nodos-*`,
        `grafo/aristas-*`, `grafo/alias` y `grafo/comunidades`.

        - Lo que ya está en memoria se conserva (el artefacto curado y lo ingerido en la sesión): la
          capa se suma encima, no lo reemplaza.
        - Un nodo del mapa con alias a un nodo curado presente NO se duplica: sus aristas se cuelgan
          del nodo curado, que pasa a llevar `id_mapa` (su ID canónico) y `tipo_mapa`. Excepción:
          las fichas `sent_tc_*` curadas no se funden con `tc:*` (su cabecera es de otra causa):
          quedan enlazadas con una arista `mismo_documento` y marcadas con `calidad_mapa`.
        - Los nodos nuevos llevan `node_type` = tipo del mapa, `label`, `capa="mapa"` y la comunidad
          del mapa; las aristas, `relation`, `weight` y `capa="mapa"`. Si el mapa ya trae una
          arista entre los mismos nodos que una curada, manda la curada. Las comunidades del mapa
          (Louvain sobre curado + capa) se aplican también a los nodos curados que lista.
        - Idempotente: la misma carpeta con el mismo `estado.json` no se vuelve a cargar; otra
          revisión reemplaza la capa anterior (y restaura lo curado que ésta había pisado).
        - Se arma sobre una copia y se cambia de una vez: una consulta en curso nunca ve el grafo a
          medio armar. Fija `origen_grafo = "mapa"`.

        Memoria: los atributos de las aristas de la capa son diccionarios compartidos entre las
        aristas de igual relación y peso (~500 para 150 mil aristas), y las particiones se leen de
        a una fila. Medido el 2026-10-09 con el mapa completo (sha fuente 9378453d: 32 462 nodos,
        150 641 aristas) sobre el curado de 14 050 nodos: 30 464 nodos y 149 096 aristas nuevos
        (1 998 fundidos con curados) en 1,4 s y ~51 MB extra (RSS y memoria viva neta); con un
        diccionario por arista y leyendo cada partición entera eran ~100 MB. La carga es perezosa
        (primera consulta que la necesita) y nunca al importar.

        Devuelve {"nodos", "aristas", "segundos"} (lo que agregó la capa) y el detalle de la carga.
        """
        inicio = time.perf_counter()
        carpeta = Path(dir_mapa)
        try:
            estado_bytes = (carpeta / "estado.json").read_bytes()
        except OSError as exc:
            raise ValueError(f"'{carpeta}' no es un mapa del corpus: falta estado.json ({exc})") from exc
        firma = hashlib.sha256(estado_bytes).hexdigest() + "|" + str(carpeta.resolve())
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()
        if self.origen_grafo == CAPA_MAPA and self._capa.get("firma") == firma:
            return dict(self._capa["resumen"], segundos=round(time.perf_counter() - inicio, 3), ya_cargada=True)

        estado = json.loads(estado_bytes.decode("utf-8"))
        declarados = sorted(r for r in (estado.get("archivos") or {}) if r.startswith("grafo/"))
        if not declarados:
            declarados = sorted(p.relative_to(carpeta).as_posix() for p in (carpeta / "grafo").glob("*.jsonl.gz"))

        # Base: lo que hay en memoria sin la capa anterior, con lo curado que ésta pisó restaurado.
        g = _copiar_digrafo(self.graph, sin_capa=self.origen_grafo == CAPA_MAPA)
        self._restaurar_previas(g, self._previas_mapa)
        nodos_g, succ, pred = g._node, g._succ, g._pred

        alias: Dict[str, str] = {}
        if "grafo/alias.jsonl.gz" in declarados:
            alias = {str(f["id"]): str(f["a"]) for f in _filas_gz(carpeta / "grafo/alias.jsonl.gz")}
        canon_a_curado: Dict[str, str] = {}
        puentes_tc: List[Tuple[str, str]] = []
        for legado in sorted(alias):
            canonico, datos = alias[legado], nodos_g.get(legado)
            if datos is None:
                continue
            if canonico.startswith("tc:") and (legado.startswith("sent_tc_") or datos.get("node_type") == "jurisprudencia_tc"):
                puentes_tc.append((legado, canonico))
                continue
            canon_a_curado.setdefault(canonico, legado)

        previas: Dict[str, Dict[str, Any]] = {}

        def pisar(nid: str, clave: str, valor: Any) -> None:
            datos = nodos_g[nid]
            guardado = previas.setdefault(nid, {})
            if clave not in guardado:
                guardado[clave] = datos.get(clave, _AUSENTE)
            datos[clave] = valor

        label_mapa: Dict[str, str] = {}
        nuevos = fusionados = 0
        for rel in declarados:
            if not rel.startswith("grafo/nodos-"):
                continue
            tipo_particion = rel[len("grafo/nodos-"):-len(".jsonl.gz")]
            for fila in _filas_gz(carpeta / rel):
                nid = str(fila["id"])
                tipo = sys.intern(str(fila.get("tipo") or tipo_particion))
                label = str(fila.get("label") or nid)
                destino = canon_a_curado.get(nid)
                if destino is None and nid in nodos_g:
                    # Un nodo en memoria con el mismo ID canónico: se marca, no se duplica.
                    destino = canon_a_curado[nid] = nid
                if destino is not None:
                    pisar(destino, "id_mapa", nid)
                    pisar(destino, "tipo_mapa", tipo)
                    if "c" in fila:
                        pisar(destino, "community", fila["c"])
                    fusionados += 1
                else:
                    atributos: Dict[str, Any] = {"label": label, "node_type": tipo, "capa": CAPA_MAPA}
                    if "c" in fila:
                        atributos["community"] = fila["c"]
                    for clave in ("fecha", "anio", "ruta", "col"):
                        if clave in fila:
                            atributos[clave] = sys.intern(fila[clave]) if clave == "col" else fila[clave]
                    g.add_node(nid, **atributos)
                    destino = nid
                    nuevos += 1
                label_mapa.setdefault(_normalize_str(label), destino)

        def resolver(x: str) -> Optional[str]:
            if x in canon_a_curado:
                return canon_a_curado[x]
            if x in nodos_g:
                return x
            canonico = alias.get(x)
            if canonico is not None:
                return canon_a_curado.get(canonico) or (canonico if canonico in nodos_g else None)
            return None

        def marcar_tc(curado: str, oficial: str) -> None:
            if nodos_g[curado].get("capa") != CAPA_MAPA:
                pisar(curado, "calidad_mapa", "cabecera_desalineada")
                pisar(curado, "documento_oficial", oficial)

        # Un diccionario por (relación, peso), compartido por todas las aristas que lo tienen: las
        # consultas no los modifican y _agregar_arista los reemplaza antes de que lo curado escriba.
        compartidos: Dict[Tuple[str, int], Dict[str, Any]] = {}
        agregadas = colgantes = 0
        for rel in declarados:
            if not rel.startswith("grafo/aristas-"):
                continue
            relacion = sys.intern(rel[len("grafo/aristas-"):-len(".jsonl.gz")])
            for fila in _filas_gz(carpeta / rel):
                s, t = resolver(str(fila["s"])), resolver(str(fila["t"]))
                if s is None or t is None:
                    colgantes += 1
                    continue
                if s == t:
                    continue
                peso = int(fila.get("w") or 1)
                previa = succ[s].get(t)
                if previa is None:
                    datos = compartidos.get((relacion, peso))
                    if datos is None:
                        datos = compartidos[(relacion, peso)] = {"relation": relacion, "weight": peso, "capa": CAPA_MAPA}
                    succ[s][t] = pred[t][s] = datos
                    agregadas += 1
                elif previa.get("capa") == CAPA_MAPA:
                    relaciones = tuple(previa.get("relaciones") or (previa["relation"],))
                    if relacion not in relaciones:
                        # Dos relaciones entre los mismos nodos (un ministro que integró y redactó):
                        # la arista pasa a tener su propio diccionario con ambas.
                        succ[s][t] = pred[t][s] = dict(previa, relaciones=relaciones + (relacion,),
                                                       weight=max(int(previa.get("weight") or 1), peso))
                if relacion in ("mismo_documento", "mismo_archivo"):
                    marcar_tc(s, t)

        for legado, canonico in puentes_tc:
            oficial = resolver(canonico)
            if oficial is None or oficial == legado:
                continue
            if succ[legado].get(oficial) is None:
                succ[legado][oficial] = pred[oficial][legado] = {"relation": "mismo_documento", "weight": 1,
                                                                  "capa": CAPA_MAPA}
                agregadas += 1
            marcar_tc(legado, oficial)

        if "grafo/comunidades.jsonl.gz" in declarados:
            for fila in _filas_gz(carpeta / "grafo/comunidades.jsonl.gz"):
                nid = str(fila["id"])
                destino = canon_a_curado.get(nid) or nid
                if "c" in fila and destino in nodos_g and nodos_g[destino].get("capa") != CAPA_MAPA:
                    pisar(destino, "community", fila["c"])

        limpiar = getattr(nx, "_clear_cache", None)
        if callable(limpiar):
            limpiar(g)
        resumen = {
            "nodos": nuevos,
            "aristas": agregadas,
            "fusionados": fusionados,
            "aristas_sin_extremo": colgantes,
            "total_nodos": g.number_of_nodes(),
            "total_aristas": g.number_of_edges(),
            "directorio": str(carpeta),
            "sha_fuente": estado.get("sha_fuente"),
            "fecha_fuente": estado.get("fecha_fuente"),
        }
        # El cambio, de una vez (seguimos bajo el RLock).
        self.graph = g
        self.origen_grafo = CAPA_MAPA
        self._capa = {"firma": firma, "resumen": resumen, "marca": self._marca_directorio(carpeta)}
        self._canon_a_curado = canon_a_curado
        self._alias_mapa = alias
        self._label_mapa = label_mapa
        self._previas_mapa = previas
        self._cache_no_dirigido = None
        return dict(resumen, segundos=round(time.perf_counter() - inicio, 3))

    @staticmethod
    def _restaurar_previas(g: nx.DiGraph, previas: Dict[str, Dict[str, Any]]) -> None:
        """Devuelve a los nodos curados los atributos que la capa del mapa había pisado."""
        for nid, atributos in previas.items():
            if nid not in g:
                continue
            datos = g.nodes[nid]
            for clave, valor in atributos.items():
                if valor is _AUSENTE:
                    datos.pop(clave, None)
                else:
                    datos[clave] = valor

    @_con_cerrojo
    def quitar_capa_mapa(self) -> bool:
        """Saca la capa del mapa del grafo en memoria (lo curado y lo ingerido se conservan, con
        sus atributos de antes). Devuelve si había una capa que quitar."""
        if self.origen_grafo != CAPA_MAPA:
            return False
        g = _copiar_digrafo(self.graph, sin_capa=True)
        self._restaurar_previas(g, self._previas_mapa)
        self.graph = g
        self._reiniciar_estado_mapa()
        self._cache_no_dirigido = None
        return True

    # ── Subgrafos y vistas por consulta ──────────────────────────────────────────────────────
    def _no_dirigido(self) -> nx.Graph:
        """Vista no dirigida del grafo para los caminos, cacheada hasta que el grafo cambia.

        Se arma con las mismas aristas y en el mismo orden que `to_undirected()` (los caminos salen
        idénticos), pero sin copiar atributos. Se invalida con la versión del grafo (cada carga o
        ingesta) y con su tamaño (por si alguien lo tocó por fuera del motor)."""
        g = self.graph
        clave = (id(g), self._version, g.number_of_nodes(), g.number_of_edges())
        cache = self._cache_no_dirigido
        if cache is None or cache[0] != clave:
            undirected = nx.Graph()
            undirected.add_nodes_from(g)
            undirected.add_edges_from(g.edges())
            cache = self._cache_no_dirigido = (clave, undirected)
        return cache[1]

    def _ordenar_vecinos(self, g: nx.DiGraph, n: str, vecinos: List[str]) -> List[str]:
        """Vecinos de `n` de más a menos peso de la arista que los une y, a igual peso, del más
        reciente al más antiguo (los sin fecha al final); el ID desempata."""
        def clave(v: str) -> Tuple[float, Tuple[int, Tuple[int, ...]], str]:
            datos = g.succ[n].get(v) or g.pred[n].get(v) or {}
            nodo = g.nodes[v]
            return (-float(datos.get("weight") or 1), _fecha_desc(str(nodo.get("fecha") or nodo.get("anio") or "")), str(v))
        return sorted(vecinos, key=clave)

    def _vecinos_acotados(self, g: nx.DiGraph, n: str, acotar_curados: bool = False) -> List[str]:
        """Vecinos de un nodo para el subgrafo, a lo más TOPE_VECINOS_POR_SALTO de la capa del mapa
        (los de más peso y más recientes primero). Los curados entran todos y en el orden de
        siempre (sucesores y luego predecesores): así el subgrafo de una institución curada es el
        mismo con o sin el mapa. Con `acotar_curados` (la ficha de un nodo del mapa) el tope vale
        para todos: una norma del mapa fundida con una curada puede tener cientos de cada lado."""
        if acotar_curados:
            vecinos = list(dict.fromkeys(itertools.chain(g.successors(n), g.predecessors(n))))
            if len(vecinos) <= TOPE_VECINOS_POR_SALTO:
                return vecinos
            return self._ordenar_vecinos(g, n, vecinos)[:TOPE_VECINOS_POR_SALTO]
        curados: List[str] = []
        del_mapa: List[str] = []
        for v in itertools.chain(g.successors(n), g.predecessors(n)):
            (del_mapa if g.nodes[v].get("capa") == CAPA_MAPA else curados).append(v)
        if len(del_mapa) > TOPE_VECINOS_POR_SALTO:
            del_mapa = self._ordenar_vecinos(g, n, list(dict.fromkeys(del_mapa)))[:TOPE_VECINOS_POR_SALTO]
        return curados + del_mapa

    def _ego(self, g: nx.DiGraph, centro: str, max_hops: int, acotar_curados: bool = False) -> Dict[str, int]:
        """Nodos a lo más a `max_hops` saltos del centro (en cualquier sentido), con su distancia.
        Sin la capa del mapa es exactamente el ego-subgrafo de siempre."""
        distancias = {centro: 0}
        frontera = [centro]
        for salto in range(1, max(0, int(max_hops)) + 1):
            siguiente: List[str] = []
            for n in frontera:
                for v in self._vecinos_acotados(g, n, acotar_curados):
                    if v not in distancias:
                        distancias[v] = salto
                        siguiente.append(v)
            frontera = siguiente
        return distancias

    @staticmethod
    def _tipo_mapa(datos: Dict[str, Any]) -> Optional[str]:
        """Tipo del mapa de un nodo (el suyo si es de la capa, `tipo_mapa` si es curado fundido)."""
        if datos.get("tipo_mapa"):
            return str(datos["tipo_mapa"])
        return str(datos.get("node_type")) if datos.get("capa") == CAPA_MAPA else None

    @staticmethod
    def _atributos_de_entrada(fila: Dict[str, Any]) -> Dict[str, Any]:
        """Atributos de nodo para una entrada del índice que se materializa en una vista."""
        col = str(fila.get("col") or "")
        atributos: Dict[str, Any] = {"label": str(fila.get("titulo") or fila.get("id")),
                                     "node_type": _TIPO_DE_COLECCION.get(col, "documento"),
                                     "capa": CAPA_MAPA, "materializado": True}
        for clave in ("col", "fecha", "anio", "ruta", "rol", "resultado", "recurso_txt"):
            if fila.get(clave) not in (None, "", []):
                atributos[clave] = fila[clave]
        return atributos

    @staticmethod
    def _referencias_de_entrada(fila: Dict[str, Any]) -> Iterator[Tuple[str, str]]:
        """(ID citado, relación) de cada referencia de una entrada del índice (ministros, sala,
        recurso, normas, roles…), en orden de campo."""
        propio = fila.get("id")
        for campo in sorted(fila):
            relacion = _RELACION_DE_CAMPO.get(campo)
            if not relacion:
                continue
            valor = fila[campo]
            for item in valor if isinstance(valor, list) else [valor]:
                destino = item[0] if isinstance(item, list) and item else item
                if isinstance(destino, str) and destino and destino != propio:
                    yield destino, relacion

    def _relacion_hacia(self, fila: Dict[str, Any], destino: str) -> str:
        for referido, relacion in self._referencias_de_entrada(fila):
            if referido == destino:
                return relacion
        return "cita"

    def _consulta_mapa(self, nodo: Optional[str], max_hops: int = 1) -> Optional[Dict[str, Any]]:
        """La VISTA de una consulta sobre un nodo del mapa, o None si el nodo es curado (o no hay capa).

        La vista es un grafo propio de la consulta: el ego-subgrafo acotado del nodo y, si es una
        norma, un ministro, una sala o un recurso, los fallos de la Corte Suprema que lo citan
        (del índice del mapa, con tope), materializados solo aquí. El grafo compartido no se toca,
        así que el resultado de una consulta no depende de cuáles se hicieron antes. Si el nodo no
        está en el grafo pero sí en el índice (un fallo de la CS que nadie cita), la vista lo
        materializa con sus referencias.

        Devuelve {"vista", "base" (grafo donde leer los vecinos del nodo), "fallos", "total",
        "con_fallos", "entrada" (la fila del índice del nodo, si la tiene)}.
        """
        if not nodo or self.origen_grafo != CAPA_MAPA:
            return None
        g = self.graph
        if nodo in g and not self._es_del_mapa(g.nodes[nodo]):
            return None
        cliente = self._cliente_activo()
        vista = nx.DiGraph()
        entrada: Optional[Dict[str, Any]] = None
        if nodo in g:
            base = g
            distancias = self._ego(g, nodo, max_hops, acotar_curados=True)
            for n in distancias:
                vista.add_node(n, **g.nodes[n])
            for u in distancias:
                for v, datos in g.succ[u].items():
                    if v in distancias:
                        vista.add_edge(u, v, **datos)
        else:
            entrada = cliente.entrada(nodo) if cliente is not None else None
            if not entrada or str(entrada.get("id")) != nodo:
                return None
            base = vista
            vista.add_node(nodo, **self._atributos_de_entrada(entrada))
            for destino, relacion in self._referencias_de_entrada(entrada):
                vecino = self._nodo_de_id(destino)
                if vecino and vecino != nodo and not vista.has_edge(nodo, vecino):
                    if vecino not in vista:
                        vista.add_node(vecino, **g.nodes[vecino])
                    vista.add_edge(nodo, vecino, relation=relacion, weight=1, capa=CAPA_MAPA)

        datos_nodo = base.nodes[nodo]
        tipo = self._tipo_mapa(datos_nodo)
        id_mapa = str(datos_nodo.get("id_mapa") or nodo)
        if entrada is None and cliente is not None and tipo in _TIPO_DE_COLECCION.values():
            try:
                entrada = cliente.entrada(id_mapa)
            except Exception:  # noqa: BLE001 — sin la fila solo falta la medición de tokens
                entrada = None
        con_fallos = bool(tipo and _TIPOS_FICHA.get(tipo, {}).get("fallos_cs"))
        fallos: List[Dict[str, Any]] = []
        total: Optional[int] = None
        if con_fallos and cliente is not None:
            try:
                fallos, total = cliente.citantes([id_mapa], ["cs"], TOPE_FALLOS_CS)
            except Exception:  # noqa: BLE001 — un índice ilegible se informa como total desconocido
                fallos, total = [], None
            for fila in fallos:
                fid = str(fila["id"])
                if fid not in vista:
                    vista.add_node(fid, **(dict(g.nodes[fid]) if fid in g else self._atributos_de_entrada(fila)))
                if not vista.has_edge(fid, nodo):
                    vista.add_edge(fid, nodo, relation=self._relacion_hacia(fila, id_mapa), weight=1,
                                   capa=CAPA_MAPA, materializada=True)
        return {"vista": vista, "base": base, "fallos": fallos, "total": total, "con_fallos": con_fallos,
                "entrada": entrada, "tipo": tipo, "id_mapa": id_mapa, "cliente": cliente}

    def vista_mapa(self, nodo: str, max_hops: int = 1) -> Optional[nx.DiGraph]:
        """Subgrafo propio de una consulta sobre un nodo del mapa (con los fallos de la CS que lo
        citan materializados), o None si el nodo es curado o no hay capa del mapa cargada. Es una
        copia: modificarla no toca el grafo compartido."""
        consulta = self._consulta_mapa(nodo, max_hops)
        return consulta["vista"] if consulta is not None else None

    # ── Fichas de los nodos del mapa ─────────────────────────────────────────────────────────
    @staticmethod
    def _linea_fallo(fila: Dict[str, Any]) -> str:
        texto = f"{cita_fallo_cs(fila)} {fila.get('titulo') or ''}".strip()
        return f"{texto} — {fila['resultado']}" if fila.get("resultado") else texto

    def _fallo_resumen(self, fila: Dict[str, Any], cliente: Any) -> Dict[str, Any]:
        """Un fallo de la CS materializado, con su corchete oficial y su archivo en HF (fijado)."""
        resumen: Dict[str, Any] = {
            "id": fila.get("id"), "rol": fila.get("rol"), "fecha": fila.get("fecha"),
            "caratula": fila.get("titulo"), "sala": fila.get("sala"), "recurso": fila.get("recurso_txt"),
            "resultado": fila.get("resultado"), "ruta": fila.get("ruta"), "cita": cita_fallo_cs(fila),
        }
        if cliente is not None and fila.get("ruta"):
            try:
                resumen["url_huggingface"] = cliente.url(str(fila["ruta"]))
            except Exception:  # noqa: BLE001 — la URL es un agregado
                pass
        return resumen

    def _grupos_vecinos(self, g: nx.DiGraph, nodo: str, sin_fallos_cs: bool) -> Dict[str, List[Tuple[Any, str, str]]]:
        """Vecinos de un nodo agrupados en las listas de su ficha (ver _CLAVES_RELACION), cada lista
        de más a menos peso y de la fecha más reciente a la más antigua. Con `sin_fallos_cs`, los
        fallos de la CS quedan fuera: van en `fallos_cs`, traídos completos del índice."""
        grupos: Dict[str, List[Tuple[Any, str, str]]] = defaultdict(list)
        vistos: Set[Tuple[str, str]] = set()
        for sentido, vecinos in (("sale", g.succ[nodo]), ("entra", g.pred[nodo])):
            for v, datos in vecinos.items():
                nodo_v = g.nodes[v]
                if sin_fallos_cs and nodo_v.get("node_type") == "sentencia_cs":
                    continue
                etiqueta = str(nodo_v.get("label") or v)
                fecha = _fecha_desc(str(nodo_v.get("fecha") or nodo_v.get("anio") or ""))
                for relacion in datos.get("relaciones") or (datos.get("relation") or "conecta_con",):
                    clave = _CLAVES_RELACION.get((relacion, sentido), "vinculos_subgrafo")
                    if clave == "vinculos_subgrafo":
                        texto = f"{relacion} -> {etiqueta}" if sentido == "sale" else f"{etiqueta} -> {relacion}"
                    else:
                        texto = etiqueta
                    if (clave, v) in vistos:
                        continue
                    vistos.add((clave, v))
                    grupos[clave].append(((-float(datos.get("weight") or 1), fecha, texto, str(v)), texto, v))
        for lista in grupos.values():
            lista.sort(key=lambda x: x[0])
        return dict(sorted(grupos.items(), key=lambda kv: _ORDEN_CLAVES.get(kv[0], len(_ORDEN_CLAVES))))

    @staticmethod
    def _conteos_vecinos(g: nx.DiGraph, nodo: str, sin_fallos_cs: bool) -> Dict[str, int]:
        conteo: Counter = Counter()
        for v in set(g.successors(nodo)) | set(g.predecessors(nodo)):
            tipo = g.nodes[v].get("node_type")
            if tipo in _TIPOS_NORMA:
                conteo["normas"] += 1
            elif tipo in _TIPOS_SENTENCIA and not (sin_fallos_cs and tipo == "sentencia_cs"):
                conteo["fallos"] += 1
            elif tipo == "via_procesal":
                conteo["vias"] += 1
            elif tipo == "institucion":
                conteo["instituciones"] += 1
        return dict(conteo)

    def _ficha_mapa(self, nodo: str, consulta: Dict[str, Any]) -> Tuple[str, Dict[str, List[Tuple[Any, str, str]]]]:
        """Ficha YAML hiper-densa de un nodo del mapa: qué es, sus listas por relación (con tope y
        total) y, para normas, ministros, salas y recursos, los fallos de la CS que lo citan."""
        g = consulta["base"]
        datos = g.nodes[nodo]
        tipo = consulta["tipo"] or str(datos.get("node_type") or "nodo")
        con_indice = consulta["con_fallos"] and consulta["total"] is not None
        grupos = self._grupos_vecinos(g, nodo, sin_fallos_cs=con_indice)
        lineas = [f"{_TIPOS_FICHA.get(tipo, {}).get('clave', tipo)}: {json.dumps(str(datos.get('label') or nodo), ensure_ascii=False)}",
                  f"id_mapa: {json.dumps(consulta['id_mapa'], ensure_ascii=False)}"]
        for clave in ("fecha", "rol", "resultado", "ruta", "calidad_mapa", "documento_oficial"):
            if datos.get(clave):
                lineas.append(f"{clave}: {json.dumps(str(datos[clave]), ensure_ascii=False)}")
        for clave, lista in grupos.items():
            lineas.append(f"{clave}: {json.dumps([texto for _, texto, _ in lista[:TOPE_LISTA_FICHA]], ensure_ascii=False)}")
            if len(lista) > TOPE_LISTA_FICHA:
                lineas.append(f"{clave}_total: {len(lista)}")
        if consulta["con_fallos"]:
            if consulta["total"] is None:
                lineas.append('fallos_cs_total: "sin índice del mapa: no se pudieron contar"')
            else:
                lineas.append(f"fallos_cs_total: {consulta['total']}")
                lineas.append(f"fallos_cs: {json.dumps([self._linea_fallo(f) for f in consulta['fallos']], ensure_ascii=False)}")
        return "\n".join(lineas), grupos

    def _resultado_mapa(self, nodo: str, consulta: Dict[str, Any]) -> Dict[str, Any]:
        """Resultado de consultar_subgrafo para un nodo del mapa: mismas claves que el de una
        institución curada, más las del mapa (capa, tipo, id_mapa, fallos_cs, fallos_cs_total)."""
        g = consulta["base"]
        datos = g.nodes[nodo]
        ficha, grupos = self._ficha_mapa(nodo, consulta)
        tokens_subgrafo = int(len(ficha.split()) * 1.3)
        # Texto que la ficha resume y que se dejó de leer: los fallos listados y el propio archivo
        # del nodo. Misma convención del motor (1,3 tokens por palabra), con ~6 bytes por palabra
        # en español UTF-8. Si no hay texto medido, no se inventa un ahorro: queda en cero.
        filas = list(consulta["fallos"]) + ([consulta["entrada"]] if consulta["entrada"] else [])
        bytes_base = sum(int(f.get("bytes") or 0) for f in filas)
        tokens_completos = int(bytes_base * 1.3 / 6)
        base_medicion = f"bytes de {len(filas)} archivo(s) del corpus que la ficha resume"
        if tokens_completos <= 0:
            tokens_completos = tokens_subgrafo
            base_medicion = "sin texto medido que la ficha reemplace: el ahorro no se informa"
        ahorro = max(0, tokens_completos - tokens_subgrafo)
        conteos = self._conteos_vecinos(g, nodo, sin_fallos_cs=consulta["con_fallos"] and consulta["total"] is not None)
        cliente = consulta["cliente"]
        resultado: Dict[str, Any] = {
            "encontrado": True,
            "nodo_id": nodo,
            "label": datos.get("label"),
            "subgrafo_resumen_yaml": ficha,
            "metricas_tokens": {
                "tokens_subgrafo": tokens_subgrafo,
                "tokens_texto_completo": tokens_completos,
                "tokens_ahorrados": ahorro,
                "porcentaje_ahorro": round((ahorro / max(1, tokens_completos)) * 100, 1),
                "factor_reduccion": f"{round(tokens_completos / max(1, tokens_subgrafo), 1)}x",
                "base_medicion": base_medicion,
            },
            "subgrafo_info": {
                "total_nodos_subgrafo": consulta["vista"].number_of_nodes(),
                "normas_conectadas": conteos.get("normas", 0),
                "fallos_conectados": conteos.get("fallos", 0) + int(consulta["total"] or 0),
                "vias_conectadas": conteos.get("vias", 0),
                "listas": {clave: len(lista) for clave, lista in grupos.items()},
            },
            "capa": CAPA_MAPA,
            "tipo": consulta["tipo"],
            "id_mapa": consulta["id_mapa"],
        }
        if consulta["con_fallos"]:
            resultado["fallos_cs"] = [self._fallo_resumen(f, cliente) for f in consulta["fallos"]]
            resultado["fallos_cs_total"] = consulta["total"]
        if cliente is not None and datos.get("ruta"):
            try:
                resultado["url_huggingface"] = cliente.url(str(datos["ruta"]))
            except Exception:  # noqa: BLE001 — la URL es un agregado
                pass
        return resultado

    def _explicacion_mapa(self, nodo: str, consulta: Dict[str, Any]) -> Dict[str, Any]:
        """explicar_institucion para un nodo del mapa: sus listas por relación y sus fallos de la CS."""
        g = consulta["base"]
        datos = g.nodes[nodo]
        tipo = consulta["tipo"] or str(datos.get("node_type") or "nodo")
        con_indice = consulta["con_fallos"] and consulta["total"] is not None
        grupos = self._grupos_vecinos(g, nodo, sin_fallos_cs=con_indice)
        lineas = [f"# {_TIPOS_FICHA.get(tipo, {}).get('titulo', 'Nodo del mapa')}: {datos.get('label')}", "",
                  f"**ID canónico:** {consulta['id_mapa']} | **Comunidad:** {datos.get('community')}"]
        for clave in ("fecha", "rol", "resultado", "ruta"):
            if datos.get(clave):
                lineas.append(f"**{clave.capitalize()}:** {datos[clave]}")
        if datos.get("calidad_mapa"):
            lineas.append(f"**Aviso de calidad:** {datos['calidad_mapa']} (documento oficial: {datos.get('documento_oficial')})")
        for clave, lista in grupos.items():
            lineas += ["", f"### {clave.replace('_', ' ').capitalize()} ({len(lista)})"]
            lineas += [f"- {texto}" for _, texto, _ in lista[:TOPE_LISTA_FICHA]]
            if len(lista) > TOPE_LISTA_FICHA:
                lineas.append(f"- … y {len(lista) - TOPE_LISTA_FICHA} más")
        if consulta["con_fallos"]:
            if consulta["total"] is None:
                lineas += ["", "### Jurisprudencia de la Corte Suprema",
                           "- Índice del mapa no disponible: no se pudieron contar los fallos que lo citan."]
            else:
                lineas += ["", f"### Jurisprudencia de la Corte Suprema ({consulta['total']} fallos en el mapa; "
                               f"se muestran {len(consulta['fallos'])})"]
                lineas += [f"- {self._linea_fallo(f)}" for f in consulta["fallos"]] or [
                    "- Ningún fallo de la Corte Suprema del corpus lo registra."]
        conteos = self._conteos_vecinos(g, nodo, sin_fallos_cs=con_indice)
        resultado: Dict[str, Any] = {
            "encontrado": True,
            "nodo_id": nodo,
            "label": datos.get("label"),
            "tipo": tipo,
            "comunidad": datos.get("community"),
            "estadisticas_conexiones": {
                "grado_total": g.in_degree(nodo) + g.out_degree(nodo),
                "normas_positivas": conteos.get("normas", 0),
                "fallos_rector": conteos.get("fallos", 0) + int(consulta["total"] or 0),
                "vias_procesales": conteos.get("vias", 0),
                "conceptos_vecinos": conteos.get("instituciones", 0),
            },
            "explicacion_markdown": "\n".join(lineas),
            "capa": CAPA_MAPA,
            "id_mapa": consulta["id_mapa"],
        }
        if consulta["con_fallos"]:
            resultado["fallos_cs"] = [self._fallo_resumen(f, consulta["cliente"]) for f in consulta["fallos"]]
            resultado["fallos_cs_total"] = consulta["total"]
        return resultado

    def _impacto_mapa(self, nodo: str, consulta: Dict[str, Any]) -> Dict[str, Any]:
        """analizar_impacto_normativo para un nodo del mapa: afectados por peso y fecha, más los
        fallos de la CS que lo citan (del índice)."""
        g = consulta["base"]
        datos = g.nodes[nodo]
        etiqueta = datos.get("label", nodo)
        directos = set(g.predecessors(nodo)) or set(g.successors(nodo))
        directos_info = [{"id": n, "label": g.nodes[n].get("label", n), "tipo": g.nodes[n].get("node_type", "institucion"),
                          "obra": g.nodes[n].get("obra", "")}
                         for n in self._ordenar_vecinos(g, nodo, sorted(directos))]
        cascada: Set[str] = set()
        for d in directos:
            for succ in g.successors(d):
                if succ != nodo and succ not in directos:
                    cascada.add(succ)
        cascada_info = [{"id": n, "label": g.nodes[n].get("label", n), "tipo": g.nodes[n].get("node_type", "institucion")}
                        for n in sorted(cascada, key=lambda x: (str(g.nodes[x].get("label", x)), x))]
        fallos_total = int(consulta["total"] or 0)
        total = len(directos) + len(cascada) + fallos_total
        nivel = "ALTO" if total >= 8 else ("MEDIO" if total >= 3 else "BAJO")
        resultado: Dict[str, Any] = {
            "encontrado": True,
            "objetivo": etiqueta,
            "tipo_nodo": consulta["tipo"] or datos.get("node_type"),
            "nivel_riesgo_impacto": nivel,
            "metricas_impacto": {
                "afectados_directos_grado_1": len(directos_info),
                "afectados_cascada_grado_2": len(cascada_info),
                "fallos_cs_grado_1": fallos_total,
                "total_entidades_impactadas": total,
            },
            "impacto_directo": directos_info[:15],
            "impacto_cascada": cascada_info[:15],
            "dictamen_sintetico": (
                f"Una reforma o variación en '{etiqueta}' genera un impacto {nivel}. Afecta directamente a "
                f"{len(directos_info)} nodos del grafo (documentos, sentencias, instituciones) y a {fallos_total} "
                f"fallos de la Corte Suprema del corpus, y repercute en cascada sobre {len(cascada_info)} más."
            ),
            "capa": CAPA_MAPA,
            "id_mapa": consulta["id_mapa"],
        }
        if consulta["con_fallos"]:
            resultado["fallos_cs"] = [self._fallo_resumen(f, consulta["cliente"]) for f in consulta["fallos"]]
            resultado["fallos_cs_total"] = consulta["total"]
        return resultado

    def _mensaje_no_encontrado(self, query: str) -> str:
        """Mensaje de «no encontrado»; con la capa del mapa, si la consulta era un rol, lo dice."""
        if self.origen_grafo == CAPA_MAPA:
            ids = _ids_de_consulta(query)
            if ids and all(i.startswith(("cs:", "tc:", "ta:")) for i in ids):
                return (f"El rol {', '.join(ids)} no está en el mapa del corpus de Hugging Face: no hay "
                        "sentencia que mostrar. Revisa el número, el año y el tribunal.")
        return f"No se encontró un nodo dogmático conectado para '{query}'."

    def integrar_con_graphify(self, graphify_out_path: str = "graphify-out/graph.json") -> Dict[str, Any]:
        """
        Fusiona el grafo de conocimiento jurídico con el grafo general de Graphify (código + AST),
        permitiendo que herramientas como 'graphify explain' y 'graph.html' abarquen la doctrina legal.
        """
        if not self.is_built:
            self.construir_grafo_desde_doctrina()

        full_path = os.path.join(BASE_DIR, graphify_out_path)
        if not os.path.exists(full_path):
            # Guardar como grafo principal
            self.guardar_grafo_json(full_path)
            return {
                "creado": True,
                "path": full_path,
                "nodos_legales": self.graph.number_of_nodes(),
                "aristas_legales": self.graph.number_of_edges()
            }

        with open(full_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

        # Aceptar ambas convenciones de esquema Node-Link ("links" estilo Graphify,
        # "edges" estilo NetworkX >= 3.6). Antes se asumía "links" y un grafo keyed
        # "edges" (incluido uno producido por guardar_grafo_json) crasheaba con
        # KeyError: 'links'.
        edge_key = "links" if "links" in existing_data else "edges" if "edges" in existing_data else "links"
        existing_data.setdefault("nodes", [])
        existing_data.setdefault(edge_key, [])

        existing_nodes = {n["id"]: n for n in existing_data.get("nodes", [])}
        existing_links = {(link_obj["source"], link_obj["target"], link_obj.get("relation", "")): link_obj for link_obj in existing_data.get(edge_key, [])}

        nodos_agregados = 0
        aristas_agregadas = 0

        # Agregar nodos jurídicos
        for nid, data in self.graph.nodes(data=True):
            if nid not in existing_nodes:
                node_entry = {
                    "id": nid,
                    "label": data.get("label", nid),
                    "file_type": data.get("file_type", "legal_doctrine"),
                    "node_type": data.get("node_type", "institucion"),
                    "community": data.get("community", 99),
                    "source_file": data.get("source_file", "doctrina/"),
                    "norm_label": data.get("norm_label", _normalize_str(data.get("label", nid))),
                    "_origin": "legal_graphify",
                    "definicion": data.get("definicion", ""),
                    "operativa_procesal": data.get("operativa_procesal", "")
                }
                existing_data["nodes"].append(node_entry)
                existing_nodes[nid] = node_entry
                nodos_agregados += 1

        # Agregar aristas jurídicas
        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relation", "relacionado_con")
            key = (u, v, rel)
            if key not in existing_links:
                link_entry = {
                    "source": u,
                    "target": v,
                    "relation": rel,
                    "_origin": "legal_graphify",
                    "confidence": "EXTRACTED",
                    "confidence_score": 1.0,
                    "weight": data.get("weight", 1.0)
                }
                existing_data[edge_key].append(link_entry)
                existing_links[key] = link_entry
                aristas_agregadas += 1

        # Si el archivo traía ambas claves, mantenerlas sincronizadas para que la
        # copia no actualizada no quede obsoleta (drift entre "edges" y "links").
        for _alias in ("edges", "links"):
            if _alias != edge_key and _alias in existing_data:
                existing_data[_alias] = existing_data[edge_key]

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        return {
            "fusionado": True,
            "path": full_path,
            "nodos_agregados": nodos_agregados,
            "aristas_agregadas": aristas_agregadas,
            "total_nodos_final": len(existing_data["nodes"]),
            "total_aristas_final": len(existing_data[edge_key])
        }


_MOTOR_COMPARTIDO: Optional[LegalGraphifyEngine] = None
_MOTOR_COMPARTIDO_LOCK = threading.Lock()


def obtener_motor_compartido() -> LegalGraphifyEngine:
    """El motor del proceso (servidor MCP y sus herramientas: corpus, ambiental, vista del grafo).

    Un solo grafo en memoria, con la capa del mapa del corpus cuando el cliente del mapa tiene una
    revisión lista: se sube en la primera consulta que la necesita, sin red y nunca al importar.
    Las herramientas lo comparten en vez de cargar cada una su copia del grafo (y de la capa)."""
    global _MOTOR_COMPARTIDO
    with _MOTOR_COMPARTIDO_LOCK:
        if _MOTOR_COMPARTIDO is None:
            _MOTOR_COMPARTIDO = LegalGraphifyEngine(usar_mapa=True)
        return _MOTOR_COMPARTIDO


def reiniciar_motor_compartido() -> None:
    """Para las pruebas: el próximo `obtener_motor_compartido()` arma un motor nuevo."""
    global _MOTOR_COMPARTIDO
    with _MOTOR_COMPARTIDO_LOCK:
        _MOTOR_COMPARTIDO = None

def main():
    """Punto de entrada CLI para LegalGraphify."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🧠 Open Legal Chile — Motor LegalGraphify (Reducción de Tokens con Grafos)"
    )
    parser.add_argument("--query", "-q", type=str, help="Consulta jurídica para extraer subgrafo sintético")
    parser.add_argument("--path", nargs=2, metavar=("ORIGEN", "DESTINO"), help="Trazar el camino relacional mínimo entre dos conceptos o normas")
    parser.add_argument("--explain", type=str, help="Desglose explicativo 360° de una institución dogmática o norma")
    parser.add_argument("--affected", type=str, help="Análisis de impacto (Blast Radius) ante reformas o cambios jurisprudenciales")
    parser.add_argument("--god-nodes", action="store_true", help="Identifica los pilares dogmáticos (God Nodes) según PageRank")
    parser.add_argument("--top", type=int, default=10, help="Número de nodos a retornar para God Nodes (por defecto 10)")
    parser.add_argument("--build", action="store_true", help="Construye y persiste el grafo completo en JSON")
    parser.add_argument("--stats", action="store_true", help="Muestra estadísticas estructurales del grafo")
    parser.add_argument("--mermaid", action="store_true", help="Imprime el diagrama de subgrafo en sintaxis Mermaid")
    parser.add_argument("--hops", type=int, default=1, help="Radio de saltos para el subgrafo (por defecto 1)")
    parser.add_argument("--merge-graphify", action="store_true", help="Fusiona con graphify-out/graph.json")

    args = parser.parse_args()
    engine = LegalGraphifyEngine()

    if args.build or not os.path.exists(DEFAULT_GRAPH_PATH):
        print("⏳ Construyendo Grafo de Conocimiento Jurídico desde los 58 textos doctrinales...")
        stats = engine.construir_grafo_desde_doctrina()
        saved = engine.guardar_grafo_json()
        print(f"✅ Grafo construido y guardado en {saved}")
        print(f"  • Total Nodos: {stats['total_nodos']}")
        print(f"  • Total Aristas: {stats['total_aristas']}")
        print(f"  • Instituciones Dogmáticas: {stats['total_secciones_instituciones']}")
        print(f"  • Normas Legales BCN: {stats['total_normas']}")
        print(f"  • Fallos Rectores CS: {stats['total_jurisprudencia']}")
        print(f"  • Vías Procesales: {stats['total_vias_procesales']}")

    if args.merge_graphify:
        m_res = engine.integrar_con_graphify()
        print(f"🔗 Fusión con Graphify completada: {m_res}")

    if args.stats:
        if not engine.is_built:
            engine.cargar_grafo_json()
        print("📊 Estadísticas de LegalGraphify:")
        print(f"  • Nodos: {engine.graph.number_of_nodes()}")
        print(f"  • Aristas: {engine.graph.number_of_edges()}")
        print(f"  • Densidad: {round(nx.density(engine.graph), 4)}")

    if args.path:
        origen, destino = args.path
        if not engine.is_built:
            if not engine.cargar_grafo_json():
                engine.construir_grafo_desde_doctrina()
        res_camino = engine.encontrar_camino(origen, destino)
        if not res_camino.get("encontrado"):
            print(f"⚠️ {res_camino.get('mensaje')}")
        else:
            print(f"\n🛤️ CAMINO RELACIONAL JURÍDICO: '{res_camino['origen']}' ➔ '{res_camino['destino']}'")
            print("═" * 70)
            for idx, c in enumerate(res_camino["caminos"], 1):
                print(f"Ruta {idx} ({c['longitud_saltos']} saltos):")
                print(f"  {c['trazado']}\n")
            print("═" * 70)

    if args.explain:
        if not engine.is_built:
            if not engine.cargar_grafo_json():
                engine.construir_grafo_desde_doctrina()
        exp = engine.explicar_institucion(args.explain)
        if not exp.get("encontrado"):
            print(f"⚠️ {exp.get('mensaje')}")
        else:
            print(f"\n{exp['explicacion_markdown']}\n")

    if args.affected:
        if not engine.is_built:
            if not engine.cargar_grafo_json():
                engine.construir_grafo_desde_doctrina()
        impact = engine.analizar_impacto_normativo(args.affected)
        if not impact.get("encontrado"):
            print(f"⚠️ {impact.get('mensaje')}")
        else:
            print(f"\n💥 ANÁLISIS DE IMPACTO NORMATIVO (Blast Radius): {impact['objetivo']}")
            print("═" * 70)
            print(f"Riesgo de Impacto:       {impact['nivel_riesgo_impacto']}")
            print(f"Afectados Directos (G1): {impact['metricas_impacto']['afectados_directos_grado_1']}")
            print(f"Afectados Cascada (G2):  {impact['metricas_impacto']['afectados_cascada_grado_2']}")
            print(f"Total Nodos en Riesgo:   {impact['metricas_impacto']['total_entidades_impactadas']}")
            print(f"\nDictamen:\n  {impact['dictamen_sintetico']}\n")
            print("Entidades Afectadas Directamente:")
            for item in impact["impacto_directo"]:
                print(f"  • [{item['tipo']}] {item['label']} ({item.get('obra', '')})")
            print("═" * 70)

    if args.god_nodes:
        if not engine.is_built:
            if not engine.cargar_grafo_json():
                engine.construir_grafo_desde_doctrina()
        gn = engine.calcular_god_nodes(top_n=args.top)
        print(f"\n🏛️ PILARES ESTRUCTURALES DEL DERECHO (God Nodes - PageRank Top {args.top}):")
        print("═" * 70)
        print("Instituciones Dogmáticas Rectoras:")
        for idx, item in enumerate(gn["god_instituciones"], 1):
            print(f"  {idx:2d}. {item['label']:<35} | PR: {item['pagerank']:.5f} | Conexiones: {item['grado_conexiones']}")
        print("\nNormas Positivas Centrales (BCN):")
        for idx, item in enumerate(gn["god_normas"], 1):
            print(f"  {idx:2d}. {item['label']:<35} | PR: {item['pagerank']:.5f} | Conexiones: {item['grado_conexiones']}")
        print("═" * 70)

    if args.query:
        if not engine.is_built:
            if not engine.cargar_grafo_json():
                engine.construir_grafo_desde_doctrina()

        if args.mermaid:
            diag = engine.exportar_subgrafo_mermaid(args.query, max_hops=args.hops)
            print(diag)
        else:
            ahorro = engine.calcular_ahorro_tokens(args.query)
            if not ahorro.get("encontrado", True):
                print(f"⚠️ {ahorro.get('mensaje')}")
                return

            m = ahorro["metricas"]
            print("\n🧠 SUBGRAFO JURÍDICO HIPER-DENSO (LegalGraphify):")
            print("═════════════════════════════════════════════════════════════")
            print(ahorro["ficha_optimizada"])
            print("═════════════════════════════════════════════════════════════")
            print("⚡ MÉTRICAS DE OPTIMIZACIÓN DE CONTEXTO:")
            print(f"  • Tokens Texto Completo (Capítulo crudo): ~{m['tokens_texto_completo']} tokens")
            print(f"  • Tokens Subgrafo Sintético:             ~{m['tokens_subgrafo']} tokens")
            print(f"  • Tokens Ahorrados:                      ~{m['tokens_ahorrados']} tokens")
            print(f"  • 🚀 Reducción de Tokens:                {m['porcentaje_ahorro']}% ({m['factor_reduccion']})")


if __name__ == "__main__":
    main()
