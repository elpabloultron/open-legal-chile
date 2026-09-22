"""Vista de los grafos: un HTML que se abre y se mira.

El motor (LegalGraphify) arma grafos; esto los hace visibles. Escribe un archivo HTML
autocontenido —los datos van adentro, la librería de dibujo se baja de un CDN, igual que
graphify-out/graph.html— con nodos coloreados por tipo o comunidad, etiquetas al pasar el mouse y
el detalle de cada nodo.

Dos entradas:

- el grafo del corpus (todo el derecho chileno indexado, o un subgrafo por consulta);
- el grafo de una carpeta de caso: cada documento es un nodo y cada sección se cuelga de él.

Lo que no se puede leer se dice: si la carpeta trae un formato que no se pudo extraer, sale en
«saltados» con su motivo, en vez de desaparecer sin aviso.
"""

from __future__ import annotations

import html as _html
import json
import os
import pathlib
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALIDA_POR_DEFECTO = os.path.join(os.path.expanduser("~"), ".openlegal", "grafos")

COLORES = {
    "obra": "#f2c14e",
    "seccion": "#5ec8e5",
    "institucion": "#9d7bea",
    "norma": "#5ee59d",
    "criterio": "#ef7d9b",
    "documento": "#f2c14e",
    "caso": "#f2c14e",
}

PLANTILLA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>{titulo}</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"
        integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"
        crossorigin="anonymous"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0f0f1a; color: #e8e8f0; font-family: -apple-system, "Segoe UI", sans-serif;
         display: flex; flex-direction: column; height: 100vh; }}
  header {{ padding: 14px 18px; border-bottom: 1px solid #262640; }}
  h1 {{ font-size: 17px; font-weight: 600; }}
  p {{ color: #a9a9c0; font-size: 13px; margin-top: 4px; }}
  #red {{ flex: 1; min-height: 60vh; }}
  footer {{ padding: 10px 18px; border-top: 1px solid #262640; color: #8f8fa8; font-size: 12px;
            display: flex; gap: 16px; flex-wrap: wrap; }}
  .punto {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
</style></head>
<body>
<header>
  <h1>{titulo}</h1>
  <p>{nota}</p>
</header>
<div id="red"></div>
<footer>
  <span><b>{nodos}</b> nodos</span><span><b>{aristas}</b> relaciones</span>
  <span>pasá el mouse por un nodo para ver su detalle · arrastrá para mover · rueda para acercar</span>
  <span id="pista"></span>
  {leyenda}
</footer>
<script>
  const nodos = new vis.DataSet({nodos_json});
  const aristas = new vis.DataSet({aristas_json});
  const opciones = {{
    nodes: {{ shape: "dot", font: {{ color: "#e8e8f0", size: 13, strokeWidth: 3, strokeColor: "#0f0f1a" }},
             borderWidth: 1 }},
    edges: {{ color: {{ color: "#3d3d5c", highlight: "#8ad0ff" }}, arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
             smooth: {{ type: "continuous" }} }},
    physics: {{ enabled: {fisica}, stabilization: {{ iterations: 220 }} }},
    interaction: {{ hover: true, tooltipDelay: 120, navigationButtons: true, keyboard: true }},
    layout: {{ improvedLayout: {mejorado} }}
  }};
  const red = new vis.Network(document.getElementById("red"), {{ nodes: nodos, edges: aristas }}, opciones);

  // Orden: se agrupa por documento (y el color y la zona dicen el área). Cada globo es un
  // documento; el doble clic lo abre y muestra las instituciones de adentro. Con miles de nodos,
  // ver todo suelto no dice nada: agrupado se lee.
  function agruparPor(campo, colorPorArea) {{
    const grupos = {{}};
    nodos.forEach(n => {{ (grupos[n[campo]] ||= []).push(n.id); }});
    Object.entries(grupos).forEach(([nombre, ids]) => {{
      red.cluster({{
        joinCondition: (opciones) => ids.includes(opciones.id),
        clusterNodeProperties: {{
          id: "grupo:" + campo + ":" + nombre,
          label: nombre.length > 42 ? nombre.slice(0, 42) + "…" : nombre,
          title: ids.length + " nodos de este documento",
          shape: "box",
          color: {{ background: "#1c1c33", border: colorPorArea || "#5a5a72" }},
          font: {{ color: "#e8e8f0", size: 14 }},
          borderWidth: 2,
          allowSingleNodeCluster: true,
        }},
      }});
    }});
  }}
  agruparPor("documento");
  red.on("doubleClick", (params) => {{
    if (params.nodes.length === 1 && red.isCluster(params.nodes[0])) {{ red.openCluster(params.nodes[0]); }}
  }});
  document.getElementById("pista") && (document.getElementById("pista").textContent =
    "Cada globo es un documento (con su color de área). Doble clic en un globo para abrir sus instituciones.");
</script>
</body></html>
"""


def _leyenda(grafos: Dict[str, str]) -> str:
    return "".join(
        f'<span><i class="punto" style="background:{color}"></i>{nombre}</span>'
        for nombre, color in sorted(grafos.items())
    )


# Colores por área del derecho. El área de cada nodo sale de su archivo fuente: la carpeta del
# corpus dice el área de los tratados, y el encabezado de cada documento dice la de los apuntes y
# los materiales docentes (que están mezclados en una misma carpeta).
COLORES_AREA = {
    "civil": "#5ec8e5", "penal": "#ef7d9b", "laboral": "#5ee59d", "familia": "#f2c14e",
    "procesal": "#9d7bea", "administrativo": "#f2994a", "constitucional": "#4f9dff",
    "comercial": "#c9c9d6", "judicial": "#8ad0ff", "general": "#8f8fa8", "otros": "#5a5a72",
}


def _areas_del_corpus() -> Dict[str, str]:
    """Devuelve {nombre de archivo: área} leyendo el corpus.

    Primero el encabezado del documento (area: ...), y si no lo trae, la carpeta donde vive.
    """
    import re as _re

    mapa: Dict[str, str] = {}
    for ruta in pathlib.Path(BASE_DIR).joinpath("doctrina").rglob("*.md"):
        area = ""
        try:
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                cabecera = f.read(700)
            encontrado = _re.search(r"^area:\s*(.+)$", cabecera, _re.MULTILINE)
            area = (encontrado.group(1).strip().strip('"').strip("'") if encontrado else "").lower()
        except OSError:
            pass
        if not area:
            partes = [x.lower() for x in ruta.parts]
            for conocida in COLORES_AREA:
                if conocida in partes:
                    area = conocida
                    break
        mapa[ruta.name] = area or "otros"
    return mapa


def _posiciones_por_area(grafo, areas: Dict[str, str]) -> Dict[str, tuple]:
    """Acomoda cada área del derecho en su propia región: se ven como grupos, no como maraña."""
    import math

    import networkx as nx

    del_area: Dict[str, list] = {}
    for nodo in grafo.nodes:
        archivo = str(grafo.nodes[nodo].get("source_file") or "")
        area = areas.get(archivo.rsplit("/", 1)[-1].rsplit("\\", 1)[-1], "")
        del_area.setdefault(area or "otros", []).append(nodo)
    if len(del_area) <= 1:
        return {}

    areas_ordenadas = sorted(del_area.items(), key=lambda kv: -len(kv[1]))
    columnas = max(2, math.ceil(math.sqrt(len(areas_ordenadas))))
    filas = math.ceil(len(areas_ordenadas) / columnas)
    ancho, alto = 4600.0, 3600.0
    ancho_celda, alto_celda = ancho / columnas, alto / filas
    ubicaciones: Dict[str, tuple] = {}
    for i, (area, nodos_del_area) in enumerate(areas_ordenadas):
        fila, columna = divmod(i, columnas)
        sub = grafo.subgraph(nodos_del_area)
        try:
            pos = nx.spring_layout(sub, seed=7, k=0.5 if len(nodos_del_area) < 3000 else 0.25,
                                   iterations=25)
        except Exception:
            return {}
        xs = [p[0] for p in pos.values()] or [0.0]
        ys = [p[1] for p in pos.values()] or [0.0]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        escala = min(ancho_celda / max(1e-9, maxx - minx), alto_celda / max(1e-9, maxy - miny)) * 0.9
        for nodo, (x, y) in pos.items():
            ubicaciones[str(nodo)] = (
                columna * ancho_celda + (x - minx) * escala,
                fila * alto_celda + (y - miny) * escala,
            )
    return ubicaciones


def _posiciones(grafo) -> Dict[str, tuple]:
    """Calcula dónde va cada nodo.

    El visor apaga la física cuando hay muchos nodos (si no, el navegador se arrastra), y sin
    física vis-network necesita coordenadas: si no se las dan, apila todos en el centro y se ve un
    círculo con líneas. Calcularlas una vez acá sale mucho más barato que en el navegador.
    """
    import networkx as nx

    n = grafo.number_of_nodes()
    if n <= 400:  # pocos: la física del visor los acomoda sola
        return {}
    try:
        iteraciones = 60 if n <= 2500 else 25
        pos = nx.spring_layout(grafo, seed=7, k=0.6 if n <= 2500 else 0.3, iterations=iteraciones)
    except Exception:
        return {}  # sin scipy no hay disposición: se avisa en la nota del HTML
    ancho, alto = 4200.0, 3200.0
    return {str(k): (float(v[0]) * ancho, float(v[1]) * alto) for k, v in pos.items()}


def _html_del_grafo(grafo, titulo: str, nota: str, salida: str) -> str:
    """Escribe el HTML y devuelve la ruta."""
    areas_corpus = _areas_del_corpus()
    ubicaciones = _posiciones_por_area(grafo, areas_corpus) or _posiciones(grafo)
    if len(grafo) > 400 and not ubicaciones:
        nota = (nota + "\n\n(Ojo: no se pudo calcular la disposición de los nodos —falta scipy en el "
                "entorno—; el visor los va a amontonar en el centro.)")
    nodos = []
    for n, datos in grafo.nodes(data=True):
        etiqueta = str(datos.get("label") or n)
        tipo = str(datos.get("tipo") or "")
        grado = grafo.degree(n)
        archivo = str(datos.get("source_file") or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        area = areas_corpus.get(archivo, "")
        nodo = {
            "id": str(n),
            "label": etiqueta[:60],
            "title": f"{etiqueta}<br><i>{tipo or 'nodo'}</i> · {grado} conexión(es)",
            "color": COLORES_AREA.get(area) or COLORES.get(tipo, "#c9c9d6"),
            "grupo": area or "otros",
            "documento": archivo or "sin documento",
            "size": 10 + min(22, 3 * grado),
            "value": grado,
        }
        if str(n) in ubicaciones:
            nodo["x"], nodo["y"] = ubicaciones[str(n)]
        nodos.append(nodo)
    aristas = []
    for u, v, datos in grafo.edges(data=True):
        if str(u) in {x["id"] for x in nodos} and str(v) in {x["id"] for x in nodos}:
            aristas.append({"from": str(u), "to": str(v),
                            "title": str(datos.get("tipo") or datos.get("label") or "")})
    hay_areas = len({x.get("grupo") for x in nodos} - {"otros"}) > 1
    if hay_areas:
        leyenda = _leyenda({g: COLORES_AREA.get(g, "#5a5a72") for g in sorted({x["grupo"] for x in nodos})})
        if nota:
            nota += "\n\nCada color es un área del derecho y cada área ocupa su propia región."
    tipos = sorted({x["color"] for x in nodos})
    leyenda = leyenda if hay_areas else _leyenda({("institución" if c == COLORES["institucion"] else
                         "obra / documento" if c == COLORES["obra"] else
                         "sección" if c == COLORES["seccion"] else
                         "norma" if c == COLORES["norma"] else "otro"): c for c in tipos})
    contenido = PLANTILLA.format(
        titulo=_html.escape(titulo),
        nota=_html.escape(nota),
        nodos=len(nodos),
        aristas=len(aristas),
        nodos_json=json.dumps(nodos, ensure_ascii=False),
        aristas_json=json.dumps(aristas, ensure_ascii=False),
        leyenda=leyenda,
        fisica="true" if len(nodos) <= 400 else "false",
        mejorado="true" if len(nodos) <= 150 else "false",
    )
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        f.write(contenido)
    return salida


def ver_corpus(consulta: Optional[str] = None, max_nodos: int = 250,
               salida: Optional[str] = None) -> Dict[str, Any]:
    """Muestra el grafo del corpus (o un subgrafo por consulta) en un HTML que se abre."""
    import legal_graphify as lg

    motor = lg.LegalGraphifyEngine()
    if not motor.cargar_grafo_json():
        return {"error": "no se pudo cargar el grafo del corpus: construilo con "
                         "`python legal_graphify.py --build`"}

    grafo = motor.graph
    muestra = False
    if consulta:
        encontrado = motor._buscar_nodo_relevante(consulta)  # noqa: SLF001 (API interna del motor)
        if not encontrado:
            return {"error": f"no encontré nada en el grafo para «{consulta}»",
                    "sugerencia": "probá con una palabra sola (despido, posesión, nulidad)"}
        vecinos = {encontrado} | set(grafo.successors(encontrado)) | set(grafo.predecessors(encontrado))
        grafo = grafo.subgraph(vecinos).copy()
        titulo = f"Grafo del corpus — subgrafo de «{consulta}»"
    else:
        if grafo.number_of_nodes() > max_nodos:
            import networkx as nx

            try:
                page = nx.pagerank(grafo, alpha=0.85, max_iter=100)
            except Exception:
                page = {n: grafo.degree(n) for n in grafo.nodes}
            top = [n for n, _ in sorted(page.items(), key=lambda x: -x[1])[:max_nodos]]
            elegidos = set(top)
            for n in top:
                elegidos |= {v for v in grafo.successors(n)} & set(top)
            grafo = grafo.subgraph(elegidos).copy()
            muestra = True
        titulo = "El grafo del derecho chileno"

    nota = (f"El corpus completo indexado por LegalGraphify. Acá se muestran {grafo.number_of_nodes()} "
            f"de los nodos más conectados (PageRank) para que se pueda leer." if muestra else
            "El corpus completo indexado por LegalGraphify.")
    archivo = salida or os.path.join(SALIDA_POR_DEFECTO, "corpus.html")
    _html_del_grafo(grafo, titulo, nota, archivo)
    return {"archivo": archivo, "nodos": grafo.number_of_nodes(), "aristas": grafo.number_of_edges(),
            "muestra": muestra, "como_abrirlo": f"abrilo en el navegador: {archivo}"}


def ver_caso(ruta: str, salida: Optional[str] = None) -> Dict[str, Any]:
    """Arma el grafo de una carpeta de caso y lo deja en un HTML que se abre."""
    import tempfile
    from pathlib import Path

    import case_intake
    import legal_graphify as lg

    origen = Path(ruta).expanduser()
    if not origen.exists():
        return {"error": f"no existe la carpeta «{ruta}»"}

    documentos = [a for a in sorted(origen.rglob("*")) if a.is_file()]
    if not documentos:
        return {"error": f"la carpeta «{ruta}» no tiene archivos"}

    leidos: List[Dict[str, Any]] = []
    saltados: List[Dict[str, str]] = []
    with tempfile.TemporaryDirectory() as temporal:
        for i, documento in enumerate(documentos, 1):
            try:
                texto, _, _ = case_intake._texto_de(str(documento))  # noqa: SLF001
            except Exception as e:  # noqa: BLE001 (lo que falle, se dice)
                saltados.append({"archivo": str(documento), "motivo": f"no se pudo leer: {e}"})
                continue
            if not (texto or "").strip():
                saltados.append({"archivo": str(documento), "motivo": "quedó sin texto (¿escaneado sin OCR?)"})
                continue
            # El texto va tal como viene: si el documento trae su título (# ...), el motor lo usa
            # como nombre del nodo; si no lo trae, cae al nombre del archivo. Anteponer un título
            # propio borraba el del documento.
            destino = Path(temporal) / f"{i:02d}_{documento.stem[:50]}.md"
            destino.write_text(texto if texto.lstrip().startswith("#") else f"# {documento.stem}\n\n{texto}\n",
                               encoding="utf-8")
            leidos.append({"archivo": str(documento), "caracteres": len(texto)})

        if not leidos:
            return {"error": "no se pudo leer ningún documento de la carpeta", "saltados": saltados,
                    "que_hacer": "si son escaneados, pasalos antes por el OCR (ocr_extract_pdf)"}

        motor = lg.LegalGraphifyEngine(doctrina_dir=temporal)
        motor.construir_grafo_desde_doctrina()
        grafo = motor.graph
        archivo = salida or os.path.join(SALIDA_POR_DEFECTO, "caso.html")
        _html_del_grafo(grafo, f"Grafo de la carpeta: {origen.name}",
                        f"Cada documento de la carpeta es un nodo y cada sección se cuelga de él. "
                        f"Se leyeron {len(leidos)} de {len(documentos)} archivos.",
                        archivo)
    return {"archivo": archivo, "nodos": grafo.number_of_nodes(), "aristas": grafo.number_of_edges(),
            "documentos_leidos": leidos, "saltados": saltados,
            "como_abrirlo": f"abrilo en el navegador: {archivo}"}
