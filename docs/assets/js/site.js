/* ==========================================================================
   Open Legal Chile — Navegación Global, Simulación Explicativa y Cotizador
   Contacto exclusivo: pablobenavidesjorquera@gmail.com · Sin precios fijos
   ========================================================================== */
(function () {
  "use strict";

  const CONTACT_EMAIL = "pablobenavidesjorquera@gmail.com";
  const AREAS = window.OLC_AREAS_DATA || [];

  function escHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ------------------------------------------------------------------------
     1. HEADER COMPARTIDO CON MEGA-MENÚ POR 8 ÁREAS
     ------------------------------------------------------------------------ */
  function renderHeader() {
    const mount = document.getElementById("siteHeader");
    if (!mount) return;
    const activePage = mount.dataset.page || "home";

    const megaCards = AREAS.map((a, idx) => `
      <a class="mega-card" href="areas.html#${escHtml(a.id)}">
        <span class="mega-card-title">
          <span>${escHtml(a.name)}</span>
          <span class="mega-card-num">0${idx + 1}</span>
        </span>
        <span class="mega-card-desc">${escHtml(a.tagline)}</span>
      </a>
    `).join("");

    const mobileAreas = AREAS.map((a) => `
      <a class="mobile-area-link" href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a>
    `).join("");

    mount.className = "site-header";
    mount.innerHTML = `
      <div class="container header-inner">
        <a class="brand-link" href="index.html" aria-label="Open Legal Chile — Inicio">
          <span class="brand-mark" aria-hidden="true">§</span>
          <span class="brand-text">
            <span class="brand-name">Open Legal Chile</span>
            <span class="brand-sub">Suite Libre v1.16.0 · Apache 2.0</span>
          </span>
        </a>

        <nav class="main-nav" aria-label="Navegación principal">
          <div class="nav-item" id="areasDropdown">
            <button type="button" class="nav-trigger ${activePage === "areas" ? "active" : ""}" id="areasTrigger" aria-expanded="false" aria-haspopup="true">
              <span>Áreas del Derecho</span>
              <svg class="nav-chevron" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
            </button>
            <div class="mega-menu" role="menu" aria-label="8 Áreas del Derecho Chileno">
              <div class="mega-header">
                <span class="mega-eyebrow">Menú por disciplina jurídica · 8 áreas cubiertas</span>
                <a class="mega-all-link" href="areas.html">Ver las 8 áreas en detalle →</a>
              </div>
              <div class="mega-grid">${megaCards}</div>
              <div class="mega-footer">
                <span>¿Necesitas capacitar a tu equipo en un área específica?</span>
                <a class="btn btn-primary btn-sm" href="capacitaciones.html#cotizacion">Pide tu cotización</a>
              </div>
            </div>
          </div>

          <a class="nav-link ${activePage === "home" ? "active" : ""}" href="index.html#como-funciona">Cómo funciona</a>
          <a class="nav-link ${activePage === "capacitaciones" ? "active" : ""}" href="capacitaciones.html">Capacitaciones</a>
          <a class="nav-link ${activePage === "demos" ? "active" : ""}" href="demos.html">Laboratorio</a>
          <a class="nav-link ${activePage === "tecnologia" ? "active" : ""}" href="tecnologia.html">Tecnología</a>
        </nav>

        <div class="header-actions">
          <a class="btn btn-outline btn-sm" href="index.html#instalar">Instalar gratis</a>
          <a class="btn btn-primary btn-sm" href="capacitaciones.html#cotizacion">Pide tu cotización</a>
          <button type="button" class="mobile-menu-btn" id="mobileMenuBtn" aria-expanded="false" aria-label="Abrir menú">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
        </div>
      </div>

      <div class="mobile-drawer" id="mobileDrawer">
        <div class="mobile-nav-group">
          <a class="mobile-nav-link" href="areas.html">Áreas del Derecho (8)</a>
          <div class="mobile-areas-grid">${mobileAreas}</div>
          <a class="mobile-nav-link" href="index.html#como-funciona">Cómo funciona</a>
          <a class="mobile-nav-link" href="capacitaciones.html">Capacitaciones y Despliegue</a>
          <a class="mobile-nav-link" href="demos.html">Laboratorio Público (Baremo y Grado)</a>
          <a class="mobile-nav-link" href="tecnologia.html">Tecnología y 95 Herramientas MCP</a>
          <a class="mobile-nav-link" href="index.html#instalar">Instalar Gratis (Apache 2.0)</a>
          <div style="margin-top: 12px;">
            <a class="btn btn-primary" style="width:100%;" href="capacitaciones.html#cotizacion">Pide tu cotización</a>
          </div>
        </div>
      </div>
    `;

    const dropdown = document.getElementById("areasDropdown");
    const trigger = document.getElementById("areasTrigger");
    let hoverTimer = null;

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
        clearTimeout(hoverTimer);
        setOpen(true);
      });
      dropdown.addEventListener("mouseleave", () => {
        hoverTimer = setTimeout(() => setOpen(false), 180);
      });
      document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) setOpen(false);
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") setOpen(false);
      });
    }

    const mobileBtn = document.getElementById("mobileMenuBtn");
    const mobileDrawer = document.getElementById("mobileDrawer");
    if (mobileBtn && mobileDrawer) {
      mobileBtn.addEventListener("click", () => {
        const isOpen = mobileDrawer.classList.toggle("open");
        mobileBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });
      mobileDrawer.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", () => {
          mobileDrawer.classList.remove("open");
          mobileBtn.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* ------------------------------------------------------------------------
     2. FOOTER INSTITUCIONAL COMPARTIDO
     ------------------------------------------------------------------------ */
  function renderFooter() {
    const mount = document.getElementById("siteFooter");
    if (!mount) return;
    mount.className = "site-footer";
    mount.innerHTML = `
      <div class="container">
        <div class="footer-grid">
          <div>
            <a class="brand-link" href="index.html" style="margin-bottom: 12px;">
              <span class="brand-mark" style="background: var(--forest-800);">§</span>
              <span class="brand-text">
                <span class="brand-name" style="color: #ffffff;">Open Legal Chile</span>
                <span class="brand-sub" style="color: var(--bronze-200);">Derecho Continental · Chile</span>
              </span>
            </a>
            <p style="font-size: 13.5px; line-height: 1.6; max-width: 340px;">
              Suite abierta de inteligencia jurídica, grafo de conocimiento y conectores oficiales del Estado de Chile. Software 100 % gratuito (Apache 2.0) y local; formación práctica y despliegue privado a medida.
            </p>
            <p style="margin-top: 14px; font-family: var(--font-mono); font-size: 12.5px; color: #ffffff;">
              Contacto comercial: <a href="mailto:${CONTACT_EMAIL}" style="color: var(--bronze-200); text-decoration: underline;">${CONTACT_EMAIL}</a>
            </p>
          </div>

          <div>
            <div class="footer-title">Áreas del Derecho</div>
            <ul class="footer-links">
              ${AREAS.slice(0, 4).map((a) => `<li><a href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a></li>`).join("")}
            </ul>
          </div>

          <div>
            <div class="footer-title">Más disciplinas</div>
            <ul class="footer-links">
              ${AREAS.slice(4).map((a) => `<li><a href="areas.html#${escHtml(a.id)}">${escHtml(a.shortName)}</a></li>`).join("")}
            </ul>
          </div>

          <div>
            <div class="footer-title">Recursos y Servicios</div>
            <ul class="footer-links">
              <li><a href="capacitaciones.html">Capacitaciones y Despliegue</a></li>
              <li><a href="capacitaciones.html#cotizacion">Pide tu cotización</a></li>
              <li><a href="demos.html">Laboratorio (Baremo y Grado)</a></li>
              <li><a href="tecnologia.html">Tecnología y 95 Herramientas</a></li>
              <li><a href="https://github.com/elpabloultron/open-legal-chile" target="_blank" rel="noreferrer">GitHub (Apache 2.0)</a></li>
              <li><a href="https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile" target="_blank" rel="noreferrer">Dataset en Hugging Face</a></li>
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

  /* ------------------------------------------------------------------------
     3. SIMULACIÓN EXPLICATIVA INTERACTIVA POR ÁREA (HERO)
     ------------------------------------------------------------------------ */
  function initExplanatorySimulation() {
    const stage = document.getElementById("explanatorySimStage");
    if (!stage || !AREAS.length) return;

    const tabsEl = document.getElementById("simAreaTabs");
    const scenarioEl = document.getElementById("simScenario");
    const promptEl = document.getElementById("simPrompt");
    const stepperEl = document.getElementById("simStepper");
    const cardEl = document.getElementById("simStepCard");
    const linkAreaEl = document.getElementById("simAreaLink");
    const linkQuoteEl = document.getElementById("simQuoteLink");
    const btnPrev = document.getElementById("simPrevStep");
    const btnNext = document.getElementById("simNextStep");
    const btnAuto = document.getElementById("simToggleAuto");

    let activeAreaIdx = 0;
    let activeStepIdx = 0;
    let autoTimer = null;

    function renderAreaTabs() {
      tabsEl.innerHTML = AREAS.map((a, idx) => `
        <button type="button" class="sim-area-tab ${idx === activeAreaIdx ? "active" : ""}" data-sim-area="${idx}">
          ${escHtml(a.shortName)}
        </button>
      `).join("");

      tabsEl.querySelectorAll("[data-sim-area]").forEach((btn) => {
        btn.addEventListener("click", () => {
          activeAreaIdx = parseInt(btn.dataset.simArea, 10);
          activeStepIdx = 0;
          render();
        });
      });
    }

    function render() {
      const area = AREAS[activeAreaIdx];
      const steps = area.simulation.steps;
      const step = steps[activeStepIdx];

      tabsEl.querySelectorAll(".sim-area-tab").forEach((b, i) => {
        b.classList.toggle("active", i === activeAreaIdx);
      });

      scenarioEl.textContent = `Escenario real (${area.shortName}): ${area.simulation.scenario}`;
      promptEl.textContent = area.simulation.prompt;

      stepperEl.innerHTML = steps.map((s, idx) => `
        <button type="button" class="sim-step-btn ${idx === activeStepIdx ? "active" : ""}" data-sim-step="${idx}">
          <span class="sim-step-num">Paso 0${idx + 1}</span>
          <span class="sim-step-label">${escHtml(s.label)}</span>
        </button>
      `).join("");

      stepperEl.querySelectorAll("[data-sim-step]").forEach((btn) => {
        btn.addEventListener("click", () => {
          activeStepIdx = parseInt(btn.dataset.simStep, 10);
          render();
        });
      });

      cardEl.innerHTML = `
        <div class="sim-card-title">${escHtml(step.title)}</div>
        <p class="sim-card-detail">${escHtml(step.detail)}</p>
        <div class="sim-chips">
          ${step.chips.map((c) => `<span class="sim-chip">${escHtml(c)}</span>`).join("")}
        </div>
        <div class="sim-output">
          <div class="sim-output-label">${escHtml(step.outputLabel)}</div>
          <div class="sim-output-text">${escHtml(step.output)}</div>
        </div>
      `;

      if (linkAreaEl) {
        linkAreaEl.href = `areas.html#${area.id}`;
        linkAreaEl.textContent = `Ver área ${area.shortName} →`;
      }
      if (linkQuoteEl) {
        linkQuoteEl.href = `capacitaciones.html?area=${encodeURIComponent(area.id)}#cotizacion`;
        linkQuoteEl.textContent = `Pide tu cotización (${area.shortName})`;
      }
    }

    function stopAuto() {
      if (autoTimer) {
        clearInterval(autoTimer);
        autoTimer = null;
      }
      if (btnAuto) btnAuto.textContent = "▶ Recorrido automático";
    }

    if (btnPrev) {
      btnPrev.addEventListener("click", () => {
        stopAuto();
        activeStepIdx = (activeStepIdx + 3) % 4;
        render();
      });
    }
    if (btnNext) {
      btnNext.addEventListener("click", () => {
        stopAuto();
        activeStepIdx = (activeStepIdx + 1) % 4;
        render();
      });
    }
    if (btnAuto) {
      btnAuto.addEventListener("click", () => {
        if (autoTimer) {
          stopAuto();
          return;
        }
        btnAuto.textContent = "⏸ Pausar recorrido";
        autoTimer = setInterval(() => {
          activeStepIdx = (activeStepIdx + 1) % 4;
          render();
        }, 4200);
      });
    }

    renderAreaTabs();
    render();
  }

  /* ------------------------------------------------------------------------
     4. ASISTENTE INTERACTIVO «PIDE TU COTIZACIÓN» (EXCLUSIVO POR MAIL)
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
      const size = sizeEl ? sizeEl.value : "6 a 15 participantes";
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
        `• Áreas del Derecho prioritarias: ${areasTxt}`,
      ];
      if (notes) {
        bodyLines.push(`• Contexto u objetivo adicional: ${notes}`);
      }
      bodyLines.push("", "Quedo atento(a) para coordinar alcances y propuesta.", "", "Saludos cordiales,");

      const body = bodyLines.join("\n");
      if (previewEl) {
        previewEl.textContent = `Para: ${CONTACT_EMAIL}\nAsunto: ${subject}\n\n${body}`;
      }
      if (mailtoBtn) {
        mailtoBtn.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      }
      return { subject, body };
    }

    form.addEventListener("input", buildSummary);
    form.addEventListener("change", buildSummary);

    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        const { subject, body } = buildSummary();
        const full = `Para: ${CONTACT_EMAIL}\nAsunto: ${subject}\n\n${body}`;
        navigator.clipboard.writeText(full).then(() => {
          const orig = copyBtn.textContent;
          copyBtn.textContent = "✓ Resumen copiado";
          setTimeout(() => { copyBtn.textContent = orig; }, 2200);
        });
      });
    }

    buildSummary();
  }

  /* ------------------------------------------------------------------------
     5. BOTONES COPIAR COMANDO
     ------------------------------------------------------------------------ */
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
    initExplanatorySimulation();
    initQuoteBuilder();
    initCopyButtons();
  });
})();
