"""
Open Legal Chile — Conversor de Sentencias Judiciales a Markdown Canónico (sentencia2md)
Transforma resoluciones y fallos judiciales de la Corte Suprema y Cortes de Apelaciones
en documentos Markdown estructurados, token-optimizados, con metadatos Frontmatter YAML,
segmentación atómica de considerandos y normalización ortotipográfica (RAE/ASALE).
"""

import os
import re
import pathlib
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_MD_DIR = BASE_DIR / "data" / "jurisprudencia_md"


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


def segmentar_secciones_sentencia(texto_integral: str) -> Dict[str, Any]:
    """
    Segmenta anatómicamente el texto de una sentencia judicial conforme al Art. 170 CPC:
    Vistos (expositiva), Considerativa (considerandos), Resolutiva, Disidencias y Costas.
    """
    texto = _limpiar_texto(texto_integral)
    if not texto:
        return {
            "vistos": "",
            "considerandos": [],
            "resolutiva": "",
            "disidencia": "",
            "prevencion": "",
            "costas": ""
        }

    # 1. Vistos / Parte Expositiva
    vistos_match = re.search(
        r"(?:VISTOS?|RESULTANDO)[:\s]*(.*?)(?=(?:Y\s+TENIENDO\s+PRESENTE|CONSIDERANDO))",
        texto,
        re.DOTALL | re.IGNORECASE
    )
    vistos = vistos_match.group(1).strip() if vistos_match else ""

    # 2. Considerativa
    considerando_match = re.search(
        r"(?:CONSIDERANDO|Y\s+TENIENDO\s+PRESENTE)[:\s]*(.*?)(?=(?:Y\s+VISTO|POR\s+ESTAS\s+CONSIDERACIONES|SE\s+RESUELVE|RESUELVO|DECLARO|POR\s+TANTO))",
        texto,
        re.DOTALL | re.IGNORECASE
    )
    considerativa_raw = considerando_match.group(1).strip() if considerando_match else ""

    # Si no se encontró separador formal pero hay texto, tomamos el cuerpo medio
    if not considerativa_raw and "CONSIDERANDO" in texto.upper():
        partes = re.split(r"CONSIDERANDO:?", texto, flags=re.IGNORECASE)
        if len(partes) > 1:
            considerativa_raw = partes[1].split("RESUELVO")[0].split("SE RESUELVE")[0].strip()

    # 3. Resolutiva
    resolutiva_match = re.search(
        r"(?:POR\s+ESTAS\s+CONSIDERACIONES|SE\s+RESUELVE|RESUELVO|DECLARO|POR\s+TANTO)[,:\s]*(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada\s+por|Redacci[oó]n\s+del|Acordada|$))",
        texto,
        re.DOTALL | re.IGNORECASE
    )
    resolutiva = resolutiva_match.group(1).strip() if resolutiva_match else ""

    # 4. Extracción de Considerandos Individuales
    # Reconoce 1°, 1.-, Primero, Décimo Quinto, etc.
    patron_considerandos = (
        r"(?:^|\n)\s*([0-9]+[°º]?|[A-Z]+[°º]?|"
        r"PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|"
        r"D[EÉ]CIMO(?:\s+(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO))?|"
        r"VIG[EÉ]SIMO(?:\s+(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO))?|"
        r"TRIG[EÉ]SIMO(?:\s+(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO))?|"
        r"CUADRAG[EÉ]SIMO(?:\s+(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO))?)"
        r"[\.:\)\s\-]+(?:Que\s+)?"
    )

    tokens = re.split(patron_considerandos, "\n" + considerativa_raw, flags=re.IGNORECASE)
    considerandos = []

    if len(tokens) >= 3:
        for i in range(1, len(tokens), 2):
            num = tokens[i].strip()
            cuerpo = tokens[i + 1].strip() if i + 1 < len(tokens) else ""
            if len(cuerpo) < 5:
                continue

            es_derecho = bool(re.search(
                r"art[íi]culo|ley|c[oó]digo|jurisprudencia|doctrina|precepto|mandato\s+legal|hermen[eé]utica|garant[íi]a|cpr|constituci[oó]n",
                cuerpo,
                re.IGNORECASE
            ))

            normas_citadas = re.findall(
                r"(?:art[íi]culo|art\.)\s+\d+(?:\s*(?:bis|ter|qu[aá]ter|inciso\s+\d+|inc\.\s*\d+))?(?:\s+(?:de\s+la\s+|del\s+)?(?:c[oó]digo\s+[a-z]+|ley\s+(?:n[°º]?\s*)?\d+[\.\d]*|cpr))?",
                cuerpo,
                re.IGNORECASE
            )

            considerandos.append({
                "numero": num,
                "texto": cuerpo,
                "tipo": "DERECHO" if es_derecho else "HECHO",
                "normas_citadas": list(dict.fromkeys(normas_citadas))
            })
    else:
        # Si no hubo split formal pero hay texto considerativo
        if considerativa_raw:
            considerandos.append({
                "numero": "Único",
                "texto": considerativa_raw,
                "tipo": "DERECHO",
                "normas_citadas": []
            })

    # 5. Votos y Disidencias
    disidencia_match = re.search(
        r"(?:Acordada\s+con\s+el\s+voto\s+en\s+contra|Voto\s+disidente|Disidente|Disiente)(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada|$))",
        texto,
        re.DOTALL | re.IGNORECASE
    )
    prevencion_match = re.search(
        r"(?:Prevenci[oó]n|Previene|Concurre\s+con\s+la\s+prevenci[oó]n)(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada|$))",
        texto,
        re.DOTALL | re.IGNORECASE
    )

    # 6. Costas (Art. 144 CPC)
    sin_motivo = bool(re.search(r"sin\s+motivo\s+plausible", texto, re.IGNORECASE))
    costas_condena = bool(re.search(r"con\s+costas|cond[eé]nase\s+(?:en|al?)\s+costas|con\s+expresa\s+condenaci[oó]n\s+en\s+costas", texto, re.IGNORECASE)) or sin_motivo
    costas_exencion = (bool(re.search(r"sin\s+costas|no\s+se\s+condena\s+en\s+costas|por\s+haber\s+tenido\s+motivo\s+plausible|con\s+motivo\s+plausible|ex[ií]mase\s+de\s+costas", texto, re.IGNORECASE)) and not sin_motivo)

    if costas_condena:
        costas_desc = "CONDENA EN COSTAS (Art. 144 CPC: litigación vencida sin motivo plausible)."
    elif costas_exencion:
        costas_desc = "EXENCIÓN DE COSTAS (Art. 144 CPC: litigación con motivo plausible)."
    else:
        costas_desc = "Sin pronunciamiento especial de costas."

    return {
        "vistos": vistos,
        "considerandos": considerandos,
        "resolutiva": resolutiva,
        "disidencia": disidencia_match.group(1).strip() if disidencia_match else "",
        "prevencion": prevencion_match.group(1).strip() if prevencion_match else "",
        "costas": costas_desc
    }


def generar_markdown_sentencia(doc: Dict[str, Any]) -> str:
    """
    Construye la representación en Markdown Canónico de la sentencia judicial
    con Frontmatter YAML y jerarquía de encabezados claros.
    """
    rol = doc.get("rol", "").strip() or "S-N"
    tribunal = doc.get("tribunal", "Corte Suprema").strip()
    sala = doc.get("sala", "").strip()
    fecha = doc.get("fecha", "").strip()
    caratula = doc.get("caratula", "").strip()
    recurso = doc.get("recurso", "").strip()
    resultado = doc.get("resultado", "").strip()
    ministros = doc.get("ministros", "").strip()
    link_oficial = doc.get("url_origen") or doc.get("link") or "https://juris.pjud.cl"
    id_pjud = doc.get("id", "")
    tipo_corte = doc.get("tipo_corte", "cs")

    texto_integral = doc.get("texto_integral") or doc.get("texto_sentencia") or ""
    secciones = segmentar_secciones_sentencia(texto_integral)

    # Encabezado Frontmatter YAML
    lines = [
        "---",
        f"rol: {_escapar_yaml_str(rol)}",
        f"tribunal: {_escapar_yaml_str(tribunal)}",
        f"tipo_corte: {_escapar_yaml_str(tipo_corte)}",
        f"sala: {_escapar_yaml_str(sala)}",
        f"fecha: {_escapar_yaml_str(fecha)}",
        f"caratula: {_escapar_yaml_str(caratula)}",
        f"recurso: {_escapar_yaml_str(recurso)}",
        f"resultado: {_escapar_yaml_str(resultado)}",
        f"ministros: {_escapar_yaml_str(ministros)}",
        f"link_oficial: {_escapar_yaml_str(link_oficial)}",
        f"id_pjud: {_escapar_yaml_str(id_pjud)}",
        f"total_considerandos: {len(secciones['considerandos'])}",
        f"fecha_conversion_utc: {_escapar_yaml_str(dt.datetime.now(dt.timezone.utc).isoformat())}",
        "formato_origen: \"Open Legal Chile sentencia2md\"",
        "---",
        "",
        f"# SENTENCIA JUDICIAL — {tribunal.upper()}",
        f"### ROL N° {rol} | FECHA: {fecha or 'Sin fecha registrada'}",
        "",
        f"- **Tribunal:** {tribunal} {('(' + sala + ')') if sala else ''}",
        f"- **Carátula:** {caratula or 'No especificada'}",
        f"- **Recurso / Procedimiento:** {recurso or 'No especificado'}",
        f"- **Resultado del Recurso:** {resultado or 'No registrado'}",
        f"- **Ministros y Redacción:** {ministros or 'No individualizados'}",
        f"- **Fuente Oficial:** [{tribunal} - juris.pjud.cl]({link_oficial})",
        "",
        "---",
        "",
        "## I. Vistos y Parte Expositiva",
        "",
        secciones["vistos"] if secciones["vistos"] else "*No consta transcripción de vistos o parte expositiva resumida.*",
        "",
        "## II. Considerandos (Fundamentos de Hecho y de Derecho)",
        ""
    ]

    # Desglose de considerandos
    if secciones["considerandos"]:
        for c in secciones["considerandos"]:
            lines.append(f"### Considerando {c['numero']}")
            lines.append(f"**Naturaleza:** {c['tipo']}")
            if c.get("normas_citadas"):
                lines.append(f"**Normas Referenciadas:** {', '.join(c['normas_citadas'])}")
            lines.append("")
            lines.append(c["texto"])
            lines.append("")
    else:
        lines.append(texto_integral if texto_integral else "*Texto de considerandos no disponible.*")
        lines.append("")

    # Parte Resolutiva
    lines.append("## III. Parte Resolutiva")
    lines.append("")
    lines.append(secciones["resolutiva"] if secciones["resolutiva"] else "*Decisión contenida en el cuerpo principal de la resolución.*")
    lines.append("")

    # Votos y Disidencias
    if secciones["disidencia"] or secciones["prevencion"]:
        lines.append("## IV. Votos Disidentes y Prevenciones")
        lines.append("")
        if secciones["disidencia"]:
            lines.append("### Voto Disidente")
            lines.append(secciones["disidencia"])
            lines.append("")
        if secciones["prevencion"]:
            lines.append("### Prevención")
            lines.append(secciones["prevencion"])
            lines.append("")

    # Costas
    lines.append("## V. Régimen de Costas (Art. 144 CPC)")
    lines.append("")
    lines.append(secciones["costas"])
    lines.append("")

    return "\n".join(lines)


def convertir_sentencia_a_md(
    doc: Dict[str, Any],
    destino_dir: Optional[pathlib.Path] = None
) -> pathlib.Path:
    """
    Convierte una sentencia (diccionario estructurado de PJUDScraper) a archivo Markdown Canónico
    y lo almacena en el directorio indicado o en data/jurisprudencia_md/[corte]/[año]/[rol].md.
    """
    rol = str(doc.get("rol", "sin_rol")).strip().replace("/", "_").replace(" ", "_")
    rol_clean = re.sub(r"[^A-Za-z0-9_\-]+", "", rol)
    corte = str(doc.get("tipo_corte", "cs")).lower()
    fecha = str(doc.get("fecha", ""))
    anio = fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else "general"

    if destino_dir is None:
        target_folder = DEFAULT_MD_DIR / corte / anio
    else:
        target_folder = pathlib.Path(destino_dir)

    target_folder.mkdir(parents=True, exist_ok=True)
    filename = f"sentencia_{corte}_{rol_clean}.md"
    file_path = target_folder / filename

    md_content = generar_markdown_sentencia(doc)
    file_path.write_text(md_content, encoding="utf-8")
    return file_path


def convertir_lote_sentencias(
    lista_docs: List[Dict[str, Any]],
    destino_dir: Optional[pathlib.Path] = None
) -> List[pathlib.Path]:
    """Convierte una lista de sentencias a Markdown Canónico en lote."""
    paths = []
    for doc in lista_docs:
        p = convertir_sentencia_a_md(doc, destino_dir=destino_dir)
        paths.append(p)
    return paths


def parsear_frontmatter_yaml(texto_md: str) -> Tuple[Dict[str, str], str]:
    """Extrae el Frontmatter YAML y el cuerpo del documento Markdown."""
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
