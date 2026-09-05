"""
Open Legal Chile — Optimizador de Tokens y Compilador Doctrinal a Markdown
Transforma textos jurídicos extensos, transcripciones u OCRs de manuales en
Markdown de Alta Densidad Dogmática (Token-Optimized Markdown).

Objetivo: Reducir entre un 80% y 92% el consumo de tokens en la ventana de contexto
del usuario o agente de IA, preservando el 100% de la sustancia conceptual,
definiciones canónicas, requisitos legales y citas oficiales.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class DoctrinaTokenOptimizer:
    def __init__(self):
        self.noise_patterns = [
            r"Página\s+\d+(?:\s+de\s+\d+)?",
            r"EDITORIAL\s+JURÍDICA\s+DE\s+CHILE",
            r"THOMSON\s+REUTERS",
            r"LIBROTECNIA",
            r"EDITORIAL\s+HAMMURABI",
            r"(?:TRATADO|MANUAL)\s+DE\s+DERECHO\s+[A-Z]+",
            r"^\s*\d+\s*$",                  # Números de página aislados
            r"©\s*Editorial.*",
            r"Todos\s+los\s+derechos\s+reservados.*",
            r"Impreso\s+en\s+Chile.*",
            r"ISBN:?\s*[\d\-]+",
        ]
        self.compiled_noise = [re.compile(p, re.IGNORECASE) for p in self.noise_patterns]

    def estimate_tokens(self, text: str) -> int:
        """Estima tokens basado en el promedio de ~4 caracteres por token en español."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.8))

    def clean_raw_text(self, raw_text: str) -> str:
        """Limpia ruido editorial, encabezados repetitivos y artefactos de escaneo."""
        lines = raw_text.splitlines()
        cleaned_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                cleaned_lines.append("")
                continue

            # Descartar líneas que calzan con patrones de ruido
            is_noise = False
            for pat in self.compiled_noise:
                if pat.search(line_str) and len(line_str) < 80:
                    is_noise = True
                    break
            if is_noise:
                continue

            # Eliminar fojas repetitivas o marcas de OCR como | ~ _ sueltos
            cleaned = re.sub(r"[\|~_]{2,}", "", line_str)
            cleaned_lines.append(cleaned)

        # Unificar múltiples saltos de línea consecutivos a máximo 2
        joined = "\n".join(cleaned_lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()

    def format_to_high_density_md(
        self,
        area: str,
        autor: str,
        obra: str,
        capitulo: str,
        instituciones: List[Dict[str, Any]]
    ) -> str:
        """
        Genera un archivo Markdown de alta densidad y ultra-bajo consumo de tokens.
        
        Args:
            area: civil, procesal, administrativo, laboral, penal, etc.
            autor: Nombre del tratadista (ej. 'René Ramos Pazos')
            obra: Nombre del manual (ej. 'De las Obligaciones')
            capitulo: Materia específica (ej. 'Efectos de las Obligaciones')
            instituciones: Lista de diccionarios con la estructura dogmática:
                {
                    "nombre": "Resolución por Inejecución (Art. 1489 CC)",
                    "definicion": "Efecto de la condición resolutoria tácita...",
                    "requisitos": ["Incumplimiento imputable", "Demandante ha cumplido o se allana", ...],
                    "clasificacion": "...",
                    "efectos": "...",
                    "articulos_bcn": ["Código Civil, Art. 1489", "Código Civil, Art. 1553"],
                    "jurisprudencia_rectora": "CS Rol N° 12.345-2022"
                }
        """
        md_lines = [
            f"# {obra.upper()}",
            f"**Tratadista:** {autor} | **Área:** {area.title()} | **Materia:** {capitulo}",
            "> 💡 *Ficha Dogmática de Alta Densidad (Token-Optimized) para Open Legal Chile.*",
            "",
            "---",
            ""
        ]

        for inst in instituciones:
            nombre = inst.get("nombre", "Institución Jurídica")
            md_lines.append(f"## 🏛️ {nombre}")
            
            if inst.get("definicion"):
                md_lines.append(f"**Definición Canónica:**  \n{inst['definicion'].strip()}\n")

            if inst.get("naturaleza"):
                md_lines.append(f"**Naturaleza Jurídica:** {inst['naturaleza'].strip()}\n")

            if inst.get("requisitos"):
                md_lines.append("**Requisitos de Procedencia:**")
                for req in inst["requisitos"]:
                    md_lines.append(f"* {req.strip()}")
                md_lines.append("")

            if inst.get("clasificacion"):
                md_lines.append(f"**Clasificación Doctrinal:**  \n{inst['clasificacion'].strip()}\n")

            if inst.get("efectos"):
                md_lines.append(f"**Efectos Jurídicos:**  \n{inst['efectos'].strip()}\n")

            if inst.get("operativa_procesal"):
                op = inst["operativa_procesal"]
                md_lines.append("**Operativa Procesal Forense:**")
                if isinstance(op, dict):
                    if op.get("via_procesal"):
                        md_lines.append(f"* **Vía Procesal:** {op['via_procesal'].strip()}")
                    if op.get("tribunal_competente"):
                        md_lines.append(f"* **Tribunal Competente:** {op['tribunal_competente'].strip()}")
                    if op.get("legitimacion_activa") or op.get("legitimacion_pasiva") or op.get("legitimacion"):
                        legit = op.get("legitimacion")
                        if not legit:
                            parts = []
                            if op.get("legitimacion_activa"):
                                parts.append(f"Activa: {op['legitimacion_activa'].strip()}")
                            if op.get("legitimacion_pasiva"):
                                parts.append(f"Pasiva: {op['legitimacion_pasiva'].strip()}")
                            legit = " | ".join(parts)
                        md_lines.append(f"* **Legitimación Procesal:** {legit}")
                    if op.get("carga_probatoria"):
                        md_lines.append(f"* **Carga Probatoria:** {op['carga_probatoria'].strip()}")
                    if op.get("medidas_precautorias"):
                        md_lines.append(f"* **Medidas Precautorias:** {op['medidas_precautorias'].strip()}")
                    if op.get("plazos_fatales"):
                        md_lines.append(f"* **Plazos Fatales:** {op['plazos_fatales'].strip()}")
                    if op.get("defensas_y_excepciones"):
                        md_lines.append(f"* **Defensas y Excepciones:** {op['defensas_y_excepciones'].strip()}")
                elif isinstance(op, list):
                    for item in op:
                        md_lines.append(f"* {item.strip()}")
                else:
                    md_lines.append(str(op).strip())
                md_lines.append("")

            if inst.get("articulos_bcn"):
                citas = [f"`[BCN - {art}]`" for art in inst["articulos_bcn"]]
                md_lines.append(f"**Concordancias Legales:** {' '.join(citas)}\n")

            if inst.get("jurisprudencia_rectora"):
                md_lines.append(f"**Criterio Jurisprudencial Rector:** `{inst['jurisprudencia_rectora']}`\n")

            md_lines.append("---\n")

        return "\n".join(md_lines).strip() + "\n"

    def compute_savings(self, raw_text: str, optimized_md: str) -> Dict[str, Any]:
        """Calcula la métrica de ahorro de tokens entre el texto crudo y el Markdown optimizado."""
        raw_tokens = self.estimate_tokens(raw_text)
        opt_tokens = self.estimate_tokens(optimized_md)
        savings_pct = round(((raw_tokens - opt_tokens) / max(1, raw_tokens)) * 100, 1)
        return {
            "tokens_texto_original": raw_tokens,
            "tokens_markdown_optimizado": opt_tokens,
            "tokens_ahorrados": raw_tokens - opt_tokens,
            "porcentaje_reduccion": f"{savings_pct}%"
        }


def clean_and_optimize_markdown(raw_text: str) -> str:
    """Limpia ruido y artefactos editoriales de un texto crudo de doctrina."""
    optimizer = DoctrinaTokenOptimizer()
    return optimizer.clean_raw_text(raw_text)


def calculate_token_compression(raw_text: str, optimized_text: str) -> Dict[str, Any]:
    """Calcula estadísticas de compresión de tokens entre texto original y optimizado."""
    optimizer = DoctrinaTokenOptimizer()
    savings = optimizer.compute_savings(raw_text, optimized_text)
    return {
        "tokens_originales": savings["tokens_texto_original"],
        "tokens_optimizados": savings["tokens_markdown_optimizado"],
        "ahorro_porcentual": float(savings["porcentaje_reduccion"].replace("%", ""))
    }

