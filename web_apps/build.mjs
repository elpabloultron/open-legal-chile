import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as esbuild from "esbuild";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC_DIR = path.join(__dirname, "src");
const OUT_DIR = path.resolve(__dirname, "..", "mcp_apps");

const APPS = [
  {
    id: "graphify",
    title: "LegalGraphify · Explorador Dogmático (Open Legal Chile)",
    entry: "graphify.js",
  },
  {
    id: "calculadoras",
    title: "Calculadoras Forenses Deterministas (Open Legal Chile)",
    entry: "calculadoras.js",
  },
  {
    id: "expediente",
    title: "Tablero Forense de Expediente y Proveídos OJV (Open Legal Chile)",
    entry: "expediente.js",
  },
];

const BASE_CSS = `
:root {
  --bg-1: var(--color-background-primary, #ffffff);
  --bg-2: var(--color-background-secondary, #f6f7f5);
  --bg-3: var(--color-background-tertiary, #edf2ee);
  --fg-1: var(--color-text-primary, #132219);
  --fg-2: var(--color-text-secondary, #47594e);
  --border: var(--color-border-primary, #d7dfd9);
  --accent: #118d4f;
  --accent-bg: #e8f5ee;
  --danger: var(--color-text-danger, #b42318);
  --danger-bg: var(--color-background-danger, #fef3f2);
  --warn: var(--color-text-warning, #9a6700);
  --warn-bg: var(--color-background-warning, #fff8eb);
  --font: var(--font-sans, system-ui, -apple-system, "Segoe UI", sans-serif);
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: var(--bg-1); color: var(--fg-1);
  font-family: var(--font); font-size: 13.5px; line-height: 1.5;
}
.app-shell { padding: 14px 16px; max-width: 1120px; margin: 0 auto; }
.app-header {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border); margin-bottom: 12px;
}
.app-title { font-size: 16px; font-weight: 700; margin: 0; }
.app-subtitle { font-size: 12px; color: var(--fg-2); margin: 2px 0 0; }
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600; background: var(--accent-bg); color: var(--accent);
  border: 1px solid var(--border);
}
.badge.warn { background: var(--warn-bg); color: var(--warn); }
.badge.danger { background: var(--danger-bg); color: var(--danger); }
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
.card {
  background: var(--bg-2); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px; margin-bottom: 10px;
}
.card h3 { margin: 0 0 8px; font-size: 13.5px; }
.field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 150px; }
label { font-size: 12px; font-weight: 600; color: var(--fg-2); }
input, select, textarea {
  width: 100%; padding: 7px 9px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--bg-1); color: var(--fg-1);
  font-family: inherit; font-size: 13px;
}
textarea { min-height: 76px; resize: vertical; }
button {
  cursor: pointer; padding: 7px 12px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--bg-1); color: var(--fg-1);
  font-family: inherit; font-size: 13px; font-weight: 600;
}
button.primary { background: var(--accent); color: #ffffff; border-color: var(--accent); }
button.tab { background: var(--bg-2); }
button.tab.active { background: var(--accent); color: #ffffff; border-color: var(--accent); }
button:disabled { opacity: 0.55; cursor: not-allowed; }
.kv { display: flex; justify-content: space-between; gap: 12px; padding: 5px 0; border-bottom: 1px dashed var(--border); }
.kv:last-child { border-bottom: none; }
.kv-k { color: var(--fg-2); font-size: 12.5px; }
.kv-v { font-weight: 600; text-align: right; }
.list { display: flex; flex-direction: column; gap: 6px; margin: 0; padding: 0; list-style: none; }
.list-item {
  background: var(--bg-1); border: 1px solid var(--border);
  border-radius: 6px; padding: 8px 10px;
}
.gate {
  margin-top: 12px; padding: 10px 12px; border-radius: 8px;
  background: var(--warn-bg); border: 1px solid var(--border); font-size: 12px; text-align: justify;
}
.status { font-size: 12px; color: var(--fg-2); margin-top: 6px; }
.svg-box { width: 100%; background: var(--bg-1); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
pre.mono {
  white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, monospace;
  font-size: 12px; background: var(--bg-1); border: 1px solid var(--border); padding: 8px; border-radius: 6px; margin: 6px 0 0;
}
`;

function escapeHtmlText(text) {
  return String(text).replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[ch]));
}

fs.mkdirSync(OUT_DIR, { recursive: true });

for (const app of APPS) {
  const entryPath = path.join(SRC_DIR, app.entry);
  if (!fs.existsSync(entryPath)) {
    throw new Error(`Falta archivo fuente MCP App: ${entryPath}`);
  }
  const result = await esbuild.build({
    entryPoints: [entryPath],
    bundle: true,
    write: false,
    format: "iife",
    platform: "browser",
    target: ["es2020"],
    charset: "utf8",
    minify: true,
    legalComments: "none",
  });
  const jsBundle = result.outputFiles[0].text.replace(/<\/script>/gi, "<\\/script>");
  const htmlDoc = [
    "<!DOCTYPE html>",
    '<html lang="es">',
    "<head>",
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    `  <title>${escapeHtmlText(app.title)}</title>`,
    `  <style>${BASE_CSS}</style>`,
    "</head>",
    "<body>",
    '  <div id="app" class="app-shell">Cargando vista jurídica…</div>',
    `  <script>\n${jsBundle}\n  </script>`,
    "</body>",
    "</html>",
  ].join("\n");

  const outFile = path.join(OUT_DIR, `${app.id}.html`);
  fs.writeFileSync(outFile, htmlDoc, "utf8");
  const sizeKb = (Buffer.byteLength(htmlDoc, "utf8") / 1024).toFixed(1);
  console.log(`Built ${path.relative(path.resolve(__dirname, ".."), outFile)} (${sizeKb} KB)`);
}
