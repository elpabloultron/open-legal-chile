"""
Open Legal Chile — Generador y Exportador Forense de Documentos Legales
Módulo para redactar y exportar demandas, recursos de protección, finiquitos,
contratos PPA y cartas de despido en formatos estándares para tribunales chilenos (Ley 20.886 OJV).
"""

from __future__ import annotations

import os
import re
import html
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union

from recurso_proteccion import RecursoProteccionEngine

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


class LegalDocumentExporter:
    """Genera documentos legales con formato forense chileno y los exporta a HTML/Markdown/Texto."""

    @staticmethod
    def format_presuma(
        materia: str,
        procedimiento: str,
        demandante: str,
        rut_dte: str,
        abogado: str,
        rut_abg: str,
        demandado: str,
        rut_ddo: str
    ) -> str:
        """Genera la presuma estándar obligatoria para la Oficina Judicial Virtual (OJV)."""
        return f"""
PROCEDIMIENTO   : {procedimiento.upper()}
MATERIA         : {materia.upper()}
DEMANDANTE      : {demandante.upper()} (RUT: {rut_dte})
ABOGADO PATROC. : {abogado.upper()} (RUT: {rut_abg})
DEMANDADO       : {demandado.upper()} (RUT: {rut_ddo})
""".strip()

    @staticmethod
    def format_presuma_recurso_proteccion(
        tribunal: str,
        recurrente_nombre: str,
        recurrente_run: str,
        recurrente_domicilio: str,
        recurrente_email: str,
        recurrido_nombre: str,
        recurrido_rut: Optional[str] = None,
        recurrido_domicilio: Optional[str] = None,
        recurrido_email: Optional[str] = None,
        representante_legal: Optional[str] = None,
        representado_nombre: Optional[str] = None,
        representado_run: Optional[str] = None,
        quinto_otrosi_titulo: Optional[str] = None
    ) -> Dict[str, str]:
        """Formatea la presuma y suma para Recursos de Protección conforme a la OJV."""
        return RecursoProteccionEngine.format_presuma_recurso_proteccion(
            tribunal=tribunal,
            recurrente_nombre=recurrente_nombre,
            recurrente_run=recurrente_run,
            recurrente_domicilio=recurrente_domicilio,
            recurrente_email=recurrente_email,
            recurrido_nombre=recurrido_nombre,
            recurrido_rut=recurrido_rut,
            recurrido_domicilio=recurrido_domicilio,
            recurrido_email=recurrido_email,
            representante_legal=representante_legal,
            representado_nombre=representado_nombre,
            representado_run=representado_run,
            quinto_otrosi_titulo=quinto_otrosi_titulo
        )

    @classmethod
    def export_brief(
        cls,
        titulo_principal: str,
        tribunal: str,
        presuma_data: Dict[str, str],
        comparecencia: str,
        hechos: str,
        derecho: str,
        peticiones: str,
        otrosies: Optional[list] = None,
        filename_base: Optional[str] = None
    ) -> Dict[str, str]:
        """Exporta un escrito judicial completo a HTML, Markdown, Texto Plano y JSON."""
        otrosies = otrosies or []

        # 1. Presuma
        presuma = cls.format_presuma(
            materia=presuma_data.get("materia", "ORDINARIO"),
            procedimiento=presuma_data.get("procedimiento", "DECLARATIVO"),
            demandante=presuma_data.get("demandante", "PARTE DEMANDANTE"),
            rut_dte=presuma_data.get("rut_dte", "XX.XXX.XXX-X"),
            abogado=presuma_data.get("abogado", "ABOGADO PATROCINANTE"),
            rut_abg=presuma_data.get("rut_abg", "XX.XXX.XXX-X"),
            demandado=presuma_data.get("demandado", "PARTE DEMANDADA"),
            rut_ddo=presuma_data.get("rut_ddo", "XX.XXX.XXX-X")
        )

        # 2. Construir Texto Completo Markdown
        otrosies_md = ""
        for idx, ot in enumerate(otrosies):
            otrosies_md += f"\n\n**{ot.get('numero', f'{idx+1}° OTROSÍ').upper()}:** {ot.get('contenido', '')}"

        md_content = f"""```
{presuma}
```

**{tribunal.upper()}**

{comparecencia}

**EN LO PRINCIPAL:** {titulo_principal}; **PRIMER OTROSÍ:** Patrocinio y Poder; {'; '.join([ot.get('numero', '') + ': ' + ot.get('titulo', '') for ot in otrosies])}.

---

### I. LOS HECHOS
{hechos}

---

### II. EL DERECHO
{derecho}

---

### POR TANTO,
{peticiones}
{otrosies_md}
"""

        # 3. Construir HTML estilizado
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo_principal} — Open Legal Chile</title>
    <style>
        body {{
            font-family: 'Times New Roman', 'Liberation Serif', Times, serif;
            font-size: 12pt;
            line-height: 1.35;
            color: #111;
            max-width: 820px;
            margin: 40px auto;
            padding: 30px;
        }}
        .presuma {{
            border: 1.5px solid #4a5568;
            padding: 14px 18px;
            font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;
            font-size: 9.5pt;
            line-height: 1.45;
            margin-bottom: 24px;
            white-space: pre-wrap;
            background: #f8fafc;
            color: #1a202c;
            word-break: break-word;
        }}
        .tribunal {{
            font-weight: bold;
            font-size: 14pt;
            text-align: center;
            margin-bottom: 20px;
        }}
        .en-lo-principal {{
            font-weight: bold;
            text-align: justify;
            margin-bottom: 20px;
            font-size: 11pt;
        }}
        h3 {{
            border-bottom: 1px solid #ccc;
            padding-bottom: 4px;
            font-size: 13pt;
            text-transform: uppercase;
            margin-top: 24px;
        }}
        h4 {{
            font-size: 11pt;
            margin-top: 14px;
            margin-bottom: 6px;
        }}
        p {{
            text-align: justify;
            text-indent: 2em;
            margin-bottom: 14px;
        }}
        .otrosi {{
            margin-top: 24px;
            padding-top: 12px;
            border-top: 1px dashed #aaa;
        }}
        .gate-warning {{
            margin-top: 40px;
            padding: 14px;
            background: #fffbeb;
            border: 1px solid #f59e0b;
            font-size: 10pt;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #92400e;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="presuma">{html.escape(presuma)}</div>
    <div class="tribunal">{html.escape(tribunal.upper())}</div>
    <p>{html.escape(comparecencia)}</p>
    <div class="en-lo-principal">EN LO PRINCIPAL: {html.escape(titulo_principal)}; y OTROSÍES que indica.</div>
    
    <h3>I. Los Hechos</h3>
    <p>{html.escape(hechos).replace(chr(10), '</p><p>')}</p>
    
    <h3>II. El Derecho</h3>
    <p>{html.escape(derecho).replace(chr(10), '</p><p>')}</p>
    
    <h3>Por Tanto</h3>
    <p>{html.escape(peticiones).replace(chr(10), '</p><p>')}</p>
    
    <div class="otrosi">
        {"".join([f"<h4>{html.escape(ot.get('numero', 'OTROSÍ'))}: {html.escape(ot.get('titulo', ''))}</h4><p>{html.escape(ot.get('contenido', ''))}</p>" for ot in otrosies])}
    </div>

    <div class="gate-warning">
        ⚖️ <strong>Compuerta de Revisión Jurídica (Open Legal Chile):</strong> Este escrito contiene análisis y propuesta de redacción conforme al ordenamiento jurídico de Chile. Debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV).
    </div>
</body>
</html>"""

        filename = filename_base or f"escrito_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        md_path = os.path.join(EXPORTS_DIR, f"{filename}.md")
        html_path = os.path.join(EXPORTS_DIR, f"{filename}.html")
        txt_path = os.path.join(EXPORTS_DIR, f"{filename}.txt")
        json_path = os.path.join(EXPORTS_DIR, f"{filename}.json")

        # 4. Texto Plano (Oficina Judicial Virtual / copiar-pegar)
        txt_content = f"""{presuma}

{tribunal.upper()}

{comparecencia}

EN LO PRINCIPAL: {titulo_principal}; {'; '.join([ot.get('numero', '') + ': ' + ot.get('titulo', '') for ot in otrosies])}.

I. LOS HECHOS
{hechos}

II. EL DERECHO
{derecho}

POR TANTO,
{peticiones}
{otrosies_md.replace('**', '').replace('`', '').strip()}
"""

        # 5. JSON estructurado (intercambio LegalTech)
        json_data = {
            "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
            "tipo_escrito": titulo_principal,
            "tribunal": tribunal.upper(),
            "presuma": {
                "materia": presuma_data.get("materia", "ORDINARIO"),
                "procedimiento": presuma_data.get("procedimiento", "DECLARATIVO"),
                "demandante": presuma_data.get("demandante", "PARTE DEMANDANTE"),
                "rut_demandante": presuma_data.get("rut_dte", "XX.XXX.XXX-X"),
                "abogado_patrocinante": presuma_data.get("abogado", "ABOGADO PATROCINANTE"),
                "rut_abogado": presuma_data.get("rut_abg", "XX.XXX.XXX-X"),
                "demandado": presuma_data.get("demandado", "PARTE DEMANDADA"),
                "rut_demandado": presuma_data.get("rut_ddo", "XX.XXX.XXX-X")
            },
            "comparecencia": comparecencia,
            "hechos": hechos,
            "derecho": derecho,
            "peticiones_concretas": peticiones,
            "otrosies": otrosies
        }

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        return {
            "filename": filename,
            "markdownPath": md_path,
            "htmlPath": html_path,
            "textPath": txt_path,
            "jsonPath": json_path,
            "exportsDir": EXPORTS_DIR
        }

    @classmethod
    def export_recurso_proteccion(
        cls,
        tribunal: str,
        recurrente: Dict[str, Any],
        recurrido: Dict[str, Any],
        acto_lesivo: str,
        fecha_acto: Union[str, date],
        hechos: List[Union[str, Dict[str, str]]],
        garantias: List[str],
        estatutos_especiales: Optional[List[str]] = None,
        oni_data: Optional[Dict[str, Any]] = None,
        oficios: Optional[List[Dict[str, str]]] = None,
        anexos: Optional[List[Dict[str, str]]] = None,
        quinto_otrosi: Optional[Dict[str, str]] = None,
        petitorio_concreto: Optional[str] = None,
        fecha_interposicion: Optional[Union[str, date]] = None,
        filename_base: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera y exporta un Recurso de Protección completo en formatos .html, .md, .txt y .json,
        conforme a las directrices procesales y de presuma anti-colapso de la OJV.
        """
        brief = RecursoProteccionEngine.generate_full_brief(
            tribunal=tribunal,
            recurrente=recurrente,
            recurrido=recurrido,
            acto_lesivo=acto_lesivo,
            fecha_acto=fecha_acto,
            hechos=hechos,
            garantias=garantias,
            estatutos_especiales=estatutos_especiales,
            oni_data=oni_data,
            oficios=oficios,
            anexos=anexos,
            quinto_otrosi=quinto_otrosi,
            petitorio_concreto=petitorio_concreto,
            fecha_interposicion=fecha_interposicion
        )

        filename = filename_base or f"recurso_proteccion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        md_path = os.path.join(EXPORTS_DIR, f"{filename}.md")
        html_path = os.path.join(EXPORTS_DIR, f"{filename}.html")
        txt_path = os.path.join(EXPORTS_DIR, f"{filename}.txt")
        json_path = os.path.join(EXPORTS_DIR, f"{filename}.json")

        # HTML estructurado con tipografía forense y presuma anti-colapso
        otrosies_html_parts = []
        for ot in brief["otrosies"]:
            otrosies_html_parts.append(
                f"<div class=\"otrosi\"><h4>{html.escape(ot['numero'])}: {html.escape(ot['titulo'])}</h4>"
                f"<p>{html.escape(ot['contenido']).replace(chr(10), '<br/>')}</p></div>"
            )

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Recurso de Protección — {html.escape(tribunal)}</title>
    <style>
        body {{
            font-family: 'Times New Roman', 'Liberation Serif', Times, serif;
            font-size: 12pt;
            line-height: 1.35;
            color: #111;
            max-width: 820px;
            margin: 40px auto;
            padding: 30px;
        }}
        .presuma {{
            border: 1.5px solid #4a5568;
            padding: 14px 18px;
            font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;
            font-size: 9.5pt;
            line-height: 1.45;
            margin-bottom: 24px;
            white-space: pre-wrap;
            background: #f8fafc;
            color: #1a202c;
            word-break: break-word;
        }}
        .tribunal {{
            font-weight: bold;
            font-size: 14pt;
            text-align: center;
            margin-bottom: 20px;
            letter-spacing: 0.05em;
        }}
        .comparecencia {{
            text-align: justify;
            margin-bottom: 18px;
            line-height: 1.45;
        }}
        .objeto {{
            text-align: justify;
            margin-bottom: 24px;
            background: #fafafa;
            padding: 12px 16px;
            border-left: 3px solid #15803d;
        }}
        h2 {{
            border-bottom: 1.5px solid #1a202c;
            padding-bottom: 4px;
            font-size: 13pt;
            text-transform: uppercase;
            margin-top: 28px;
            letter-spacing: 0.04em;
        }}
        h3 {{
            font-size: 11.5pt;
            margin-top: 18px;
            margin-bottom: 8px;
        }}
        h4 {{
            font-size: 11pt;
            margin-top: 12px;
            margin-bottom: 6px;
            color: #1e293b;
        }}
        p {{
            text-align: justify;
            margin-bottom: 14px;
        }}
        .otrosi {{
            margin-top: 24px;
            padding-top: 14px;
            border-top: 1px dashed #cbd5e1;
        }}
        .gate-warning {{
            margin-top: 40px;
            padding: 14px;
            background: #fffbeb;
            border: 1px solid #f59e0b;
            font-size: 10pt;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #92400e;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    {brief['presuma_html']}

    <div class="tribunal">{html.escape(tribunal.upper())}</div>

    <div class="comparecencia">{html.escape(brief['comparecencia'])}</div>

    <div class="objeto">{html.escape(brief['objeto']).replace(chr(10), '<br/>')}</div>

    <h2>I. Los Hechos (Cronología Fundante)</h2>
    <div>{html.escape(brief['hechos']).replace(chr(10), '<br/>')}</div>

    <h2>II. El Derecho y Garantías Constitucionales Afectadas</h2>
    <div>{html.escape(brief['derecho']).replace(chr(10), '<br/>')}</div>

    <h2>Por Tanto</h2>
    <div>{html.escape(brief['por_tanto']).replace(chr(10), '<br/>')}</div>

    {"".join(otrosies_html_parts)}

    <div class="gate-warning">
        ⚖️ <strong>Compuerta de Revisión Jurídica (Open Legal Chile):</strong> Este Recurso de Protección ha sido formulado conforme al Auto Acordado de la Excma. Corte Suprema (Acta N.° 94-2015). En virtud del artículo 20 de la CPR y del Numeral 2.° de dicho Auto Acordado, no requiere patrocinio obligatorio de abogado, debiendo ser firmado por el recurrente antes de su ingreso formal a la Oficina Judicial Virtual (OJV).
    </div>
</body>
</html>"""

        # Texto plano puro para OJV
        txt_content = f"""{brief['presuma_plain']}

{brief['comparecencia']}

{brief['objeto']}

I. LOS HECHOS (CRONOLOGÍA FUNDANTE)
{brief['hechos']}

II. EL DERECHO Y GARANTÍAS CONSTITUCIONALES AFECTADAS
{brief['derecho']}

POR TANTO,
{brief['por_tanto']}

""" + "\n\n".join([f"{ot['numero']}: {ot['titulo']}\n{ot['contenido']}" for ot in brief["otrosies"]])

        # Guardar archivos
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(brief["markdown_full"])

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)

        with open(json_path, "w", encoding="utf-8") as f:
            json_export = dict(brief)
            json_export["fecha_generacion"] = datetime.now().isoformat(timespec="seconds")
            json.dump(json_export, f, ensure_ascii=False, indent=2)

        return {
            "filename": filename,
            "markdownPath": md_path,
            "htmlPath": html_path,
            "textPath": txt_path,
            "jsonPath": json_path,
            "exportsDir": EXPORTS_DIR,
            "deadline_info": brief["deadline_info"],
            "preferente": brief["preferente"]
        }
