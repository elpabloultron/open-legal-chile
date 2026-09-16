"""
Open Legal Chile — Ingestor Doctrinal & Conversor a Markdown Canónico (doc2md_ingestor)
Transforma textos jurídicos desestructurados, PDFs y documentos en Markdown canónico token-optimizado
siguiendo estrictamente las normas ortotipográficas RAE/ASALE y el estándar de Derecho Continental de Chile.
Sincroniza de inmediato el Knowledge Graph (legal_knowledge_graph.json) y el índice SQLite FTS5 de doctrina.
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
import defusedxml.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTRINA_DIR = os.path.join(BASE_DIR, "doctrina")
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_GRAPH_PATH = os.path.join(DATA_DIR, "legal_knowledge_graph.json")


def extract_text_from_source(source: str | Path) -> str:
    """
    Extrae texto crudo a partir de una ruta de archivo (PDF, DOCX, TXT, MD) o devuelve el texto directamente.
    Para DOCX utiliza descompresión XML pura de la biblioteca estándar (cero dependencias externas).
    Para PDF utiliza PyMuPDF (fitz) o el motor forense local si está disponible.
    """
    if isinstance(source, Path):
        source = str(source)

    if os.path.exists(source) and os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()

        if ext in (".txt", ".md"):
            try:
                with open(source, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(source, "r", encoding="latin-1", errors="ignore") as f:
                    return f.read()

        elif ext == ".docx":
            # Extracción pura con zipfile y xml.etree (sin dependencias externas)
            try:
                with zipfile.ZipFile(source) as docx_zip:
                    xml_content = docx_zip.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    paragraphs = []
                    for p in tree.findall(".//w:p", namespaces):
                        texts = [t.text for t in p.findall(".//w:t", namespaces) if t.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    return "\n\n".join(paragraphs)
            except Exception as e:
                raise RuntimeError(f"Error al extraer texto de archivo DOCX '{source}': {e}")

        elif ext == ".pdf":
            try:
                import fitz  # type: ignore # PyMuPDF
                doc = fitz.open(source)
                pages_text = [page.get_text() for page in doc]
                text = "\n\n".join(pages_text).strip()
                if text:
                    return text
            except Exception:
                pass

            # Fallback a ForensicOCREngine si el PDF es escaneado
            try:
                from forensic_ocr import ForensicOCREngine
                ocr = ForensicOCREngine()
                res = ocr.extract_from_pdf(source)
                if res and "pages" in res:
                    ocr_text = "\n\n".join([p.get("text", "") for p in res["pages"] if p.get("text")]).strip()
                    if ocr_text:
                        return ocr_text
            except Exception:
                pass

            raise RuntimeError(
                f"No fue posible extraer texto del archivo PDF '{source}'. "
                "Verifica que el archivo no esté corrupto o protegido con clave."
            )
        else:
            # Archivo genérico: intentar leer como texto UTF-8
            try:
                with open(source, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                with open(source, "r", encoding="latin-1", errors="ignore") as f:
                    return f.read()

    # Si no es un archivo existente, se asume que es el contenido de texto en sí
    return str(source)


def clean_unwanted_hyphens_and_breaks(text: str) -> str:
    """
    Limpia saltos de línea quebrados y une palabras divididas por guion al final de línea
    (ej. 'obli-\\n   gaciones' -> 'obligaciones').
    """
    if not text:
        return ""

    # 1. Unir palabras divididas por guion al final de línea
    text = re.sub(r"([a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+)-\s*\n\s*([a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+)", r"\1\2", text)

    # 2. Suprimir numeración de páginas flotante o encabezados comunes
    text = re.sub(r"\n\s*(?:Página|Pág\.?)\s*\d+\s*(?:de\s*\d+)?\s*\n", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\n\s*---\s*\d+\s*---\s*\n", "\n\n", text)

    # 3. Unir líneas huérfanas dentro de un mismo párrafo preservando saltos dobles
    lines = text.split("\n")
    cleaned_paragraphs: List[str] = []
    current_para: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                cleaned_paragraphs.append(" ".join(current_para))
                current_para = []
        elif stripped.startswith(("#", "-", "*", ">", "|", "1.", "2.", "3.", "4.", "5.")):
            if current_para:
                cleaned_paragraphs.append(" ".join(current_para))
                current_para = []
            cleaned_paragraphs.append(stripped)
        else:
            current_para.append(stripped)

    if current_para:
        cleaned_paragraphs.append(" ".join(current_para))

    result = "\n\n".join(cleaned_paragraphs)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def apply_ortotipografia_rae_chile(text: str) -> str:
    """
    Aplica estrictamente las normas de la RAE, ASALE y la Academia Chilena de la Lengua:
    1. Comillas primarias angulares o latinas (« »); comillas dobles inglesas (" ") solo dentro de citas.
    2. Puntuación SIEMPRE fuera de las comillas de cierre: «ejemplo», «ejemplo».
    3. Signos de apertura obligatorios: ¿ y ¡.
    4. Cifras con coma decimal en Chile (12,5 %) y espacio obligatorio antes de %.
    5. RUT con puntos en millares y guion antes del dígito verificador (12.345.678-9).
    6. Abreviaturas oficiales: N.° para número, Art. para artículo, inc. para inciso.
    """
    if not text:
        return ""

    res = text

    # 1. Espacio antes de porcentaje: '100%' -> '100 %', '25.5%' -> '25.5 %'
    res = re.sub(r"(\d+)%", r"\1 %", res)

    # 2. Coma decimal en Chile para porcentajes y decimales habituales
    res = re.sub(r"(\d+)\.(\d+)\s*%", r"\1,\2 %", res)
    res = re.sub(r"(\b\d+)\.(\d+)\s*(UF|UTM|pesos)", r"\1,\2 \3", res)

    # 3. Normalizar comillas dobles inglesas a latinas « » si no están ya en latinas
    res = re.sub(r'(?<!\w)"([^"\n]+?)"(?!\w)', r'«\1»', res)

    # 4. Puntuación fuera de las comillas de cierre: «ejemplo.» -> «ejemplo».
    res = re.sub(r'([«“"])([^»”"]+?)([,\.;:])([»”"])', r'\1\2\4\3', res)

    # 5. Normalizar abreviaturas: N° -> N.° | No. -> N.°
    res = re.sub(r"\bN°\s*", "N.° ", res)
    res = re.sub(r"\bNo\.\s*(\d+)", r"N.° \1", res)

    # 6. Normalizar Art. / Arts.
    res = re.sub(r"\b[Aa]rt(?:[ií]culo)?\s*(\d+)", r"Art. \1", res)
    res = re.sub(r"\b[Aa]rt(?:[ií]culos)?\s*(\d+)", r"Arts. \1", res)
    res = re.sub(r"\b[Ii]nciso\s*(\d+)", r"inc. \1", res)

    # 7. Normalizar formato de RUT chileno: XX.XXX.XXX-Y
    def _format_rut(match: re.Match[str]) -> str:
        raw_num = match.group(1).replace(".", "").replace(" ", "")
        dv = match.group(2).upper()
        if len(raw_num) in (7, 8):
            num = int(raw_num)
            formatted = f"{num:,}".replace(",", ".")
            return f"{formatted}-{dv}"
        return match.group(0)

    res = re.sub(r"\b(\d{1,2}(?:\.?\d{3}){2})-?([0-9kK])\b", _format_rut, res)

    return res


def standardize_legal_citations(text: str) -> str:
    """
    Detecta menciones a cuerpos legales, Códigos de la República y jurisprudencia
    y las transforma al estándar de citación oficial entre corchetes de Open Legal Chile:
    - [BCN - Código Civil, Art. 1545]
    - [BCN - Ley N° 21.643, Art. 2]
    - [CS - Rol N° 12.345-2023]
    - [Dictamen DT N° 1234/15]
    - [Dictamen CGR N° E123456]
    """
    if not text:
        return ""

    res = text

    # 1. Códigos Fundamentales de Chile
    codigos_map = [
        (r"\b(?:del\s+)?Código Civil\b", "Código Civil"),
        (r"\b(?:del\s+)?Código del Trabajo\b", "Código del Trabajo"),
        (r"\b(?:del\s+)?Código de Procedimiento Civil\b", "Código de Procedimiento Civil"),
        (r"\b(?:del\s+)?Código Penal\b", "Código Penal"),
        (r"\b(?:del\s+)?Código de Comercio\b", "Código de Comercio"),
        (r"\b(?:del\s+)?Código Tributario\b", "Código Tributario"),
        (r"\b(?:del\s+)?Código Procesal Penal\b", "Código Procesal Penal"),
        (r"\b(?:del\s+)?Código Orgánico de Tribunales\b", "Código Orgánico de Tribunales"),
        (r"\b(?:del\s+)?Código de Aguas\b", "Código de Aguas"),
        (r"\b(?:del\s+)?Código de Minería\b", "Código de Minería"),
    ]

    for pattern, nombre_codigo in codigos_map:
        res = re.sub(
            rf"\b(Arts?\.?\s*\d+(?:\s*(?:bis|ter|quater))?(?:\s*(?:inc\.?\s*\d+|N\.?°?\s*\d+))*)\s+{pattern}",
            rf"[BCN - {nombre_codigo}, \1]",
            res,
            flags=re.IGNORECASE,
        )
        # Formato inverso: 'Código Civil, Art. 1545' (con negative lookbehind para evitar duplicar)
        res = re.sub(
            rf"(?<!\[BCN -\s)\b{nombre_codigo},?\s+(Arts?\.?\s*\d+(?:\s*(?:bis|ter|quater))?(?:\s*(?:inc\.?\s*\d+|N\.?°?\s*\d+))*)",
            rf"[BCN - {nombre_codigo}, \1]",
            res,
            flags=re.IGNORECASE,
        )

    # Siglas breves: CC, CPC, CPP, CP, CT, COT
    siglas_map = {
        "CC": "Código Civil",
        "CPC": "Código de Procedimiento Civil",
        "CPP": "Código Procesal Penal",
        "CP": "Código Penal",
        "CT": "Código del Trabajo",
        "COT": "Código Orgánico de Tribunales",
    }
    for sigla, nombre_codigo in siglas_map.items():
        res = re.sub(
            rf"\b(Arts?\.?\s*\d+(?:\s*(?:bis|ter|quater))?(?:\s*(?:inc\.?\s*\d+|N\.?°?\s*\d+))*)\s+del\s+{sigla}\b",
            rf"[BCN - {nombre_codigo}, \1]",
            res,
        )
        res = re.sub(
            rf"\b(Arts?\.?\s*\d+(?:\s*(?:bis|ter|quater))?(?:\s*(?:inc\.?\s*\d+|N\.?°?\s*\d+))*)\s+{sigla}\b(?!\w)",
            rf"[BCN - {nombre_codigo}, \1]",
            res,
        )

    # 2. Leyes de la República: 'Ley N° 21.643', 'Ley 19.886'
    def _format_ley(m: re.Match[str]) -> str:
        num = m.group(1).replace(".", "")
        art_part = f", {m.group(2).strip()}" if m.group(2) else ""
        return f"[BCN - Ley N° {num}{art_part}]"

    res = re.sub(
        r"\bLey\s*(?:N\.?°?|número)?\s*(\d{1,2}(?:\.?\d{3}))(?:\s*,?\s*(Arts?\.?\s*\d+(?:\s*(?:bis|ter))?(?:\s*inc\.?\s*\d+)?))?\b",
        _format_ley,
        res,
        flags=re.IGNORECASE,
    )

    # 3. Constitución Política: 'Art. 19 N° 24 de la Constitución'
    res = re.sub(
        r"\b(Arts?\.?\s*\d+(?:\s*N\.?°?\s*\d+)?(?:\s*inc\.?\s*\d+)?)\s+(?:de\s+la\s+)?(?:Constitución|CPR|Constitución Política)\b",
        r"[CPR 1980 - \1]",
        res,
        flags=re.IGNORECASE,
    )

    # 4. Roles de la Corte Suprema y Cortes de Apelaciones: 'Rol N° 12.345-2023'
    def _format_rol(m: re.Match[str]) -> str:
        rol_num = m.group(1)
        tribunal = m.group(2) or "CS"
        trib_code = "CS" if any(t in tribunal.upper() for t in ["SUPREMA", "CS"]) else tribunal
        return f"[{trib_code} - Rol N° {rol_num}]"

    res = re.sub(
        r"\bRol\s*(?:N\.?°?|número)?\s*(\d+[\.\d]*-\d{4})\s*(?:(?:de\s+la\s+)?(Corte Suprema|CS|C\.?A\.?\s+de\s+[A-Za-z]+))?\b",
        _format_rol,
        res,
        flags=re.IGNORECASE,
    )

    # 5. Dictámenes DT y CGR
    res = re.sub(
        r"\bDictamen\s*(?:DT)?\s*(?:N\.?°?|número)?\s*(\d+/\d{2,4})\b",
        r"[Dictamen DT N° \1]",
        res,
        flags=re.IGNORECASE,
    )
    res = re.sub(
        r"\bDictamen\s*(?:CGR)?\s*(?:N\.?°?|número)?\s*([E]?\d{5,8}(?:/\d{2,4})?)\b",
        r"[Dictamen CGR N° \1]",
        res,
        flags=re.IGNORECASE,
    )

    # Evitar duplicaciones de corchetes como [[BCN - ...]]
    res = re.sub(r"\[\[(.*?)\]\]", r"[\1]", res)

    return res


def segment_institutions(clean_text: str) -> List[Dict[str, Any]]:
    """
    Segmenta un texto dogmático o procesal en instituciones jurídicas individuales,
    extrayendo definición, requisitos, operativa procesal, concordancias y precedentes.
    """
    institutions: List[Dict[str, Any]] = []

    # Intentar división por encabezados de nivel 2 o secciones numéricas
    raw_sections = re.split(r"\n(?=##\s+|###\s+|(?:\d+\.|\bI{1,3}\.|\bIV\.|\bV\.|\bVI\.)\s+[A-ZÁÉÍÓÚÑ])", clean_text)

    for sec in raw_sections:
        sec_str = sec.strip()
        if not sec_str or len(sec_str) < 30:
            continue

        lines = [line.strip() for line in sec_str.split("\n") if line.strip()]
        if not lines:
            continue

        # Determinar título
        header_candidate = lines[0]
        header_clean = re.sub(r"^(?:#+|\d+\.|\bI{1,3}\.|\bIV\.|\bV\.|\bVI\.)\s*", "", header_candidate).strip()
        header_clean = re.sub(r"^🏛️\s*", "", header_clean).strip()

        if len(header_clean) < 3 or header_clean.lower().startswith(("capítulo", "introducción", "bibliografía", "índice")):
            continue

        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # 1. Definición Canónica
        def_match = re.search(r"(?:Definición(?:\s*Canónica)?|Concepto|Noción):\s*(.*?)(?=\n\n|\n\*\*|\n\*|\Z)", body, re.DOTALL | re.IGNORECASE)
        if def_match:
            definicion = def_match.group(1).strip()
        else:
            first_p = lines[1] if len(lines) > 1 else body[:250]
            definicion = first_p.strip()

        # 2. Requisitos / Elementos
        req_match = re.search(r"(?:Requisitos(?:\s*Copulativos)?|Elementos|Condiciones|Clasificación):\s*(.*?)(?=\n\n(?:Operativa|Concordancias|Criterio)|\n\*\*Operativa|\Z)", body, re.DOTALL | re.IGNORECASE)
        requisitos = req_match.group(1).strip() if req_match else ""

        # 3. Operativa Procesal Forense
        proc_match = re.search(r"(?:Operativa\s*Procesal\s*Forense|Vía\s*Procesal|Efectos\s*Procesales|Titularidad\s*y\s*Plazos):\s*(.*?)(?=\n\n(?:Concordancias|Criterio)|\n\*\*Concordancias|\Z)", body, re.DOTALL | re.IGNORECASE)
        operativa = proc_match.group(1).strip() if proc_match else ""

        # 4. Concordancias BCN
        concordancias = re.findall(r"\[BCN\s*-\s*[^\]]+\]", body)
        if not concordancias:
            concordancias = re.findall(r"(?:Arts?\.?\s*\d+(?:\s*(?:bis|ter|quater))?(?:\s*(?:inc\.?\s*\d+|N\.?°?\s*\d+))*\s*(?:del\s*)?(?:Código Civil|Código del Trabajo|CPC|CPP|CP|COT|CPR|Ley\s*\d+[\.\d]*))", body)

        # 5. Criterios Jurisprudenciales
        criterios = re.findall(r"\[(?:CS|C\.?A\.?)\s*-\s*Rol\s*[^\]]+\]", body)
        if not criterios:
            criterios = re.findall(r"Rol\s*N\.?°?\s*\d+[\.\d]*-\d{4}", body)

        institutions.append({
            "titulo": header_clean,
            "definicion": definicion,
            "requisitos": requisitos,
            "operativa": operativa,
            "concordancias": list(dict.fromkeys(concordancias)),
            "criterios": list(dict.fromkeys(criterios)),
            "contenido_crudo": sec_str
        })

    # Si no se detectaron secciones específicas, crear una sola institución global
    if not institutions and len(clean_text.strip()) > 30:
        concordancias = re.findall(r"\[BCN\s*-\s*[^\]]+\]", clean_text)
        criterios = re.findall(r"\[(?:CS|C\.?A\.?)\s*-\s*Rol\s*[^\]]+\]", clean_text)
        institutions.append({
            "titulo": "Institución Principal",
            "definicion": clean_text[:400].strip(),
            "requisitos": "",
            "operativa": "",
            "concordancias": list(dict.fromkeys(concordancias)),
            "criterios": list(dict.fromkeys(criterios)),
            "contenido_crudo": clean_text.strip()
        })

    return institutions


def convert_text_to_canonical_markdown(
    raw_text: str,
    obra: str = "Tratado Doctrinal",
    autor: str = "Doctrina Nacional",
    area: str = "Derecho Civil",
    materia: str = "Teoría General",
) -> str:
    """
    Convierte cualquier texto o extracto en el formato Markdown canónico token-optimizado
    de Open Legal Chile y LegalGraphify.
    """
    cleaned = clean_unwanted_hyphens_and_breaks(raw_text)
    orto = apply_ortotipografia_rae_chile(cleaned)
    standardized = standardize_legal_citations(orto)

    institutions = segment_institutions(standardized)

    output_lines = [
        f"# {obra.upper()}",
        f"**Tratadista:** {autor} | **Área:** {area.title()} | **Materia:** {materia}",
        "> 💡 *Ficha Dogmática Canónica de Alta Densidad (Token-Optimized) para Open Legal Chile.*",
        "",
        "---",
        ""
    ]

    for inst in institutions:
        titulo = inst["titulo"]
        definicion = inst["definicion"]
        requisitos = inst["requisitos"]
        operativa = inst["operativa"]
        concordancias = inst["concordancias"]
        criterios = inst["criterios"]

        output_lines.append(f"## 🏛️ {titulo}")
        output_lines.append("**Definición Canónica:**  ")
        output_lines.append(definicion or "Institución jurídica del ordenamiento nacional.")
        output_lines.append("")

        if requisitos:
            output_lines.append("**Requisitos y Clasificación:**")
            output_lines.append(requisitos)
            output_lines.append("")

        output_lines.append("**Operativa Procesal Forense:**")
        if operativa:
            output_lines.append(operativa)
        else:
            output_lines.append("Se hace valer en juicio ordinario o especial respectivo mediante acción o excepción procesal oportuna conforme a las reglas generales.")
        output_lines.append("")

        concord_str = " ".join([f"`{c}`" if not str(c).startswith("`") else str(c) for c in concordancias]) if concordancias else "`[BCN - Código Civil, Art. 1437]`"
        output_lines.append(f"**Concordancias Legales:** {concord_str}  ")

        criterios_str = " ".join([f"`{c}`" if not str(c).startswith("`") else str(c) for c in criterios]) if criterios else "`[CS - Jurisprudencia Unificada]`"
        output_lines.append(f"**Criterio Jurisprudencial Rector:** {criterios_str}")
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    return "\n".join(output_lines).strip() + "\n"


def ingestar_documento_doctrinal(
    file_path: str,
    area: str = "civil",
    tratadista: str = "",
    obra: str = "",
    materia: str = "",
    actualizar_grafo: bool = True,
    target_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pipeline de ingesta integral:
    1. Extrae texto de la fuente (PDF, DOCX, TXT, MD).
    2. Aplica ortotipografía RAE/ASALE y estandarización de citas chilenas.
    3. Genera Markdown canónico token-optimizado y lo persiste en disco.
    4. Sincroniza automáticamente:
       - El índice SQLite FTS5 de doctrina (doctrina.db).
       - El Knowledge Graph multidimensional (data/legal_knowledge_graph.json) si actualizar_grafo es True.
    """
    raw_text = extract_text_from_source(file_path)
    if not raw_text.strip():
        raise ValueError(f"El archivo o texto fuente '{file_path}' está vacío.")

    # Inferir metadatos si no fueron provistos
    base_name = os.path.splitext(os.path.basename(file_path))[0] if os.path.exists(file_path) else "documento_doctrinal"
    inferred_obra = obra or base_name.replace("_", " ").title()
    inferred_autor = tratadista or "Doctrina Nacional"
    inferred_area = area or "civil"
    inferred_materia = materia or "Dogmática Jurídica"

    canonical_md = convert_text_to_canonical_markdown(
        raw_text=raw_text,
        obra=inferred_obra,
        autor=inferred_autor,
        area=inferred_area,
        materia=inferred_materia
    )

    # Determinar ruta de destino
    if target_path:
        out_file = Path(target_path)
    else:
        norm_area = inferred_area.lower().strip()
        if "laboral" in norm_area or "trabajo" in norm_area:
            sub_dir = "laboral"
        elif "penal" in norm_area:
            sub_dir = "penal"
        elif "procesal" in norm_area:
            sub_dir = "procesal"
        elif "admin" in norm_area:
            sub_dir = "administrativo"
        elif "const" in norm_area:
            sub_dir = "constitucional"
        elif "comerc" in norm_area:
            sub_dir = "comercial"
        else:
            sub_dir = "civil"

        dest_dir = os.path.join(DOCTRINA_DIR, sub_dir)
        os.makedirs(dest_dir, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", base_name.lower()).strip("_") or "doctrina_nueva"
        out_file = Path(dest_dir) / f"{safe_name}.md"

    os.makedirs(out_file.parent, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(canonical_md)

    # Métricas de compresión de tokens (~3.8 caracteres por token)
    tokens_orig = max(1, int(len(raw_text) / 3.8))
    tokens_md = max(1, int(len(canonical_md) / 3.8))
    ahorro_pct = round(((tokens_orig - tokens_md) / tokens_orig) * 100, 1)

    # Contar instituciones detectadas
    inst_count = len(re.findall(r"^##\s+🏛️", canonical_md, re.MULTILINE))
    if inst_count == 0:
        inst_count = len(re.findall(r"^##\s+", canonical_md, re.MULTILINE))

    # Sincronización automática 1: Índice SQLite FTS5 de doctrina
    fts_actualizado = False
    total_inst_fts = 0
    try:
        from doctrina_connector import index_all_doctrina
        total_inst_fts = index_all_doctrina()
        fts_actualizado = True
    except Exception as e:
        print(f"Advertencia al indexar doctrina FTS5: {e}", file=sys.stderr)

    # Sincronización automática 2: Grafo de Conocimiento (LegalGraphify)
    grafo_actualizado = False
    total_nodos = 0
    total_aristas = 0
    if actualizar_grafo:
        try:
            from legal_graphify import LegalGraphifyEngine
            engine = LegalGraphifyEngine(doctrina_dir=DOCTRINA_DIR)
            engine.construir_grafo_desde_doctrina()
            engine.guardar_grafo_json(DEFAULT_GRAPH_PATH)
            grafo_actualizado = True
            total_nodos = engine.graph.number_of_nodes()
            total_aristas = engine.graph.number_of_edges()
        except Exception as e:
            print(f"Advertencia al actualizar Knowledge Graph: {e}", file=sys.stderr)

    return {
        "status": "success",
        "file_path": str(file_path),
        "markdown_path": str(out_file),
        "area": inferred_area,
        "tratadista": inferred_autor,
        "obra": inferred_obra,
        "instituciones_detectadas": inst_count,
        "tokens_original": tokens_orig,
        "tokens_markdown": tokens_md,
        "tokens_ahorrados": tokens_orig - tokens_md,
        "ahorro_tokens_pct": ahorro_pct,
        "grafo_actualizado": grafo_actualizado,
        "fts_actualizado": fts_actualizado,
        "total_nodos_grafo": total_nodos,
        "total_aristas_grafo": total_aristas,
        "total_instituciones_fts": total_inst_fts,
        "mensaje": f"Documento asimilado exitosamente: {inst_count} instituciones dogmáticas incorporadas al canon."
    }
