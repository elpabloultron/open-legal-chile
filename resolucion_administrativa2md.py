"""
Open Legal Chile — Conversor Universal de Resoluciones y Dictámenes Administrativos a Markdown Canónico
(resolucion_administrativa2md.py / dictamen2md.py)

Estandariza pronunciamientos, dictámenes, circulares, instrucciones y sentencias regulatorias
de los órganos del Estado chileno (CGR, DT, SII, TDLC, CMF, Panel de Expertos y SMA) en Markdown
canónico token-optimizado con Frontmatter YAML y segmentación anatómica.
"""

import os
import re
import pathlib
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_MD_DIR = BASE_DIR / "data" / "dictamenes_md"


def _limpiar_texto(texto: str) -> str:
    """Limpia saltos de línea excesivos y normaliza espacios en blanco."""
    if not texto:
        return ""
    texto = re.sub(r"\r\n|\r", "\n", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _escapar_yaml_str(valor: Any) -> str:
    """Escapa de forma segura cadenas para Frontmatter YAML."""
    if valor is None:
        return '""'
    s = str(valor).strip().replace('"', '\\"')
    return f'"{s}"'


def segmentar_secciones_administrativas(texto_integral: str, organismo: str = "CGR") -> Dict[str, Any]:
    """
    Segmenta anatómicamente el texto de un dictamen o resolución administrativa:
    Antecedentes/Vistos, Marco Normativo, Consideraciones/Análisis y Conclusión/Doctrina.
    """
    texto = _limpiar_texto(texto_integral)
    if not texto:
        return {
            "antecedentes": "",
            "marco_normativo": [],
            "consideraciones": [],
            "conclusion": ""
        }

    # Detección de normas legales citadas en el texto (Leyes, Códigos, Artículos, DFL, DL, CPR)
    patron_normas = (
        r"(?:(?:art[íi]culo|art\.)\s+\d+(?:\s*(?:bis|ter|qu[aá]ter|inciso\s+\d+|inc\.\s*\d+))?\s*(?:de\s+la\s+|del\s+)?(?:c[oó]digo\s+[a-z]+|ley\s+(?:n[°º]?\s*)?\d+[\.\d]*|dfl\s+\d+(?:/\d+)?|dl\s+\d+|cpr)?|"
        r"ley\s+(?:n[°º]?\s*)?\d+[\.\d]*|c[oó]digo\s+(?:civil|del\s+trabajo|tributario|penal|de\s+procedimiento\s+civil|cpc)|"
        r"dfl\s+(?:n[°º]?\s*)?\d+(?:/\d+)?|dl\s+(?:n[°º]?\s*)?\d+|cpr|constituci[oó]n\s+pol[íi]tica)"
    )
    normas_encontradas = re.findall(patron_normas, texto, re.IGNORECASE)
    normas_unicas = list(dict.fromkeys([n.strip() for n in normas_encontradas if len(n.strip()) > 3]))

    # Segmentación por fórmulas administrativas de cierre / conclusión
    patron_conclusion = (
        r"(?:En\s+consecuencia|En\s+m[eé]rito\s+de\s+lo\s+expuesto|Por\s+consiguiente|"
        r"Esta\s+Contralor[íi]a\s+General\s+concluye|Cumplo\s+con\s+informar|Se\s+resuelve|"
        r"Por\s+tanto|En\s+estas\s+condiciones|Concluyentemente)[,:\s]+(.*?)(?=(?:Saluda\s+atentamente|Dios\s+guarde|Pronunciado\s+por|$))"
    )
    m_conclusion = re.search(patron_conclusion, texto, re.DOTALL | re.IGNORECASE)
    conclusion = m_conclusion.group(1).strip() if m_conclusion else ""

    # Segmentación de antecedentes iniciales
    patron_antecedentes = (
        r"^(.*?)(?=(?:Sobre\s+el\s+particular|Al\s+respecto|En\s+cuanto\s+al\s+fondo|"
        r"En\s+primer\s+lugar|Analizados\s+los\s+antecedentes|Considerando))"
    )
    m_antecedentes = re.search(patron_antecedentes, texto, re.DOTALL | re.IGNORECASE)
    antecedentes = m_antecedentes.group(1).strip() if m_antecedentes else texto[:400].strip()

    # Consideraciones y párrafos de análisis
    # Soporta tanto división por doble salto como por líneas independientes
    lineas_raw = [lin.strip() for lin in re.split(r"\n\s*\n|\n(?=[A-ZÁÉÍÓÚ0-9«\-])", texto) if len(lin.strip()) > 25]
    consideraciones: List[Dict[str, Any]] = []

    for lin in lineas_raw:
        # Excluir saludos o encabezados de pie puros
        if re.search(r"^(?:Saluda\s+atentamente|Dios\s+guarde|Santiago,|Valpara[íi]so,|Concepci[oó]n,|Jorge\s+Berm|Pronunciado\s+por)", lin, re.IGNORECASE):
            continue
        es_derecho = bool(re.search(r"art[íi]culo|ley|c[oó]digo|dictamen|doctrina|precepto|jurisprudencia|dfl|dl|cpr", lin, re.IGNORECASE))
        consideraciones.append({
            "numero": len(consideraciones) + 1,
            "texto": lin,
            "es_analisis_juridico": es_derecho
        })

    return {
        "antecedentes": antecedentes,
        "marco_normativo": normas_unicas[:15],
        "consideraciones": consideraciones,
        "conclusion": conclusion if conclusion else (consideraciones[-1]["texto"] if consideraciones else "")
    }


def generar_markdown_resolucion(doc: Dict[str, Any]) -> str:
    """Construye la representación en Markdown Canónico con Frontmatter YAML estructurado."""
    organismo = (doc.get("organismo") or "ADMINISTRACIÓN").strip().upper()
    tipo_acto = (doc.get("tipo_acto") or "Dictamen").strip()
    identificador = (doc.get("identificador") or doc.get("numero") or doc.get("docId") or "S-N").strip()
    fecha = (doc.get("fecha") or "").strip()
    materia = (doc.get("materia") or doc.get("titulo") or "").strip()
    origen = (doc.get("origen_division") or doc.get("origen_") or "").strip()
    firmante = (doc.get("firmante") or doc.get("ministros") or "").strip()
    link_oficial = doc.get("link_oficial") or doc.get("link") or doc.get("url") or doc.get("pdfUrl") or ""

    texto_integral = doc.get("texto_integral") or doc.get("texto") or doc.get("documento") or materia or ""
    secciones = segmentar_secciones_administrativas(texto_integral, organismo=organismo)

    fuentes_legales = doc.get("fuentes_legales") or secciones["marco_normativo"]
    if isinstance(fuentes_legales, str):
        fuentes_legales = [f.strip() for f in fuentes_legales.split(",") if f.strip()]

    # YAML Frontmatter
    lines = [
        "---",
        f"organismo: {_escapar_yaml_str(organismo)}",
        f"tipo_acto: {_escapar_yaml_str(tipo_acto)}",
        f"identificador: {_escapar_yaml_str(identificador)}",
        f"fecha: {_escapar_yaml_str(fecha)}",
        f"materia: {_escapar_yaml_str(materia)}",
        f"origen_division: {_escapar_yaml_str(origen)}",
        f"firmante: {_escapar_yaml_str(firmante)}",
        f"link_oficial: {_escapar_yaml_str(link_oficial)}",
        f"total_parrafos_analisis: {len(secciones['consideraciones'])}",
        f"fecha_conversion_utc: {_escapar_yaml_str(dt.datetime.now(dt.timezone.utc).isoformat())}",
        "formato_origen: \"Open Legal Chile resolucion_administrativa2md\"",
        "---",
        "",
        f"# {tipo_acto.upper()} {organismo} — N° {identificador}",
        f"### FECHA: {fecha or 'Sin fecha registrada'}",
        "",
        f"- **Órgano Emisor:** {organismo} {('— ' + origen) if origen else ''}",
        f"- **Materia / Descriptor:** {materia or 'No especificada'}",
        f"- **Firmante / Autoridad:** {firmante or 'Autoridad facultada por ley'}",
        f"- **Fuente Oficial:** [{organismo} - Enlace Verificable]({link_oficial})" if link_oficial else f"- **Fuente:** {organismo} (Publicación Oficial)",
        "",
        "---",
        "",
        "## I. Materia y Síntesis Oficial",
        "",
        materia if materia else "*Sin resumen de materia registrado.*",
        "",
        "## II. Antecedentes y Vistos",
        "",
        secciones["antecedentes"] if secciones["antecedentes"] else "*Antecedentes contenidos en el cuerpo de la resolución.*",
        "",
        "## III. Marco Normativo Aplicable",
        ""
    ]

    if fuentes_legales:
        for f in fuentes_legales:
            lines.append(f"- `{f}`")
        lines.append("")
    else:
        lines.append("*Normativa invocada en las consideraciones de fondo.*")
        lines.append("")

    lines.append("## IV. Consideraciones y Análisis Jurídico")
    lines.append("")

    if secciones["consideraciones"]:
        for c in secciones["consideraciones"]:
            tipo_label = "Fundamento Jurídico" if c["es_analisis_juridico"] else "Antecedente de Hecho / Operativo"
            lines.append(f"### Párrafo {c['numero']} ({tipo_label})")
            lines.append(c["texto"])
            lines.append("")
    else:
        lines.append(texto_integral if texto_integral else "*Texto del pronunciamiento no disponible.*")
        lines.append("")

    lines.append("## V. Conclusión y Doctrina Vinculante")
    lines.append("")
    lines.append(secciones["conclusion"] if secciones["conclusion"] else "*Criterio adoptado en el cuerpo resolutivo del instrumento.*")
    lines.append("")

    return "\n".join(lines)


def convertir_dictamen_a_md(
    doc: Dict[str, Any],
    destino_dir: Optional[pathlib.Path] = None
) -> pathlib.Path:
    """Convierte un dictamen o resolución administrativa a archivo Markdown Canónico."""
    organismo = str(doc.get("organismo", "general")).lower().strip()
    ident = str(doc.get("identificador") or doc.get("numero") or doc.get("docId") or "sin_numero").strip()
    ident_clean = re.sub(r"[^A-Za-z0-9_\-]+", "_", ident).strip("_")
    fecha = str(doc.get("fecha", ""))
    anio = fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else "general"

    if destino_dir is None:
        target_folder = DEFAULT_MD_DIR / organismo / anio
    else:
        target_folder = pathlib.Path(destino_dir)

    target_folder.mkdir(parents=True, exist_ok=True)
    filename = f"resolucion_{organismo}_{ident_clean}.md"
    file_path = target_folder / filename

    md_content = generar_markdown_resolucion(doc)
    file_path.write_text(md_content, encoding="utf-8")
    return file_path


def convertir_lote_dictamenes(
    lista_docs: List[Dict[str, Any]],
    destino_dir: Optional[pathlib.Path] = None
) -> List[pathlib.Path]:
    """Convierte una lista de dictámenes o resoluciones a Markdown en lote."""
    paths = []
    for doc in lista_docs:
        p = convertir_dictamen_a_md(doc, destino_dir=destino_dir)
        paths.append(p)
    return paths


def parsear_frontmatter_dictamen_yaml(texto_md: str) -> Tuple[Dict[str, str], str]:
    """Extrae el Frontmatter YAML y el cuerpo de una resolución administrativa en Markdown."""
    meta = {}
    cuerpo = texto_md
    if texto_md.startswith("---"):
        partes = texto_md.split("---", 2)
        if len(partes) >= 3:
            raw_yaml = partes[1]
            cuerpo = partes[2].strip()
            for line in raw_yaml.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k:
                        meta[k] = v
    return meta, cuerpo


# Alias para compatibilidad directa
convertir_resolucion_a_md = convertir_dictamen_a_md
convertir_lote_resoluciones = convertir_lote_dictamenes
parsear_frontmatter_yaml = parsear_frontmatter_dictamen_yaml
