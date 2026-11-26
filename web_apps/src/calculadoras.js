import {
  clearNode,
  createGateElement,
  el,
  mountMcpApp,
  renderCitasCard,
  renderKVCard,
} from "./common.js";

mountMcpApp({
  appName: "open-legal-chile-calculadoras",
  initDom(root, api) {
    let activeTab = "plazos";
    const statusLine = el("div", { className: "status", textContent: "Seleccione una calculadora determinista (cálculo ejecutado en Python/BCN/SII)." });
    const tabsBar = el("div", { className: "row", style: "margin-bottom:10px;" });
    const formCard = el("div", { className: "card" });
    const resultBox = el("div");

    const TABS = [
      { id: "plazos", label: "Plazos Procesales" },
      { id: "finiquito", label: "Finiquito Laboral CT" },
      { id: "cuantias", label: "Cuantías y Alimentos UTM" },
      { id: "indicadores", label: "UF / UTM / Conversor SII" },
    ];

    function renderResult(data) {
      clearNode(resultBox);
      if (!data || typeof data !== "object") return;
      if (data.error) {
        resultBox.appendChild(
          el("div", { className: "card", style: "border-color:var(--danger);" }, [
            el("strong", { style: "color:var(--danger);", textContent: `Error: ${data.error}` }),
          ])
        );
        return;
      }

      if (data.fecha_vencimiento) {
        resultBox.appendChild(
          renderKVCard("Resultado de Plazo Procesal", [
            ["Régimen aplicado", data.regimen],
            ["Fecha notificación", data.fecha_notificacion],
            ["Inicio cómputo", data.fecha_inicio_computo],
            ["Fecha de vencimiento", `${data.fecha_vencimiento} (${data.dia_semana_vencimiento || ""})`],
            ["Estado", data.estado],
            ["Feriados en ventana", data.feriados_en_ventana],
            ["Norma base", data.norma_base],
          ])
        );
      } else if (data.finiquito_base || data.escenario_demanda_judicial) {
        const fb = data.finiquito_base || {};
        const dem = data.escenario_demanda_judicial || {};
        resultBox.appendChild(
          renderKVCard("Liquidación Laboral Determinista", [
            ["Causal", data.causal?.descripcion || data.causal],
            ["Años computables", data.antiguedad?.anios_indemnizables ?? data.antiguedad?.anios_completos],
            ["Base Art. 172 CT (CLP)", data.base_calculo?.base_indemnizacion_clp],
            ["Aviso previo (CLP)", fb.indemnizacion_sustitutiva_aviso_previo_clp],
            ["Años de servicio (CLP)", fb.indemnizacion_anios_servicio_clp],
            ["Feriado proporcional (CLP)", fb.feriado_proporcional_clp],
            ["Total finiquito base (CLP)", fb.total_finiquito_base_clp],
            ["Recargo Art. 168 CT (CLP)", dem.recargo_legal_art_168_clp],
            ["Total escenario demanda (CLP)", dem.total_estimado_demanda_clp],
            ["Caducidad Art. 168 CT", data.caducidad_art_168_ct?.fecha_limite_demanda],
          ])
        );
      } else if (data.pension_minima || data.multa_rango_clp) {
        const pairs = [["Tipo cuantía", data.tipo], ["UTM utilizada (CLP)", data.utm_utilizada]];
        if (data.pension_minima) {
          pairs.push(["Regla mínimo alimentos", data.regla_minimo]);
          pairs.push(["Mínimo (CLP)", data.pension_minima.clp]);
          pairs.push(["Mínimo (UTM)", data.pension_minima.utm]);
        }
        if (data.tope_50_por_ciento_rentas) {
          pairs.push(["Tope 50 % rentas (CLP)", data.tope_50_por_ciento_rentas.clp]);
        }
        if (data.multa_rango_clp) {
          pairs.push(["Grado penal", data.descripcion_grado || data.grado_pena]);
          pairs.push(["Rango días-multa", `${data.rango_dias_multa?.min} a ${data.rango_dias_multa?.max}`]);
          pairs.push(["Monto mínimo (CLP)", data.multa_rango_clp.min]);
          pairs.push(["Monto máximo (CLP)", data.multa_rango_clp.max]);
        }
        resultBox.appendChild(renderKVCard("Cálculo de Cuantías Legales", pairs));
      } else if (data.monto_destino !== undefined || data.uf_actual !== undefined || data.uf_valor !== undefined) {
        resultBox.appendChild(
          renderKVCard("Indicadores SII / Conversión Monetaria", [
            ["Origen", data.monto_origen !== undefined ? `${data.monto_origen} ${data.moneda_origen}` : undefined],
            ["Resultado", data.monto_destino !== undefined ? `${data.monto_destino} ${data.moneda_destino}` : undefined],
            ["Equivalente CLP", data.monto_clp_equivalente],
            ["UF utilizada", data.uf_utilizada ?? data.uf_valor],
            ["UTM utilizada", data.utm_utilizada ?? data.utm_valor],
            ["Fecha referencia", data.fecha_valor ?? data.fecha],
          ])
        );
      } else if (data.calculadoras) {
        resultBox.appendChild(
          renderKVCard("Estación de Calculadoras Listas", [
            ["Feriados del año cargados", data.total_feriados_anio],
            ["Calculadoras disponibles", (data.calculadoras || []).join(", ")],
          ])
        );
      }

      const citasCard = renderCitasCard(data.citas);
      if (citasCard) resultBox.appendChild(citasCard);
    }

    function renderForm() {
      clearNode(formCard);
      for (const btn of tabsBar.querySelectorAll("button.tab")) {
        btn.className = btn.dataset.tab === activeTab ? "tab active" : "tab";
      }

      if (activeTab === "plazos") {
        const fNotif = el("input", { type: "date", value: new Date().toISOString().slice(0, 10) });
        const fDias = el("input", { type: "number", value: "15", min: "1" });
        const fReg = el("select", {}, [
          el("option", { value: "judicial_cpc", textContent: "Judicial CPC (lun-sáb, Art. 66 CPC)" }),
          el("option", { value: "laboral", textContent: "Laboral (lun-sáb, Art. 168/435 CT)" }),
          el("option", { value: "administrativo", textContent: "Administrativo (lun-vie, Art. 25 Ley 19.880)" }),
          el("option", { value: "corridos", textContent: "Días corridos (Protección Art. 20 CPR)" }),
        ]);
        const fSusp = el("input", { type: "number", value: "0", min: "0" });
        formCard.appendChild(
          el("div", { className: "grid-2" }, [
            el("div", { className: "field" }, [el("label", { textContent: "Fecha notificación" }), fNotif]),
            el("div", { className: "field" }, [el("label", { textContent: "Días de plazo" }), fDias]),
            el("div", { className: "field" }, [el("label", { textContent: "Régimen legal" }), fReg]),
            el("div", { className: "field" }, [el("label", { textContent: "Días suspensión DT (si laboral)" }), fSusp]),
          ])
        );
        formCard.appendChild(
          el("div", { className: "row", style: "margin-top:10px;" }, [
            el("button", {
              className: "primary",
              textContent: "Calcular Vencimiento Fatal",
              onClick: async () => {
                statusLine.textContent = "Calculando plazo con feriados legales de Chile…";
                const res = await api.callTool("calcular_plazo_procesal", {
                  fecha_notificacion: fNotif.value,
                  plazo_dias: Number(fDias.value || 1),
                  regimen: fReg.value,
                  dias_suspension_dt: Number(fSusp.value || 0),
                });
                renderResult(res);
                statusLine.textContent = "Cómputo completado.";
              },
            }),
          ])
        );
      } else if (activeTab === "finiquito") {
        const fIng = el("input", { type: "date", value: "2022-03-01" });
        const fTer = el("input", { type: "date", value: new Date().toISOString().slice(0, 10) });
        const fRem = el("input", { type: "number", value: "1500000", min: "1" });
        const fCau = el("select", {}, [
          el("option", { value: "161", textContent: "Art. 161 (Necesidades de la empresa)" }),
          el("option", { value: "159", textContent: "Art. 159 (Término plazo/obra)" }),
          el("option", { value: "160", textContent: "Art. 160 (Causales disciplinarias)" }),
          el("option", { value: "171_autodespido", textContent: "Art. 171 (Despido indirecto / autodespido)" }),
          el("option", { value: "renuncia", textContent: "Renuncia voluntaria" }),
        ]);
        const fUf = el("input", { type: "number", value: "", placeholder: "Opcional (ej. 38500)" });
        const fAfc = el("input", { type: "number", value: "0", min: "0" });
        const fAvi = el("input", { type: "checkbox" });
        formCard.appendChild(
          el("div", { className: "grid-2" }, [
            el("div", { className: "field" }, [el("label", { textContent: "Fecha ingreso" }), fIng]),
            el("div", { className: "field" }, [el("label", { textContent: "Fecha término" }), fTer]),
            el("div", { className: "field" }, [el("label", { textContent: "Última remuneración Art. 172 (CLP)" }), fRem]),
            el("div", { className: "field" }, [el("label", { textContent: "Causal invocada" }), fCau]),
            el("div", { className: "field" }, [el("label", { textContent: "Aporte empleador AFC (CLP)" }), fAfc]),
            el("div", { className: "field" }, [el("label", { textContent: "UF manual (CLP, opcional)" }), fUf]),
          ])
        );
        formCard.appendChild(
          el("div", { className: "row", style: "margin-top:10px;" }, [
            el("label", { className: "row" }, [fAvi, el("span", { textContent: "Empleador otorgó aviso previo (30 días)" })]),
            el("button", {
              className: "primary",
              textContent: "Liquidar Finiquito y Demanda",
              onClick: async () => {
                statusLine.textContent = "Calculando indemnizaciones Arts. 163/168/172 CT…";
                const args = {
                  fecha_ingreso: fIng.value,
                  fecha_termino: fTer.value,
                  remuneracion_mensual_clp: Number(fRem.value || 0),
                  causal: fCau.value,
                  aviso_previo_dado: Boolean(fAvi.checked),
                  aporte_empleador_afc_clp: Number(fAfc.value || 0),
                };
                if (fUf.value.trim()) args.uf_valor = Number(fUf.value);
                const res = await api.callTool("calcular_finiquito_laboral", args);
                renderResult(res);
                statusLine.textContent = "Liquidación completada.";
              },
            }),
          ])
        );
      } else if (activeTab === "cuantias") {
        const fTipo = el("select", {}, [
          el("option", { value: "alimentos_utm", textContent: "Pensión de alimentos UTM (Ley 14.908 / 21.389)" }),
          el("option", { value: "dias_multa_natural", textContent: "Días-multa persona natural (Ley 21.595)" }),
          el("option", { value: "dias_multa_persona_juridica", textContent: "Días-multa persona jurídica (Ley 20.393)" }),
        ]);
        const fImm = el("input", { type: "number", value: "510636" });
        const fHijos = el("input", { type: "number", value: "1", min: "1" });
        const fIng = el("input", { type: "number", value: "1500000" });
        const fUtm = el("input", { type: "number", value: "", placeholder: "Opcional (ej. 67294)" });
        formCard.appendChild(
          el("div", { className: "grid-2" }, [
            el("div", { className: "field" }, [el("label", { textContent: "Tipo cuantía legal" }), fTipo]),
            el("div", { className: "field" }, [el("label", { textContent: "IMM / Ingreso base (CLP)" }), fImm]),
            el("div", { className: "field" }, [el("label", { textContent: "Número de hijos (alimentos)" }), fHijos]),
            el("div", { className: "field" }, [el("label", { textContent: "Ingreso líquido / diario (CLP)" }), fIng]),
            el("div", { className: "field" }, [el("label", { textContent: "UTM manual (CLP, opcional)" }), fUtm]),
          ])
        );
        formCard.appendChild(
          el("div", { className: "row", style: "margin-top:10px;" }, [
            el("button", {
              className: "primary",
              textContent: "Calcular Cuantía Legal",
              onClick: async () => {
                statusLine.textContent = "Calculando cuantía legal…";
                const args = {
                  tipo: fTipo.value,
                  imm_clp: Number(fImm.value || 500000),
                  numero_hijos: Number(fHijos.value || 1),
                  ingreso_liquido_alimentante_clp: Number(fIng.value || 0),
                  ingreso_diario_liquido_clp: Number(fIng.value || 0),
                };
                if (fUtm.value.trim()) args.utm_valor = Number(fUtm.value);
                const res = await api.callTool("calcular_cuantias_legales", args);
                renderResult(res);
                statusLine.textContent = "Cuantía calculada.";
              },
            }),
          ])
        );
      } else {
        const fMonto = el("input", { type: "number", value: "100", step: "any" });
        const fDesde = el("select", {}, [
          el("option", { value: "UF", textContent: "UF" }),
          el("option", { value: "UTM", textContent: "UTM" }),
          el("option", { value: "UTA", textContent: "UTA" }),
          el("option", { value: "CLP", textContent: "CLP" }),
        ]);
        const fHacia = el("select", {}, [
          el("option", { value: "CLP", textContent: "CLP" }),
          el("option", { value: "UF", textContent: "UF" }),
          el("option", { value: "UTM", textContent: "UTM" }),
          el("option", { value: "UTA", textContent: "UTA" }),
        ]);
        const fUf = el("input", { type: "number", value: "", placeholder: "UF manual (opcional)" });
        formCard.appendChild(
          el("div", { className: "grid-2" }, [
            el("div", { className: "field" }, [el("label", { textContent: "Monto" }), fMonto]),
            el("div", { className: "field" }, [el("label", { textContent: "Desde" }), fDesde]),
            el("div", { className: "field" }, [el("label", { textContent: "Hacia" }), fHacia]),
            el("div", { className: "field" }, [el("label", { textContent: "UF manual (opcional)" }), fUf]),
          ])
        );
        formCard.appendChild(
          el("div", { className: "row", style: "margin-top:10px;" }, [
            el("button", {
              className: "primary",
              textContent: "Convertir vía Indicadores SII",
              onClick: async () => {
                statusLine.textContent = "Consultando indicadores SII…";
                const args = { accion: "convertir", monto: Number(fMonto.value || 0), desde: fDesde.value, hacia: fHacia.value };
                if (fUf.value.trim()) args.uf_valor = Number(fUf.value);
                const res = await api.callTool("indicadores_economicos_chile", args);
                renderResult(res);
                statusLine.textContent = "Conversión completada.";
              },
            }),
          ])
        );
      }
    }

    root.appendChild(
      el("div", { className: "app-header" }, [
        el("div", {}, [
          el("h1", { className: "app-title", textContent: "Calculadoras Forenses Deterministas · Chile" }),
          el("p", { className: "app-subtitle", textContent: "Cero aritmética LLM · Feriados oficiales, Arts. 66 CPC, 161-172 CT, Ley 21.595 y SII" }),
        ]),
        el("span", { className: "badge", textContent: "Determinista Python" }),
      ])
    );

    for (const t of TABS) {
      tabsBar.appendChild(
        el("button", {
          className: t.id === activeTab ? "tab active" : "tab",
          "data-tab": t.id,
          textContent: t.label,
          onClick: () => {
            activeTab = t.id;
            renderForm();
          },
        })
      );
    }

    root.appendChild(tabsBar);
    root.appendChild(formCard);
    root.appendChild(statusLine);
    root.appendChild(resultBox);
    root.appendChild(createGateElement());
    renderForm();

    api._handleIncoming = (data) => {
      if (data?.vista && TABS.some((t) => t.id === data.vista)) {
        activeTab = data.vista;
        renderForm();
      } else if (data?.fecha_vencimiento) {
        activeTab = "plazos";
        renderForm();
      } else if (data?.finiquito_base) {
        activeTab = "finiquito";
        renderForm();
      } else if (data?.pension_minima || data?.multa_rango_clp) {
        activeTab = "cuantias";
        renderForm();
      }
      renderResult(data);
    };
  },
  onToolResult(data) {
    if (this?._handleIncoming) this._handleIncoming(data);
  },
});
