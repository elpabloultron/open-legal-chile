"""Construye el PowerPoint de la charla con el sistema de diseño de la casa.

Diseño propio (inspirado en la arquitectura de bloques de python-pptx-theme-kit, sin copiar su
código —es GPL—): paleta institucional azul tinta + bronce, tipografías Calibri, portada y
separadores con red de nodos, tarjetas, números grandes, marcos para imágenes y **videos
incrustados** de las animaciones (se reproducen dentro de la presentación).

Se ejecuta con el venv del proyecto (python-pptx):
    .venv/bin/python docs/charla/construir_deck.py
"""
from __future__ import annotations

import pathlib

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

CHARLA = pathlib.Path(__file__).resolve().parent
IMG = CHARLA / "img"
VID = CHARLA / "video"
SALIDA = CHARLA / "Open_Legal_Chile_como_funciona.pptx"

# ── sistema de diseño ───────────────────────────────────────────────────────────────────────
TINTA = RGBColor(0x12, 0x22, 0x2F)
AZUL = RGBColor(0x1F, 0x3B, 0x57)
AZUL_M = RGBColor(0x2E, 0x5D, 0x8A)
BRONCE = RGBColor(0xB5, 0x8B, 0x2A)
GRIS_F = RGBColor(0xF4, 0xF6, 0xF9)
GRIS_B = RGBColor(0xD8, 0xE0, 0xE8)
GRIS_T = RGBColor(0x5A, 0x70, 0x86)
CLARO = RGBColor(0xB9, 0xC7, 0xD6)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
VERDE = RGBColor(0x1E, 0x7A, 0x5A)
CREMA = RGBColor(0xFD, 0xF6, 0xE3)
DORADO_T = RGBColor(0x7A, 0x64, 0x20)
FUENTE_T = "Calibri Light"
FUENTE = "Calibri"
ANCHO, ALTO = 13.333, 7.5


def nueva(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(s, x, y, w, h, relleno=None, linea=None, radio=None, grosor=0.75):
    forma = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radio is not None else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if radio is not None:
        try:
            forma.adjustments[0] = radio
        except Exception:
            pass
    if relleno is None:
        forma.fill.background()
    else:
        forma.fill.solid()
        forma.fill.fore_color.rgb = relleno
    if linea is None:
        forma.line.fill.background()
    else:
        forma.line.color.rgb = linea
        forma.line.width = Pt(grosor)
    forma.shadow.inherit = False
    return forma


def texto(s, x, y, w, h, partes, size=12.0, color=TINTA, bold=False, fuente=FUENTE,
          align=PP_ALIGN.LEFT, interlineado=1.08, espacio=4.0, anchor=MSO_ANCHOR.TOP):
    caja = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caja.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(partes, str):
        partes = [[(partes, {})]]
    for i, parrafo in enumerate(partes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = interlineado
        p.space_after = Pt(espacio)
        if isinstance(parrafo, str):
            parrafo = [(parrafo, {})]
        for t, est in parrafo:
            r = p.add_run()
            r.text = t
            f = r.font
            f.size = Pt(est.get("size", size))
            f.bold = est.get("bold", bold)
            f.name = est.get("fuente", fuente)
            f.color.rgb = est.get("color", color)
            if est.get("italic"):
                f.italic = True
    return caja


def vinetas(s, x, y, w, items, size=11.6, color=GRIS_T, space=8.0, alto=4.2):
    partes = []
    for it in items:
        if isinstance(it, tuple):
            partes.append([("•  ", {"color": AZUL_M, "bold": True}), (it[0], {"color": color, "bold": True}),
                           (it[1], {"color": color})])
        else:
            partes.append([("•  ", {"color": AZUL_M, "bold": True}), (it, {"color": color})])
    return texto(s, x, y, w, alto, partes, size=size, espacio=space, interlineado=1.14)


def chrome(s, seccion, numero, oscuro=False):
    linea_col = RGBColor(0x2E, 0x46, 0x60) if oscuro else GRIS_B
    txt_col = CLARO if oscuro else GRIS_T
    rect(s, 0.55, 7.06, 12.23, 0.012, relleno=linea_col)
    texto(s, 0.55, 7.11, 8.0, 0.3, "Open Legal Chile · prueba en vivo · septiembre 2026",
          size=9, color=txt_col)
    texto(s, 11.55, 7.11, 1.23, 0.3, f"{numero:02d}", size=9, color=txt_col, align=PP_ALIGN.RIGHT)
    if seccion:
        texto(s, 0.55, 0.4, 10.0, 0.26, seccion.upper(), size=9.5, color=BRONCE, bold=True)


def titulo(s, cadena, y=0.7, size=27, w=12.2):
    texto(s, 0.55, y, w, 0.68, cadena, size=size, color=TINTA, fuente=FUENTE_T, interlineado=1.0)
    rect(s, 0.56, y + 0.68, 1.05, 0.045, relleno=BRONCE)


def tarjeta(s, x, y, w, h, titulo_, cuerpo, acento=AZUL_M, chico=False, relleno_=GRIS_F):
    rect(s, x, y, w, h, relleno=relleno_, radio=0.06)
    rect(s, x, y, 0.055, h, relleno=acento)
    if titulo_:
        texto(s, x + 0.22, y + 0.14, w - 0.42, 0.3, titulo_,
              size=12.3 if not chico else 11.4, bold=True, color=TINTA)
    texto(s, x + 0.22, y + (0.56 if titulo_ else 0.16), w - 0.44, max(0.4, h - 0.7),
          cuerpo, size=11 if not chico else 10.2, color=GRIS_T, interlineado=1.16)


def bigcard(s, x, y, w, h, numero, etiqueta, acento=AZUL_M):
    rect(s, x, y, w, h, relleno=GRIS_F, radio=0.07)
    rect(s, x, y, w, 0.05, relleno=acento)
    texto(s, x + 0.08, y + 0.32, w - 0.16, 0.62, numero, size=29, bold=True, color=AZUL,
          align=PP_ALIGN.CENTER, fuente=FUENTE_T)
    texto(s, x + 0.14, y + 1.0, w - 0.28, h - 1.05, etiqueta, size=10.2, color=GRIS_T,
          align=PP_ALIGN.CENTER, interlineado=1.12)


def marco_imagen(s, ruta, x, y, w, h, pie=None):
    rect(s, x + 0.06, y + 0.08, w, h, relleno=GRIS_B)
    rect(s, x, y, w, h, relleno=BLANCO, linea=GRIS_B)
    s.shapes.add_picture(str(ruta), Inches(x + 0.09), Inches(y + 0.09),
                         width=Inches(w - 0.18), height=Inches(h - 0.18))
    if pie:
        texto(s, x, y + h + 0.08, w, 0.32, pie, size=10, color=GRIS_T, interlineado=1.06)


def marco_video(s, nombre, x, y, w, h, pie=None):
    mp4, poster = VID / f"{nombre}.mp4", VID / f"{nombre}_poster.png"
    rect(s, x + 0.06, y + 0.08, w, h, relleno=GRIS_B)
    rect(s, x, y, w, h, relleno=BLANCO, linea=GRIS_B)
    s.shapes.add_movie(str(mp4), Inches(x + 0.09), Inches(y + 0.09),
                       Inches(w - 0.18), Inches(h - 0.18),
                       poster_frame_image=str(poster), mime_type="video/mp4")
    if pie:
        texto(s, x, y + h + 0.08, w, 0.42, pie, size=10, color=GRIS_T, interlineado=1.08)


def fondo_arte(s, prs, arte):
    s.shapes.add_picture(str(arte), 0, 0, width=prs.slide_width, height=prs.slide_height)


def notas(s, cadena):
    s.notes_slide.notes_text_frame.text = cadena


# ── el deck ─────────────────────────────────────────────────────────────────────────────────
def construir():
    prs = Presentation()
    prs.slide_width = Inches(ANCHO)
    prs.slide_height = Inches(ALTO)
    n = 0

    # 1 · portada
    n += 1
    s = nueva(prs)
    fondo_arte(s, prs, IMG / "portada_nodos.png")
    texto(s, 0.9, 2.02, 8.6, 0.3, "PRUEBA EN VIVO · FACULTAD DE DERECHO", size=11, color=BRONCE, bold=True)
    texto(s, 0.9, 2.42, 10.6, 1.5, "Open Legal Chile", size=52, color=BLANCO, fuente=FUENTE_T)
    rect(s, 0.92, 3.78, 1.3, 0.05, relleno=BRONCE)
    texto(s, 0.9, 4.02, 9.6, 1.0,
          "Cómo funciona, de lo más básico a lo más complejo: la IA, el agente, las herramientas, el grafo\n"
          "y las reglas de la casa — con una prueba en vivo.", size=14.5, color=CLARO, interlineado=1.25)
    texto(s, 0.9, 6.35, 9.0, 0.35, "Pablo Benavides Jorquera · Septiembre 2026", size=11.5, color=CLARO)
    texto(s, 0.9, 6.72, 11.4, 0.32,
          "Sistema que cita: cada dato muestra de dónde viene.", size=10, color=RGBColor(0x8F, 0xA8, 0xC0))
    notas(s, "Presentación breve. Después, preguntas al azar de los asistentes. Las animaciones se "
             "reproducen dentro de las láminas (clic sobre el video) o desde docs/charla/*.html.")

    # 2 · agenda
    n += 1
    s = nueva(prs)
    chrome(s, None, n)
    titulo(s, "Lo que verán hoy")
    items = [
        ("01", "Los cimientos", "Qué es un LLM, un agente, MCP y una skill.\nCon ejemplos y animaciones."),
        ("02", "El conocimiento", "El corpus chileno, cómo se construyó el grafo\ny cuánto ahorra en tokens."),
        ("03", "El sistema", "Las herramientas, las cifras y las reglas\nde la casa: citas y honestidad."),
        ("04", "Prueba en vivo", "Preguntas al azar. Van a ver las fuentes\naparecer al final de cada respuesta."),
    ]
    for k, (num, t_, d_) in enumerate(items):
        x = 0.55 + k * 3.13
        rect(s, x, 1.95, 2.93, 3.6, relleno=GRIS_F, radio=0.06)
        rect(s, x, 1.95, 2.93, 0.05, relleno=BRONCE if k == 3 else AZUL_M)
        texto(s, x + 0.25, 2.25, 2.4, 0.9, num, size=40, color=GRIS_B, fuente=FUENTE_T, bold=True)
        texto(s, x + 0.25, 3.12, 2.45, 0.4, t_, size=15, bold=True, color=TINTA)
        texto(s, x + 0.25, 3.58, 2.45, 1.7, d_, size=10.6, color=GRIS_T, interlineado=1.2)
    notas(s, "Cuatro partes; la prueba en vivo va al final (o cuando quieran, si se aburren).")

    # 3 · separador parte 1
    n += 1
    s = nueva(prs)
    fondo_arte(s, prs, IMG / "seccion_nodos.png")
    texto(s, 2.6, 1.1, 4.0, 2.4, "1", size=170, color=RGBColor(0x2A, 0x4A, 0x6B), fuente=FUENTE_T, bold=True)
    texto(s, 0.9, 2.6, 8.0, 0.32, "PARTE 1", size=12, color=BRONCE, bold=True)
    texto(s, 0.9, 3.0, 10.5, 0.9, "Los cimientos", size=40, color=BLANCO, fuente=FUENTE_T)
    texto(s, 0.9, 4.0, 9.6, 1.1,
          "Qué es una IA y por qué se equivoca · qué es un agente · el enchufe de las herramientas (MCP)\n"
          "· qué es una skill · y cómo se ve todo junto, por capas.", size=13, color=CLARO, interlineado=1.3)
    notas(s, "Antes del sistema, las piezas básicas. Cada concepto con su ejemplo.")

    # 4 · LLM (bullets + video)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "¿Qué es una IA? ¿Y un «LLM»?", size=24)
    vinetas(s, 0.55, 1.72, 6.6, [
        ("Es una máquina que apuesta a la palabra siguiente: ", "así se entrenó, leyendo millones de textos."),
        ("No consulta una base de datos ni «sabe» derecho: ", "calcula probabilidades."),
        ("Fortaleza: redacta, resume, traduce. ", "Debilidad: inventa con seguridad."),
    ], size=11.4, alto=1.9)
    marco_video(s, "animacion_llm", 0.55, 3.62, 7.1, 3.2,
                "La máquina de la siguiente palabra: elige «Corte» porque lo leyó miles de veces — y puede "
                "equivocarse con la misma seguridad.")
    notas(s, "Correr el video (clic) y volver sobre la frase: no es una enciclopedia, es un redactor "
             "probabilístico. Ese defecto explica todo lo que sigue.")

    # 5 · en qué se equivoca
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "En qué se equivoca (y cómo lo compensamos)")
    tarjeta(s, 0.55, 1.85, 3.9, 4.0, "El riesgo",
            "Un modelo solo puede inventar una cita de un fallo que no existe, un artículo que no dice "
            "eso, un plazo que suena razonable. Y lo dice con la misma seguridad con que acierta.")
    tarjeta(s, 4.72, 1.85, 3.9, 4.0, "La respuesta de la casa",
            "No se le pide memoria: se le conectan fuentes reales (BCN, Contraloría, DT, doctrina, "
            "corpus) y se le exige citar. Lo que no tiene fuente, se dice.", acento=VERDE)
    tarjeta(s, 8.89, 1.85, 3.9, 4.0, "La regla",
            "Toda respuesta que use una fuente la cita. En los documentos, a pie de página. En la "
            "conversación, al final. Sin fuente verificable: se dice.", acento=BRONCE,
            relleno_=CREMA)
    notas(s, "Aquí está el porqué de las reglas: sin citas, un LLM es un pasante que no sabés si "
             "estudió o improvisó.")

    # 6 · harness
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "¿Qué es un agente (o «harness»)?")
    tarjeta(s, 0.55, 1.85, 3.9, 3.9, "El motor",
            "El LLM solo: puede conversar, pero no busca, no lee tus archivos, no usa herramientas y "
            "olvida todo al cerrar.")
    tarjeta(s, 4.72, 1.85, 3.9, 3.9, "El auto completo",
            "El agente le da al motor: herramientas (MCP), procedimientos (skills), memoria, permisos "
            "y reglas. Decide cuándo usar cada cosa y deja rastro.", acento=VERDE)
    tarjeta(s, 8.89, 1.85, 3.9, 3.9, "Ejemplos",
            "Claude Code · Antigravity · Hermes (el de esta casa). Todos hablan el mismo idioma de "
            "herramientas.", acento=BRONCE)
    notas(s, "Ejemplo vivo para la demo: «analizame esta carpeta» — el agente llama solo a las "
             "herramientas, sin comandos.")

    # 7 · MCP
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "¿Qué es MCP? El enchufe de las herramientas")
    texto(s, 0.55, 1.8, 6.4, 3.6,
          [[("Un protocolo estándar: ", {"bold": True, "color": TINTA}),
            ("como el USB-C, deja que cualquier agente use las mismas herramientas sin trabajo a "
             "medida.", {})],
           [("Open Legal Chile expone 74 herramientas por MCP: ", {"bold": True, "color": TINTA}),
            ("BCN, Contraloría, Dirección del Trabajo, SII, CMF, SMA, PJUD, doctrina, grafo…", {})],
           [("El abogado no llama comandos: ", {"bold": True, "color": TINTA}),
            ("pregunta en lenguaje natural y el agente elige el enchufe correcto.", {})]],
          size=11.6, color=GRIS_T, interlineado=1.22, espacio=9)
    rect(s, 7.4, 2.25, 1.35, 1.35, relleno=AZUL, radio=0.5)
    texto(s, 7.4, 2.68, 1.35, 0.5, "Agente", size=12, color=BLANCO, bold=True, align=PP_ALIGN.CENTER)
    for k, h in enumerate(["BCN", "Contraloría", "DT", "Doctrina", "Grafo"]):
        y = 1.62 + k * 0.68
        rect(s, 9.4, y, 3.35, 0.52, relleno=GRIS_F, radio=0.22, linea=GRIS_B)
        texto(s, 9.62, y + 0.13, 3.0, 0.3, h, size=11, color=TINTA, bold=True)
        rect(s, 8.75, y + 0.26, 0.65, 0.012, relleno=GRIS_B)
    notas(s, "Ventaja: se conecta una vez y sirve para cualquier cliente de IA que hable MCP.")

    # 8 · skill
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "¿Qué es una skill? El manual de procedimiento")
    vinetas(s, 0.55, 1.8, 6.2, [
        ("Un procedimiento escrito ", "que el agente lee antes de actuar: como un protocolo del estudio."),
        ("La casa tiene 18 skills: ", "laboral, familia, contratos, societario, dossier, auditoría…"),
        ("Regla de oro: ", "lo que no tiene fuente verificable, se dice; no se inventa."),
    ], size=11.4, alto=2.2)
    rect(s, 7.15, 1.8, 5.63, 3.9, relleno=GRIS_F, radio=0.05)
    rect(s, 7.15, 1.8, 0.055, 3.9, relleno=AZUL_M)
    texto(s, 7.42, 1.98, 5.1, 0.3, "Ejemplo real: chilean-case-intake", size=11.5, bold=True, color=TINTA)
    texto(s, 7.42, 2.36, 5.12, 3.2,
          "Cuando llega una carpeta de caso, la skill define el procedimiento:\n\n"
          "1.  Detectar la materia por código (patrones chilenos: Rol, RIT, palabras clave).\n"
          "2.  Leer todos los documentos, incluido lo escaneado (OCR en español).\n"
          "3.  Armar la línea de tiempo y las partes.\n"
          "4.  Buscar normas, dictámenes y doctrina — cada uno con su fuente.\n"
          "5.  Redactar el informe en Word, con citas a pie de página.",
          size=10.6, color=GRIS_T, interlineado=1.22, espacio=2)
    notas(s, "Las skills son la diferencia entre un chat genérico y un sistema que trabaja como el "
             "estudio.")

    # 9 · capas
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 1 · Los cimientos", n)
    titulo(s, "Todo junto, por capas")
    marco_imagen(s, IMG / "capas.png", 2.35, 1.6, 8.6, 5.1,
                 "Del modelo al escritorio: LLM → agente → MCP → herramientas, skills, corpus y "
                 "conectores → el abogado preguntando.")
    notas(s, "Recorrer las capas de arriba abajo: cada una agrega algo que al LLM solo le falta.")

    # 10 · separador parte 2
    n += 1
    s = nueva(prs)
    fondo_arte(s, prs, IMG / "seccion_nodos.png")
    texto(s, 2.6, 1.1, 4.0, 2.4, "2", size=170, color=RGBColor(0x2A, 0x4A, 0x6B), fuente=FUENTE_T, bold=True)
    texto(s, 0.9, 2.6, 8.0, 0.32, "PARTE 2", size=12, color=BRONCE, bold=True)
    texto(s, 0.9, 3.0, 10.5, 0.9, "El conocimiento", size=40, color=BLANCO, fuente=FUENTE_T)
    texto(s, 0.9, 4.0, 9.8, 1.1,
          "El corpus chileno en Markdown · cómo se construyó el grafo · el ahorro de tokens medido\n"
          "· y cómo operan las citas.", size=13, color=CLARO, interlineado=1.3)
    notas(s, "Del conocimiento: cómo el sistema sabe derecho chileno sin leer todo cada vez.")

    # 11 · problema del contexto
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "El problema del contexto")
    bigcard(s, 0.55, 1.9, 2.95, 1.95, "248", "documentos completos en Markdown")
    bigcard(s, 3.68, 1.9, 2.95, 1.95, "68,9 M", "caracteres: decenas de miles de páginas")
    bigcard(s, 6.81, 1.9, 2.95, 1.95, "≈ 4", "caracteres por token: cada palabra leída cuesta")
    bigcard(s, 9.94, 1.9, 2.85, 1.95, "99,9 %", "menos tokens consultando por el grafo", acento=BRONCE)
    vinetas(s, 0.55, 4.15, 12.2, [
        "Leer el corpus entero en cada consulta es caro, lento — y peor: lo importante se diluye.",
        "La salida no es leer más, sino leer mejor: un mapa del derecho chileno y la página exacta.",
    ], size=11.8, alto=1.6)
    notas(s, "Analogía: al abogado no se le da la biblioteca entera; se le da el mapa y la página "
             "exacta.")

    # 12 · cómo se construyó el grafo (video)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "Cómo se construyó el grafo", size=24)
    marco_video(s, "animacion_grafo", 0.55, 1.72, 7.1, 5.1,
                "Seis etapas, todas reproducibles: del PDF al mapa que ahorra tokens.")
    texto(s, 7.95, 1.8, 4.85, 4.6,
          [[("1. ", {"bold": True, "color": AZUL_M}), ("248 documentos de origen, incluidos los escaneados (OCR en español).", {})],
           [("2. ", {"bold": True, "color": AZUL_M}), ("Texto a Markdown con ficha: definición, concordancias y fuente.", {})],
           [("3. ", {"bold": True, "color": AZUL_M}), ("Cada institución, norma y fallo es un nodo.", {})],
           [("4. ", {"bold": True, "color": AZUL_M}), ("Las citas entre documentos son las aristas.", {})],
           [("5. ", {"bold": True, "color": AZUL_M}), ("46 comunidades: los grupos del derecho chileno.", {})],
           [("6. ", {"bold": True, "color": AZUL_M}), ("Las 21 guías entran y se enlazan al corpus.", {})]],
          size=11.2, color=GRIS_T, interlineado=1.2, espacio=9)
    notas(s, "El grafo se reindexa con cada corpus nuevo; cada nodo guarda su archivo de origen.")

    # 13 · el grafo en números
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "El grafo, en números")
    bigcard(s, 0.55, 2.0, 2.95, 2.0, "11.640", "nodos: instituciones, normas, fallos y obras")
    bigcard(s, 3.68, 2.0, 2.95, 2.0, "22.170", "aristas: cómo se conectan entre sí")
    bigcard(s, 6.81, 2.0, 2.95, 2.0, "46", "comunidades detectadas (Leiden)")
    bigcard(s, 9.94, 2.0, 2.85, 2.0, "202", "obras y guías que lo alimentan")
    vinetas(s, 0.55, 4.35, 12.2, [
        "Preguntar al grafo devuelve solo el vecindario relevante: las normas, fallos y doctrina de ese tema.",
        "Cada nodo se puede rastrear hasta su archivo y su enlace: el mapa no inventa, resume.",
    ], size=11.8, alto=1.4)
    notas(s, "Ejemplos reales: «recurso de protección» → Cea Egaña; «falta de servicio» → Bermúdez Soto.")

    # 14 · subgrafo (imagen real)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "Así se ve (muestra real del grafo)")
    marco_imagen(s, IMG / "subgrafo.png", 2.2, 1.6, 8.9, 5.05,
                 "Muestra real: vecindario de un caso sobre despido (181 de los 11.640 nodos). "
                 "Azul: instituciones · verde: normas · rojo: fallos · dorado: obras.")
    notas(s, "Es una muestra de verdad, no una ilustración: sale del grafo que está en el dataset.")

    # 15 · ahorro (video + gráfico)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "El ahorro de tokens, medido", size=24)
    marco_video(s, "animacion_ahorro", 0.55, 1.72, 7.1, 4.55, None)
    marco_imagen(s, IMG / "ahorro.png", 7.95, 1.72, 4.85, 2.72, None)
    vinetas(s, 7.95, 4.72, 4.9, [
        "«despido»: 123 tokens por el grafo vs 113.458 leyendo el corpus.",
        "«corrupción»: 137 vs 89.720. «prescripción»: 157 vs 850.",
    ], size=11, alto=1.8, space=6)
    texto(s, 0.55, 6.55, 7.1, 0.4, "Medido por el propio sistema (calcular_ahorro_tokens). "
          "Escala logarítmica en el gráfico.", size=10, color=GRIS_T)
    notas(s, "El ahorro no es teoría: cada consulta se puede medir y auditar.")

    # 16 · citas (video)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "Cómo operan las citas", size=24)
    marco_video(s, "animacion_citas", 0.55, 1.72, 7.1, 5.1,
                "Dos vías, una regla: toda fuente se cita y se puede rastrear hasta su origen.")
    tarjeta(s, 7.95, 1.8, 4.85, 2.3, "En un documento",
            "Informe, análisis, memorándum, escrito: las citas van a pie de página, numeradas, con "
            "fuente · identificador · enlace.", acento=AZUL_M)
    tarjeta(s, 7.95, 4.3, 4.85, 2.3, "En la conversación",
            "La respuesta va primero y las citas al final, después del texto. Sin fuente verificable "
            "se dice: nunca se rellena el hueco.", acento=BRONCE, relleno_=CREMA)
    notas(s, "Las reglas están en las 18 skills y en los 19 agentes: no dependen del ánimo del momento.")

    # 17 · flujo (video)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "El camino de una pregunta", size=24)
    marco_video(s, "animacion_flujo", 0.55, 1.72, 7.1, 5.1, None)
    texto(s, 7.95, 1.85, 4.85, 4.8,
          [[("1.  Mesa de entrada. ", {"bold": True, "color": TINTA}), ("Decide por código, no adivinando.", {})],
           [("2.  Conectores del Estado. ", {"bold": True, "color": TINTA}), ("DT, BCN… con su enlace.", {})],
           [("3.  Doctrina y guías. ", {"bold": True, "color": TINTA}), ("Índice de búsqueda del corpus.", {})],
           [("4.  Grafo. ", {"bold": True, "color": TINTA}), ("El subgrafo mínimo del tema.", {})],
           [("5.  Respuesta citada. ", {"bold": True, "color": TINTA}), ("Fuentes al final, rastreables.", {})]],
          size=11.2, color=GRIS_T, interlineado=1.2, espacio=11)
    notas(s, "Cada etapa deja rastro: la respuesta se puede rastrear hasta su origen.")

    # 18 · caso completo (video)
    n += 1
    s = nueva(prs)
    chrome(s, "Parte 2 · El conocimiento", n)
    titulo(s, "Un caso, de punta a punta", size=24)
    marco_video(s, "animacion_caso", 0.55, 1.72, 7.1, 5.1,
                "«Analizá esta carpeta»: de los documentos al informe en Word, con citas.")
    vinetas(s, 7.95, 1.9, 4.9, [
        ("La carpeta entra tal como está: ", "incluso escaneados y fotos."),
        ("La mesa de entrada decide por código: ", "materia y figura según patrones chilenos."),
        ("Cada fuente responde con su enlace: ", "lista para citar."),
        ("El informe sale en Word, editable, ", "con las citas a pie de página."),
    ], size=11, alto=3.4, space=9)
    notas(s, "Este es el flujo que van a ver en la prueba en vivo.")

    # 19 · números OLC
    n += 1
    s = nueva(prs)
    chrome(s, None, n)
    titulo(s, "Open Legal Chile, en números")
    bigcard(s, 0.55, 1.95, 2.95, 1.9, "74", "herramientas MCP")
    bigcard(s, 3.68, 1.95, 2.95, 1.9, "10", "conectores del Estado")
    bigcard(s, 6.81, 1.95, 2.95, 1.9, "248", "documentos completos (68,9 M de caracteres)")
    bigcard(s, 9.94, 1.95, 2.85, 1.9, "11.640", "nodos del grafo, con visor interactivo")
    bigcard(s, 0.55, 4.05, 2.95, 1.9, "19", "agentes especializados")
    bigcard(s, 3.68, 4.05, 2.95, 1.9, "18", "skills de procedimiento")
    bigcard(s, 6.81, 4.05, 2.95, 1.9, "6,17 M", "caracteres de guías de la Academia Judicial")
    bigcard(s, 9.94, 4.05, 2.85, 1.9, "2", "grafos: el corpus y las guías, enlazados", acento=BRONCE)
    notas(s, "Todo público: PyPI (openlegal-chile), GitHub y Hugging Face con el corpus completo.")

    # 20 · reglas de la casa
    n += 1
    s = nueva(prs)
    chrome(s, None, n)
    titulo(s, "Las reglas de la casa: citas y honestidad")
    filas = [
        ("Toda fuente se cita.", "En documentos, a pie de página. En la conversación, al final.", AZUL_M),
        ("Los documentos salen en Word.", "Editables, no sólo PDF: el abogado corrige sin conversiones.", VERDE),
        ("Sin fuente verificable, se dice.", "«No tengo fuente para esto» es una respuesta válida.", BRONCE),
        ("Datos de personas, fuera del dataset.", "El corpus público no lleva información personal.", AZUL_M),
        ("Herramienta que puede mentir, no existe.", "La consulta de causas del PJUD se retiró: no había "
         "puerta pública y podía dar información errónea.", RGBColor(0x8F, 0x2F, 0x2F)),
    ]
    for k, (t_, d_, acento) in enumerate(filas):
        y = 1.62 + k * 1.06
        rect(s, 0.55, y, 12.23, 0.94, relleno=GRIS_F, radio=0.10)
        rect(s, 0.55, y, 0.06, 0.94, relleno=acento)
        texto(s, 0.85, y + 0.13, 11.7, 0.32, t_, size=12.6, bold=True, color=TINTA)
        texto(s, 0.85, y + 0.48, 11.7, 0.36, d_, size=10.8, color=GRIS_T, interlineado=1.1)
    notas(s, "Estas reglas viven en AGENTS.md, las 18 skills y los 19 agentes, con pruebas que las "
             "cuidan.")

    # 21 · cierre
    n += 1
    s = nueva(prs)
    fondo_arte(s, prs, IMG / "portada_nodos.png")
    texto(s, 0.9, 1.5, 8.0, 0.32, "PRUEBA EN VIVO", size=12, color=BRONCE, bold=True)
    texto(s, 0.9, 1.92, 11.4, 1.0, "En vivo: pregunten lo que quieran", size=40, color=BLANCO, fuente=FUENTE_T)
    texto(s, 0.9, 3.15, 11.0, 1.7,
          [[("Preguntas al azar, en lenguaje natural: ", {"bold": True, "color": BLANCO}),
            ("casos, plazos, dictámenes, doctrina, análisis de documentos.", {})],
           [("Van a ver las herramientas trabajar y las fuentes aparecer al final. ", {"bold": True, "color": BLANCO}),
            ("Si una fuente no responde, el sistema lo dice: no rellena el hueco.", {})]],
          size=13, color=CLARO, interlineado=1.3, espacio=10)
    texto(s, 0.9, 5.35, 12.0, 1.0,
          "github.com/elpabloultron/open-legal-chile   ·   pypi.org/project/openlegal-chile   ·   "
          "huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile",
          size=11.5, color=CLARO, interlineado=1.4)
    notas(s, "Cerrar invitando a preguntas difíciles: ahí se ve la diferencia entre citar de verdad y "
             "aparentar.")

    # 22 · fuentes
    n += 1
    s = nueva(prs)
    chrome(s, None, n)
    titulo(s, "Fuentes de esta presentación")
    texto(s, 0.55, 1.75, 12.2, 4.9,
          [[("1.", {"bold": True, "color": AZUL_M}), ("  [Corpus completo en Hugging Face] ", {"bold": True, "color": TINTA}),
            ("huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile — 248 documentos, "
             "2 grafos y sus enlaces.", {})],
           [("2.", {"bold": True, "color": AZUL_M}), ("  [Código y auditoría] ", {"bold": True, "color": TINTA}),
            ("github.com/elpabloultron/open-legal-chile — CI, auditoría 360° y 251 pruebas.", {})],
           [("3.", {"bold": True, "color": AZUL_M}), ("  [Paquete instalable] ", {"bold": True, "color": TINTA}),
            ("pypi.org/project/openlegal-chile (1.6.4).", {})],
           [("4.", {"bold": True, "color": AZUL_M}), ("  [Cifras del grafo y del ahorro] ", {"bold": True, "color": TINTA}),
            ("medidas por el propio sistema (legal_graphify: 11.640 nodos · 22.170 aristas · "
             "calcular_ahorro_tokens).", {})],
           [("5.", {"bold": True, "color": AZUL_M}), ("  [Guías de la Academia Judicial] ", {"bold": True, "color": TINTA}),
            ("guias.academiajudicial.cl — 21 guías, en Markdown completo dentro del corpus.", {})],
           [("6.", {"bold": True, "color": AZUL_M}), ("  [Doctrina] ", {"bold": True, "color": TINTA}),
            ("Apuntes de Juan Andrés Orrego Acuña (juanandresorrego.cl) y materiales docentes de la "
             "Academia Judicial.", {})],
           [("7.", {"bold": True, "color": AZUL_M}), ("  [Normativa y dictámenes] ", {"bold": True, "color": TINTA}),
            ("bcn.cl/leychile · contraloría.cl · dt.gob.cl — citados en cada respuesta que los use.", {})]],
          size=11.2, color=GRIS_T, interlineado=1.22, espacio=10)
    notas(s, "La presentación practica lo que predica: sus propias cifras van con fuente.")

    prs.save(str(SALIDA))
    return SALIDA, n


if __name__ == "__main__":
    ruta, laminas = construir()
    print(f"  ✓ {ruta.name} · {laminas} láminas · {ruta.stat().st_size/1e6:.1f} MB")
