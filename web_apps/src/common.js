import {
  App,
  applyDocumentTheme,
  applyHostStyleVariables,
} from "@modelcontextprotocol/ext-apps";

export const GATE_TEXT =
  "⚖️ Compuerta de Revisión Jurídica (Open Legal Chile): Esta vista interactiva presenta análisis técnico y cómputos deterministas conforme al ordenamiento jurídico de la República de Chile. Todo escrito o actuación procesal debe ser validado por un abogado habilitado antes de su firma e ingreso en la Oficina Judicial Virtual (OJV).";

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "className") node.className = String(v);
    else if (k === "textContent") node.textContent = String(v);
    else if (k === "value") node.value = String(v);
    else if (k === "checked") node.checked = Boolean(v);
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else {
      node.setAttribute(k, String(v));
    }
  }
  const list = Array.isArray(children) ? children : [children];
  for (const child of list) {
    if (child === undefined || child === null || child === false) continue;
    if (typeof child === "string" || typeof child === "number") {
      node.appendChild(document.createTextNode(String(child)));
    } else {
      node.appendChild(child);
    }
  }
  return node;
}

export function svgEl(tag, attrs = {}, children = []) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null) continue;
    node.setAttribute(k, String(v));
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child) node.appendChild(child);
  }
  return node;
}

export function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

export function extractToolData(result) {
  if (!result || typeof result !== "object") return {};
  if (result.structuredContent && typeof result.structuredContent === "object") {
    return result.structuredContent;
  }
  const items = Array.isArray(result.content) ? result.content : [];
  for (const item of items) {
    if (item && item.type === "text" && typeof item.text === "string") {
      try {
        const parsed = JSON.parse(item.text);
        if (parsed && typeof parsed === "object") return parsed;
      } catch (_err) {
        return { text: item.text };
      }
    }
  }
  return {};
}

export function formatValue(val) {
  if (val === null || val === undefined) return "—";
  if (typeof val === "number") return Number.isInteger(val) ? val.toLocaleString("es-CL") : val.toLocaleString("es-CL", { maximumFractionDigits: 2 });
  if (typeof val === "boolean") return val ? "Sí" : "No";
  if (Array.isArray(val)) return val.map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v))).join(", ") || "—";
  if (typeof val === "object") return JSON.stringify(val);
  return String(val);
}

export function renderKVCard(title, pairs) {
  const card = el("div", { className: "card" }, [el("h3", { textContent: title })]);
  for (const [label, value] of pairs) {
    if (value === undefined) continue;
    card.appendChild(
      el("div", { className: "kv" }, [
        el("span", { className: "kv-k", textContent: label }),
        el("span", { className: "kv-v", textContent: formatValue(value) }),
      ])
    );
  }
  return card;
}

export function renderCitasCard(citas) {
  if (!Array.isArray(citas) || citas.length === 0) return null;
  const list = el("ul", { className: "list" });
  for (const c of citas.slice(0, 8)) {
    const label = c.formato || c.identificador || c.fuente || "Fuente";
    const meta = [c.url, c.texto ? String(c.texto).slice(0, 220) : ""].filter(Boolean).join(" · ");
    list.appendChild(
      el("li", { className: "list-item" }, [
        el("div", { style: "font-weight:600; font-size:12.5px;", textContent: label }),
        meta ? el("div", { style: "font-size:11.5px; color:var(--fg-2); margin-top:2px;", textContent: meta }) : null,
      ])
    );
  }
  return el("div", { className: "card" }, [el("h3", { textContent: "Fuentes y Citas Verificables" }), list]);
}

export async function mountMcpApp({ appName, onToolInput, onToolResult, initDom }) {
  const root = document.getElementById("app");
  clearNode(root);

  const app = new App({ name: appName, version: "2.0.0" }, {});
  const capsState = { serverTools: false, message: false, updateModelContext: false };

  const applyThemeFromCtx = (ctx) => {
    if (!ctx) return;
    if (ctx.theme) applyDocumentTheme(ctx.theme);
    if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  };

  const api = {
    app,
    caps: capsState,
    async callTool(name, args = {}) {
      const res = await app.callServerTool({ name, arguments: args });
      return extractToolData(res);
    },
    async attachContext(text) {
      if (!capsState.updateModelContext) return false;
      await app.updateModelContext({ content: [{ type: "text", text }] });
      return true;
    },
    async sendUserMessage(text) {
      if (!capsState.message) return false;
      await app.sendMessage({ role: "user", content: [{ type: "text", text }] });
      return true;
    },
  };

  app.ontoolinput = (params) => {
    if (onToolInput) onToolInput.call(api, params?.arguments || {});
  };
  app.ontoolresult = (result) => {
    if (onToolResult) onToolResult.call(api, extractToolData(result), result);
  };
  app.onhostcontextchanged = (ctx) => applyThemeFromCtx(ctx);
  app.ontoolcancelled = () => {};

  initDom(root, api);

  try {
    await app.connect();
    applyThemeFromCtx(app.getHostContext());
    const hc = app.getHostCapabilities() || {};
    capsState.serverTools = Boolean(hc.serverTools);
    capsState.message = Boolean(hc.message);
    capsState.updateModelContext = Boolean(hc.updateModelContext);
    if (api.onCapabilitiesReady) api.onCapabilitiesReady(capsState);
  } catch (_err) {
    // Vista abierta fuera de un host MCP: mantiene UI visible en modo solo lectura.
    if (api.onStandalone) api.onStandalone();
  }

  return api;
}

export function createGateElement() {
  return el("div", { className: "gate", textContent: GATE_TEXT });
}
