import {
  clearNode,
  createGateElement,
  el,
  mountMcpApp,
  renderKVCard,
  svgEl,
} from "./common.js";

const TIPO_COLOR = {
  articulo_legal: "#118d4f",
  institucion_dogmatica: "#1d4ed8",
  fallo_judicial: "#9a6700",
  doctrina: "#6d28d9",
};

mountMcpApp({
  appName: "open-legal-chile-graphify",
  initDom(root, api) {
    const queryInput = el("input", {
      type: "text",
      placeholder: "Ej.: simulacion, nulidad, responsabilidad extracontractual, Art. 1545 CC",
      value: "simulacion",
    });
    const hopsSelect = el("select", { style: "max-width: 110px;" }, [
      el("option", { value: "1", textContent: "1 salto" }),
      el("option", { value: "2", textContent: "2 saltos" }),
    ]);
    const statusLine = el("div", { className: "status", textContent: "Listo para consultar LegalGraphify." });
    const bodyBox = el("div");
    const detailBox = el("div");
    let currentData = null;

    const btnCtx = el("button", {
      textContent: "Adjuntar subgrafo al chat",
      style: "display:none;",
      onClick: async () => {
        if (!currentData) return;
        const txt = currentData.subgrafo_resumen_yaml || JSON.stringify(currentData).slice(0, 2000);
        await api.attachContext(`Subgrafo LegalGraphify:\n${txt}`);
        statusLine.textContent = "Contexto adjuntado al próximo mensaje del chat.";
      },
    });

    api.onCapabilitiesReady = (caps) => {
      if (caps.updateModelContext) btnCtx.style.display = "inline-block";
    };

    async function inspectNode(label) {
      if (!label) return;
      statusLine.textContent = `Consultando explicación dogmática de «${label}»…`;
      try {
        const info = await api.callTool("graphify_explicar_institucion", { query: label });
        renderDetail(info);
        statusLine.textContent = `Institución cargada: ${info.label || label}.`;
      } catch (err) {
        statusLine.textContent = `No se pudo explicar nodo: ${err?.message || err}`;
      }
    }

    function renderDetail(info) {
      clearNode(detailBox);
      if (!info || !info.encontrado) {
        detailBox.appendChild(
          el("div", { className: "card" }, [
            el("p", { textContent: info?.mensaje || "Sin ficha detallada para ese nodo." }),
          ])
        );
        return;
      }
      detailBox.appendChild(
        renderKVCard(`Ficha 360° · ${info.label || "Institución"}`, [
          ["Identificador", info.nodo_id],
          ["Tipo", info.tipo],
          ["Comunidad", info.comunidad],
          ["Tendencia jurisprudencial", info.tendencia_jurisprudencial || "Consultar corpus CS/CA"],
        ])
      );
      if (info.explicacion_markdown) {
        detailBox.appendChild(
          el("div", { className: "card" }, [
            el("h3", { textContent: "Síntesis dogmática" }),
            el("pre", { className: "mono", textContent: String(info.explicacion_markdown).slice(0, 2400) }),
          ])
        );
      }
    }

    function renderGraphSvg(centerLabel, vecinos) {
      const width = 680;
      const height = 270;
      const cx = width / 2;
      const cy = height / 2;
      const svg = svgEl("svg", {
        viewBox: `0 0 ${width} ${height}`,
        width: "100%",
        height: String(height),
        role: "img",
        "aria-label": `Subgrafo de ${centerLabel}`,
      });
      const shown = (vecinos || []).slice(0, 10);
      const radius = 102;
      shown.forEach((n, idx) => {
        const angle = (Math.PI * 2 * idx) / Math.max(1, shown.length) - Math.PI / 2;
        const nx = cx + Math.cos(angle) * radius * 1.65;
        const ny = cy + Math.sin(angle) * radius * 0.92;
        svg.appendChild(svgEl("line", { x1: cx, y1: cy, x2: nx, y2: ny, stroke: "#b7c6bc", "stroke-width": "1.5" }));
        const fill = TIPO_COLOR[n.tipo] || "#47594e";
        const g = svgEl("g", { style: "cursor:pointer;" });
        g.addEventListener("click", () => inspectNode(n.label));
        g.appendChild(svgEl("circle", { cx: nx, cy: ny, r: "10", fill }));
        const text = svgEl("text", {
          x: nx,
          y: ny > cy ? ny + 21 : ny - 14,
          "text-anchor": "middle",
          "font-size": "11",
          fill: "currentColor",
        });
        text.textContent = String(n.label || n.id).slice(0, 26);
        g.appendChild(text);
        svg.appendChild(g);
      });
      svg.appendChild(svgEl("circle", { cx, cy, r: "16", fill: "#0b5d34" }));
      const rootTxt = svgEl("text", { x: cx, y: cy + 30, "text-anchor": "middle", "font-size": "12", "font-weight": "700", fill: "currentColor" });
      rootTxt.textContent = String(centerLabel || "Corpus").slice(0, 32);
      svg.appendChild(rootTxt);
      return el("div", { className: "svg-box" }, [svg]);
    }

    function renderData(data) {
      currentData = data || {};
      clearNode(bodyBox);
      clearNode(detailBox);

      if (Array.isArray(currentData.comunidades)) {
        const list = el("ul", { className: "list" });
        for (const com of currentData.comunidades.slice(0, 12)) {
          const reps = (com.representativos || []).slice(0, 4);
          const item = el("li", { className: "list-item" }, [
            el("div", { className: "row", style: "justify-content:space-between;" }, [
              el("strong", { textContent: `Comunidad #${com.comunidad} (${com.area_principal || "general"})` }),
              el("span", { className: "badge", textContent: `${com.tamano || 0} nodos` }),
            ]),
          ]);
          const btnRow = el("div", { className: "row", style: "margin-top:6px;" });
          for (const r of reps) {
            btnRow.appendChild(
              el("button", {
                textContent: String(r),
                onClick: async () => {
                  queryInput.value = String(r);
                  const sg = await api.callTool("graphify_consulta_subgrafo", { query: String(r), max_hops: 1 });
                  renderData(sg);
                },
              })
            );
          }
          item.appendChild(btnRow);
          list.appendChild(item);
        }
        bodyBox.appendChild(
          renderKVCard("Panorama del Corpus LegalGraphify", [
            ["Comunidades totales", currentData.comunidades_totales],
            ["Nodos indexados", currentData.nodos_totales],
          ])
        );
        bodyBox.appendChild(el("div", { className: "card" }, [el("h3", { textContent: "Comunidades estructurales" }), list]));
        return;
      }

      if (!currentData.encontrado) {
        bodyBox.appendChild(
          el("div", { className: "card" }, [
            el("p", { textContent: currentData.mensaje || "Ingrese un concepto o norma chilena para explorar el subgrafo." }),
          ])
        );
        return;
      }

      const info = currentData.subgrafo_info || {};
      const metricas = currentData.metricas_tokens || {};
      bodyBox.appendChild(
        renderKVCard(`Subgrafo: ${currentData.label || queryInput.value}`, [
          ["Nodos del subgrafo", info.total_nodos_subgrafo],
          ["Normas BCN conectadas", info.normas_conectadas],
          ["Fallos CS/CA conectados", info.fallos_conectados],
          ["Reducción de tokens", metricas.porcentaje_ahorro ? `${metricas.porcentaje_ahorro} %` : "99,9 % mediana"],
        ])
      );

      const vecinos = currentData.ppr_vecinos_clave || [];
      if (vecinos.length > 0) {
        bodyBox.appendChild(
          el("div", { className: "card" }, [
            el("h3", { textContent: "Mapa relacional (clic en un nodo para ver ficha dogmática)" }),
            renderGraphSvg(currentData.label, vecinos),
          ])
        );
        const list = el("ul", { className: "list" });
        for (const v of vecinos.slice(0, 12)) {
          list.appendChild(
            el("li", { className: "list-item row", style: "justify-content:space-between;" }, [
              el("div", {}, [
                el("strong", { textContent: v.label || v.id }),
                el("span", { className: "badge", style: "margin-left:8px;", textContent: v.tipo || "nodo" }),
              ]),
              el("button", { textContent: "Explicar 360°", onClick: () => inspectNode(v.label) }),
            ])
          );
        }
        bodyBox.appendChild(el("div", { className: "card" }, [el("h3", { textContent: "Vecinos relevantes (Personalized PageRank)" }), list]));
      }
      if (currentData.subgrafo_resumen_yaml) {
        bodyBox.appendChild(
          el("div", { className: "card" }, [
            el("h3", { textContent: "Ficha sintética" }),
            el("pre", { className: "mono", textContent: currentData.subgrafo_resumen_yaml }),
          ])
        );
      }
    }

    async function runQuery() {
      const q = queryInput.value.trim();
      if (!q) return;
      statusLine.textContent = `Consultando subgrafo de «${q}»…`;
      try {
        const res = await api.callTool("graphify_consulta_subgrafo", {
          query: q,
          max_hops: Number(hopsSelect.value || 1),
        });
        renderData(res);
        statusLine.textContent = "Subgrafo actualizado.";
      } catch (err) {
        statusLine.textContent = `Error al consultar subgrafo: ${err?.message || err}`;
      }
    }

    root.appendChild(
      el("div", { className: "app-header" }, [
        el("div", {}, [
          el("h1", { className: "app-title", textContent: "LegalGraphify · Grafo Multiplex Chileno" }),
          el("p", { className: "app-subtitle", textContent: "Exploración dogmática, normas BCN y fallos por Personalized PageRank" }),
        ]),
        el("span", { className: "badge", textContent: "MCP App ui://" }),
      ])
    );

    root.appendChild(
      el("div", { className: "card" }, [
        el("div", { className: "row" }, [
          queryInput,
          hopsSelect,
          el("button", { className: "primary", textContent: "Consultar Subgrafo", onClick: runQuery }),
          el("button", {
            textContent: "Ver Comunidades",
            onClick: async () => {
              statusLine.textContent = "Cargando comunidades del corpus…";
              const res = await api.callTool("graphify_resumen_comunidades", { top_n: 8 });
              renderData(res);
              statusLine.textContent = "Resumen de comunidades cargado.";
            },
          }),
          btnCtx,
        ]),
        statusLine,
      ])
    );

    root.appendChild(bodyBox);
    root.appendChild(detailBox);
    root.appendChild(createGateElement());

    api._renderData = renderData;
    api._queryInput = queryInput;
  },
  onToolInput(args) {
    if (args?.query && this._queryInput) {
      // handled dynamically via renderData when result arrives
    }
  },
  onToolResult(data) {
    if (this?._renderData) this._renderData(data);
  },
});
