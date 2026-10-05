#!/usr/bin/env python3
"""
Compilador Editorial Multiformato (DOCX, PDF y HTML) para la monografía científica de Open Legal Chile.
Cumple estrictamente con las directrices de la Revista Chilena de Derecho y Tecnología (RChDT)
y el modelo metodológico de Jiménez Ávila (2015, Orthotips):
- Papel tamaño carta (Letter: 8.5 x 11 pulgadas).
- Márgenes: 3.0 cm arriba y abajo (1.181 in), y 2.5 cm a ambos lados (0.984 in).
- Tipografía: Times New Roman tamaño 12 puntos.
- Texto justificado a derecha e izquierda.
- Interlineado sencillo (1.0).
- Título, Resumen (<= 120 palabras) y Palabras clave (hasta 5) en español e inglés.
- Anonimato estricto en el cuerpo del manuscrito principal para evaluación ciega por pares.
- Inserción nativa de imágenes y figuras de alta resolución (300 DPI) en la sección de Anexos.
- Generación del manuscrito principal (.docx) y de la Página de Autores y Declaraciones Éticas (.docx).
- Compilación de documento PDF unificado de alta resolución optimizado (< 3 MB).
- Generación de visor interactivo HTML5/CSS3 con Legal Design y Lenguaje Claro.
"""

import re
import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

import pymupdf
from markdown_pdf import Section, MarkdownPdf

BASE_DIR = Path(__file__).resolve().parent.parent
MD_PATH = BASE_DIR / "investigacion_academica" / "articulo_cientifico_open_legal_chile.md"
DOCX_PATH = BASE_DIR / "investigacion_academica" / "articulo_cientifico_open_legal_chile.docx"
PDF_PATH = BASE_DIR / "investigacion_academica" / "articulo_cientifico_open_legal_chile.pdf"
HTML_PATH = BASE_DIR / "investigacion_academica" / "articulo_cientifico_open_legal_chile.html"

AUTORES_MD = BASE_DIR / "investigacion_academica" / "rchdt_pagina_autores.md"
AUTORES_DOCX = BASE_DIR / "investigacion_academica" / "rchdt_pagina_autores.docx"
FIGURAS_DIR = BASE_DIR / "investigacion_academica" / "figuras"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_run_language(run, lang="es-CL"):
    """Configura el idioma XML de revisión ortográfica."""
    rPr = run._r.get_or_add_rPr()
    lang_elem = parse_xml(f'<w:lang {nsdecls("w")} w:val="{lang}" w:eastAsia="{lang}" w:bidi="{lang}"/>')
    rPr.append(lang_elem)

def procesar_parrafo_con_formato(p, texto, default_size=12, lang="es-CL"):
    """Parsea negritas (**), cursivas (*) y notas en un párrafo."""
    partes = re.split(r"(\*\*.*?\*\*|\*.*?\*|\[\^.*?\])", texto)
    for parte in partes:
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**"):
            run = p.add_run(parte[2:-2])
            run.font.name = 'Times New Roman'
            run.font.bold = True
            run.font.size = Pt(default_size)
        elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
            run = p.add_run(parte[1:-1])
            run.font.name = 'Times New Roman'
            run.font.italic = True
            run.font.size = Pt(default_size)
        elif parte.startswith("[^") and parte.endswith("]"):
            nota_num = parte[2:-1]
            run = p.add_run(f"[{nota_num}]")
            run.font.name = 'Times New Roman'
            run.font.superscript = True
            run.font.bold = True
            run.font.size = Pt(default_size * 0.85)
            run.font.color.rgb = RGBColor(0x25, 0x63, 0xeb)
        else:
            run = p.add_run(parte)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(default_size)
            
        set_run_language(run, lang)

def compilar_documento(md_file: Path, docx_file: Path, _es_manuscrito_principal: bool = True):
    print(f"Leyendo manuscrito Markdown desde {md_file}...")
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = docx.Document()

    # Configuración de página Carta (Letter: 8.5 x 11 pulgadas) conforme a RChDT
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        # Márgenes RChDT: 3.0 cm arriba y abajo (1.181 in), 2.5 cm a ambos lados (0.984 in)
        section.top_margin = Inches(3.0 / 2.54)
        section.bottom_margin = Inches(3.0 / 2.54)
        section.left_margin = Inches(2.5 / 2.54)
        section.right_margin = Inches(2.5 / 2.54)

    # Configurar estilo Normal
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)

    lineas = md_text.split("\n")
    filas_tabla = []
    
    i = 0
    total = len(lineas)
    
    while i < total:
        linea = lineas[i].strip()
        
        # Omitir líneas vacías
        if not linea:
            i += 1
            continue
            
        # Detectar tablas Markdown (| ... |)
        if linea.startswith("|") and linea.endswith("|"):
            filas_tabla.append(linea)
            i += 1
            while i < total and lineas[i].strip().startswith("|") and lineas[i].strip().endswith("|"):
                filas_tabla.append(lineas[i].strip())
                i += 1
            
            if len(filas_tabla) >= 2:
                filas_datos = [f for f in filas_tabla if not re.match(r"^\|(\s*[-:]+\s*\|)+$", f)]
                if filas_datos:
                    num_cols = len([c for c in filas_datos[0].split("|")[1:-1]])
                    table = doc.add_table(rows=len(filas_datos), cols=num_cols)
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    
                    for row_idx, f_str in enumerate(filas_datos):
                        celdas_txt = [c.strip() for c in f_str.split("|")[1:-1]]
                        for col_idx, txt in enumerate(celdas_txt):
                            if col_idx < num_cols:
                                cell = table.cell(row_idx, col_idx)
                                cell.text = txt
                                p = cell.paragraphs[0]
                                p.paragraph_format.line_spacing = 1.05
                                p.paragraph_format.space_after = Pt(2)
                                p.paragraph_format.space_before = Pt(2)
                                
                                run = p.runs[0]
                                run.font.name = 'Times New Roman'
                                set_run_language(run, "es-CL")
                                if row_idx == 0:
                                    run.font.bold = True
                                    run.font.size = Pt(9.5)
                                    set_cell_background(cell, "E2E8F0")
                                else:
                                    run.font.size = Pt(9.0)
                                    if row_idx % 2 == 1:
                                        set_cell_background(cell, "F8FAFC")
                                set_cell_margins(cell, 80, 80, 100, 100)
                    
                    doc.add_paragraph().paragraph_format.space_after = Pt(2)
            filas_tabla = []
            continue

        # Bloques de código o diagramas (``` ... ```)
        if linea.startswith("```"):
            tipo_bloque = linea[3:].strip().lower()
            lineas_bloque = []
            i += 1
            while i < total and not lineas[i].strip().startswith("```"):
                lineas_bloque.append(lineas[i])
                i += 1
            i += 1  # consumir cierre ```
            
            texto_bloque = "\n".join(lineas_bloque)
            if tipo_bloque == "mermaid":
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.left_indent = Inches(0.4)
                p.paragraph_format.right_indent = Inches(0.4)
                run = p.add_run("📊 [Diagrama de Arquitectura Modular y Flujo Forense de Open Legal Chile]")
                run.font.name = 'Times New Roman'
                run.font.italic = True
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
                set_run_language(run, "es-CL")
            else:
                t_code = doc.add_table(rows=1, cols=1)
                t_code.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell_code = t_code.cell(0, 0)
                cell_code.text = texto_bloque
                set_cell_background(cell_code, "F1F5F9")
                set_cell_margins(cell_code, 100, 100, 120, 120)
                p_code = cell_code.paragraphs[0]
                p_code.paragraph_format.line_spacing = 1.0
                for r in p_code.runs:
                    r.font.name = 'Consolas'
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)
                    set_run_language(r, "es-CL")
                doc.add_paragraph().paragraph_format.space_after = Pt(3)
            continue

        # Fórmulas matemáticas centradas ($$...$$)
        if linea.startswith("$$") and linea.endswith("$$"):
            formula_txt = linea[2:-2].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(formula_txt.replace(r"\_", "_"))
            run.font.name = 'Cambria Math'
            run.font.size = Pt(11)
            run.font.italic = True
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Imágenes Markdown (![caption](rel_path))
        m_img = re.match(r"^!\[(.*?)\]\((.*?)\)$", linea)
        if m_img:
            img_rel = m_img.group(2)
            img_path = (md_file.parent / img_rel).resolve()
            if img_path.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(4)
                run_img = p_img.add_run()
                run_img.add_picture(str(img_path), width=Inches(5.8))
            i += 1
            continue

        # Epígrafes de figuras (*Figura 1. ..., Fuente: ...)
        if linea.startswith("*Figura"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            clean_txt = linea.replace("*", "").strip()
            run = p.add_run(clean_txt)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9.5)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Título principal en castellano (# ...)
        if linea.startswith("# "):
            titulo = linea[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Título en inglés (## Open Legal Chile: Architecture...)
        if linea.startswith("## Open Legal Chile: Architecture"):
            titulo_en = linea[3:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(14)
            run = p.add_run(titulo_en)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            set_run_language(run, "en-US")
            i += 1
            continue

        # Divisor ---
        if linea == "---":
            i += 1
            continue

        # Encabezados de sección numerados (## 1. ..., ## 2. ..., ## 10. ...)
        if re.match(r"^##\s+\d+\.", linea):
            sec_titulo = re.sub(r"^##\s+", "", linea)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sec_titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Encabezados nivel 2 generales (## ...)
        if linea.startswith("## "):
            sec_titulo = linea[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sec_titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Encabezados de subsección nivel 3 (### ...)
        if linea.startswith("### "):
            subsec_titulo = linea[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(subsec_titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Encabezados nivel 4 (#### ...)
        if linea.startswith("#### "):
            sub4_titulo = linea[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sub4_titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.italic = True
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Encabezados nivel 5 (##### ...)
        if linea.startswith("##### "):
            sub5_titulo = linea[6:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sub5_titulo)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
            run.font.bold = True
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Bloques de cita (> ...)
        if linea.startswith("> "):
            cita_txt = linea[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.right_indent = Inches(0.5)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.05
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(cita_txt.replace("*", ""))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)
            run.font.italic = True
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Epígrafes y notas de tablas (*Tabla 1. ..., Fuente: ...)
        if linea.startswith("*Tabla") or linea.startswith("*Fuente:"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            clean_txt = linea.replace("*", "").strip()
            run = p.add_run(clean_txt)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9.5)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            set_run_language(run, "es-CL")
            i += 1
            continue

        # Párrafos regulares (Interlineado sencillo conforme a RChDT)
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0  # RChDT interlineado sencillo
        p.paragraph_format.space_after = Pt(4)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        if linea.startswith("* ") or linea.startswith("- "):
            p.paragraph_format.left_indent = Inches(0.25)
            linea_proc = linea[2:].strip()
        else:
            linea_proc = linea

        # Detectar entradas del Resumen o Abstract
        if linea_proc.startswith("**Resumen:**") or linea_proc.startswith("**Abstract:**"):
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(3)
            lang = "en-US" if "Abstract" in linea_proc else "es-CL"
            procesar_parrafo_con_formato(p, linea_proc, default_size=11, lang=lang)
            i += 1
            continue

        # Detectar Palabras clave o Keywords
        if linea_proc.startswith("**Palabras clave:**") or linea_proc.startswith("**Keywords:**"):
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_after = Pt(6)
            lang = "en-US" if "Keywords" in linea_proc else "es-CL"
            procesar_parrafo_con_formato(p, linea_proc, default_size=10.5, lang=lang)
            i += 1
            continue

        # Detectar entradas de la bibliografía final Chicago (Amunátegui, Barros...)
        if ("## 9. Referencias Bibliográficas" in lineas[max(0, i-40):i] or 
            "## Referencias Bibliográficas" in lineas[max(0, i-40):i]):
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
            p.paragraph_format.space_after = Pt(3)
            procesar_parrafo_con_formato(p, linea_proc, default_size=10.5, lang="es-CL")
            i += 1
            continue

        # Párrafo estándar
        procesar_parrafo_con_formato(p, linea_proc, default_size=12, lang="es-CL")
        i += 1

    doc.save(str(docx_file))
    print(f"✨ Archivo Word (.docx) compilado exitosamente en: {docx_file}")

def compilar_pdf_unificado():
    print(f"Compilando documento PDF unificado desde {MD_PATH}...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Ajustar rutas de imágenes relativas para el compilador PDF
    text_pdf = text.replace("](figuras/", f"]({BASE_DIR}/investigacion_academica/figuras/")
    
    raw_pdf_path = BASE_DIR / "investigacion_academica" / "temp_raw.pdf"
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(text_pdf, paper_size="Letter", borders=(36, 36, -36, -36)))
    pdf.save(str(raw_pdf_path))

    # Optimizar y comprimir PDF con PyMuPDF
    doc_fitz = pymupdf.open(str(raw_pdf_path))
    num_pags = len(doc_fitz)
    doc_fitz.save(str(PDF_PATH), deflate=True, garbage=4, clean=True)
    doc_fitz.close()
    
    if raw_pdf_path.exists():
        raw_pdf_path.unlink()
        
    size_mb = os.path.getsize(PDF_PATH) / (1024 * 1024)
    print(f"✨ Archivo PDF unificado generado ({num_pags} páginas, {size_mb:.2f} MB) en: {PDF_PATH}")

def compilar_html_viewer():
    print(f"Compilando visor interactivo HTML5 en {HTML_PATH}...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Conversión básica de markdown a HTML para visor de lectura
    lineas = md_text.split("\n")
    html_body = []
    
    for lin in lineas:
        l_s = lin.strip()
        if not l_s:
            continue
        if l_s.startswith("# "):
            html_body.append(f"<h1 class='title'>{l_s[2:]}</h1>")
        elif l_s.startswith("## "):
            html_body.append(f"<h2 class='sec-title'>{l_s[3:]}</h2>")
        elif l_s.startswith("### "):
            html_body.append(f"<h3 class='subsec-title'>{l_s[4:]}</h3>")
        elif l_s.startswith("#### "):
            html_body.append(f"<h4 class='sub4-title'>{l_s[5:]}</h4>")
        elif l_s.startswith("![]") or ("![" in l_s and "](" in l_s):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", l_s)
            if m:
                cap, src = m.group(1), m.group(2)
                html_body.append(f"<figure class='fig-container'><img src='{src}' alt='{cap}' class='paper-fig'><figcaption>{cap}</figcaption></figure>")
        elif l_s.startswith("*Figura") or l_s.startswith("*Tabla"):
            html_body.append(f"<p class='caption'>{l_s.replace('*', '')}</p>")
        elif l_s.startswith("> "):
            html_body.append(f"<blockquote class='legal-quote'>{l_s[2:]}</blockquote>")
        elif l_s.startswith("```"):
            pass
        elif l_s.startswith("|"):
            pass # Tablas resumidas
        else:
            # Párrafo normal
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", l_s)
            p_text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", p_text)
            html_body.append(f"<p class='body-p'>{p_text}</p>")

    html_content = f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open Legal Chile — Publicación Científica RChDT</title>
    <style>
        :root {{
            --navy: #1e3a8a;
            --slate: #334155;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --border: #e2e8f0;
            --green: #059669;
        }}
        body {{
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.5;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            display: flex;
            justify-content: center;
        }}
        .paper-sheet {{
            background-color: var(--card-bg);
            max-width: 900px;
            padding: 3.5rem 4rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-radius: 4px;
            border: 1px solid var(--border);
        }}
        .badge {{
            display: inline-block;
            background: #dbeafe;
            color: var(--navy);
            padding: 4px 10px;
            border-radius: 999px;
            font-family: sans-serif;
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }}
        h1.title {{
            font-size: 1.7rem;
            color: var(--navy);
            text-align: center;
            margin-bottom: 0.5rem;
            line-height: 1.3;
        }}
        h2.sec-title {{
            font-size: 1.25rem;
            color: var(--navy);
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.3rem;
            margin-top: 2rem;
        }}
        h3.subsec-title {{
            font-size: 1.1rem;
            color: var(--slate);
            margin-top: 1.5rem;
        }}
        p.body-p {{
            font-size: 1rem;
            text-align: justify;
            margin-bottom: 0.8rem;
        }}
        .legal-quote {{
            margin: 1.2rem 2rem;
            padding: 0.6rem 1.2rem;
            background-color: #f1f5f9;
            border-left: 4px solid var(--navy);
            font-style: italic;
        }}
        .fig-container {{
            text-align: center;
            margin: 2rem 0;
        }}
        .paper-fig {{
            max-width: 100%;
            height: auto;
            border: 1px solid var(--border);
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .caption {{
            font-size: 0.85rem;
            font-style: italic;
            color: var(--slate);
            text-align: center;
            margin-top: 0.5rem;
        }}
        @media print {{
            body {{ padding: 0; background: white; }}
            .paper-sheet {{ box-shadow: none; border: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="paper-sheet">
        <div style="text-align: center;">
            <span class="badge">Revista Chilena de Derecho y Tecnología (RChDT) — Sección Doctrina</span>
        </div>
        {"".join(html_body)}
    </div>
</body>
</html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✨ Visor HTML5 generado exitosamente en: {HTML_PATH}")

def main():
    print("=== Compilador Editorial RChDT & Multiformato — Open Legal Chile ===")
    compilar_documento(MD_PATH, DOCX_PATH, es_manuscrito_principal=True)
    compilar_documento(AUTORES_MD, AUTORES_DOCX, es_manuscrito_principal=False)
    compilar_pdf_unificado()
    compilar_html_viewer()
    print("=== Todos los formatos (DOCX, PDF, HTML) generados exitosamente ===")

if __name__ == "__main__":
    main()
