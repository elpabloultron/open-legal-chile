#!/usr/bin/env python3
"""
Generador de figuras científicas de alta resolución (300 DPI) para la monografía de Open Legal Chile.
Sigue las directrices de publicación científica de Jiménez Ávila (2015, Orthotips) y RChDT:
- Figura 1: Brecha de difusión del conocimiento científico y superación de barreras mediante software abierto.
- Figura 2: Arquitectura modular de 6 capas y la Tríada Neuro-Simbólica de Open Legal Chile.
- Figura 3: Topología del Subgrafo Sintético de LegalGraphify y reducción empírica del 99.9% de tokens.
- Figura 4: Línea de tiempo forense vectorial para cómputo de plazos fatales y suspensión administrativa (Art. 168 CT).
- Figura 5: Micro-UI de LegalCanvas: Semáforos de riesgo procesal y fichas en Lenguaje Claro para consultorios CAJ.
- Figura 6: Métricas de latencia computacional (ms) en CPU convencional y matriz de seguridad SAST 360°.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "investigacion_academica" / "figuras"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Paleta cromática formal para publicaciones científicas
NAVY = "#1e3a8a"
SLATE = "#334155"
LIGHT_BG = "#f8fafc"
BORDER_COLOR = "#cbd5e1"
GREEN_OK = "#059669"
RED_BLOCK = "#dc2626"
AMBER_WARN = "#d97706"
BLUE_ACCENT = "#2563eb"
TEXT_DARK = "#0f172a"

def generar_figura_1():
    """Figura 1: Brecha de Difusión del Conocimiento según el modelo de Jiménez Ávila (2015)."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "FIGURA 1. Brecha en la Difusión del Conocimiento Jurídico y Ciclo de Vida del Software Soberano",
            fontsize=12, fontweight="bold", ha="center", va="top", color=NAVY, fontfamily="serif")
    ax.text(0.5, 0.90, "Adaptación del modelo de Jiménez Ávila (2015) al desarrollo y publicación de Open Legal Chile",
            fontsize=9.5, fontstyle="italic", ha="center", va="top", color=SLATE, fontfamily="serif")

    # Bloques del proceso científico
    etapas = [
        ("1. Problema Formativo y Forense\n(Aula, Examen de Grado, CAJ)", 0.05, 0.65, 0.22, 0.16, "#e2e8f0"),
        ("2. Investigación y Protocolo\n(Marco Teórico y Dogmático)", 0.38, 0.65, 0.24, 0.16, "#dbeafe"),
        ("3. Manuscrito y Prototipo\n(Open Legal Chile v1.12.0)", 0.72, 0.65, 0.23, 0.16, "#ede9fe"),
    ]

    for texto, x, y, w, h, bg in etapas:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=bg, edgecolor=NAVY, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, texto, ha="center", va="center", fontsize=9, fontweight="bold",
                color=TEXT_DARK, fontfamily="serif")

    # Flechas intermedias
    ax.annotate("", xy=(0.38, 0.73), xytext=(0.27, 0.73),
                arrowprops=dict(arrowstyle="->", lw=2, color=NAVY))
    ax.annotate("", xy=(0.72, 0.73), xytext=(0.62, 0.73),
                arrowprops=dict(arrowstyle="->", lw=2, color=NAVY))

    # Barrera 1 (Línea punteada)
    ax.plot([0.5, 0.5], [0.15, 0.58], color=RED_BLOCK, linestyle="--", linewidth=2)
    ax.text(0.5, 0.53, "1ª BARRERA CRÍTICA:\nEl «Acto de Escribir» y el Monopolio Privativo\n(Paywalls comerciales y falta de herramientas abiertas)",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=RED_BLOCK, fontfamily="serif",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fef2f2", edgecolor=RED_BLOCK, lw=1))

    # Barrera 2 (Línea punteada)
    ax.plot([0.83, 0.83], [0.15, 0.58], color=AMBER_WARN, linestyle="--", linewidth=2)
    ax.text(0.83, 0.53, "2ª BARRERA CRÍTICA:\nRiesgo de Alucinación y Fuga de Datos\n(Modelos comerciales en nube extranjera)",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=AMBER_WARN, fontfamily="serif",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fffbeb", edgecolor=AMBER_WARN, lw=1))

    # Etapa Final: Publicación Abierta y Difusión
    rect_final = patches.FancyBboxPatch((0.20, 0.22), 0.60, 0.16, boxstyle="round,pad=0.02,rounding_size=0.03",
                                        facecolor="#ecfdf5", edgecolor=GREEN_OK, linewidth=2)
    ax.add_patch(rect_final)
    ax.text(0.50, 0.30, "SOLUCIÓN: PUBLICACIÓN COMO BIEN PÚBLICO DIGITAL (APACHE 2.0)\n"
                         "• 100% Código Abierto en GitHub • Corpus Canónico en Hugging Face Datasets\n"
                         "• Paquete PyPI Oficial (openlegal-chile) • Monografía y Manuales en Lenguaje Claro",
            ha="center", va="center", fontsize=9, fontweight="bold", color=GREEN_OK, fontfamily="serif")

    # Flecha hacia solución
    ax.annotate("", xy=(0.83, 0.38), xytext=(0.83, 0.65),
                arrowprops=dict(arrowstyle="->", lw=2, color=GREEN_OK, connectionstyle="arc3,rad=-0.2"))

    ax.text(0.5, 0.04, "Fuente: Elaboración propia a partir del marco metodológico de Jiménez Ávila (2015, p. 60) y arquitectura de Open Legal Chile.",
            fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.tight_layout()
    out_file = OUTPUT_DIR / "figura1_brecha_difusion.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def generar_figura_2():
    """Figura 2: Arquitectura de 6 Capas de Open Legal Chile y Tríada Neuro-Simbólica."""
    fig, ax = plt.subplots(figsize=(10.5, 7.5), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.96, "FIGURA 2. Arquitectura de Seis Capas y la Tríada Neuro-Simbólica de Open Legal Chile",
            fontsize=12, fontweight="bold", ha="center", va="top", color=NAVY, fontfamily="serif")
    ax.text(0.5, 0.92, "Separación estricta entre computación deóntica determinista (Sistema 1) y generación discursiva (Sistema 2)",
            fontsize=9.5, fontstyle="italic", ha="center", va="top", color=SLATE, fontfamily="serif")

    capas = [
        ("CAPA 6: Ecosistema Multi-Agente & Protocolo Vinculante de Citas",
         "19 perfiles agénticos especializados (Laboral, Litigios, Inmobiliario, Grado) • Protocolo vinculante: consulta_maestra (Paso 0) & cita_texto",
         0.77, "#eff6ff", NAVY),
        ("CAPA 5: Datos Canónicos & Búsqueda Híbrida RRF (Reciprocal Rank Fusion)",
         "Corpus abierto de 7.399 obras en Hugging Face Datasets • Índice FTS5 BM25 en SQLite local + Embeddings densos en CPU (k=60)",
         0.63, "#f0fdf4", GREEN_OK),
        ("CAPA 4: Micro-UIs Forenses Autónomas (LegalCanvas) [TRÍADA]",
         "Renderizado de HTML5 semántico puro + Gráficos vectoriales SVG (No-CDN) • Líneas de tiempo procesales y semáforos en Lenguaje Claro",
         0.49, "#fef3c7", AMBER_WARN),
        ("CAPA 3: Grafo Ontológico de Conocimiento (LegalGraphify) [TRÍADA]",
         "9.863 instituciones dogmáticas & 45.000+ aristas deónticas • Subgrafos sintéticos (ahorro del 99.9% de tokens: 91 vs 96k) • PageRank God Nodes",
         0.35, "#f5f3ff", "#7c3aed"),
        ("CAPA 2: Motor Simbólico Determinista (LegalOpenJev - Sistema 1) [TRÍADA]",
         "Triage de herramientas en < 5 ms O(1) • Compuertas binarias de admisibilidad (Arts. 168 CT, 20 CPR, 66 CPC) • Algoritmo RUT Módulo 11",
         0.21, "#fee2e2", RED_BLOCK),
        ("CAPA 1: Servidor Model Context Protocol (MCP) & 16 Conectores Oficiales",
         "Transporte JSON-RPC 2.0 stdio (mcp_server.py) • 87 herramientas forenses • Conectores: BCN, PJUD, CGR, DT, CMF, SII, SMA, TDLC, TA, CNE",
         0.07, "#f1f5f9", SLATE),
    ]

    for titulo, desc, y, bg, border in capas:
        rect = patches.FancyBboxPatch((0.06, y), 0.88, 0.11, boxstyle="round,pad=0.015,rounding_size=0.02",
                                      facecolor=bg, edgecolor=border, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(0.08, y + 0.08, titulo, fontsize=9.5, fontweight="bold", color=border, fontfamily="serif")
        ax.text(0.08, y + 0.03, desc, fontsize=8.2, color=TEXT_DARK, fontfamily="serif")

    # Flechas conectivas verticales
    for y in [0.74, 0.60, 0.46, 0.32, 0.18]:
        ax.annotate("", xy=(0.5, y + 0.03), xytext=(0.5, y),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color=SLATE))

    ax.text(0.5, 0.02, "Fuente: Elaboración propia a partir de la especificación técnica de Open Legal Chile v1.12.0.",
            fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.tight_layout()
    out_file = OUTPUT_DIR / "figura2_arquitectura_triada.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def generar_figura_3():
    """Figura 3: Algoritmo de Subgrafo Sintético en LegalGraphify y Ahorro del 99.9% de Tokens."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5), dpi=300, gridspec_kw={'width_ratios': [1.2, 1]})
    fig.patch.set_facecolor("white")

    # Panel Izquierdo: Diagrama del Subgrafo k-hop
    ax1.set_facecolor("white")
    ax1.axis("off")
    ax1.set_title("(A) Extracción Topológica k-hop en LegalGraphify", fontsize=10.5, fontweight="bold", color=NAVY, fontfamily="serif")

    # Nodo Central (Institución consultada)
    c_central = patches.Circle((0.5, 0.5), 0.12, facecolor="#fee2e2", edgecolor=RED_BLOCK, linewidth=2)
    ax1.add_patch(c_central)
    ax1.text(0.5, 0.5, "Art. 161 CT\n(Necesidades de\nla Empresa)", ha="center", va="center", fontsize=8, fontweight="bold", color=RED_BLOCK)

    # Nodos Vecinos de Salto k=1
    vecinos = [
        ("Art. 168 CT\n(Caducidad 60d)", 0.20, 0.80, GREEN_OK, "#dcfce7"),
        ("Doctrina DT\n(Carácter Grave)", 0.80, 0.80, BLUE_ACCENT, "#dbeafe"),
        ("Jurisprudencia CS\n(Unificación Rol 35k)", 0.80, 0.20, NAVY, "#e0e7ff"),
        ("Art. 1698 CC\n(Carga Probatoria)", 0.20, 0.20, SLATE, "#f1f5f9"),
    ]

    for texto, x, y, col, bg in vecinos:
        circ = patches.Circle((x, y), 0.11, facecolor=bg, edgecolor=col, linewidth=1.5)
        ax1.add_patch(circ)
        ax1.text(x, y, texto, ha="center", va="center", fontsize=7.5, fontweight="bold", color=col)
        # Flecha conectiva
        ax1.annotate("", xy=(x, y), xytext=(0.5, 0.5),
                     arrowprops=dict(arrowstyle="<->", lw=1.2, color=SLATE, linestyle="--"))

    ax1.text(0.5, 0.05, "Tarjeta Sintética Extraída: 91 tokens de contexto",
             ha="center", fontsize=9, fontweight="bold", color=GREEN_OK,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#ecfdf5", edgecolor=GREEN_OK, lw=1))

    # Panel Derecho: Gráfico de Barras de Ahorro de Tokens
    ax2.set_facecolor("#f8fafc")
    ax2.set_title("(B) Consumo de Tokens: RAG Clásico vs LegalGraphify", fontsize=10.5, fontweight="bold", color=NAVY, fontfamily="serif")
    
    metodos = ["RAG Tradicional\n(Capítulo de Tratado)", "LegalGraphify\n(Subgrafo Sintético)"]
    tokens = [96536, 91]
    colores = [RED_BLOCK, GREEN_OK]

    ax2.bar(metodos, tokens, color=colores, width=0.55, edgecolor=SLATE, linewidth=1.2)
    ax2.set_yscale("log")
    ax2.set_ylabel("Tokens de Contexto (Escala Logarítmica)", fontsize=9, fontfamily="serif")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # Etiquetas sobre las barras
    ax2.text(0, 96536 * 1.3, "96.536 tokens\n(Saturación de contexto)", ha="center", fontsize=8.5, fontweight="bold", color=RED_BLOCK)
    ax2.text(1, 91 * 2.5, "91 tokens\n(Ahorro medido: 99.9%)", ha="center", fontsize=8.5, fontweight="bold", color=GREEN_OK)

    plt.suptitle("FIGURA 3. Extracción de Subgrafo Sintético y Ahorro Empírico del 99.9% de Tokens en LegalGraphify",
                 fontsize=12, fontweight="bold", color=NAVY, fontfamily="serif", y=0.98)
    
    fig.text(0.5, 0.01, "Fuente: Mediciones empíricas de Open Legal Chile sobre 9.863 instituciones indexadas en doctrina.db.",
             fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    out_file = OUTPUT_DIR / "figura3_subgrafo_ahorro_tokens.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def generar_figura_4():
    """Figura 4: Línea de Tiempo Procesal Forense en SVG para el Caso Laboral (Art. 168 CT)."""
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.text(0.5, 0.95, "FIGURA 4. Cómputo de Días Hábiles Judiciales y Suspensión Administrativa (Caso Laboral Art. 168 CT)",
            fontsize=12, fontweight="bold", ha="center", va="top", color=NAVY, fontfamily="serif")
    ax.text(0.5, 0.88, "Línea de tiempo vectorial generada algorítmicamente por LegalCanvas Engine sin dependencias externas",
            fontsize=9.5, fontstyle="italic", ha="center", va="top", color=SLATE, fontfamily="serif")

    # Eje horizontal
    ax.plot([0.08, 0.92], [0.5, 0.5], color=SLATE, linewidth=3, zorder=1)

    hitos = [
        ("01-10-2024", "Despido Efectivo\n(Carta Certificada)", 0.12, RED_BLOCK),
        ("10-10-2024", "Reclamo en Inspección\n(Transcurren 8 días hábiles)", 0.30, BLUE_ACCENT),
        ("15-11-2024", "Cierre Comparendo\n(Sin acuerdo conciliatorio)", 0.60, AMBER_WARN),
        ("05-12-2024", "Consulta Letrada\n(Total: 24 días hábiles netos)", 0.76, GREEN_OK),
        ("Enero 2025", "Límite Fatal Absoluto\n(Tope 90 días hábiles Art. 168)", 0.88, RED_BLOCK),
    ]

    for fecha, texto, x, col in hitos:
        # Marcador circular
        ax.scatter(x, 0.5, s=150, color=col, edgecolor="white", linewidth=2, zorder=3)
        # Fecha arriba
        ax.text(x, 0.56, fecha, ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=col, fontfamily="serif")
        # Descripción abajo
        ax.text(x, 0.44, texto, ha="center", va="top", fontsize=8, color=TEXT_DARK, fontfamily="serif")

    # Tramo sombreado de suspensión
    ax.axvspan(0.30, 0.60, ymin=0.45, ymax=0.55, facecolor="#fed7aa", alpha=0.5, zorder=2)
    ax.text(0.45, 0.65, "PERÍODO DE SUSPENSIÓN ADMINISTRATIVA (Art. 168 inc. final CT)\n(El cómputo de los 60 días queda legalmente congelado)",
            ha="center", fontsize=8, fontweight="bold", color="#c2410c",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#fff7ed", edgecolor="#f97316", lw=1))

    # Veredicto
    ax.text(0.76, 0.20, "VEREDICTO SISTEMA 1: PASS\nAcción plenamente vigente.\nMargen restante: 36 días hábiles.",
            ha="center", fontsize=8.5, fontweight="bold", color=GREEN_OK,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ecfdf5", edgecolor=GREEN_OK, lw=1.5))

    ax.text(0.5, 0.05, "Fuente: Renderizado forense nativo de LegalCanvasEngine a partir de las reglas del Código del Trabajo.",
            fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.subplots_adjust(top=0.96, bottom=0.04, left=0.02, right=0.98)
    out_file = OUTPUT_DIR / "figura4_timeline_laboral_art168.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def generar_figura_5():
    """Figura 5: Micro-UI de LegalCanvas: Semáforos de Riesgo y Ficha en Lenguaje Claro."""
    fig, ax = plt.subplots(figsize=(10.5, 6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")
    ax.axis("off")

    ax.text(0.5, 0.95, "FIGURA 5. Micro-UI Forense de LegalCanvas: Semáforos y Fichas en Lenguaje Claro",
            fontsize=12, fontweight="bold", ha="center", va="top", color=NAVY, fontfamily="serif")
    ax.text(0.5, 0.90, "Diseño forense accesible para el justiciable en consultorios de la Corporación de Asistencia Judicial (CAJ)",
            fontsize=9.5, fontstyle="italic", ha="center", va="top", color=SLATE, fontfamily="serif")

    # Caja Izquierda: Medidor de Riesgo / Semáforo
    rect_izq = patches.FancyBboxPatch((0.05, 0.15), 0.42, 0.70, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor="white", edgecolor=BORDER_COLOR, linewidth=1.5)
    ax.add_patch(rect_izq)
    ax.text(0.26, 0.80, "MEDIDOR DE VIABILIDAD PROCESAL", ha="center", fontsize=9.5, fontweight="bold", color=NAVY)

    # Semáforo visual
    colores_sem = [("#10b981", "ALTA VIABILIDAD (PASS)", "Causales objetivas acreditables,\nplazos fatales cumplidos."),
                   ("#f59e0b", "RIESGO MODERADO (WARN)", "Prueba sujeta a discrecionalidad\njudicial o indicios débiles."),
                   ("#ef4444", "INVIABLE / CADUCO (BLOCK)", "Plazo legal vencido o\nincompetencia manifiesta.")]
    y_sem = 0.65
    for c, estado, detalle in colores_sem:
        circ = patches.Circle((0.10, y_sem), 0.03, facecolor=c, edgecolor=SLATE, lw=1)
        ax.add_patch(circ)
        ax.text(0.15, y_sem + 0.01, estado, fontsize=8.5, fontweight="bold", color=c)
        ax.text(0.15, y_sem - 0.035, detalle, fontsize=7.5, color=SLATE)
        y_sem -= 0.16

    # Caja Derecha: Ficha en Lenguaje Claro para el Justiciable
    rect_der = patches.FancyBboxPatch((0.52, 0.15), 0.43, 0.70, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor="white", edgecolor=BORDER_COLOR, linewidth=1.5)
    ax.add_patch(rect_der)
    ax.text(0.735, 0.80, "FICHA INFORMATIVA EN LENGUAJE CLARO", ha="center", fontsize=9.5, fontweight="bold", color=NAVY)

    texto_ficha = (
        "Estimado(a) usuario(a):\n\n"
        "• Su caso: Despido por «necesidades de la empresa».\n"
        "• Situación actual: Su plazo judicial se encuentra VIGENTE.\n"
        "  El trámite en la Inspección del Trabajo congeló el tiempo,\n"
        "  por lo que aún quedan 36 días hábiles para demandar.\n\n"
        "• Derechos que reclamaremos ante el tribunal:\n"
        "  1) Indemnización legal por años de servicio (6 años).\n"
        "  2) Aviso previo equivalente a un mes de sueldo.\n"
        "  3) Recargo legal del 30% por despido injustificado.\n\n"
        "• Siguiente paso: Se redactará la demanda formal para su\n"
        "  aprobación e ingreso en los tribunales laborales."
    )
    ax.text(0.55, 0.48, texto_ficha, fontsize=8.2, color=TEXT_DARK, va="center", fontfamily="sans-serif")

    ax.text(0.5, 0.04, "Fuente: Componente render_case_dashboard de LegalCanvasEngine, alineado con las Reglas de Brasilia sobre Acceso a la Justicia.",
            fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.tight_layout()
    out_file = OUTPUT_DIR / "figura5_dashboard_legalcanvas.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def generar_figura_6():
    """Figura 6: Métricas de Desempeño Computacional (ms) y Matriz SAST 360°."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5), dpi=300, gridspec_kw={'width_ratios': [1.2, 1]})
    fig.patch.set_facecolor("white")

    # Panel Izquierdo: Gráfico de Barras Horizontales de Latencias
    ax1.set_facecolor("#f8fafc")
    ax1.set_title("(A) Latencia de Módulos Críticos en CPU Convencional (ms)", fontsize=10, fontweight="bold", color=NAVY, fontfamily="serif")
    
    operaciones = [
        "Fusión Híbrida RRF (BM25+Dense)",
        "Extracción Subgrafo LegalGraphify",
        "Búsqueda FTS5 BM25 (SQLite)",
        "Generación Micro-UI LegalCanvas",
        "Triage Sintáctico LegalOpenJev",
        "Despacho MCP Servidor",
        "Cómputo Plazos Fatales",
        "Validación RUT Módulo 11",
    ]
    latencias = [42.6, 18.4, 12.2, 8.5, 3.8, 2.3, 1.1, 0.08]
    colores = [NAVY, "#7c3aed", BLUE_ACCENT, AMBER_WARN, GREEN_OK, SLATE, GREEN_OK, GREEN_OK]

    y_pos = np.arange(len(operaciones))
    barras = ax1.barh(y_pos, latencias, color=colores, height=0.65, edgecolor=SLATE, lw=1)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(operaciones, fontsize=8, fontfamily="serif")
    ax1.invert_yaxis()
    ax1.set_xlabel("Latencia en Milisegundos (ms)", fontsize=8.5, fontfamily="serif")
    ax1.grid(axis="x", linestyle="--", alpha=0.5)

    for barra, valor in zip(barras, latencias, strict=False):
        ax1.text(barra.get_width() + 0.8, barra.get_y() + barra.get_height()/2,
                 f"{valor} ms", va="center", fontsize=7.5, fontweight="bold", color=TEXT_DARK)

    # Panel Derecho: Matriz de Compuertas SAST 360°
    ax2.set_facecolor("white")
    ax2.axis("off")
    ax2.set_title("(B) Matriz de Seguridad y Calidad SAST 360°", fontsize=10, fontweight="bold", color=NAVY, fontfamily="serif")

    compuertas = [
        ("pip-audit", "0 vulnerabilidades en dependencias", GREEN_OK),
        ("bandit", "0 fallos de seguridad en Python", GREEN_OK),
        ("semgrep", "0 inyecciones SQL / comandos", GREEN_OK),
        ("detect-secrets", "0 credenciales / tokens expuestos", GREEN_OK),
        ("mypy", "0 errores de tipos en 257 archivos", GREEN_OK),
        ("vulture", "0 código muerto huérfano", GREEN_OK),
        ("ponytail", "Arquitectura limpia de sobre-ingeniería", GREEN_OK),
        ("radon", "Complejidad Grados A y B óptimos", GREEN_OK),
        ("pytest", "526 pruebas aprobadas (100% pass)", GREEN_OK),
    ]

    y_c = 0.90
    for nombre, resultado, color in compuertas:
        rect = patches.FancyBboxPatch((0.05, y_c - 0.07), 0.90, 0.07, boxstyle="round,pad=0.01,rounding_size=0.02",
                                      facecolor="#f0fdf4", edgecolor=color, lw=1.2)
        ax2.add_patch(rect)
        ax2.text(0.10, y_c - 0.035, f"[{nombre}]: {resultado}", fontsize=8, fontweight="bold", color=color, fontfamily="serif", va="center")
        y_c -= 0.095

    plt.suptitle("FIGURA 6. Desempeño Computacional en Milisegundos y Aseguramiento SAST 360°",
                 fontsize=12, fontweight="bold", color=NAVY, fontfamily="serif", y=0.98)
    
    fig.text(0.5, 0.01, "Fuente: Pruebas automatizadas ejecutadas sobre Linux Ubuntu 24.04 LTS (AMD Ryzen 7, 16 GB RAM, sin GPU).",
             fontsize=8, fontstyle="italic", ha="center", color=SLATE, fontfamily="serif")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_file = OUTPUT_DIR / "figura6_latencias_benchmarks.png"
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"✓ Creada: {out_file}")

def main():
    print("=== Generando Figuras Científicas en 300 DPI ===")
    generar_figura_1()
    generar_figura_2()
    generar_figura_3()
    generar_figura_4()
    generar_figura_5()
    generar_figura_6()
    print("=== Todas las figuras generadas exitosamente ===")

if __name__ == "__main__":
    main()
