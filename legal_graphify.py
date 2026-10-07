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
import json
import unicodedata
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set, Tuple

import networkx as nx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_GRAPH_PATH = os.path.join(DATA_DIR, "legal_knowledge_graph.json")


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


# Lo que sigue a la cabecera en una nota de modificación del margen: «, Nº 2», «Nº 25», «L. 19.250».
_RE_NOTA_DE_MARGEN = re.compile(r"(?:,|N[º°]|L\.\s*\d|Ley\s+N?[º°]?\s*\d)")


def _articulos_de_texto(texto: str) -> Dict[str, str]:
    """Artículos (clave -> cuerpo sin el rótulo) de un texto corrido de código, sin pisar homónimos.

    Un texto de código descargado del BCN trae, además del código, sus leyes anexas y sus
    transitorios, y en todos hay un «Artículo 1». El nodo del grafo se identifica por la etiqueta
    «<código>, Art. N»; con el recorrido anterior el último «Artículo 1» del texto reemplazaba los
    atributos del primero (el mismo defecto que tuvo el parser de `bcn_connector`). Se reutiliza su
    lectura de cabeceras y su segmentación por cuerpos: el mapa sale del cuerpo con más artículos.
    """
    # Perezoso: bcn_connector importa la configuración de red, que el grafo no necesita para nada más.
    from bcn_connector import _cabecera, _segmentar_articulos

    # Solo cuenta como rótulo una línea que EMPIEZA con «Art.»/«Artículo» en mayúscula inicial: en
    # minúscula es una remisión en medio de una frase («…lo dispuesto en el\nartículo 12 de esta ley»).
    inicio_articulo = re.compile(r"^(?=\s*(?:ART|Art)[A-Za-zÍíÁá\ufffd]*\.?\s*\d)", re.MULTILINE)
    # El margen del texto oficial trae notas de modificación en línea propia («Art. 1º, Nº 2», «Art. 16»):
    # empiezan con «Art.» pero no son artículos. Medido sobre el Código Civil, 150 de los 2.901 cortes
    # eran notas; cada una, leída como «Artículo 1», hacía retroceder la numeración y partía el código en
    # 75 cuerpos (el principal conservaba 794 de 2.567 artículos). Una cabecera sin cuerpo, o seguida de una
    # nota («, Nº 2», «Nº 25», «L. 19.250»), se reincorpora al artículo anterior. Es una heurística: la vía
    # exacta es pasar `articulos=` (el mapa del conector), que no reinterpreta ningún texto.
    fragmentos: List[str] = []
    for fragmento in inicio_articulo.split(texto):
        if not fragmento.strip():
            continue
        cabecera = _cabecera(fragmento.lstrip())
        resto = fragmento.lstrip()[cabecera["fin"]:].lstrip() if cabecera else ""
        if fragmentos and cabecera and (not resto or _RE_NOTA_DE_MARGEN.match(resto)):
            fragmentos[-1] += fragmento
        else:
            fragmentos.append(fragmento)
    estructuras = [{"tipoParte": "Artículo", "texto": f.lstrip()} for f in fragmentos]
    articulos: Dict[str, str] = {}
    for clave, fragmento in _segmentar_articulos(estructuras)["articulos"].items():
        cabecera = _cabecera(fragmento)
        fin = cabecera["fin"] if cabecera else 0
        articulos[clave] = fragmento[fin:].lstrip(" \t\r\n.-–:_").strip()
    return articulos


def extract_articulos_de_codigo(codigo_nombre: str, texto: str,
                                articulos: Optional[Dict[str, str]] = None) -> nx.DiGraph:
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

    Si ya se tiene el mapa de artículos que entrega `BCNClient.get_codigo(...)["articulos"]`
    (clave -> texto con rótulo), se pasa en `articulos` y no se re-interpreta ningún texto: es la
    vía correcta, porque ese mapa ya viene segmentado por cuerpos y sin artículos pisados.
    """
    grafo = nx.DiGraph()
    codigo_id = _sanitize_id(codigo_nombre, "codigo")
    grafo.add_node(codigo_id, label=codigo_nombre, node_type="cuerpo_legal", community=2)

    if articulos is None:
        articulos = _articulos_de_texto(texto)
    else:
        from bcn_connector import _cabecera

        limpios: Dict[str, str] = {}
        for clave, cuerpo in articulos.items():
            cabecera = _cabecera(str(cuerpo))
            fin = cabecera["fin"] if cabecera else 0
            limpios[clave] = str(cuerpo)[fin:].lstrip(" \t\r\n.-–:_").strip()
        articulos = limpios

    for clave, cuerpo in articulos.items():
        etiqueta = f"{codigo_nombre}, Art. {clave}"
        nodo_id = _sanitize_id(etiqueta, "norma")
        grafo.add_node(
            nodo_id,
            label=etiqueta,
            node_type="articulo_legal",
            texto=cuerpo[:500],
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

    def __init__(self, doctrina_dir: str = DOCTRINA_DIR):
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

    def _actualizar_indice_invertido(self) -> None:
        """Construye índices invertidos en memoria O(1) para resolución ultra-rápida de nodos."""
        self._label_index.clear()
        self._word_to_nodes.clear()
        self._def_word_to_nodes.clear()
        for nid, d in self.graph.nodes(data=True):
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

    def construir_grafo_desde_doctrina(self) -> Dict[str, Any]:
        """
        Escanea el directorio de doctrina e indexa todas las entidades dogmáticas y relaciones.
        """
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
                try:
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                except ValueError:
                    # Windows: la carpeta y el repo pueden estar en discos distintos (C: y D:)
                    # y relpath no cruza unidades. Se usa la ruta normalizada, que alcanza para
                    # las comprobaciones por subcadena que vienen después.
                    rel_path = filepath.replace(chr(92), '/')
                archivos_procesados += 1

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

                frontmatter, body = self._parse_frontmatter(text)

                # Extraer título de obra y tratadista
                obra_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                obra = frontmatter.get("titulo") or (obra_match.group(1).strip() if obra_match else file.replace(".md", ""))

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
                self.graph.add_edge(obra_id, autor_id, relation="escrito_por", weight=1.0)

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
                    self.graph.add_edge(inst_id, autor_id, relation="analizado_por", weight=1.0)
                    self.graph.add_edge(inst_id, obra_id, relation="contenido_en", weight=1.0)

                    # Procesar y conectar Normas Legales
                    normas_vistas: Set[str] = set()
                    for norm_text in concordancias_raw:
                        clean_norm = norm_text.replace("BCN -", "").strip(" `[]")
                        if not clean_norm or clean_norm in normas_vistas or len(clean_norm) < 3:
                            continue
                        normas_vistas.add(clean_norm)

                        norm_id = _sanitize_id(clean_norm, "norma")
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

                        self.graph.add_edge(inst_id, norm_id, relation="fundamenta_en", weight=1.0)

                    # Procesar y conectar Jurisprudencia CS
                    fallos_vistos: Set[str] = set()
                    for f_text in jurisprudencia_raw:
                        clean_f = f_text.strip(" `[]")
                        if not clean_f or clean_f in fallos_vistos or len(clean_f) < 4:
                            continue
                        fallos_vistos.add(clean_f)

                        fallo_id = _sanitize_id(clean_f, "fallo")
                        if not self.graph.has_node(fallo_id):
                            self.graph.add_node(
                                fallo_id,
                                label=clean_f,
                                node_type="jurisprudencia",
                                file_type="legal_ruling",
                                source_file=rel_path,
                                community=3
                            )
                        self.graph.add_edge(inst_id, fallo_id, relation="criterio_jurisprudencial", weight=1.0)

                    # Extraer y conectar Vías Procesales
                    if operativa_procesal:
                        vias_detectadas = re.findall(
                            r"(?:demanda\s+ordinaria|accion\s+reivindicatoria|recurso\s+de\s+casacion|recurso\s+de\s+apelacion|recurso\s+de\s+proteccion|tutela\s+laboral|juicio\s+ejecutivo|juicio\s+sumario|excepcion\s+dilatoria|excepcion\s+perentoria|procedimiento\s+abreviado|audiencia\s+preparatoria|medida\s+precautoria|medida\s+cautelar)",
                            _normalize_str(operativa_procesal)
                        )
                        for via in set(vias_detectadas):
                            via_id = _sanitize_id(via, "via")
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
                            self.graph.add_edge(inst_id, via_id, relation="via_procesal", weight=1.0)

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

    def _conectar_instituciones_cruzadas(self) -> None:
        """Enlaza instituciones jurídicas que comparten normas clave o se citan dogmáticamente."""
        # Enlace por normas compartidas
        norma_a_insts: Dict[str, List[str]] = {}
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") == "fundamenta_en":
                norma_a_insts.setdefault(v, []).append(u)

        for _norma_node, insts in norma_a_insts.items():
            if len(insts) > 1:
                for i in range(len(insts)):
                    for j in range(i + 1, min(len(insts), i + 4)):
                        if not self.graph.has_edge(insts[i], insts[j]):
                            self.graph.add_edge(
                                insts[i],
                                insts[j],
                                relation="comparte_norma",
                                weight=0.8
                            )

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

        # 1. Coincidencia exacta O(1) en instituciones
        if q_norm in self.instituciones_index:
            return self.instituciones_index[q_norm]

        # 2. Coincidencia en normas
        for name, nid in self.normas_index.items():
            if q_norm in name:
                preds = list(self.graph.predecessors(nid))
                if preds:
                    return preds[0]
                return nid

        # 2.5 Coincidencia por contención o todas las palabras en instituciones canónicas
        # Prioriza la entidad dogmática con mayor grado y penaliza fragmentos no normalizados
        candidatos_sub: List[Tuple[int, int, str]] = []  # (-score, len(label), nid)
        palabras_q_list = [w for w in q_norm.split() if len(w) > 2]

        if len(q_norm) > 3:
            for name, nid in self.instituciones_index.items():
                if q_norm in name or (len(palabras_q_list) > 1 and all(w in name for w in palabras_q_list)):
                    if self.graph.has_node(nid):
                        deg = self.graph.degree(nid)
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
                    preds = list(self.graph.predecessors(nid))
                    if preds:
                        return preds[0]
                return nid

            for lbl_norm, nid in self._label_index.items():
                if q_norm in lbl_norm:
                    if self.graph.has_node(nid):
                        deg = self.graph.degree(nid)
                        score = deg * 10
                        target_nid = nid
                        if self.graph.nodes[nid].get("node_type") == "via_procesal":
                            preds = list(self.graph.predecessors(nid))
                            if preds:
                                target_nid = preds[0]
                                deg = self.graph.degree(target_nid)
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
            mejores.sort(key=lambda nid: (-self.graph.degree(nid), nid))
            return mejores[0]

        # 4. Último recurso: el término puede no nombrar ningún nodo y, aun así, ser el
        # tema de una obra ('compraventa' aparece en 4 tratados sin ser el label de
        # ninguna institución). Se busca en el TEXTO del corpus y se avisa de dónde salió.
        return self._buscar_por_corpus(query)

    def _buscar_por_corpus(self, query: str) -> Optional[str]:
        """
        Resuelve una consulta que no calza con ningún nodo buscándola en el texto de las obras.
        Devuelve la institución mejor conectada entre las obras que la mencionan, y deja un
        aviso: la coincidencia es de texto, no de nombre. Preferible a responder "no encontrado"
        cuando el tema sí está en la doctrina.
        """
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
            key=lambda n: self.graph.degree(n),
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

    def ingerir_codigo_bcn(self, codigo_nombre: str, texto: str,
                           articulos: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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

        extraido = extract_articulos_de_codigo(codigo_nombre, texto, articulos=articulos)
        articulos_detectados = sum(
            1 for _, d in extraido.nodes(data=True) if d.get("node_type") == "articulo_legal"
        )
        if articulos_detectados == 0:
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
            "articulos_detectados": articulos_detectados,
            "nodos_nuevos": nodos_nuevos,
            "enlaces_nuevos": enlaces_nuevos,
            "grafo": {
                "nodos": self.graph.number_of_nodes(),
                "aristas": self.graph.number_of_edges(),
            },
            "advertencias": list(self.advertencias),
        }

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
        if not self.is_built:
            # Artefacto publicado primero (instantáneo); reconstruir desde doctrina es el
            # último recurso: en frío cuesta decenas de segundos.
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        nodo_central = self._buscar_nodo_relevante(query)
        if not nodo_central or not self.graph.has_node(nodo_central):
            return {
                "encontrado": False,
                "query": query,
                "mensaje": f"No se encontró un nodo dogmático conectado para '{query}'.",
                "sugerencias": list(self.instituciones_index.keys())[:5]
            }

        central_data = self.graph.nodes[nodo_central]

        # Extraer ego-subgrafo
        sub_nodes = set([nodo_central])
        current_layer = set([nodo_central])
        for _ in range(max_hops):
            next_layer = set()
            for n in current_layer:
                next_layer.update(self.graph.successors(n))
                next_layer.update(self.graph.predecessors(n))
            sub_nodes.update(next_layer)
            current_layer = next_layer

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
        """Genera diagrama Mermaid interactivo centrado en el subgrafo de la consulta."""
        if not self.is_built:
            # Mismo orden que consultar_subgrafo: artefacto publicado antes de reconstruir.
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        nodo_central = self._buscar_nodo_relevante(query)
        if not nodo_central or not self.graph.has_node(nodo_central):
            return "```mermaid\ngraph TD\n    A[\"No se encontró nodo para la consulta\"]\n```"

        sub_nodes = set([nodo_central])
        current_layer = set([nodo_central])
        for _ in range(max_hops):
            next_layer = set()
            for n in current_layer:
                next_layer.update(self.graph.successors(n))
                next_layer.update(self.graph.predecessors(n))
            sub_nodes.update(next_layer)
            current_layer = next_layer

        lines = [
            "```mermaid",
            "---",
            f"title: Subgrafo de Conocimiento Jurídico — {self.graph.nodes[nodo_central].get('label', query)}",
            "---",
            "graph TD",
            "    %% Clases estilizadas",
            "    classDef central fill:#1a237e,stroke:#3949ab,stroke-width:3px,color:#ffffff,font-weight:bold;",
            "    classDef institucion fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;",
            "    classDef norma fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;",
            "    classDef fallo fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c;",
            "    classDef via fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f;",
            "    classDef autor fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;",
            ""
        ]

        # Nodos
        for nid in sorted(sub_nodes):
            data = self.graph.nodes[nid]
            lbl = data.get("label", nid).replace('"', "'").replace("\n", " ")
            if len(lbl) > 40:
                lbl = lbl[:37] + "..."
            ntype = data.get("node_type", "institucion")
            lines.append(f'    {nid}["{lbl}"]')

            if nid == nodo_central:
                lines.append(f"    class {nid} central;")
            elif ntype in ("institucion", "obra"):
                lines.append(f"    class {nid} institucion;")
            elif ntype == "articulo_legal":
                lines.append(f"    class {nid} norma;")
            elif ntype == "jurisprudencia":
                lines.append(f"    class {nid} fallo;")
            elif ntype == "via_procesal":
                lines.append(f"    class {nid} via;")
            elif ntype == "autor":
                lines.append(f"    class {nid} autor;")

        lines.append("")

        # Aristas
        subgraph = self.graph.subgraph(sub_nodes)
        for u, v, data in subgraph.edges(data=True):
            rel = data.get("relation", "")
            if rel:
                rel_clean = rel.replace("_", " ")
                lines.append(f"    {u} -->|{rel_clean}| {v}")
            else:
                lines.append(f"    {u} --> {v}")

        lines.append("```")
        return "\n".join(lines)

    def encontrar_camino(self, origen: str, destino: str, max_caminos: int = 3) -> Dict[str, Any]:
        """
        Calcula y traza los caminos relacionales mínimos entre dos conceptos, instituciones o normas.
        Permite a LLMs y abogados deducir cadenas de subsunción y argumentación dogmática.
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

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

        undirected = self.graph.to_undirected()

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
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        nodo = self._buscar_nodo_relevante(query)
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
        """
        if not self.is_built:
            if not self.cargar_grafo_json():
                self.construir_grafo_desde_doctrina()

        nodo = self._buscar_nodo_relevante(objetivo)
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

    def guardar_grafo_json(self, filepath: str = DEFAULT_GRAPH_PATH) -> str:
        """Serializa el grafo en formato Node-Link JSON estándar de NetworkX / Graphify.

        Emite una única clave de aristas ("edges" con NetworkX >= 3.6). Duplicar la
        misma lista bajo "edges" y "links" no aportaba compatibilidad real (los
        lectores de este módulo aceptan cualquiera de las dos) y sí inflaba el
        archivo ~39%, además de permitir que ambas copias divergieran al editarse
        sólo una de ellas.
        """
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

    def cargar_grafo_json(self, filepath: Optional[str] = None) -> bool:
        """Carga el grafo serializado desde un archivo JSON para consulta instantánea.

        Sin `filepath` usa DEFAULT_GRAPH_PATH — evaluado en la llamada, no al definir la clase,
        para que las pruebas (y cada runtime) puedan apuntar a otro artefacto.
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

    def integrar_con_graphify(self, graphify_out_path: str = "graphify-doctrinal/graph.json") -> Dict[str, Any]:
        """
        Fusiona el grafo jurídico con el grafo DOCTRINAL de Graphify (graphify-doctrinal/graph.json:
        código histórico más doctrina), que alimenta los visualizadores publicados en Hugging Face.
        El grafo de código local de la CLI no se fusiona: lo diluiría (21.521 contra 3.740 nodos,
        medido el 07-10-2026). La fusión es idempotente.
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
    parser.add_argument("--merge-graphify", action="store_true", help="Fusiona con graphify-doctrinal/graph.json (grafo doctrinal de graphify)")

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
