#!/usr/bin/env python3
"""
Generador de cuadros e infografías científicas a 300 DPI para reemplazar
tablas y cuadros de texto ASCII en el artículo científico de Open Legal Chile.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

FIG_DIR = Path("investigacion_academica/figuras")
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CBD5E1'

# 1. Cuadro 1: Principios Arquitectónicos Fundamentales
def generar_cuadro_principios():
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=300)
    ax.set_facecolor('#F8FAFC')
    fig.patch.set_facecolor('#FFFFFF')
    
    pilares = [
        ("1. Soberanía Local-First", "• Zero Data Leak estricto\n• Ejecución 100% desconectada\n• CPU convencional sin GPU\n• Cumplimiento Art. 247 CP", "#1E3A8A", "#EFF6FF"),
        ("2. Subsunción Tripartita", "• Norma positiva BCN literal\n• Tratados canónicos (HF)\n• Fallo rector CS / CGR / DT\n• Cero alucinación normativa", "#047857", "#ECFDF5"),
        ("3. Tríada Neuro-Simbólica", "• Sistema 1: Reglas < 5 ms\n• Aritmética de días hábiles\n• Validación RUT Módulo 11\n• Sistema 2: Síntesis LLM", "#B45309", "#FFFBEB"),
        ("4. Bien Público Digital", "• Licencia abierta Apache 2.0\n• 7.399 obras en Hugging Face\n• Código 100% auditable\n• Democratización A2J Chile", "#6D28D9", "#F5F3FF")
    ]
    
    for i, (titulo, desc, color_head, color_bg) in enumerate(pilares):
        x = i * 2.45 + 0.15
        y = 0.15
        w = 2.3
        h = 2.8
        
        # Rectángulo de fondo
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=color_bg, edgecolor=color_head, linewidth=1.5)
        ax.add_patch(rect)
        
        # Cabecera
        head_rect = patches.FancyBboxPatch((x, y + h - 0.75), w, 0.75, boxstyle="round,pad=0.08,rounding_size=0.15",
                                            facecolor=color_head, edgecolor=color_head)
        ax.add_patch(head_rect)
        
        # Texto cabecera
        ax.text(x + w/2, y + h - 0.38, titulo, color="white", fontsize=9.5, fontweight="bold",
                ha="center", va="center")
        
        # Texto cuerpo
        ax.text(x + 0.15, y + (h - 0.85)/2, desc, color="#1F2937", fontsize=8.2, va="center",
                linespacing=1.5)
        
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.2)
    ax.axis('off')
    
    out_path = FIG_DIR / "cuadro1_principios_arquitectonicos.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generado: {out_path}")

# 2. Cuadro 2: Arquitectura Modular de Seis Capas
def generar_cuadro_arquitectura():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_facecolor('#FFFFFF')
    fig.patch.set_facecolor('#FFFFFF')
    
    capas = [
        ("CAPA 6: Ecosistema Multi-Agente & Protocolo Vinculante de Citas", 
         "19 perfiles agénticos soberanos (Laboral, Litigios, Grado, Inmobiliario) • Protocolo obligatorio consulta_maestra y cita_texto", "#1E3A8A", "#DBEAFE"),
        ("CAPA 5: Datos Canónicos & Búsqueda Híbrida RRF (BM25 + Embeddings)", 
         "Corpus de 7.399 obras y 11 revistas científicas en Hugging Face • SQLite FTS5 léxico + modelos densos locales en CPU", "#0284C7", "#E0F2FE"),
        ("CAPA 4: Micro-UIs Forenses Autónomas (LegalCanvas)", 
         "Generación de paneles interactivos en HTML5 semántico y SVG puro (Zero-CDN) • Semáforos de riesgo procesal y Lenguaje Claro", "#0D9488", "#CCFBF1"),
        ("CAPA 3: Grafo de Conocimiento Ontológico (LegalGraphify)", 
         "9.863 instituciones dogmáticas interconectadas • Subgrafos sintéticos con ahorro empírico del 99.9% de tokens de contexto", "#059669", "#D1FAE5"),
        ("CAPA 2: Motor Simbólico Determinista (LegalOpenJev)", 
         "Triage de herramientas en < 5 ms • Compuertas de caducidad laboral (Art. 168 CT), plazos procesales y validación RUT Módulo 11", "#D97706", "#FEF3C7"),
        ("CAPA 1: Servidor MCP y 87 Conectores Oficiales del Estado de Chile", 
         "Transporte estándar JSON-RPC 2.0 sobre stdio • 16 conectores oficiales: BCN, PJUD, CGR, DT, SII, CMF, SMA, TDLC, 1TA/2TA/3TA", "#4F46E5", "#EEF2FF")
    ]
    
    y_start = 4.4
    h = 0.72
    gap = 0.12
    
    for i, (titulo, desc, col_border, col_bg) in enumerate(capas):
        y = y_start - i * (h + gap)
        
        # Caja exterior
        rect = patches.FancyBboxPatch((0.2, y), 9.6, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                                      facecolor=col_bg, edgecolor=col_border, linewidth=1.4)
        ax.add_patch(rect)
        
        # Barra lateral izquierda decorativa
        bar = patches.FancyBboxPatch((0.2, y), 0.25, h, boxstyle="square,pad=0",
                                     facecolor=col_border, edgecolor=col_border)
        ax.add_patch(bar)
        
        # Título y descripción
        ax.text(0.6, y + h - 0.25, titulo, color="#0F172A", fontsize=9.2, fontweight="bold", va="center")
        ax.text(0.6, y + 0.23, desc, color="#334155", fontsize=7.8, va="center")
        
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis('off')
    
    out_path = FIG_DIR / "cuadro2_arquitectura_modular.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generado: {out_path}")

# 3. Cuadro 3: Matriz de Privacidad y Retención de Datos
def generar_cuadro_privacidad():
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=300)
    ax.axis('off')
    
    cols = ["Dimensión Forense", "IA de Consumo Pública\n(ChatGPT, Claude Free)", "APIs Corporativas Nube\n(OpenAI API, Claude API)", "Open Legal Chile\n(Soberana Local-First)"]
    
    filas = [
        ["Entrenamiento con Datos", "SÍ (Retención activa ToS)", "NO (Bajo acuerdo ZDR)", "NUNCA (Cero retención)"],
        ["Revisión Humana Externa", "SÍ (Muestreo de calidad)", "Excepcional (Abuse 30d)", "IMPOSIBLE (Código local)"],
        ["Ubicación de Cómputo", "Servidores en extranjero", "Data centers extranjero", "Memoria RAM local / CPU"],
        ["Secreto Profesional (Art. 247)", "INADMISIBLE (Infracción)", "Riesgo transfronterizo", "PLENO (Por diseño)"],
        ["Ley N° 21.719 (Protección Datos)", "Infracción transferencia", "Exige DPA internacional", "CUMPLIMIENTO TOTAL"],
        ["Costo de Acceso", "Suscripción privativa", "Pago por millón tokens", "GRATUITO (Apache 2.0)"]
    ]
    
    tabla = ax.table(cellText=filas, colLabels=cols, loc='center', cellLoc='center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8.2)
    tabla.scale(1.0, 1.8)
    
    # Estilizar encabezados
    for j in range(len(cols)):
        celda = tabla[0, j]
        celda.set_facecolor('#1E293B')
        celda.set_text_props(color='white', weight='bold', size=8.5)
    
    # Colores por columna
    for i in range(1, len(filas) + 1):
        # Dimensión
        tabla[i, 0].set_facecolor('#F1F5F9')
        tabla[i, 0].set_text_props(weight='bold', color='#1E293B')
        # Consumo (rojo suave)
        tabla[i, 1].set_facecolor('#FEF2F2')
        tabla[i, 1].set_text_props(color='#991B1B')
        # API (amarillo suave)
        tabla[i, 2].set_facecolor('#FFFBEB')
        tabla[i, 2].set_text_props(color='#92400E')
        # Open Legal (verde suave)
        tabla[i, 3].set_facecolor('#ECFDF5')
        tabla[i, 3].set_text_props(color='#065F46', weight='bold')
        
    out_path = FIG_DIR / "cuadro3_matriz_privacidad_retencion.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generado: {out_path}")

if __name__ == "__main__":
    generar_cuadro_principios()
    generar_cuadro_arquitectura()
    generar_cuadro_privacidad()
    print("✓ Todos los cuadros gráficos a 300 DPI generados exitosamente.")
