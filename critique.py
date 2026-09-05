"""
Open Legal Chile — Motor de Crítica Forense en 5 Dimensiones (Legal Critique Engine)
Inspirado en el sistema de auto-crítica de 5 dimensiones de Open Design, adaptado
estrictamente para el Ordenamiento Jurídico de la República de Chile (Civil Law).
"""

import sys
from typing import Dict, Any, Optional
from chat_engine import LegalChatEngine

CRITIQUE_SYSTEM_PROMPT = """Eres el Auditor Forense Principal de Open Legal Chile.
Tu misión es auditar y criticar exhaustivamente un escrito judicial, contrato o dictamen
bajo el Derecho Continental Chileno (Civil Law) a través de 5 dimensiones estrictas:

1. JERARQUÍA NORMATIVA Y LEGALIDAD (Art. 1 Código Civil / CPR 1980):
   - ¿Se respetan las fuentes formales del derecho? (Constitución > Ley > Decreto/Reglamento).
   - ¿Se citan los artículos vigentes y pertinentes de los Códigos o Leyes especiales?
   - Prohibición estricta de términos de Common Law (sin discovery, punitive damages, at-will).

2. DOCTRINA Y JURISPRUDENCIA APLICABLE (CGR, DT, CS, C.A., TDLC):
   - ¿Se incorpora la doctrina administrativa vinculante o judicial relevante?
   - ¿Se cita correctamente el formato [BCN - ...], [Dictamen DT N° X/AAAA], [Dictamen CGR N° X (AAAA)], [CS - Rol N° ..., Fecha: ...]?

3. ESTRUCTURA FORENSE Y TRAMITACIÓN DIGITAL (Ley 20.886 / CPC):
   - ¿Cumple con la Presuma OJV, comparecencia, capítulos de Hechos y Derecho, Por Tanto y Otrosíes?

4. COHERENCIA FÁCTICA Y CARGA DE LA PRUEBA (Art. 1698 Código Civil):
   - ¿Los hechos sustentan lógicamente las peticiones concretas?
   - ¿Se ofrece prueba idónea para los hechos controvertidos?

5. COMPUERTAS ÉTICAS Y PLAZOS FATALES:
   - ¿Se advierten plazos fatales (recursos, apelaciones, descargos)?
   - ¿Contiene la compuerta de revisión para el abogado habilitado?

Devuelve tu informe estructurado con puntuación (1 a 10) por dimensión y recomendaciones concretas de corrección."""

class LegalCritiqueEngine:
    def __init__(self):
        self.chat_engine = LegalChatEngine()

    @staticmethod
    def critique_soberano_local(text: str) -> str:
        """
        Auditor Forense Determinista en 5 Dimensiones (100% Offline / Cero API Keys).
        Evalúa el texto conforme a los estándares de la Ley 20.886, Código Civil,
        Código de Procedimiento Civil, Código del Trabajo y práctica forense chilena.
        """
        t_lower = text.lower()

        # --- Dimensión 1: Jerarquía Normativa y Legalidad ---
        d1_findings = []
        d1_score = 5
        leyes_detectadas = []
        for kw in ["código civil", "código del trabajo", "código de procedimiento civil", "código penal", "código de comercio", "constitución", "cpr", "ley n°", "ley 2", "dfl"]:
            if kw in t_lower:
                leyes_detectadas.append(kw.upper())
        if leyes_detectadas:
            d1_score += min(5, len(leyes_detectadas) * 2)
            d1_findings.append(f"Cita fuentes legales formales: {', '.join(set(leyes_detectadas))}.")
        else:
            d1_score = 3
            d1_findings.append("No se observan citas directas a Códigos de la República o Leyes especiales.")

        # Anglicismos prohibidos (Common Law)
        anglicismos = []
        for term in ["discovery", "punitive damages", "at-will", "at will", "subpoena", "interrogatories", "grand jury", "deposition", "tort of"]:
            if term in t_lower:
                anglicismos.append(term)
        if anglicismos:
            d1_score = max(1, d1_score - 4)
            d1_findings.append(f"ALERTA: Se detectaron términos de Common Law prohibidos en Chile: {', '.join(anglicismos)}.")
        else:
            d1_findings.append("Cumplimiento estricto de terminología de Derecho Continental (Civil Law).")

        d1_score = max(1, min(10, d1_score))

        # --- Dimensión 2: Doctrina y Jurisprudencia Aplicable ---
        d2_findings = []
        d2_score = 4
        fuentes_juris = []
        for kw in ["dictamen", "contraloría", "cgr", "dirección del trabajo", "dt", "corte suprema", "corte de apelaciones", "rol n°", "tribunal constitucional", "tc", "tdlc", "claro solar", "alessandri", "somarriva"]:
            if kw in t_lower:
                fuentes_juris.append(kw.title())
        if fuentes_juris:
            d2_score += min(6, len(fuentes_juris) * 2)
            d2_findings.append(f"Incorpora referencias a jurisprudencia/doctrina: {', '.join(set(fuentes_juris))}.")
        else:
            d2_findings.append("Se recomienda incorporar dictámenes administrativos (CGR/DT) o fallos de unificación de la Corte Suprema.")

        d2_score = max(1, min(10, d2_score))

        # --- Dimensión 3: Estructura Forense y OJV (Ley 20.886 / CPC) ---
        d3_findings = []
        d3_score = 3
        elementos_ojv = []
        if any(w in t_lower for w in ["en lo principal", "presuma", "suma:", "procedimiento:"]):
            elementos_ojv.append("Presuma/Suma")
        if any(w in t_lower for w in ["s.j.l.", "i. corte", "juzgado de letras"]):
            elementos_ojv.append("Tribunal Encabezado")
        if any(w in t_lower for w in ["a us.", "respetuosamente digo", "rut", "cédula", "domiciliado"]):
            elementos_ojv.append("Comparecencia Formal")
        if any(w in t_lower for w in ["hechos", "antecedentes", "en lo fáctico"]):
            elementos_ojv.append("Capítulo de Hechos")
        if any(w in t_lower for w in ["derecho", "fundamentos de derecho"]):
            elementos_ojv.append("Capítulo de Derecho")
        if any(w in t_lower for w in ["por tanto", "pido a us.", "ruego a us."]):
            elementos_ojv.append("Peticiones Concretas (Por Tanto)")
        if any(w in t_lower for w in ["otrosí", "primer otrosí", "patrocinio"]):
            elementos_ojv.append("Otrosíes / Poder")

        d3_score += len(elementos_ojv)
        if len(elementos_ojv) >= 4:
            d3_findings.append(f"Estructura procesal OJV identificada: {', '.join(elementos_ojv)}.")
        else:
            d3_findings.append(f"Estructura procesal incompleta para OJV. Solo contiene: {', '.join(elementos_ojv) if elementos_ojv else 'Formato libre'}.")

        d3_score = max(1, min(10, d3_score))

        # --- Dimensión 4: Coherencia Fáctica y Carga de la Prueba (Art. 1698 CC) ---
        d4_findings = []
        d4_score = 5
        if any(w in t_lower for w in ["prueba", "documental", "testigos", "testifical", "peritaje", "pericial", "confesional", "art. 1698", "art. 341"]):
            d4_score += 4
            d4_findings.append("Ofrece y articula medios de prueba conforme al Art. 341 CPC y Art. 1698 CC.")
        else:
            d4_score = 4
            d4_findings.append("Débil fundamentación probatoria: no se individualizan medios de prueba específicos para acreditar los hechos controvertidos.")

        d4_score = max(1, min(10, d4_score))

        # --- Dimensión 5: Compuertas Éticas y Plazos Fatales ---
        d5_findings = []
        d5_score = 5
        if any(w in t_lower for w in ["plazo", "días hábiles", "fatal", "caducidad", "prescripción"]):
            d5_score += 2
            d5_findings.append("Identifica plazos procesales o fatales.")
        else:
            d5_findings.append("No advierte expresamente sobre los plazos fatales para deducir excepciones o recursos.")

        if any(w in t_lower for w in ["ley 18.120", "patrocinio", "poder", "abogado habilitado"]):
            d5_score += 3
            d5_findings.append("Cumple con la advertencia de patrocinio letrado obligatorio (Ley 18.120).")
        else:
            d5_findings.append("Omitió la mención formal de patrocinio y poder bajo la Ley 18.120.")

        d5_score = max(1, min(10, d5_score))

        # Nota Promedio Ponderado
        promedio = round((d1_score * 0.25) + (d2_score * 0.20) + (d3_score * 0.20) + (d4_score * 0.20) + (d5_score * 0.15), 1)

        report = [
            "### 📋 INFORME DE AUDITORÍA FORENSE 5D — OPEN LEGAL CHILE",
            "**Modalidad:** Motor Soberano Local (100% Offline / Cero API Keys)",
            f"**Calificación Global:** **{promedio} / 10.0**\n",
            "| Dimensión Forense | Calificación | Estado |",
            "| :--- | :---: | :--- |",
            f"| **1. Jerarquía Normativa y Legalidad (Civil Law)** | **{d1_score}/10** | {'✅ Conforme' if d1_score >= 7 else '⚠️ Mejorable'} |",
            f"| **2. Doctrina y Jurisprudencia Vinculante** | **{d2_score}/10** | {'✅ Conforme' if d2_score >= 7 else '⚠️ Requiere citas'} |",
            f"| **3. Estructura Forense y OJV (Ley 20.886 / CPC)** | **{d3_score}/10** | {'✅ Conforme' if d3_score >= 7 else '⚠️ Incompleta'} |",
            f"| **4. Carga de la Prueba (Art. 1698 CC / Art. 341 CPC)** | **{d4_score}/10** | {'✅ Conforme' if d4_score >= 7 else '⚠️ Sin prueba idónea'} |",
            f"| **5. Plazos Fatales y Patrocinio (Ley 18.120)** | **{d5_score}/10** | {'✅ Conforme' if d5_score >= 7 else '⚠️ Falta advertencia'} |\n",
            "#### 🔍 Hallazgos por Dimensión:",
            "1. **Legalidad:** " + " ".join(d1_findings),
            "2. **Jurisprudencia:** " + " ".join(d2_findings),
            "3. **Estructura OJV:** " + " ".join(d3_findings),
            "4. **Carga Probatoria:** " + " ".join(d4_findings),
            "5. **Ética y Plazos:** " + " ".join(d5_findings) + "\n",
            "#### 🛠️ Recomendaciones de Subsanación:",
            "• Incorporar Presuma formal y desglose de Otrosíes para tramitación en Oficina Judicial Virtual.",
            "• Reforzar el petitorio con ofrecimiento expreso de prueba documental y testimonial bajo apercibimiento.",
            "• Añadir otrosí de patrocinio y poder ratificando el cumplimiento de la Ley 18.120."
        ]

        return "\n".join(report)

    def critique(self, text: str, provider: Optional[str] = None, api_key: str = "", model: str = "") -> Dict[str, Any]:
        """Ejecuta una auditoría forense completa sobre el texto legal provisto."""
        if not text or not text.strip():
            return {"error": "El texto para auditar no puede estar vacío."}

        prov = (provider or LegalChatEngine.detect_provider()).lower().strip()

        # Si opera bajo el motor soberano por defecto (100% open source y sin API keys):
        if prov in ("soberano", "local"):
            critique_text = self.critique_soberano_local(text)
            return {
                "documentLength": len(text),
                "critique": critique_text,
                "provider": "soberano",
                "model": "soberano-v1-offline"
            }

        # Si el usuario solicitó explícitamente un proveedor externo o modelo LLM:
        res = self.chat_engine.chat(
            user_message=f"Por favor realiza la auditoría de 5 dimensiones sobre este texto:\n\n{text}",
            provider=prov,
            api_key=api_key,
            model=model,
            history=[],
            system_prompt=CRITIQUE_SYSTEM_PROMPT
        )

        return {
            "documentLength": len(text),
            "critique": res.get("reply", res.get("error", "Error generando crítica")),
            "provider": res.get("provider"),
            "model": res.get("model")
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        engine = LegalCritiqueEngine()
        result = engine.critique(content)
        print(result["critique"])
    else:
        print("Uso: python critique.py <archivo_a_auditar.txt>")
