/* ==========================================================================
   Open Legal Chile — Interacciones Estilo Graphify (v2.0.0)
   Header segmentado · Mega-Menú 8 Áreas · Setup Prompt · Viewfinder · FAQ · Cotizador
   ========================================================================== */
(function () {
  "use strict";

  const CONTACT_EMAIL = "pablobenavidesjorquera@gmail.com";
  const AREAS = window.OLC_AREAS_DATA || [];

  const HARNESS_ICONS = {
    antigravity: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3L4.5 20.5h3.4l1.6-4h5l1.6 4h3.4L12 3z" stroke="#60a5fa" stroke-width="1.7" stroke-linejoin="round"/><path d="M10.4 13.4L12 9.2l1.6 4.2h-3.2z" fill="#34d399"/><circle cx="12" cy="4.2" r="1.4" fill="#fbbf24"/></svg>`,
    "claude-code": `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><g stroke="#e07a5f" stroke-width="2" stroke-linecap="round"><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="5.6" y1="5.6" x2="18.4" y2="18.4"/><line x1="18.4" y1="5.6" x2="5.6" y2="18.4"/></g><circle cx="12" cy="12" r="2.2" fill="#e07a5f"/></svg>`,
    codex: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.2c-2.2 0-4.1 1.4-4.7 3.4-2 .4-3.5 2.2-3.5 4.3 0 1.4.7 2.7 1.7 3.5-.4 2 .5 4.1 2.4 5.1 1.7.9 3.8.6 5.2-.7 2 .3 4-.7 4.9-2.5.9-1.8.5-4-.9-5.3.4-2-.5-4.1-2.4-5.1-.8-.4-1.7-.7-2.7-.7z" stroke="#ffffff" stroke-width="1.65"/><polygon points="12,8.4 15.1,10.2 15.1,13.8 12,15.6 8.9,13.8 8.9,10.2" stroke="#4dea9c" stroke-width="1.4" fill="none"/></svg>`,
    hermes: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 8.5c3.5-.5 6.2.8 7.5 3.5H7.2c-1.8 0-3.2-1.4-4.2-3.5z" fill="#fbbf24"/><path d="M21 8.5c-3.5-.5-6.2.8-7.5 3.5h3.3c1.8 0 3.2-1.4 4.2-3.5z" fill="#fbbf24"/><path d="M12 5v14M8.5 14.5h7M9.5 18.5h5" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="5.5" r="1.6" fill="#ffffff"/></svg>`,
    cursor: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><polygon points="12,3 20.5,7.8 20.5,16.2 12,21 3.5,16.2 3.5,7.8" stroke="#ffffff" stroke-width="1.5" fill="rgba(255,255,255,0.08)"/><polygon points="12,3 20.5,7.8 12,12.4 3.5,7.8" fill="rgba(255,255,255,0.28)"/><line x1="12" y1="12.4" x2="12" y2="21" stroke="#4dea9c" stroke-width="1.6"/></svg>`,
    vscode: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M16.8 3.5L21 5.5v13l-4.2 2-7.8-6.2-4.2 3.2-1.8-1.1 3.4-4.4-3.4-4.4 1.8-1.1 4.2 3.2 7.8-6.2z" stroke="#38bdf8" stroke-width="1.6" fill="rgba(56,189,248,0.18)" stroke-linejoin="round"/><path d="M16.8 7.6v8.8L11.5 12l5.3-4.4z" fill="#062314"/></svg>`,
    mcp: `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 15.5l6.5-6.5a2.8 2.8 0 114 4L9.8 17.7" stroke="#4dea9c" stroke-width="1.7" stroke-linecap="round"/><path d="M10.5 9l4-4a2.8 2.8 0 114 4l-6.5 6.5" stroke="#ffffff" stroke-width="1.7" stroke-linecap="round"/><circle cx="6.2" cy="18.2" r="1.5" fill="#4dea9c"/></svg>`
  };

  const SETUP_PRESETS = [
    {
      id: "antigravity",
      name: "Google Antigravity",
      short: "Antigravity",
      cmd: "pip install openlegal-chile && openlegal plugin instalar antigravity"
    },
    {
      id: "claude-code",
      name: "Claude Code",
      short: "Claude Code",
      cmd: "pip install openlegal-chile && openlegal plugin instalar claude-code"
    },
    {
      id: "codex",
      name: "OpenAI Codex",
      short: "Codex",
      cmd: "pip install openlegal-chile && openlegal plugin instalar codex"
    },
    {
      id: "hermes",
      name: "Hermes Agent",
      short: "Hermes",
      cmd: "pip install openlegal-chile && openlegal plugin instalar hermes"
    },
    {
      id: "cursor",
      name: "Cursor",
      short: "Cursor",
      cmd: "pip install openlegal-chile && openlegal plugin instalar cursor"
    },
    {
      id: "vscode",
      name: "VS Code",
      short: "VS Code",
      cmd: "pip install openlegal-chile && openlegal plugin instalar vscode"
    },
    {
      id: "mcp",
      name: "Auto-detectar todos los harnesses",
      short: "Todos (Auto)",
      cmd: "pip install openlegal-chile && openlegal plugin instalar"
    }
  ];

  function escHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ------------------------------------------------------------------------
     1. HEADER ESTILO GRAPHIFY CON BARRA SEGMENTADA Y MEGA-MENÚ 8 ÁREAS
     ------------------------------------------------------------------------ */
  function renderHeader() {
    const mount = document.getElementById("siteHeader");
    if (!mount) return;
    const activePage = mount.dataset.page || "home";

    const megaCards = AREAS.map((a, idx) => `
      <a class="op-mega-card" href="areas.html#${escHtml(a.id)}">
        <span class="op-mega-title">
          <span>${escHtml(a.name)}</span>
          <span class="op-mega-num">0${idx + 1}</span>
        </span>
        <span class="op-mega-desc">${escHtml(a.tagline)}</span>
      </a>
    `).join("");

    const mobileAreas = AREAS.map((a) => `
      <a class="sheet-area" href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a>
    `).join("");

    mount.className = "op-header";
    mount.innerHTML = `
      <a class="op-logo" href="index.html" aria-label="Open Legal Chile — Inicio">
        <svg width="26" height="26" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <polygon points="14,2 25,8.5 25,19.5 14,26 3,19.5 3,8.5" stroke="currentColor" stroke-width="2" fill="none"/>
          <circle cx="14" cy="9" r="2.2" fill="currentColor"/>
          <circle cx="8.5" cy="18" r="2.2" fill="currentColor"/>
          <circle cx="19.5" cy="18" r="2.2" fill="currentColor"/>
          <line x1="14" y1="9" x2="8.5" y2="18" stroke="currentColor" stroke-width="1.6"/>
          <line x1="14" y1="9" x2="19.5" y2="18" stroke="currentColor" stroke-width="1.6"/>
          <line x1="8.5" y1="18" x2="19.5" y2="18" stroke="currentColor" stroke-width="1.6"/>
        </svg>
        <span class="op-logo-word">Open Legal Chile</span>
      </a>

      <nav class="op-nav" aria-label="Navegación principal">
        <div class="op-nav-item" id="areasDropdown">
          <button type="button" class="op-nav-trigger ${activePage === "areas" ? "active" : ""}" id="areasTrigger" aria-expanded="false" aria-haspopup="true">
            <span>Áreas del Derecho</span>
            <svg class="op-chevron" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
          </button>
          <div class="op-mega" role="menu" aria-label="Menú por las 8 Áreas del Derecho">
            <div class="op-mega-head">
              <span class="op-eyebrow">Menú por área · 8 disciplinas</span>
              <a href="areas.html" style="font-size:12.5px; font-weight:600; color:var(--green);">Ver las 8 áreas →</a>
            </div>
            <div class="op-mega-grid">${megaCards}</div>
            <div class="op-mega-foot">
              <span>Plataforma gratis (Apache 2.0) · Talleres y despliegue por área</span>
              <a class="pill primary sm" href="capacitaciones.html#cotizacion">Pide tu cotización</a>
            </div>
          </div>
        </div>
        <div class="op-nav-item"><a class="op-nav-link ${activePage === "home" ? "active" : ""}" href="index.html#como-funciona">Cómo funciona</a></div>
        <div class="op-nav-item"><a class="op-nav-link ${activePage === "capacitaciones" ? "active" : ""}" href="capacitaciones.html">Capacitaciones</a></div>
        <div class="op-nav-item"><a class="op-nav-link ${activePage === "demos" ? "active" : ""}" href="demos.html">Laboratorio</a></div>
        <div class="op-nav-item"><a class="op-nav-link ${activePage === "tecnologia" ? "active" : ""}" href="tecnologia.html">Tecnología</a></div>
      </nav>

      <div class="op-right">
        <a class="op-gh-badge" href="https://github.com/elpabloultron/open-legal-chile" target="_blank" rel="noreferrer" aria-label="Repositorio Open Legal Chile en GitHub">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a12 12 0 00-3.79 23.39c.6.11.82-.26.82-.58v-2.02c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.33-1.76-1.33-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 016 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.49 5.92.43.37.82 1.1.82 2.22v3.29c0 .32.22.7.83.58A12 12 0 0012 .5z"/></svg>
          <span>v2.0.0</span>
        </a>
        <a class="pill ghost sm" href="index.html#instalar">Instalar plugin</a>
        <a class="pill primary sm" href="capacitaciones.html#cotizacion">Pide tu cotización</a>
        <button type="button" class="nav-burger" id="navBurger" aria-expanded="false" aria-label="Abrir menú">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
      </div>
    `;

    // Hoja móvil (nav-sheet)
    let sheet = document.getElementById("navSheet");
    if (!sheet) {
      sheet = document.createElement("div");
      sheet.id = "navSheet";
      sheet.className = "nav-sheet";
      mount.insertAdjacentElement("afterend", sheet);
    }
    sheet.innerHTML = `
      <div class="sheet-links">
        <a class="sheet-link" href="areas.html">Áreas del Derecho (8)</a>
        <div class="sheet-areas-grid">${mobileAreas}</div>
        <a class="sheet-link" href="index.html#como-funciona">Cómo funciona</a>
        <a class="sheet-link" href="capacitaciones.html">Capacitaciones y Despliegue</a>
        <a class="sheet-link" href="demos.html">Laboratorio (Baremo y Grado)</a>
        <a class="sheet-link" href="tecnologia.html">Tecnología y 112 Herramientas MCP</a>
        <a class="sheet-link" href="index.html#instalar">Instalar el plugin completo</a>
        <div style="margin-top:12px;">
          <a class="pill primary lg" style="width:100%;" href="capacitaciones.html#cotizacion">Pide tu cotización →</a>
        </div>
      </div>
    `;

    // Scroll state sobre hero verde
    function onScroll() {
      mount.classList.toggle("scrolled", window.scrollY > 36);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    // Mega-menú hover + click
    const dropdown = document.getElementById("areasDropdown");
    const trigger = document.getElementById("areasTrigger");
    let timer = null;
    function setOpen(open) {
      if (!dropdown || !trigger) return;
      dropdown.classList.toggle("open", open);
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    }
    if (dropdown && trigger) {
      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        setOpen(!dropdown.classList.contains("open"));
      });
      dropdown.addEventListener("mouseenter", () => {
        clearTimeout(timer);
        setOpen(true);
      });
      dropdown.addEventListener("mouseleave", () => {
        timer = setTimeout(() => setOpen(false), 180);
      });
      document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) setOpen(false);
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") setOpen(false);
      });
    }

    // Burger móvil
    const burger = document.getElementById("navBurger");
    if (burger && sheet) {
      burger.addEventListener("click", () => {
        const open = sheet.classList.toggle("open");
        burger.setAttribute("aria-expanded", open ? "true" : "false");
      });
      sheet.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", () => {
          sheet.classList.remove("open");
          burger.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* ------------------------------------------------------------------------
     2. HERO «COPIAR INSTALACIÓN» + LOGOS INTERACTIVOS DE HARNESSES
     ------------------------------------------------------------------------ */
  function initHeroSetupPrompt() {
    const control = document.getElementById("heroSetupControl");
    const copyBtn = document.getElementById("heroSetupCopy");
    const copyLabel = document.getElementById("heroSetupLabel");
    const toggleBtn = document.getElementById("heroSetupToggle");
    const menu = document.getElementById("heroSetupMenu");
    const heroLogos = document.getElementById("heroHarnessLogos");
    const ctaBadges = document.getElementById("ctaHarnessBadges");
    const ctaCmdCode = document.getElementById("ctaCmdCode");
    const ctaCopyBtn = document.getElementById("ctaCopyBtn");

    let current = SETUP_PRESETS[0];

    function selectPreset(id) {
      const found = SETUP_PRESETS.find((x) => x.id === id);
      if (!found) return;
      current = found;
      if (copyLabel) copyLabel.textContent = `COPIAR PLUGIN · ${current.short.toUpperCase()}`;
      if (ctaCmdCode) ctaCmdCode.textContent = current.cmd;
      if (ctaCopyBtn) ctaCopyBtn.setAttribute("data-copy", current.cmd);
      renderAll();
    }

    function renderAll() {
      if (menu) {
        menu.innerHTML = SETUP_PRESETS.map((p) => `
          <button type="button" class="setup-option ${p.id === current.id ? "active" : ""}" data-preset="${p.id}">
            <span style="display:inline-flex; align-items:center; gap:8px;">
              <span style="width:16px; height:16px; display:inline-block;">${HARNESS_ICONS[p.id] || ""}</span>
              <span>${escHtml(p.name)}</span>
            </span>
            <span style="color:var(--mint); font-size:10px;">${p.id === current.id ? "activo" : "elegir"}</span>
          </button>
        `).join("");
        menu.querySelectorAll("[data-preset]").forEach((btn) => {
          btn.addEventListener("click", () => {
            selectPreset(btn.dataset.preset);
            menu.classList.remove("open");
          });
        });
      }

      if (heroLogos) {
        heroLogos.innerHTML = SETUP_PRESETS.map((p) => `
          <button type="button" class="harness-logo-btn ${p.id === current.id ? "active" : ""}" data-logo-preset="${p.id}" aria-label="Configurar para ${escHtml(p.name)}">
            ${HARNESS_ICONS[p.id] || ""}
            <span class="harness-tooltip">${escHtml(p.name)}</span>
          </button>
        `).join("") + `<span class="harness-more-tag">+5 más</span>`;

        heroLogos.querySelectorAll("[data-logo-preset]").forEach((btn) => {
          btn.addEventListener("click", () => selectPreset(btn.dataset.logoPreset));
        });
      }

      if (ctaBadges) {
        ctaBadges.innerHTML = SETUP_PRESETS.map((p) => `
          <button type="button" class="harness-inline-badge ${p.id === current.id ? "active" : ""}" data-cta-preset="${p.id}">
            <span style="display:inline-grid; place-items:center; width:18px; height:18px; background:#062314; border-radius:2px; padding:2px;">${HARNESS_ICONS[p.id] || ""}</span>
            <span>${escHtml(p.short)}</span>
          </button>
        `).join("");
        ctaBadges.querySelectorAll("[data-cta-preset]").forEach((btn) => {
          btn.addEventListener("click", () => selectPreset(btn.dataset.ctaPreset));
        });
      }
    }

    if (toggleBtn && menu && control) {
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        menu.classList.toggle("open");
      });
      document.addEventListener("click", (e) => {
        if (!control.contains(e.target) && !menu.contains(e.target)) {
          menu.classList.remove("open");
        }
      });
    }

    if (copyBtn && control) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(current.cmd).then(() => {
          control.setAttribute("data-copied", "true");
          const prev = copyLabel ? copyLabel.textContent : "";
          if (copyLabel) copyLabel.textContent = `✓ COPIADO PARA ${current.short.toUpperCase()}`;
          setTimeout(() => {
            control.setAttribute("data-copied", "false");
            if (copyLabel) copyLabel.textContent = prev;
          }, 2200);
        });
      });
    }

    renderAll();
  }

  /* ------------------------------------------------------------------------
     3. SIMULACIÓN EXPLICATIVA «CÓMO FUNCIONA» (BARRA VERDE + VIEWFINDER)
     ------------------------------------------------------------------------ */
  function renderStepDiagramSvg(stepIdx) {
    const active = (i) => (i === stepIdx ? "#118d4f" : i < stepIdx ? "#062314" : "#b9c4be");
    const fill = (i) => (i === stepIdx ? "#118d4f" : "#ffffff");
    const textCol = (i) => (i === stepIdx ? "#ffffff" : "#062314");
    const nodes = [
      { x: 18, label: "01. PC Local" },
      { x: 148, label: "02. BCN + HF" },
      { x: 278, label: "03. Goldfish" },
      { x: 408, label: "04. Word .docx" }
    ];
    return `
      <svg viewBox="0 0 536 62" width="100%" height="62" role="img" aria-label="Esquema del paso ${stepIdx + 1} de 4">
        <line x1="120" y1="31" x2="148" y2="31" stroke="${active(1)}" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="250" y1="31" x2="278" y2="31" stroke="${active(2)}" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="380" y1="31" x2="408" y2="31" stroke="${active(3)}" stroke-width="1.5" stroke-dasharray="3 3"/>
        ${nodes.map((n, i) => `
          <rect x="${n.x}" y="12" width="108" height="38" rx="2" fill="${fill(i)}" stroke="${active(i)}" stroke-width="1.5"/>
          <text x="${n.x + 54}" y="35" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="${textCol(i)}">${n.label}</text>
        `).join("")}
      </svg>
    `;
  }

  function initHowItWorksSimulation() {
    const pillsWrap = document.getElementById("howAreaPills");
    const stepsWrap = document.getElementById("howStepsList");
    const vfBox = document.getElementById("howViewfinder");
    if (!pillsWrap || !stepsWrap || !vfBox || !AREAS.length) return;

    let areaIdx = 0;
    let stepIdx = 0;
    let autoTimer = null;

    function stopAuto() {
      if (autoTimer) {
        clearInterval(autoTimer);
        autoTimer = null;
      }
      const b = document.getElementById("howAutoBtn");
      if (b) b.textContent = "▶ Recorrido automático";
    }

    function render() {
      const area = AREAS[areaIdx];
      const steps = area.simulation.steps;
      const step = steps[stepIdx];

      pillsWrap.innerHTML = AREAS.map((a, idx) => `
        <button type="button" class="area-pill-btn ${idx === areaIdx ? "active" : ""}" data-how-area="${idx}">
          0${idx + 1}. ${escHtml(a.shortName)}
        </button>
      `).join("");

      pillsWrap.querySelectorAll("[data-how-area]").forEach((btn) => {
        btn.addEventListener("click", () => {
          stopAuto();
          areaIdx = parseInt(btn.dataset.howArea, 10);
          stepIdx = 0;
          render();
        });
      });

      stepsWrap.innerHTML = steps.map((st, idx) => `
        <div class="how-step-item ${idx === stepIdx ? "active" : ""}" data-how-step="${idx}">
          <button type="button" class="how-step-title-btn">
            <span class="how-step-title">${escHtml(st.label)}</span>
          </button>
          <p class="how-step-desc">${escHtml(st.detail)}</p>
        </div>
      `).join("");

      stepsWrap.querySelectorAll("[data-how-step]").forEach((el) => {
        el.addEventListener("click", () => {
          stopAuto();
          stepIdx = parseInt(el.dataset.howStep, 10);
          render();
        });
      });

      vfBox.innerHTML = `
        <div>
          <div class="vf-head">
            <span class="vf-meta">Simulación explicativa · ${escHtml(area.shortName)} · Paso 0${stepIdx + 1}/04</span>
            <span class="vf-local-tag">100 % Local-First</span>
          </div>
          <div class="vf-diagram" style="margin-top:12px;">
            ${renderStepDiagramSvg(stepIdx)}
          </div>
          <div style="margin-top:14px;">
            <div class="vf-scenario"><strong>Escenario:</strong> ${escHtml(area.simulation.scenario)}</div>
            <div class="vf-prompt">${escHtml(area.simulation.prompt)}</div>
            <div class="vf-chips">
              ${step.chips.map((c) => `<span class="vf-chip">${escHtml(c)}</span>`).join("")}
            </div>
          </div>
        </div>
        <div>
          <div class="vf-output">
            <div class="vf-output-lbl">${escHtml(step.outputLabel)}</div>
            <div class="vf-output-txt">${escHtml(step.output)}</div>
          </div>
          <div class="vf-bar">
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button type="button" class="pill ghost sm" id="howPrevBtn">← Anterior</button>
              <button type="button" class="pill ghost sm" id="howNextBtn">Siguiente →</button>
              <button type="button" class="pill ghost sm" id="howAutoBtn">${autoTimer ? "⏸ Pausar" : "▶ Recorrido automático"}</button>
            </div>
            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
              <a href="areas.html#${escHtml(area.id)}" style="font-size:12.5px; font-weight:600; color:var(--ink);">Ver área →</a>
              <a href="capacitaciones.html?area=${encodeURIComponent(area.id)}#cotizacion" class="pill green sm">Pide tu cotización</a>
            </div>
          </div>
        </div>
      `;

      const prevBtn = document.getElementById("howPrevBtn");
      const nextBtn = document.getElementById("howNextBtn");
      const autoBtn = document.getElementById("howAutoBtn");
      if (prevBtn) prevBtn.addEventListener("click", () => { stopAuto(); stepIdx = (stepIdx + 3) % 4; render(); });
      if (nextBtn) nextBtn.addEventListener("click", () => { stopAuto(); stepIdx = (stepIdx + 1) % 4; render(); });
      if (autoBtn) {
        autoBtn.addEventListener("click", () => {
          if (autoTimer) {
            stopAuto();
            return;
          }
          autoBtn.textContent = "⏸ Pausar";
          autoTimer = setInterval(() => {
            stepIdx = (stepIdx + 1) % 4;
            render();
          }, 4200);
        });
      }
    }

    render();
  }

  /* ------------------------------------------------------------------------
     4. ACORDEÓN FAQ ESTILO GRAPHIFY
     ------------------------------------------------------------------------ */
  function initFaq() {
    document.querySelectorAll(".faq-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const row = btn.closest(".faq-row");
        if (!row) return;
        const isOpen = row.classList.toggle("open");
        btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
        const sign = btn.querySelector(".faq-sign");
        if (sign) sign.textContent = isOpen ? "−" : "+";
      });
    });
  }

  /* ------------------------------------------------------------------------
     5. ASISTENTE «PIDE TU COTIZACIÓN» (EXCLUSIVO POR CORREO, SIN PRECIOS)
     ------------------------------------------------------------------------ */
  function initQuoteBuilder() {
    const form = document.getElementById("quoteBuilderForm");
    if (!form) return;

    const orgEl = document.getElementById("qOrg");
    const serviceEl = document.getElementById("qService");
    const modeEl = document.getElementById("qMode");
    const sizeEl = document.getElementById("qSize");
    const notesEl = document.getElementById("qNotes");
    const areasWrap = document.getElementById("qAreasCheckboxes");
    const previewEl = document.getElementById("quotePreviewText");
    const mailtoBtn = document.getElementById("quoteMailtoBtn");
    const copyBtn = document.getElementById("quoteCopyBtn");

    const params = new URLSearchParams(window.location.search);
    const preArea = params.get("area") || "";
    const preService = params.get("servicio") || "";

    if (preService && serviceEl) {
      Array.from(serviceEl.options).forEach((opt) => {
        if (opt.value === preService) serviceEl.value = preService;
      });
    }

    if (areasWrap && AREAS.length) {
      areasWrap.innerHTML = AREAS.map((a) => `
        <label class="area-check-pill">
          <input type="checkbox" name="qArea" value="${escHtml(a.name)}" ${preArea === a.id ? "checked" : ""} />
          <span>${escHtml(a.shortName)}</span>
        </label>
      `).join("");
    }

    function buildSummary() {
      const org = orgEl ? orgEl.value : "Estudio Jurídico";
      const service = serviceEl ? serviceEl.value : "Taller Práctico por Área";
      const mode = modeEl ? modeEl.value : "Online en vivo";
      const size = sizeEl ? sizeEl.value : "6 a 15 personas";
      const notes = notesEl ? notesEl.value.trim() : "";
      const selectedAreas = Array.from(form.querySelectorAll('input[name="qArea"]:checked')).map((i) => i.value);
      const areasTxt = selectedAreas.length ? selectedAreas.join(", ") : "Por definir en reunión inicial";

      const subject = `Solicitud de cotización — ${service} (${org}) · Open Legal Chile`;
      const bodyLines = [
        "Hola Pablo,",
        "",
        "Quisiera pedir una cotización para Open Legal Chile con el siguiente detalle:",
        "",
        `• Organización: ${org}`,
        `• Servicio de interés: ${service}`,
        `• Modalidad preferida: ${mode}`,
        `• Tamaño estimado del equipo: ${size}`,
        `• Áreas del Derecho prioritarias: ${areasTxt}`
      ];
      if (notes) bodyLines.push(`• Contexto u objetivo adicional: ${notes}`);
      bodyLines.push("", "Quedo atento(a) para coordinar alcances y propuesta.", "", "Saludos cordiales,");

      const body = bodyLines.join("\n");
      if (previewEl) previewEl.textContent = `Para: ${CONTACT_EMAIL}\nAsunto: ${subject}\n\n${body}`;
      if (mailtoBtn) mailtoBtn.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      return { subject, body };
    }

    form.addEventListener("input", buildSummary);
    form.addEventListener("change", buildSummary);

    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        const { subject, body } = buildSummary();
        navigator.clipboard.writeText(`Para: ${CONTACT_EMAIL}\nAsunto: ${subject}\n\n${body}`).then(() => {
          const orig = copyBtn.textContent;
          copyBtn.textContent = "✓ Texto copiado";
          setTimeout(() => { copyBtn.textContent = orig; }, 2200);
        });
      });
    }

    buildSummary();
  }

  /* ------------------------------------------------------------------------
     6. FOOTER ESTILO GRAPHIFY
     ------------------------------------------------------------------------ */
  function renderFooter() {
    const mount = document.getElementById("siteFooter");
    if (!mount) return;
    mount.className = "op-footer";
    mount.innerHTML = `
      <div class="wrap">
        <div class="footer-grid">
          <div>
            <a class="op-logo" href="index.html" style="margin-bottom:10px;">
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none" aria-hidden="true">
                <polygon points="14,2 25,8.5 25,19.5 14,26 3,19.5 3,8.5" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="14" cy="9" r="2.2" fill="currentColor"/>
                <circle cx="8.5" cy="18" r="2.2" fill="currentColor"/>
                <circle cx="19.5" cy="18" r="2.2" fill="currentColor"/>
              </svg>
              <span class="op-logo-word">Open Legal Chile</span>
            </a>
            <p style="font-size:13.5px; line-height:1.6; max-width:340px;">
              Suite abierta de inteligencia jurídica y grafo de conocimiento para el Derecho Continental de Chile. Plataforma 100 % gratuita (Apache 2.0) y local; formación práctica y despliegue a medida.
            </p>
            <p style="margin-top:12px; font-family:var(--font-mono); font-size:12px; color:var(--ink);">
              Cotizaciones: <a href="mailto:${CONTACT_EMAIL}" style="color:var(--green); text-decoration:underline;">${CONTACT_EMAIL}</a>
            </p>
          </div>
          <div>
            <div class="footer-col-title">Áreas (01–04)</div>
            <ul class="footer-links">
              ${AREAS.slice(0, 4).map((a) => `<li><a href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a></li>`).join("")}
            </ul>
          </div>
          <div>
            <div class="footer-col-title">Áreas (05–08)</div>
            <ul class="footer-links">
              ${AREAS.slice(4).map((a) => `<li><a href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a></li>`).join("")}
            </ul>
          </div>
          <div>
            <div class="footer-col-title">Producto y Servicios</div>
            <ul class="footer-links">
              <li><a href="capacitaciones.html">Capacitaciones y Despliegue</a></li>
              <li><a href="capacitaciones.html#cotizacion">Pide tu cotización</a></li>
              <li><a href="demos.html">Laboratorio (Baremo y Grado)</a></li>
              <li><a href="tecnologia.html">Tecnología y 112 MCP</a></li>
              <li><a href="https://github.com/elpabloultron/open-legal-chile" target="_blank" rel="noreferrer">GitHub (Apache 2.0)</a></li>
              <li><a href="https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile" target="_blank" rel="noreferrer">Hugging Face Dataset</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <div>Open Legal Chile — Un proyecto open source · Desarrollado por Pablo Benavides J. · Web: <a href="https://elpabloultron.github.io/open-legal-chile/">elpabloultron.github.io/open-legal-chile</a></div>
          <div><a href="mailto:${CONTACT_EMAIL}">${CONTACT_EMAIL}</a> · v2.0.0</div>
        </div>
      </div>
    `;
  }

  function initCopyButtons() {
    document.querySelectorAll("[data-copy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const txt = btn.getAttribute("data-copy") || "";
        navigator.clipboard.writeText(txt).then(() => {
          const orig = btn.textContent;
          btn.textContent = "✓ Copiado";
          setTimeout(() => { btn.textContent = orig; }, 1800);
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderHeader();
    renderFooter();
    initHeroSetupPrompt();
    initHowItWorksSimulation();
    initFaq();
    initQuoteBuilder();
    initCopyButtons();
  });
})();
