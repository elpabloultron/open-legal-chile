import {
  clearNode,
  createGateElement,
  el,
  mountMcpApp,
  renderCitasCard,
  renderKVCard,
} from "./common.js";

mountMcpApp({
  appName: "open-legal-chile-expediente",
  initDom(root, api) {
    const entradaInput = el("textarea", {
      placeholder:
        "Pegue aquí el relato del caso, ruta de carpeta de expediente o texto de un proveído OJV (ej. «Recíbase la causa a prueba» o «Despido trabajador Art. 161 CT»).",
    });
    const fechaNotifInput = el("input", { type: "date", value: new Date().toISOString().slice(0, 10) });
    const procSelect = el("select", {}, [
      el("option", { value: "civil", textContent: "Civil (CPC)" }),
      el("option", { value: "laboral", textContent: "Laboral (CT)" }),
      el("option", { value: "administrativo", textContent: "Administrativo (Ley 19.880)" }),
    ]);
    const statusLine = el("div", { className: "status", textContent: "Listo para clasificar causas o analizar proveídos OJV." });
    const bodyBox = el("div");
    let lastData = null;

    const btnChat = el("button", {
      textContent: "Enviar resumen al chat",
      style: "display:none;",
      onClick: async () => {
        if (!lastData) return;
        const resumen = lastData.resumen || lastData.instruccion_abogado || JSON.stringify(lastData).slice(0, 1200);
        await api.sendUserMessage(`Continúa a partir de este análisis del tablero:\n${resumen}`);
        statusLine.textContent = "Resumen enviado a la conversación.";
      },
    });

    api.onCapabilitiesReady = (caps) => {
      if (caps.message) btnChat.style.display = "inline-block";
    };

    function renderData(data) {
      lastData = data || {};
      clearNode(bodyBox);

      if (data.tipo_tramite || data.cargas_procesales_y_plazos) {
        const sev = String(data.severidad || "MEDIA").toUpperCase();
        const badgeCls = sev.includes("CRÍT") ? "badge danger" : sev.includes("ALTA") ? "badge warn" : "badge";
        bodyBox.appendChild(
          el("div", { className: "card" }, [
            el("div", { className: "row", style: "justify-content:space-between;" }, [
              el("h3", { textContent: data.tipo_tramite || "Proveído analizado" }),
              el("span", { className: badgeCls, textContent: sev }),
            ]),
            el("p", { style: "margin:4px 0 0;", textContent: data.instruccion_abogado || "" }),
          ])
        );

        const plazos = data.cargas_procesales_y_plazos || [];
        if (plazos.length > 0) {
          const list = el("ul", { className: "list" });
          for (const p of plazos) {
            list.appendChild(
              el("li", { className: "list-item" }, [
                el("div", { className: "row", style: "justify-content:space-between;" }, [
                  el("strong", { textContent: p.accion || "Actuación" }),
                  el("span", {
                    className: p.fatal ? "badge danger" : "badge",
                    textContent: p.fatal ? `FATAL · ${p.dias_habiles} días hábiles` : `${p.dias_habiles} días`,
                  }),
                ]),
                el("div", {
                  style: "font-size:12px; color:var(--fg-2); margin-top:4px;",
                  textContent: [
                    p.articulo,
                    p.fecha_vencimiento ? `Vence: ${p.fecha_vencimiento} (${p.dia_semana_vencimiento || ""})` : "",
                    p.estado || "",
                  ].filter(Boolean).join(" · "),
                }),
              ])
            );
          }
          bodyBox.appendChild(el("div", { className: "card" }, [el("h3", { textContent: "Plazos y Cargas Procesales" }), list]));
        }
        return;
      }

      if (data.plan || data.materia || data.guia_inicial) {
        if (data.guia_inicial) {
          bodyBox.appendChild(
            renderKVCard("Mesa de Entrada Lista", [
              ["Estado", data.mensaje || "Ingrese texto o carpeta de expediente"],
              ["Herramientas clave", (data.herramientas_disponibles || []).join(", ")],
            ])
          );
          return;
        }
        bodyBox.appendChild(
          renderKVCard("Carátula Forense de Causa", [
            ["Materia", data.materia_etiqueta || data.materia],
            ["Fuero probable", data.fuero_probable],
            ["Roles/RIT detectados", data.deteccion?.roles],
            ["Instituciones jurídicas", data.instituciones],
          ])
        );

        const faltantes = data.faltantes || [];
        if (faltantes.length > 0) {
          const fl = el("ul", { className: "list" });
          for (const f of faltantes) {
            fl.appendChild(el("li", { className: "list-item", textContent: typeof f === "string" ? f : JSON.stringify(f) }));
          }
          bodyBox.appendChild(el("div", { className: "card" }, [el("h3", { textContent: "Antecedentes faltantes declarados" }), fl]));
        }

        const plan = data.plan || [];
        if (plan.length > 0) {
          const pl = el("ul", { className: "list" });
          for (const step of plan) {
            pl.appendChild(
              el("li", { className: "list-item" }, [
                el("div", { style: "font-weight:700;", textContent: step.herramienta || "Paso" }),
                el("div", { style: "font-size:12px; color:var(--fg-2);", textContent: step.por_que || "" }),
              ])
            );
          }
          bodyBox.appendChild(el("div", { className: "card" }, [el("h3", { textContent: "Plan de Trabajo Sugerido" }), pl]));
        }

        const citasCard = renderCitasCard(data.citas_hf);
        if (citasCard) bodyBox.appendChild(citasCard);
      } else if (data.encontrado === false && data.mensaje) {
        bodyBox.appendChild(el("div", { className: "card" }, [el("p", { textContent: data.mensaje })]));
      }
    }

    root.appendChild(
      el("div", { className: "app-header" }, [
        el("div", {}, [
          el("h1", { className: "app-title", textContent: "Tablero Forense de Causa y Proveídos OJV" }),
          el("p", { className: "app-subtitle", textContent: "Mesa de entrada chilena + cómputo de plazos fatales Art. 66 CPC / Ley N.° 20.886" }),
        ]),
        el("span", { className: "badge", textContent: "OJV · Mesa" }),
      ])
    );

    root.appendChild(
      el("div", { className: "card" }, [
        el("div", { className: "field", style: "margin-bottom:8px;" }, [
          el("label", { textContent: "Relato, ruta de carpeta o texto del proveído judicial" }),
          entradaInput,
        ]),
        el("div", { className: "grid-2", style: "margin-bottom:10px;" }, [
          el("div", { className: "field" }, [el("label", { textContent: "Procedimiento" }), procSelect]),
          el("div", { className: "field" }, [el("label", { textContent: "Fecha de notificación (si es proveído)" }), fechaNotifInput]),
        ]),
        el("div", { className: "row" }, [
          el("button", {
            className: "primary",
            textContent: "Analizar Causa (Mesa de Entrada)",
            onClick: async () => {
              const txt = entradaInput.value.trim();
              if (!txt) return;
              statusLine.textContent = "Clasificando materia y armando plan…";
              const res = await api.callTool("caso_analizar", { entrada: txt });
              renderData(res);
              statusLine.textContent = "Análisis de causa listo.";
            },
          }),
          el("button", {
            textContent: "Analizar Proveído OJV",
            onClick: async () => {
              const txt = entradaInput.value.trim();
              if (!txt) return;
              statusLine.textContent = "Analizando resolución judicial y plazos fatales…";
              const res = await api.callTool("vigilante_analizar_resolucion", {
                resolucion_texto: txt,
                procedimiento: procSelect.value,
                fecha_notificacion: fechaNotifInput.value,
              });
              renderData(res);
              statusLine.textContent = "Análisis de proveído completado.";
            },
          }),
          btnChat,
        ]),
        statusLine,
      ])
    );

    root.appendChild(bodyBox);
    root.appendChild(createGateElement());
    api._renderData = renderData;
    api._entradaInput = entradaInput;
  },
  onToolResult(data) {
    if (this?._renderData) this._renderData(data);
  },
});
