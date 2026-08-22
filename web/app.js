// Open Legal Chile — Lógica del Cliente Web Frontend

const API_BASE = window.location.origin;

// Tab Navigation
const tabButtons = document.querySelectorAll('.nav-item');
const tabPanes = document.querySelectorAll('.tab-pane');
const pageTitle = document.getElementById('page-title');
const pageDesc = document.getElementById('page-desc');

const tabMeta = {
    'universal': { title: 'Búsqueda Jurídica Universal', desc: 'Consulta simultánea en BCN, Contraloría, Dirección del Trabajo, SMA y TDLC' },
    'leyes': { title: 'Leyes y Códigos de la República', desc: 'Consultas directas a la Biblioteca del Congreso Nacional (BCN Ley Chile)' },
    'cgr': { title: 'Contraloría General de la República', desc: 'Dictámenes jurídicos vinculantes e Informes Finales de Auditoría' },
    'dt': { title: 'Dirección del Trabajo (DT)', desc: 'Dictámenes, Ordinarios y Doctrina Laboral vinculante' },
    'energia': { title: 'Derecho Eléctrico y Energía', desc: 'Capacidad instalada CNE, proyectos en el SEA y discrepancias del Panel de Expertos' },
    'cmf': { title: 'Comisión para el Mercado Financiero', desc: 'Normas de Carácter General (NCG), Circulares y Resoluciones' },
    'sii': { title: 'Servicio de Impuestos Internos', desc: 'Circulares e Instrucciones Tributarias del Director del SII' },
    'sma': { title: 'Superintendencia del Medio Ambiente', desc: 'Procedimientos sancionatorios ambientales y fiscalizaciones SNIFA' },
    'tdlc': { title: 'Tribunal de Libre Competencia', desc: 'Sentencias contenciosas e Instrucciones de Carácter General (DL 211)' },
    'config': { title: 'Configuración & Seguridad de API Keys', desc: 'Administración de credenciales protegidas en archivo .env' }
};

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabKey = btn.getAttribute('data-tab');
        
        tabButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));
        
        btn.classList.add('active');
        const activePane = document.getElementById(`tab-${tabKey}`);
        if (activePane) activePane.classList.add('active');
        
        if (tabMeta[tabKey]) {
            pageTitle.textContent = tabMeta[tabKey].title;
            pageDesc.textContent = tabMeta[tabKey].desc;
        }

        if (tabKey === 'config') checkConfigStatus();
    });
});

// Helper Fetch
async function apiGet(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        return await res.json();
    } catch (e) {
        console.error("API Error:", e);
        return { error: e.message };
    }
}

// 1. Búsqueda Universal
const universalQuery = document.getElementById('universal-query');
const btnUniversal = document.getElementById('btn-universal-search');
const universalResults = document.getElementById('universal-results');
const universalLoading = document.getElementById('universal-loading');

async function performUniversalSearch(query) {
    if (!query) return;
    universalLoading.classList.remove('hidden');
    universalResults.innerHTML = '';

    const data = await apiGet(`/api/buscar?q=${encodeURIComponent(query)}`);
    universalLoading.classList.add('hidden');

    let html = '';

    // CGR Results
    if (data.cgr && data.cgr.length > 0) {
        data.cgr.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-cgr">Contraloría (CGR)</span>
                    <h4 class="card-title">Dictamen CGR N° ${item.docId}</h4>
                    <p class="card-desc">${item.materia || item.texto.substring(0, 180) + '...'}</p>
                    <div class="card-meta">
                        <span>📅 ${item.fecha || 'Oficial'}</span>
                        ${item.pdfUrl ? `<a href="${item.pdfUrl}" target="_blank" class="card-link">📄 Ver PDF</a>` : ''}
                    </div>
                </div>
            `;
        });
    }

    // DT Results
    if (data.dt && data.dt.length > 0) {
        data.dt.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-dt">Dirección del Trabajo</span>
                    <h4 class="card-title">${item.titulo}</h4>
                    <p class="card-desc">${item.doctrina ? item.doctrina.substring(0, 200) + '...' : (item.materias || '')}</p>
                    <div class="card-meta">
                        <span>📌 DT Laboral</span>
                        <a href="${item.url}" target="_blank" class="card-link">🔗 Ficha DT</a>
                    </div>
                </div>
            `;
        });
    }

    // TDLC Results
    if (data.tdlc && data.tdlc.length > 0) {
        data.tdlc.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-tdlc">Libre Competencia (TDLC)</span>
                    <h4 class="card-title">${item.titulo}</h4>
                    <p class="card-desc">Sentencia o pronunciamiento en materia de libre competencia.</p>
                    <div class="card-meta">
                        <span>📅 ${item.fecha || ''}</span>
                        <a href="${item.link}" target="_blank" class="card-link">🔗 Sentencia TDLC</a>
                    </div>
                </div>
            `;
        });
    }

    // SMA Results
    if (data.sma && data.sma.length > 0) {
        data.sma.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-sma">Ambiental (SMA)</span>
                    <h4 class="card-title">[${item.expediente}] ${item.titular}</h4>
                    <p class="card-desc">Unidad: ${item.unidadFiscalizable} (${item.categoria}) | Estado: ${item.estado}</p>
                    <div class="card-meta">
                        <span>📍 ${item.region}</span>
                        <a href="${item.fichaUrl}" target="_blank" class="card-link">🔗 Ficha SNIFA</a>
                    </div>
                </div>
            `;
        });
    }

    if (!html) {
        html = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No se encontraron resultados para "${query}". Intenta con otros términos.</div>`;
    }

    universalResults.innerHTML = html;
}

btnUniversal.addEventListener('click', () => performUniversalSearch(universalQuery.value));
universalQuery.addEventListener('keypress', (e) => { if (e.key === 'Enter') performUniversalSearch(universalQuery.value); });

function quickSearch(tag) {
    universalQuery.value = tag;
    performUniversalSearch(tag);
}

// 2. BCN Leyes y Códigos
const bcnSelect = document.getElementById('bcn-codigo-select');
const bcnArtInput = document.getElementById('bcn-art-input');
const btnBcn = document.getElementById('btn-bcn-search');
const bcnResults = document.getElementById('bcn-results');

btnBcn.addEventListener('click', async () => {
    const cod = bcnSelect.value;
    const art = bcnArtInput.value.trim();
    bcnResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando BCN Ley Chile...</span></div>';

    const data = await apiGet(`/api/bcn/codigo?nombre=${cod}&art=${encodeURIComponent(art)}`);
    if (data.error) {
        bcnResults.innerHTML = `<div style="color: var(--accent-rose);">${data.error}</div>`;
        return;
    }

    if (art) {
        bcnResults.innerHTML = `
            <h3>${data.codigo} — Artículo ${data.articulo}</h3>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">📅 Versión vigente BCN: ${data.fechaVersion || 'Oficial'}</div>
            <div class="doc-text">${data.texto || 'Texto no disponible'}</div>
        `;
    } else {
        bcnResults.innerHTML = `
            <h3>${data.titulo}</h3>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">Total Artículos indexados: ${Object.keys(data.articulos || {}).length} | Versión: ${data.fechaVersion}</div>
            <p>Selecciona o ingresa un artículo específico arriba para ver su redacción oficial.</p>
        `;
    }
});

// 3. Contraloría (CGR)
const cgrSourceSelect = document.getElementById('cgr-source-select');
const cgrQueryInput = document.getElementById('cgr-query-input');
const btnCgr = document.getElementById('btn-cgr-search');
const cgrResults = document.getElementById('cgr-results');

btnCgr.addEventListener('click', async () => {
    const src = cgrSourceSelect.value;
    const q = cgrQueryInput.value.trim() || 'compras publicas';
    cgrResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando sistema de la Contraloría...</span></div>';

    const data = await apiGet(`/api/cgr?q=${encodeURIComponent(q)}&source=${src}`);
    let html = `<div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">Total registros encontrados: <strong>${data.total || 0}</strong></div>`;

    if (data.resultados && data.resultados.length > 0) {
        data.resultados.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-cgr">${src === 'auditoria' ? 'Informe de Auditoría' : 'Dictamen CGR'}</span>
                    <h4 class="card-title">${src === 'auditoria' ? item.nombre : `Dictamen CGR N° ${item.docId}`}</h4>
                    <p class="card-desc">${item.materia || item.texto.substring(0, 250) + '...'}</p>
                    <div class="card-meta">
                        <span>📅 Fecha: ${item.fecha}</span>
                        ${item.pdfUrl ? `<a href="${item.pdfUrl}" target="_blank" class="card-link">📄 Descargar PDF Oficial</a>` : ''}
                    </div>
                </div>
            `;
        });
    } else {
        html += '<div>No se encontraron dictámenes con ese criterio.</div>';
    }
    cgrResults.innerHTML = html;
});

// 4. Dirección del Trabajo (DT)
const dtQueryInput = document.getElementById('dt-query-input');
const btnDt = document.getElementById('btn-dt-search');
const dtResults = document.getElementById('dt-results');

btnDt.addEventListener('click', async () => {
    const q = dtQueryInput.value.trim() || '344';
    dtResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando base doctrinal de la DT...</span></div>';

    const data = await apiGet(`/api/dt?q=${encodeURIComponent(q)}`);
    let html = '';
    if (data.resultados && data.resultados.length > 0) {
        data.resultados.forEach(item => {
            html += `
                <div class="card">
                    <span class="card-badge badge-dt">Doctrina Laboral</span>
                    <h4 class="card-title">${item.titulo}</h4>
                    ${item.materias ? `<p style="font-size: 13px; color: #93C5FD;">📌 <strong>Materias:</strong> ${item.materias}</p>` : ''}
                    <p class="card-desc">📜 <strong>Doctrina:</strong> ${item.doctrina ? item.doctrina : 'Consultar texto completo'}</p>
                    <div class="card-meta">
                        <span>DT Chile</span>
                        <a href="${item.url}" target="_blank" class="card-link">🔗 Ver en DT Oficial</a>
                    </div>
                </div>
            `;
        });
    } else {
        html = '<div>No se encontraron ordinarios con ese número o materia.</div>';
    }
    dtResults.innerHTML = html;
});

// 5. Energía
const btnCneCap = document.getElementById('btn-cne-capacidad');
const btnCneProy = document.getElementById('btn-cne-proyectos');
const btnPanel = document.getElementById('btn-panel-discrepancias');
const energiaResults = document.getElementById('energia-results');

btnCneCap.addEventListener('click', async () => {
    energiaResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Obteniendo capacidad instalada de la CNE...</span></div>';
    const data = await apiGet('/api/cne/capacidad');
    let html = `<div style="margin-bottom: 12px;">Muestra de centrales generadoras activas (${data.total}):</div>`;
    (data.datos || []).slice(0, 10).forEach(c => {
        html += `
            <div class="card">
                <h4 class="card-title">${c.central} (${c.tipo_tecnologia || c.tecnologia || 'Central'})</h4>
                <p class="card-desc">Titular / Razón Social: <strong>${c.razon_social || c.propietario || 'N/A'}</strong></p>
                <div class="card-meta">
                    <span>⚡ Estado: En Operación</span>
                    <span>CNE Energía Abierta</span>
                </div>
            </div>
        `;
    });
    energiaResults.innerHTML = html;
});

btnCneProy.addEventListener('click', async () => {
    energiaResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Obteniendo proyectos SEA de la CNE...</span></div>';
    const data = await apiGet('/api/cne/proyectos');
    let html = `<div style="margin-bottom: 12px;">Muestra de proyectos energéticos en el SEA (${data.total}):</div>`;
    (data.datos || []).slice(0, 10).forEach(p => {
        html += `
            <div class="card">
                <h4 class="card-title">${p.nombre_proyecto || p.proyecto}</h4>
                <p class="card-desc">Titular: ${p.titular || 'N/A'} | Tipo: ${p.tipo || 'Energía'}</p>
                <div class="card-meta">
                    <span>🌱 Estado SEA: ${p.estado || 'En Calificación'}</span>
                </div>
            </div>
        `;
    });
    energiaResults.innerHTML = html;
});

btnPanel.addEventListener('click', async () => {
    energiaResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando Panel de Expertos...</span></div>';
    const data = await apiGet('/api/panel');
    let html = `<div style="margin-bottom: 12px;">Últimas discrepancias ante el Panel de Expertos:</div>`;
    (data.datos || []).forEach(d => {
        html += `
            <div class="card">
                <h4 class="card-title">Discrepancia N° ${d.numero}</h4>
                <p class="card-desc">Materia: ${d.materia || 'Tarifas y Peajes de Transmisión'}</p>
                <div class="card-meta">
                    <span>⚖️ Dictamen Vinculante</span>
                    <span>Documentos: ${d.documentos ? d.documentos.length : 0}</span>
                </div>
            </div>
        `;
    });
    energiaResults.innerHTML = html;
});

// 6. CMF
const cmfQueryInput = document.getElementById('cmf-query-input');
const btnCmf = document.getElementById('btn-cmf-search');
const cmfResults = document.getElementById('cmf-results');

btnCmf.addEventListener('click', async () => {
    const q = cmfQueryInput.value.trim();
    cmfResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando normativa CMF...</span></div>';
    const data = await apiGet(`/api/cmf?q=${encodeURIComponent(q)}`);
    let html = '';
    (data.datos || []).forEach(item => {
        html += `
            <div class="card">
                <h4 class="card-title">${item.titulo}</h4>
                <div class="card-meta">
                    <span>🏢 CMF Mercado de Valores</span>
                    ${item.pdfUrl ? `<a href="${item.pdfUrl}" target="_blank" class="card-link">📄 Descargar PDF</a>` : ''}
                </div>
            </div>
        `;
    });
    cmfResults.innerHTML = html || '<div>No se encontraron normas CMF.</div>';
});

// 7. SII
const siiAnioSelect = document.getElementById('sii-anio-select');
const btnSii = document.getElementById('btn-sii-search');
const siiResults = document.getElementById('sii-results');

btnSii.addEventListener('click', async () => {
    const yr = siiAnioSelect.value;
    siiResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando Circulares SII...</span></div>';
    const data = await apiGet(`/api/sii?anio=${yr}`);
    let html = `<div style="margin-bottom: 12px;">Total Circulares ${yr}: <strong>${data.total || 0}</strong></div>`;
    (data.datos || []).forEach(c => {
        html += `
            <div class="card">
                <h4 class="card-title">${c.titulo}</h4>
                <div class="card-meta">
                    <span>💰 Año ${c.anio}</span>
                    <a href="${c.pdfUrl}" target="_blank" class="card-link">📄 PDF Oficial SII</a>
                </div>
            </div>
        `;
    });
    siiResults.innerHTML = html;
});

// 8. SMA (Ambiental)
const smaNombreInput = document.getElementById('sma-nombre-input');
const smaExpInput = document.getElementById('sma-exp-input');
const btnSma = document.getElementById('btn-sma-search');
const smaResults = document.getElementById('sma-results');

btnSma.addEventListener('click', async () => {
    const nom = smaNombreInput.value.trim();
    const exp = smaExpInput.value.trim();
    smaResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando SNIFA (SMA)...</span></div>';
    const data = await apiGet(`/api/sma?nombre=${encodeURIComponent(nom)}&expediente=${encodeURIComponent(exp)}`);
    let html = `<div style="margin-bottom: 12px;">Total Sancionatorios registrados: <strong>${data.total || 0}</strong></div>`;
    (data.resultados || []).forEach(s => {
        html += `
            <div class="card">
                <span class="card-badge badge-sma">[${s.expediente}] ${s.estado}</span>
                <h4 class="card-title">${s.titular}</h4>
                <p class="card-desc">Unidad Fiscalizable: <strong>${s.unidadFiscalizable}</strong> (${s.categoria})</p>
                <div class="card-meta">
                    <span>📍 ${s.region}</span>
                    <a href="${s.fichaUrl}" target="_blank" class="card-link">🔗 Ficha Oficial SNIFA</a>
                </div>
            </div>
        `;
    });
    smaResults.innerHTML = html;
});

// 9. TDLC
const tdlcQueryInput = document.getElementById('tdlc-query-input');
const btnTdlc = document.getElementById('btn-tdlc-search');
const tdlcResults = document.getElementById('tdlc-results');

btnTdlc.addEventListener('click', async () => {
    const q = tdlcQueryInput.value.trim();
    tdlcResults.innerHTML = '<div class="loader"><div class="spinner"></div><span>Consultando TDLC...</span></div>';
    const data = await apiGet(`/api/tdlc?q=${encodeURIComponent(q)}`);
    let html = '';
    (data.datos || []).forEach(t => {
        html += `
            <div class="card">
                <h4 class="card-title">${t.titulo}</h4>
                <div class="card-meta">
                    <span>📅 Fecha: ${t.fecha || 'Oficial'}</span>
                    <a href="${t.link}" target="_blank" class="card-link">🔗 Sentencia TDLC</a>
                </div>
            </div>
        `;
    });
    tdlcResults.innerHTML = html || '<div>No se encontraron sentencias TDLC.</div>';
});

// 10. Check Configuration
async function checkConfigStatus() {
    const bcnBadge = document.getElementById('cfg-bcn-status');
    const cneBadge = document.getElementById('cfg-cne-status');
    const data = await apiGet('/api/status');

    if (data.config) {
        if (data.config.BCN_CONFIGURED) {
            bcnBadge.className = 'status-badge ok';
            bcnBadge.textContent = '✅ Configurada';
        } else {
            bcnBadge.className = 'status-badge missing';
            bcnBadge.textContent = '⚠️ Falta BCN_API_KEY';
        }

        if (data.config.CNE_CONFIGURED) {
            cneBadge.className = 'status-badge ok';
            cneBadge.textContent = '✅ Configurada';
        } else {
            cneBadge.className = 'status-badge missing';
            cneBadge.textContent = '⚠️ Falta CNE_EMAIL/PASSWORD';
        }
    }
}

// ==========================================================================
// 11. CHAT JURÍDICO AI MULTI-PROVEEDOR
// ==========================================================================
const chatMessagesContainer = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const btnChatSend = document.getElementById('btn-chat-send');
const chatProviderSelect = document.getElementById('chat-provider-select');
const customApiKeyInput = document.getElementById('custom-api-key-input');

// Cargar API key guardada en localStorage
const savedApiKey = localStorage.getItem('openlegal_custom_api_key');
if (savedApiKey && customApiKeyInput) {
    customApiKeyInput.value = savedApiKey;
}

if (customApiKeyInput) {
    customApiKeyInput.addEventListener('input', () => {
        localStorage.setItem('openlegal_custom_api_key', customApiKeyInput.value.trim());
    });
}

let chatHistory = [];

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    
    // Bloques de código ``` ... ```
    formatted = formatted.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre style="background: rgba(0,0,0,0.5); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle); overflow-x: auto; font-family: var(--font-mono); font-size: 13px; margin: 8px 0;"><code>$2</code></pre>');
    
    // Código en línea `...`
    formatted = formatted.replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 12px; color: var(--accent-cyan);">$1</code>');
    
    // Encabezados
    formatted = formatted.replace(/^### (.*$)/gim, '<h4 style="margin: 12px 0 6px 0; color: var(--accent-blue); font-size: 15px; font-weight: 600;">$1</h4>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h3 style="margin: 16px 0 8px 0; color: #F1F5F9; font-size: 16px; font-weight: 700; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">$1</h3>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h2 style="margin: 20px 0 10px 0; color: #FFFFFF; font-size: 18px; font-weight: 800;">$1</h2>');

    // Negritas
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #F8FAFC; font-weight: 600;">$1</strong>');
    
    // Cursivas
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Citas legales estrictas [BCN - ...] [Dictamen DT ...] [CPR 1980 ...] [CS ...]
    formatted = formatted.replace(/(\[(?:BCN|CPR|Dictamen|CS|C\.A\.|NCG|Circular|SMA|TDLC)[^\]]+\])/g, '<span style="color: #93C5FD; font-weight: 600; background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3); padding: 1px 6px; border-radius: 4px; font-size: 12px; display: inline-block; margin: 1px 0;">$1</span>');
    
    // Listas con viñetas
    formatted = formatted.replace(/^\s*[-*]\s+(.*$)/gim, '<li style="margin-left: 18px; margin-bottom: 4px;">$1</li>');
    
    // Saltos de línea (respetando bloques)
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    let selectedValue = chatProviderSelect.value;
    let provider = selectedValue;
    let model = undefined;

    if (selectedValue.includes(':')) {
        const parts = selectedValue.split(':');
        provider = parts[0];
        model = parts[1];
    }

    const apiKey = getSavedApiKeyFor(provider) || (customApiKeyInput ? customApiKeyInput.value.trim() : "");

    // 1. Render User Message
    chatInput.value = '';
    const userMsgHtml = `
        <div class="message user">
            <div class="avatar">👤</div>
            <div class="msg-content">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
        </div>
    `;
    chatMessagesContainer.insertAdjacentHTML('beforeend', userMsgHtml);

    // 2. Render Typing Indicator
    const typingId = 'typing-' + Date.now();
    const modelDisplayName = model ? `${provider.toUpperCase()} (${model})` : provider.toUpperCase();
    const typingHtml = `
        <div id="${typingId}" class="message assistant">
            <div class="avatar">⚖️</div>
            <div class="msg-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
                <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">Consultando a ${modelDisplayName} y bases de Chile...</span>
            </div>
        </div>
    `;
    chatMessagesContainer.insertAdjacentHTML('beforeend', typingHtml);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

    // 3. Post to backend API
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: jsonPayload = JSON.stringify({
                message: text,
                provider: provider,
                model: model,
                apiKey: apiKey || undefined,
                history: chatHistory
            })
        });

        const data = await response.json();
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        if (data.error) {
            const errorHtml = `
                <div class="message assistant">
                    <div class="avatar">⚠️</div>
                    <div class="msg-content" style="border-color: rgba(244,63,94,0.4); background: rgba(244,63,94,0.08);">
                        <strong style="color: var(--accent-rose);">Aviso del Sistema:</strong>
                        <p style="margin-top: 4px;">${escapeHtml(data.error)}</p>
                        <p style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">💡 Recuerda que puedes configurar tu API Key en el archivo <code>.env</code> o ingresarla arriba en el campo de texto.</p>
                    </div>
                </div>
            `;
            chatMessagesContainer.insertAdjacentHTML('beforeend', errorHtml);
        } else {
            // Add to history
            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: data.reply });

            const contextBadge = data.contextUsed ? `<div class="context-tag">🛰️ Contexto Jurídico Chileno Inyectado</div>` : '';
            const assistantHtml = `
                <div class="message assistant">
                    <div class="avatar">⚖️</div>
                    <div class="msg-content">
                        ${contextBadge}
                        <div>${formatMarkdown(data.reply)}</div>
                    </div>
                </div>
            `;
            chatMessagesContainer.insertAdjacentHTML('beforeend', assistantHtml);
        }

    } catch (e) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        chatMessagesContainer.insertAdjacentHTML('beforeend', `<div class="message assistant"><div class="avatar">❌</div><div class="msg-content" style="color: var(--accent-rose);">Error de conexión con el servidor local: ${e.message}</div></div>`);
    }

    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

if (btnChatSend) {
    btnChatSend.addEventListener('click', sendChatMessage);
}

if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

function sendPromptTemplate(promptText) {
    if (chatInput) {
        chatInput.value = promptText;
        chatInput.focus();
    }
}

// ==========================================================================
// 12. CENTRO DE CONEXIONES IA MULTI-SUITE (GOOGLE, CLAUDE, OPENAI, DEEPSEEK, OLLAMA)
// ==========================================================================

const SUITES = ['gemini', 'anthropic', 'openai', 'deepseek', 'ollama'];

function openConnectionsModal() {
    const modal = document.getElementById('ai-connections-modal');
    if (modal) {
        modal.classList.remove('hidden');
        loadSavedKeysToInputs();
    }
}

function closeConnectionsModal() {
    const modal = document.getElementById('ai-connections-modal');
    if (modal) modal.classList.add('hidden');
    updateConnectionBadges();
}

function switchSuiteTab(suiteId) {
    document.querySelectorAll('.conn-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-suite') === suiteId);
    });
    document.querySelectorAll('.suite-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `suite-pane-${suiteId}`);
    });
}

function loadSavedKeysToInputs() {
    SUITES.forEach(suite => {
        const input = document.getElementById(`input-key-${suite}`);
        const saved = localStorage.getItem(`openlegal_key_${suite}`);
        if (input && saved) input.value = saved;
    });
    const hostInput = document.getElementById('input-host-ollama');
    const savedHost = localStorage.getItem('openlegal_host_ollama');
    if (hostInput && savedHost) hostInput.value = savedHost;
}

async function verifyAndSaveKey(provider) {
    const input = document.getElementById(`input-key-${provider}`);
    const feedback = document.getElementById(`feedback-${provider}`);
    if (!input || !feedback) return;

    const key = input.value.trim();
    if (!key) {
        feedback.className = 'conn-feedback error';
        feedback.textContent = '❌ Debes ingresar una clave o token para probar.';
        feedback.classList.remove('hidden');
        return;
    }

    feedback.className = 'conn-feedback';
    feedback.textContent = '⏳ Probando conexión en vivo con el proveedor...';
    feedback.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/api/verify-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: provider, apiKey: key })
        });
        const data = await res.json();

        if (data.valid) {
            localStorage.setItem(`openlegal_key_${provider}`, key);
            feedback.className = 'conn-feedback success';
            feedback.textContent = `✅ ¡Conexión exitosa y verificada con ${provider.toUpperCase()} (${data.model || 'Activo'})!`;
            updateConnectionBadges();
            updateActiveProviderUI();
        } else {
            feedback.className = 'conn-feedback error';
            feedback.textContent = `❌ Falló la autenticación: ${data.error || 'Clave inválida o sin saldo'}`;
        }
    } catch (e) {
        feedback.className = 'conn-feedback error';
        feedback.textContent = `❌ Error de red al verificar: ${e.message}`;
    }
}

async function detectOllamaModels() {
    const hostInput = document.getElementById('input-host-ollama');
    const feedback = document.getElementById('feedback-ollama');
    const listEl = document.getElementById('ollama-models-list');
    if (!hostInput || !feedback || !listEl) return;

    const host = hostInput.value.trim() || 'http://localhost:11434';
    feedback.className = 'conn-feedback';
    feedback.textContent = `🔍 Consultando Ollama en ${host}...`;
    feedback.classList.remove('hidden');

    try {
        const res = await fetch(`${host}/api/tags`);
        const data = await res.json();
        if (data.models && data.models.length > 0) {
            localStorage.setItem('openlegal_host_ollama', host);
            localStorage.setItem('openlegal_connected_ollama', 'true');
            feedback.className = 'conn-feedback success';
            feedback.textContent = `✅ Ollama detectado con ${data.models.length} modelo(s) local(es) listo(s).`;
            
            listEl.innerHTML = data.models.map(m => `<span class="badge-tag">🦙 ${m.name}</span>`).join(' ');
            listEl.classList.remove('hidden');
            updateConnectionBadges();
        } else {
            feedback.className = 'conn-feedback error';
            feedback.textContent = '⚠️ Ollama responde pero no tiene modelos descargados (ej. `ollama run deepseek-r1:8b`).';
        }
    } catch (e) {
        feedback.className = 'conn-feedback error';
        feedback.textContent = `❌ No se pudo conectar a Ollama en ${host}. ¿Está iniciado el servicio en tu PC?`;
    }
}

function updateConnectionBadges() {
    let connectedCount = 0;
    SUITES.forEach(suite => {
        const hasKey = !!localStorage.getItem(`openlegal_key_${suite}`) || (suite === 'ollama' && localStorage.getItem('openlegal_connected_ollama') === 'true');
        const badge = document.getElementById(`badge-conn-${suite}`);
        if (badge) {
            badge.className = hasKey ? 'dot-status dot-connected' : 'dot-status dot-disconnected';
        }
        if (hasKey) connectedCount++;
    });

    const countBadge = document.getElementById('connected-count-badge');
    if (countBadge) countBadge.textContent = `${connectedCount}/${SUITES.length}`;
}

function getSavedApiKeyFor(provider) {
    return localStorage.getItem(`openlegal_key_${provider}`) || '';
}

function updateActiveProviderUI() {
    const select = document.getElementById('chat-provider-select');
    const badgeName = document.getElementById('active-provider-name');
    const badgeStatus = document.getElementById('active-provider-status');
    const initials = document.getElementById('active-provider-initials');

    if (!select || !badgeName || !badgeStatus) return;

    const val = select.value;
    const provider = val.split(':')[0] || 'gemini';
    const hasKey = !!getSavedApiKeyFor(provider);

    const names = {
        'gemini': 'Google Gemini',
        'anthropic': 'Anthropic Claude',
        'openai': 'OpenAI',
        'deepseek': 'DeepSeek R1',
        'ollama': 'Ollama Local'
    };

    badgeName.textContent = names[provider] || provider;
    badgeStatus.textContent = hasKey ? '⚡ Conectado' : '⚪ Verificado en .env';
    if (initials) initials.textContent = provider.charAt(0).toUpperCase();
}

if (chatProviderSelect) {
    chatProviderSelect.addEventListener('change', updateActiveProviderUI);
}

// Inicializar estado de conexiones
setTimeout(() => {
    updateConnectionBadges();
    updateActiveProviderUI();
}, 300);

// ==========================================================================
// 13. REDACTOR FORENSE & EXPORTADOR OJV
// ==========================================================================
const forenseTemplates = {
    demanda_civil: {
        tribunal: "S.J.L. EN LO CIVIL DE SANTIAGO",
        titulo: "DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO CON INDEMNIZACIÓN DE PERJUICIOS",
        comparecencia: "PABLO BENAVIDES JORQUERA, cédula nacional de identidad N° XX.XXX.XXX-X, profesión u oficio ingeniero, domiciliado para estos efectos en Av. Libertador Bernardo O'Higgins N° 1234, comuna de Santiago, a US. respetuosamente digo:",
        hechos: "1. Con fecha 15 de marzo de 2025, las partes celebraron un contrato de prestación de servicios y desarrollo de software.\n2. Que la demandada incurrió en incumplimiento grave y culpable de sus obligaciones esenciales pactadas en la cláusula quinta.",
        derecho: "Fundo la presente acción en lo dispuesto en los artículos 1489, 1545, 1546, 1556 y siguientes del Código Civil de la República de Chile, en relación con las reglas de la sana crítica y procedimiento ordinario del Código de Procedimiento Civil.",
        peticiones: "POR TANTO, A US. PIDO se sirva tener por interpuesta demanda ordinaria de resolución de contrato con indemnización de perjuicios, acogerla a tramitación y en definitiva declarar resuelto el contrato con costas."
    },
    proteccion: {
        tribunal: "I. CORTE DE APELACIONES DE SANTIAGO",
        titulo: "DEDUCE RECURSO DE PROTECCIÓN CONSTITUCIONAL",
        comparecencia: "JUAN PÉREZ GONZÁLEZ, cédula de identidad N° XX.XXX.XXX-X, domiciliado en Santiago, a US. Iltma. respetuosamente digo:",
        hechos: "1. Que con fecha 10 de agosto de 2026, la recurrida procedió a ejecutar un acto arbitrario e ilegal consistente en la privación unilateral del derecho legítimo del recurrente.\n2. Dicho acto carece de todo fundamento jurídico y vulnera de manera flagrante las garantías constitucionales aseguradas en nuestra Carta Fundamental.",
        derecho: "Se funda el presente recurso en el artículo 20 de la Constitución Política de la República de Chile, en relación con las garantías fundamentales consagradas en el artículo 19 N° 1 (Derecho a la vida y a la integridad física y psíquica), N° 2 (Igualdad ante la ley) y N° 24 (Derecho de propiedad).",
        peticiones: "POR TANTO, A US. ILTMA. PIDO se sirva tener por interpuesto recurso de protección, acogerlo a tramitación, pedir informe a la recurrida y en definitiva restablecer el imperio del derecho adoptando de inmediato las providencias necesarias."
    },
    demanda_laboral: {
        tribunal: "S.J.L. DEL TRABAJO DE SANTIAGO",
        titulo: "DEMANDA POR DESPIDO INJUSTIFICADO, COBRO DE INDEMNIZACIONES Y PRESTACIONES LABORALES",
        comparecencia: "MARÍA ROJAS SILVA, cédula nacional de identidad N° XX.XXX.XXX-X, trabajadora, domiciliada en Santiago, a US. respetuosamente digo:",
        hechos: "1. Que presté servicios para la demandada desde el 01 de junio de 2021 hasta el 30 de julio de 2026, desempeñando el cargo de ejecutiva comercial con una última remuneración de $1.200.000 mensuales.\n2. Con fecha 30 de julio de 2026, la demandada me comunicó mi despido invocando la causal del artículo 161 inciso 1° del Código del Trabajo (Necesidades de la Empresa), causal que resulta del todo improcedente e injustificada por cuanto no concurren los requisitos objetivos y permanentes exigidos por la ley y la jurisprudencia uniforme.",
        derecho: "Fundo la demanda en los artículos 161, 168, 172, 173 y 446 del Código del Trabajo (DFL 1 de 2003), doctrina uniforme de la Dirección del Trabajo y reiterada jurisprudencia de la Excma. Corte Suprema.",
        peticiones: "POR TANTO, A US. PIDO tener por interpuesta demanda en juicio del trabajo, acogerla a tramitación y en definitiva declarar que el despido ha sido injustificado, condenando a la demandada al pago del recargo legal del 30%, indemnización sustitutiva del aviso previo e indemnización por años de servicio con reajustes, intereses y costas."
    },
    carta_despido: {
        tribunal: "COMUNICACIÓN EXTRAJUDICIAL FORMAL (ART. 162 CÓDIGO DEL TRABAJO)",
        titulo: "CARTA DE COMUNICACIÓN DE TÉRMINO DE CONTRATO DE TRABAJO (ART. 161 INCISO 1°)",
        comparecencia: "EMPRESA COMERCIAL SPA, RUT 76.XXX.XXX-K, representada por don Pedro Morales, a don/doña TRABAJADOR/A:",
        hechos: "Por medio de la presente, comunicamos a usted que con fecha 31 de agosto de 2026 se ha resuelto poner término a su contrato individual de trabajo, por la causal prevista en el artículo 161 inciso primero del Código del Trabajo, esto es, Necesidades de la Empresa, derivadas de un proceso de reestructuración interna y modernización tecnológica del área comercial que torna indispensable la supresión de su cargo.",
        derecho: "Conforme a los artículos 161, 162 y 163 del Código del Trabajo, se acompaña copia del estado de pago de sus cotizaciones previsionales al día, informándole que su finiquito estará a su disposición dentro de los 10 días hábiles siguientes.",
        peticiones: "Se deja constancia de la puesta a disposición del aviso y pago de la indemnización por años de servicio y sustitutiva del aviso previo de conformidad a la ley."
    },
    otrosi_poder: {
        tribunal: "TRIBUNAL COMPETENTE",
        titulo: "PRIMER OTROSÍ: PATROCINIO Y PODER",
        comparecencia: "LA PARTE COMPARECIENTE:",
        hechos: "Que por este acto vengo en designar como abogado patrocinante y en conferir poder con todas y cada una de las facultades de ambos incisos del artículo 7° del Código de Procedimiento Civil, en especial las de desistirse en primera instancia de la acción deducida, aceptar la demanda contraria, absolver posiciones, renunciar los recursos o los términos legales, transigir, comprometer, otorgar a los árbitros facultades de arbitradores, aprobar convenios y percibir.",
        derecho: "Artículos 1° y 2° de la Ley N° 18.120 sobre Comparecencia en Juicio, y Ley N° 20.886 sobre Tramitación Digital de Procedimientos Judiciales.",
        peticiones: "POR TANTO, RUEGO A US. tener por constituido el patrocinio y por conferido el poder con las facultades señaladas, el cual es suscrito por el letrado mediante firma electrónica."
    },
    contrato_ppa: {
        tribunal: "CONTRATO PRIVADO DE SUMINISTRO ELÉCTRICO (PPA)",
        titulo: "CONTRATO DE COMPRAVENTA DE ENERGÍA Y POTENCIA (PPA CLIENTE LIBRE)",
        comparecencia: "Entre GENERADORA RENOVABLE CHILE SPA y CLIENTE LIBRE INDUSTRIAL S.A.:",
        hechos: "1. La Generadora es propietaria de centrales de generación de energía solar y eólica conectadas al Sistema Eléctrico Nacional (SEN).\n2. El Cliente Libre requiere el suministro firme y continuo de 15 GWh anuales de energía 100% renovable para sus operaciones productivas.",
        derecho: "Ley General de Servicios Eléctricos (DFL 4/2006), Decreto Supremo N° 86/2012 del Ministerio de Energía, Resoluciones Exentas de la Comisión Nacional de Energía (CNE) y dictámenes del Panel de Expertos.",
        peticiones: "Las partes acuerdan los términos de precio fijo en USD/MWh, punto de inyección y retiro, traspaso de peajes de transmisión y mecanismos de solución de controversias ante el Panel de Expertos o Arbitraje CAM Santiago."
    }
};

function loadForenseTemplate() {
    const sel = document.getElementById('forense-template-select');
    if (!sel) return;
    const tmpl = forenseTemplates[sel.value];
    if (tmpl) {
        document.getElementById('forense-tribunal').value = tmpl.tribunal;
        document.getElementById('forense-titulo').value = tmpl.titulo;
        document.getElementById('forense-comparecencia').value = tmpl.comparecencia;
        document.getElementById('forense-hechos').value = tmpl.hechos;
        document.getElementById('forense-derecho').value = tmpl.derecho;
        document.getElementById('forense-peticiones').value = tmpl.peticiones;
        updateForensePreview();
    }
}

function updateForensePreview() {
    const preview = document.getElementById('forense-preview-content');
    if (!preview) return;

    const tribunal = document.getElementById('forense-tribunal')?.value || '';
    const titulo = document.getElementById('forense-titulo')?.value || '';
    const comparecencia = document.getElementById('forense-comparecencia')?.value || '';
    const hechos = document.getElementById('forense-hechos')?.value || '';
    const derecho = document.getElementById('forense-derecho')?.value || '';
    const peticiones = document.getElementById('forense-peticiones')?.value || '';

    preview.innerHTML = `
<div style="color: #60A5FA; font-weight: bold; margin-bottom: 12px;">${escapeHtml(tribunal)}</div>
<div style="margin-bottom: 12px;">${escapeHtml(comparecencia)}</div>
<div style="font-weight: bold; margin-bottom: 16px; color: #34D399;">EN LO PRINCIPAL: ${escapeHtml(titulo)}</div>
<div style="font-weight: bold; color: #93C5FD; margin-top: 14px;">I. LOS HECHOS</div>
<div style="margin-bottom: 12px;">${escapeHtml(hechos).replace(/\n/g, '<br>')}</div>
<div style="font-weight: bold; color: #93C5FD; margin-top: 14px;">II. EL DERECHO</div>
<div style="margin-bottom: 12px;">${escapeHtml(derecho).replace(/\n/g, '<br>')}</div>
<div style="font-weight: bold; color: #F59E0B; margin-top: 14px;">POR TANTO</div>
<div>${escapeHtml(peticiones).replace(/\n/g, '<br>')}</div>
<div style="margin-top: 24px; padding: 10px; background: rgba(245,158,11,0.1); border-left: 3px solid #F59E0B; font-size: 11px; color: #FCD34D;">
    ⚖️ <strong>Compuerta de Revisión:</strong> Borrador conforme a Ley 20.886 OJV. Validar con abogado patrocinante habilitado.
</div>
    `;
}

// Bind live input changes
['forense-tribunal', 'forense-titulo', 'forense-comparecencia', 'forense-hechos', 'forense-derecho', 'forense-peticiones'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateForensePreview);
});

async function exportLegalDocument() {
    const payload = {
        tribunal: document.getElementById('forense-tribunal')?.value || '',
        titulo_principal: document.getElementById('forense-titulo')?.value || '',
        comparecencia: document.getElementById('forense-comparecencia')?.value || '',
        hechos: document.getElementById('forense-hechos')?.value || '',
        derecho: document.getElementById('forense-derecho')?.value || '',
        peticiones: document.getElementById('forense-peticiones')?.value || '',
        presuma: {
            procedimiento: "ORDINARIO / CONSTITUCIONAL",
            materia: "ACCIONES Y CONTRATOS",
            demandante: "COMPARECIENTE",
            rut_dte: "XX.XXX.XXX-X",
            abogado: "ABOGADO PATROCINANTE",
            rut_abg: "XX.XXX.XXX-X",
            demandado: "PARTE RECURRIDA / DEMANDADA",
            rut_ddo: "XX.XXX.XXX-X"
        },
        otrosies: [
            { numero: "PRIMER OTROSÍ", titulo: "Patrocinio y Poder", contenido: "Tener presente patrocinio y poder conferido bajo la Ley 18.120 y Ley 20.886." }
        ]
    };

    try {
        const res = await fetch(`${API_BASE}/api/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.markdownPath) {
            const badge = document.getElementById('export-status');
            if (badge) {
                badge.style.display = 'inline-block';
                badge.textContent = `✅ Guardado: ${data.filename}.html`;
            }
            alert(`🎉 ¡Escrito judicial exportado con éxito!\n\nArchivos generados en carpeta exports/:\n• ${data.filename}.html\n• ${data.filename}.md`);
        }
    } catch (e) {
        alert(`Error al exportar documento: ${e.message}`);
    }
}

// Initial preview update on load
setTimeout(updateForensePreview, 500);


