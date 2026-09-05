"""
Open Legal Chile — Generador y Exportador Forense de Documentos Legales
Módulo para redactar y exportar demandas, recursos de protección, finiquitos,
contratos PPA y cartas de despido en formatos estándares para tribunales chilenos (Ley 20.886 OJV).
"""

import os
import re
import html
import json
from datetime import datetime
from typing import Dict, Any, Optional

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


class LegalDocumentExporter:
    """Genera documentos legales con formato forense chileno y los exporta a HTML/Markdown/Texto."""

    @staticmethod
    def format_presuma(materia: str, procedimiento: str, demandante: str, rut_dte: str, abogado: str, rut_abg: str, demandado: str, rut_ddo: str) -> str:
        """Genera la presuma estándar obligatoria para la Oficina Judicial Virtual (OJV)."""
        return f"""
PROCEDIMIENTO   : {procedimiento.upper()}
MATERIA         : {materia.upper()}
DEMANDANTE      : {demandante.upper()} (RUT: {rut_dte})
ABOGADO PATROC. : {abogado.upper()} (RUT: {rut_abg})
DEMANDADO       : {demandado.upper()} (RUT: {rut_ddo})
""".strip()

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
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.8;
            color: #111;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }}
        .presuma {{
            border: 1px solid #333;
            padding: 12px;
            font-family: monospace;
            font-size: 13px;
            margin-bottom: 24px;
            white-space: pre-wrap;
            background: #FAFAFA;
        }}
        .tribunal {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 20px;
        }}
        .en-lo-principal {{
            font-weight: bold;
            text-align: justify;
            margin-bottom: 20px;
        }}
        h3 {{
            border-bottom: 1px solid #ccc;
            padding-bottom: 4px;
            font-size: 15px;
            text-transform: uppercase;
        }}
        p {{
            text-align: justify;
            text-indent: 2em;
            margin-bottom: 14px;
        }}
        .otrosi {{
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px dashed #aaa;
        }}
        .gate-warning {{
            margin-top: 40px;
            padding: 12px;
            background: #FFFBEB;
            border: 1px solid #F59E0B;
            font-size: 12px;
            font-family: sans-serif;
            color: #92400E;
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
