"""
Open Legal Chile — Motor de Grafo de Caso (case_graph.py)
Construye y actualiza el subgrafo de conocimiento ontológico específico de un caso procesal
utilizando la estructura de LegalGraphify y NetworkX.
Relaciona partes, hechos cronológicos, documentos, normas BCN y fuentes de Hugging Face.
"""

from __future__ import annotations

import os
import re
import json
import html
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import networkx as nx

from citas_legales import detectar_normas


def _sanitizar_id(texto: str, prefijo: str = "") -> str:
    """Genera un identificador alfanumérico limpio para nodos del grafo."""
    norm = re.sub(r"[^\w\d]+", "_", (texto or "").lower()).strip("_")
    if not norm:
        norm = "nodo"
    if norm[0].isdigit():
        norm = f"id_{norm}"
    if prefijo:
        return f"{prefijo}_{norm}"
    return norm


def extraer_entidades_de_markdown(texto: str) -> Dict[str, Any]:
    """Extrae hechos, partes, fechas, montos y normas de un texto Markdown de caso."""
    # Fechas
    fechas = list(set(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", texto)))
    # Montos
    montos = list(set(re.findall(r"\$\s?\d[\d.]{3,}|\b\d[\d.]{4,}\s?(?:pesos|clp)\b", texto, re.IGNORECASE)))
    # RUTs
    ruts = list(set(re.findall(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b", texto)))

    # Normas detectadas
    normas = detectar_normas(texto)

    # Hechos probables: líneas o párrafos que contienen fechas o montos
    lineas = texto.split("\n")
    hechos: List[str] = []
    for linea in lineas:
        l_str = linea.strip().lstrip("#-*> ").strip()
        if len(l_str) > 25 and (any(f in l_str for f in fechas) or any(m in l_str for m in montos)):
            hechos.append(l_str[:250])

    # Partes probables (heurística sobre títulos y encabezados procesales)
    partes: List[Dict[str, str]] = []
    match_dte = re.search(r"(?i)\b(?:demandante|recurrente|solicitante|denunciante)\s*:\s*([^\n,]+)", texto)
    if match_dte:
        partes.append({"rol": "demandante", "nombre": match_dte.group(1).strip()})
    match_dda = re.search(r"(?i)\b(?:demandado|recurrido|denunciado|requerido)\s*:\s*([^\n,]+)", texto)
    if match_dda:
        partes.append({"rol": "demandado", "nombre": match_dda.group(1).strip()})

    return {
        "fechas": fechas,
        "montos": montos,
        "ruts": ruts,
        "normas": normas,
        "hechos": hechos[:15],
        "partes": partes,
    }


class CaseGraphEngine:
    """Motor de grafo ontológico para un caso procesal en Open Legal Chile."""

    def __init__(self, workspace_path: Path | str):
        self.workspace_path = Path(workspace_path)
        self.grafo_dir = self.workspace_path / "grafo"
        self.markdown_dir = self.workspace_path / "markdown"
        self.grafo_dir.mkdir(parents=True, exist_ok=True)
        self.graph = nx.DiGraph()

    def construir_o_actualizar(self, metadatos_caso: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Lee los archivos de markdown/ y construye el grafo de conocimiento del caso."""
        self.graph.clear()
        meta = metadatos_caso or {}
        id_caso = meta.get("id_caso") or self.workspace_path.name

        # Nodo raíz del caso
        nodo_caso = f"caso_{_sanitizar_id(id_caso)}"
        self.graph.add_node(
            nodo_caso,
            label=f"Caso: {meta.get('rol_rit') or id_caso}",
            tipo="caso",
            materia=meta.get("materia", "general"),
            fuero=meta.get("fuero_probable", ""),
            fecha_creacion=meta.get("fecha_creacion", ""),
        )

        if not self.markdown_dir.exists():
            return self._guardar_y_resumir()

        # Recorrer archivos en markdown/
        for md_file in sorted(self.markdown_dir.glob("*.md")):
            nombre_doc = md_file.stem
            texto = md_file.read_text(encoding="utf-8", errors="ignore")
            es_fuente_hf = (md_file.name == "fuentes_hf.md")

            nodo_doc = _sanitizar_id(nombre_doc, "doc")
            tipo_doc = "fuente_huggingface" if es_fuente_hf else "documento_caso"
            self.graph.add_node(
                nodo_doc,
                label=f"Doc: {nombre_doc}",
                tipo=tipo_doc,
                archivo=md_file.name,
                tamanio_caracteres=len(texto),
            )
            self.graph.add_edge(nodo_doc, nodo_caso, relacion="pertenece_a")

            entidades = extraer_entidades_de_markdown(texto)

            # Agregar nodos de partes procesales
            for parte in entidades["partes"]:
                nodo_parte = _sanitizar_id(parte["nombre"], "parte")
                self.graph.add_node(
                    nodo_parte,
                    label=f"{parte['rol'].capitalize()}: {parte['nombre']}",
                    tipo="parte_procesal",
                    rol=parte["rol"],
                )
                self.graph.add_edge(nodo_parte, nodo_caso, relacion="interviene_en")
                self.graph.add_edge(nodo_doc, nodo_parte, relacion="menciona_parte")

            # Agregar nodos de normas legales
            for norma in entidades["normas"]:
                if norma.get("familia") == "codigo":
                    etiqueta_norma = f"{norma['obra'].capitalize()}, Art. {norma.get('articulo', '')}"
                else:
                    etiqueta_norma = f"Ley N° {norma.get('numero', '')}, Art. {norma.get('articulo', '')}"
                nodo_norma = _sanitizar_id(etiqueta_norma, "norma")
                self.graph.add_node(
                    nodo_norma,
                    label=etiqueta_norma,
                    tipo="norma_legal",
                    familia=norma.get("familia", ""),
                )
                self.graph.add_edge(nodo_doc, nodo_norma, relacion="invoca_norma")
                self.graph.add_edge(nodo_norma, nodo_caso, relacion="fundamento_de")

            # Agregar hechos fácticos con fecha
            for idx, hecho in enumerate(entidades["hechos"]):
                nodo_hecho = f"{nodo_doc}_h{idx+1}"
                self.graph.add_node(
                    nodo_hecho,
                    label=hecho[:80] + ("..." if len(hecho) > 80 else ""),
                    texto_completo=hecho,
                    tipo="hecho_factico",
                )
                self.graph.add_edge(nodo_doc, nodo_hecho, relacion="constata_hecho")
                self.graph.add_edge(nodo_hecho, nodo_caso, relacion="hecho_de")

        return self._guardar_y_resumir()

    def _guardar_y_resumir(self) -> Dict[str, Any]:
        """Serializa el grafo en JSON y genera el visualizador HTML."""
        json_path = self.grafo_dir / "grafo_caso.json"
        html_path = self.grafo_dir / "grafo_caso.html"

        try:
            data = nx.node_link_data(self.graph, edges="edges")
        except TypeError:
            data = nx.node_link_data(self.graph)

        # Garantizar compatibilidad con versiones de NetworkX tanto antiguas como modernas
        if "links" in data and "edges" not in data:
            data["edges"] = data["links"]
        elif "edges" in data and "links" not in data:
            data["links"] = data["edges"]

        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Generar vista HTML interactiva
        self._generar_html_interactivo(html_path, data)

        resumen = {
            "total_nodos": self.graph.number_of_nodes(),
            "total_aristas": self.graph.number_of_edges(),
            "tipos_nodos": {},
            "grafo_json": str(json_path),
            "grafo_html": str(html_path),
        }
        for _, n_data in self.graph.nodes(data=True):
            tipo = n_data.get("tipo", "otro")
            resumen["tipos_nodos"][tipo] = resumen["tipos_nodos"].get(tipo, 0) + 1

        return resumen

    def _generar_html_interactivo(self, target_path: Path, data: Dict[str, Any]) -> None:
        """Escribe un archivo HTML interactivo autónomo para explorar el grafo del caso."""
        nodos_json = json.dumps(data.get("nodes", []), ensure_ascii=False)
        aristas = data.get("edges") or data.get("links") or []
        aristas_json = json.dumps(aristas, ensure_ascii=False)

        colores = {
            "caso": "#8B5CF6",
            "documento_caso": "#3B82F6",
            "fuente_huggingface": "#F59E0B",
            "parte_procesal": "#EC4899",
            "hecho_factico": "#10B981",
            "norma_legal": "#6366F1",
            "otro": "#9CA3AF"
        }

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Grafo de Caso — Open Legal Chile</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; }}
    #header {{ padding: 12px 20px; background: #1e293b; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
    h1 {{ font-size: 1.1rem; margin: 0; font-weight: 600; color: #38bdf8; }}
    #stats {{ font-size: 0.85rem; color: #94a3b8; }}
    #legend {{ padding: 8px 20px; background: #1e293b; display: flex; gap: 15px; font-size: 0.8rem; border-bottom: 1px solid #334155; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }}
    #container {{ width: 100vw; height: calc(100vh - 90px); display: flex; }}
    #graph {{ flex: 1; height: 100%; }}
    #details {{ width: 320px; background: #1e293b; border-left: 1px solid #334155; padding: 20px; overflow-y: auto; font-size: 0.85rem; }}
    .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
  </style>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
  <div id="header">
    <h1>⚖️ Grafo de Caso — Open Legal Chile</h1>
    <div id="stats">Nodos: {len(data.get("nodes", []))} | Relaciones: {len(data.get("links", []))}</div>
  </div>
  <div id="legend">
    <span><span class="dot" style="background:#8B5CF6"></span>Caso</span>
    <span><span class="dot" style="background:#3B82F6"></span>Documentos</span>
    <span><span class="dot" style="background:#F59E0B"></span>Hugging Face</span>
    <span><span class="dot" style="background:#EC4899"></span>Partes</span>
    <span><span class="dot" style="background:#10B981"></span>Hechos</span>
    <span><span class="dot" style="background:#6366F1"></span>Normas BCN</span>
  </div>
  <div id="container">
    <div id="graph"></div>
    <div id="details">
      <h3>Detalle del Elemento</h3>
      <p id="detail-content" style="color: #94a3b8;">Haz clic en un nodo para ver sus propiedades jurídicas.</p>
    </div>
  </div>
  <script>
    const rawNodes = {nodos_json};
    const rawLinks = {aristas_json};
    const colores = {json.dumps(colores)};

    const nodes = new vis.DataSet(rawNodes.map(n => ({{
      id: n.id,
      label: n.label || n.id,
      color: colores[n.tipo] || colores.otro,
      font: {{ color: '#f8fafc', size: 12 }},
      shape: n.tipo === 'caso' ? 'star' : n.tipo === 'norma_legal' ? 'box' : 'dot',
      size: n.tipo === 'caso' ? 25 : 15,
      meta: n
    }})));

    const edges = new vis.DataSet(rawLinks.map(l => ({{
      from: l.source,
      to: l.target,
      label: l.relacion || '',
      font: {{ color: '#64748b', size: 9, align: 'middle' }},
      arrows: 'to',
      color: {{ color: '#475569' }}
    }})));

    const container = document.getElementById('graph');
    const network = new vis.Network(container, {{ nodes, edges }}, {{
      physics: {{ solver: 'forceAtlas2Based', stabilization: {{ iterations: 100 }} }},
      interaction: {{ hover: true }}
    }});

    network.on('click', function(params) {{
      if (params.nodes.length > 0) {{
        const nodeId = params.nodes[0];
        const node = nodes.get(nodeId);
        const m = node.meta;
        let html = '<h4>' + (m.label || m.id) + '</h4>';
        html += '<p><strong>Tipo:</strong> ' + (m.tipo || 'N/A') + '</p>';
        for (let k in m) {{
          if (!['id', 'label', 'tipo'].includes(k)) {{
            html += '<p><strong>' + k + ':</strong> ' + m[k] + '</p>';
          }}
        }}
        document.getElementById('detail-content').innerHTML = html;
      }}
    }});
  </script>
</body>
</html>"""
        target_path.write_text(html_content, encoding="utf-8")
