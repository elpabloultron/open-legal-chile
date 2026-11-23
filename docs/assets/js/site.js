/* ==========================================================================
   Open Legal Chile — Interacciones Estilo Graphify (v1.16.0)
   Header segmentado · Mega-Menú 8 Áreas · Setup Prompt · Viewfinder · FAQ · Cotizador
   ========================================================================== */
(function () {
  "use strict";

  const CONTACT_EMAIL = "pablobenavidesjorquera@gmail.com";
  const AREAS = window.OLC_AREAS_DATA || [];

  const SETUP_PRESETS = [
    {
      id: "antigravity",
      name: "Google Antigravity",
      cmd: "pip install openlegal-chile && openlegal instalar --harness antigravity"
    },
    {
      id: "claude",
      name: "Claude Code",
      cmd: "pip install openlegal-chile && openlegal instalar --harness claude"
    },
    {
      id: "cursor",
      name: "Cursor",
      cmd: "pip install openlegal-chile && openlegal instalar --harness cursor"
    },
    {
      id: "vscode",
      name: "VS Code",
      cmd: "pip install openlegal-chile && openlegal instalar --harness vscode"
    },
    {
      id: "codex",
      name: "Codex CLI",
      cmd: "pip install openlegal-chile && openlegal instalar --harness codex"
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
          <span>v1.16.0</span>
        </a>
        <a class="pill ghost sm" href="index.html#instalar">Instalar gratis</a>
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
        <a class="sheet-link" href="tecnologia.html">Tecnología y 95 Herramientas MCP</a>
        <a class="sheet-link" href="index.html#instalar">Instalar gratis (Apache 2.0)</a>
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
     2. HERO «COPIAR PROMPT DE CONFIGURACIÓN» (ESTILO GRAPHIFY)
     ------------------------------------------------------------------------ */
  function initHeroSetupPrompt() {
    const control = document.getElementById("heroSetupControl");
    const copyBtn = document.getElementById("heroSetupCopy");
    const copyLabel = document.getElementById("heroSetupLabel");
    const toggleBtn = document.getElementById("heroSetupToggle");
    const menu = document.getElementById("heroSetupMenu");
    if (!control || !copyBtn || !toggleBtn || !menu) return;

    let current = SETUP_PRESETS[0];

    function renderMenu() {
      menu.innerHTML = SETUP_PRESETS.map((p) => `
        <button type="button" class="setup-option ${p.id === current.id ? "active" : ""}" data-preset="${p.id}">
          <span>${escHtml(p.name)}</span>
          <span style="color:var(--mint); font-size:10px;">${p.id === current.id ? "activo" : "elegir"}</span>
        </button>
      `).join("");
      menu.querySelectorAll("[data-preset]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const found = SETUP_PRESETS.find((x) => x.id === btn.dataset.preset);
          if (found) {
            current = found;
            if (copyLabel) copyLabel.textContent = `COPIAR INSTALACIÓN · ${current.name.toUpperCase()}`;
            renderMenu();
          }
          menu.classList.remove("open");
        });
      });
    }

    toggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.classList.toggle("open");
    });

    document.addEventListener("click", (e) => {
      if (!control.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove("open");
      }
    });

    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(current.cmd).then(() => {
        control.setAttribute("data-copied", "true");
        const prev = copyLabel ? copyLabel.textContent : "";
        if (copyLabel) copyLabel.textContent = `✓ COPIADO: ${current.cmd}`;
        setTimeout(() => {
          control.setAttribute("data-copied", "false");
          if (copyLabel) copyLabel.textContent = prev;
        }, 2400);
      });
    });

    renderMenu();
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
              <li><a href="tecnologia.html">Tecnología y 95 MCP</a></li>
              <li><a href="https://github.com/elpabloultron/open-legal-chile" target="_blank" rel="noreferrer">GitHub (Apache 2.0)</a></li>
              <li><a href="https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile" target="_blank" rel="noreferrer">Hugging Face Dataset</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <div>Open Legal Chile — Un proyecto open source · Desarrollado por Pablo Benavides J. · Web: <a href="https://elpabloultron.github.io/open-legal-chile/">elpabloultron.github.io/open-legal-chile</a></div>
          <div><a href="mailto:${CONTACT_EMAIL}">${CONTACT_EMAIL}</a> · v1.16.0</div>
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
