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

    def critique(self, text: str, provider: Optional[str] = None, api_key: str = "", model: str = "") -> Dict[str, Any]:
        """Ejecuta una auditoría forense completa sobre el texto legal provisto."""
        if not text or not text.strip():
            return {"error": "El texto para auditar no puede estar vacío."}

        res = self.chat_engine.chat(
            user_message=f"Por favor realiza la auditoría de 5 dimensiones sobre este texto:\n\n{text}",
            provider=provider,
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
