"""
Open Legal Chile — Motor Socrático de Examen de Grado y Cédulas Jurídicas
Democratiza la preparación del Examen de Grado de Derecho en Chile conectando
cédulas de examen con la doctrina canónica (SQLite FTS5) y los Códigos de la República.
"""

import os
import sys
import json
import random
from typing import Dict, Any, List, Optional

# Conexión con doctrina canónica
try:
    from doctrina_connector import search_doctrina, get_institucion
except ImportError:
    search_doctrina = None
    get_institucion = None

CEDULAS_DATA = {
    "civil": {
        "obligaciones": [
            {
                "id": "civ_obl_01",
                "tema": "Efectos de las Obligaciones e Incumplimiento Contractual",
                "pregunta": "¿Cuáles son los requisitos de la indemnización de perjuicios contractual y qué postura doctrinaria tiene René Ramos Pazos sobre la imputabilidad y la mora del deudor?",
                "articulos": ["Art. 1556 CC", "Art. 1557 CC", "Art. 1558 CC"],
                "doctrina_autor": "Ramos Pazos",
                "obra": "ramos_pazos_obligaciones",
                "criterio_evaluacion": "Debe mencionar: 1) Infracción contractual, 2) Imputabilidad (dolo o culpa), 3) Mora del deudor, 4) Daño o perjuicio cierto, 5) Relación de causalidad. Según Ramos Pazos, la mora es el retardo imputable que persiste tras la reconvención judicial."
            },
            {
                "id": "civ_obl_02",
                "tema": "Resolución por Inejecución y Condición Resolutoria Tácita",
                "pregunta": "Explique los elementos del Art. 1489 del Código Civil. ¿Opera de pleno derecho la resolución o requiere sentencia judicial? ¿Qué facultades tiene el contratante cumplidor?",
                "articulos": ["Art. 1489 CC", "Art. 1490 CC", "Art. 1491 CC"],
                "doctrina_autor": "Ramos Pazos",
                "obra": "ramos_pazos_obligaciones",
                "criterio_evaluacion": "Debe distinguir entre condición resolutoria ordinaria y tácita. La tácita requiere sentencia judicial y da acción alternativa: cumplimiento o resolución, ambas con indemnización de perjuicios."
            }
        ],
        "responsabilidad": [
            {
                "id": "civ_resp_01",
                "tema": "Estatuto de la Responsabilidad Extracontractual",
                "pregunta": "Defina los elementos de la responsabilidad aquiliana según Enrique Barros Bourie y explique cómo opera la presunción de culpa por el hecho propio del Art. 2329 CC.",
                "articulos": ["Art. 2314 CC", "Art. 2329 CC", "Art. 2332 CC"],
                "doctrina_autor": "Barros Bourie",
                "obra": "barros_bourie_responsabilidad",
                "criterio_evaluacion": "Elementos: capacidad delictual, hecho voluntario, culpa o dolo, nexo causal y daño. Explicar la tesis de Ducci/Barros sobre el Art. 2329 como presunción general de culpa por actividades peligrosas."
            }
        ],
        "bienes": [
            {
                "id": "civ_bien_01",
                "tema": "Posesión y Acciones Protectoras del Dominio",
                "pregunta": "¿Cómo define Daniel Peñailillo la posesión conforme al Art. 700 CC? Distinga entre posesión regular e irregular y señale qué acción tiene el poseedor regular que perdió la posesión.",
                "articulos": ["Art. 700 CC", "Art. 702 CC", "Art. 894 CC"],
                "doctrina_autor": "Peñailillo",
                "obra": "penailillo_bienes",
                "criterio_evaluacion": "Definición legal del 700 (tenencia con ánimo de señor o dueño). Regular: justo título y buena fe inicial, más tradición si es traslaticio. Acción publiciana (Art. 894) para el poseedor regular camino a usucapir."
            }
        ]
    },
    "procesal": {
        "recursos": [
            {
                "id": "proc_rec_01",
                "tema": "Recurso de Apelación y Plazos Fatales",
                "pregunta": "Conforme a Cristián Maturana y Mario Mosquera, ¿cuál es el plazo para interponer apelación contra sentencia definitiva e interlocutoria? ¿Cómo se tramita la apelación subsidiaria a la reposición?",
                "articulos": ["Art. 181 CPC", "Art. 189 CPC", "Art. 194 CPC"],
                "doctrina_autor": "Maturana & Mosquera",
                "obra": "maturana_mosquera_recursos",
                "criterio_evaluacion": "Plazo: 10 días para definitiva, 5 días para interlocutoria. Subsidiaria a la reposición: debe interponerse dentro de 3 días fatales en el mismo escrito."
            },
            {
                "id": "proc_rec_02",
                "tema": "Recurso de Casación en la Forma",
                "pregunta": "Indique las causales principales del Art. 768 CPC y explique el trámite esencial de preparación del recurso de casación en la forma.",
                "articulos": ["Art. 768 CPC", "Art. 769 CPC", "Art. 170 CPC"],
                "doctrina_autor": "Maturana & Mosquera",
                "obra": "maturana_mosquera_recursos",
                "criterio_evaluacion": "Causales: incompetencia, falta de considerandos del 170, ultrapetita, etc. Preparación: haber reclamado previamente la falta ejerciendo oportunamente los recursos que la ley franquea."
            }
        ]
    }
}

FLASHCARDS_DATA = [
    {
        "area": "civil",
        "tipo": "definicion",
        "titulo": "Definición de Contrato (Art. 1438 CC)",
        "contenido": "Contrato o convención es un acto por el cual una parte se obliga para con otra a dar, hacer o no hacer alguna cosa. Cada parte puede ser una o muchas personas.",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Esencial. Comisión suele criticar que confunde contrato con convención (género y especie)."
    },
    {
        "area": "civil",
        "tipo": "definicion",
        "titulo": "Definición de Posesión (Art. 700 CC)",
        "contenido": "La posesión es la tenencia de una cosa determinada con ánimo de señor o dueño, sea que el dueño o el que se da por tal tenga la cosa por sí mismo, o por otra persona que la tenga en lugar y a nombre de él.",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Elementos subjetivo (ánimo) y objetivo (corpus)."
    },
    {
        "area": "civil",
        "tipo": "plazo",
        "titulo": "Prescripción Extintiva Ordinaria vs Ejecutiva",
        "contenido": "Acción ejecutiva: 3 años. Acción ordinaria: 5 años. La acción ejecutiva prescribe en 3 años y se convierte en ordinaria por 2 años más (Art. 2515 CC).",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Pregunta clásica de examen."
    },
    {
        "area": "civil",
        "tipo": "plazo",
        "titulo": "Prescripción de la Acción Extracontractual (Art. 2332 CC)",
        "contenido": "4 años contados desde la perpetración del acto ilícito (no desde que se manifiesta el daño según doctrina tradicional, aunque Barros Bourie distingue la manifestación del perjuicio).",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Regla estricta del Código Civil."
    },
    {
        "area": "procesal",
        "tipo": "plazo",
        "titulo": "Término Probatorio Ordinario (Art. 328 CPC)",
        "contenido": "20 días hábiles fatales para todos los medios probatorios que deban rendirse en el territorio jurisdiccional del tribunal.",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Plazo común y fatal."
    },
    {
        "area": "procesal",
        "tipo": "plazo",
        "titulo": "Plazo para Deducir Excepciones Dilatorias (Art. 305 CPC)",
        "contenido": "Dentro del término de emplazamiento y antes de contestar la demanda, todas en un mismo escrito.",
        "relevancia_grado": "⭐⭐⭐⭐⭐ Preclusión procesal."
    }
]


class ExamenGradoEngine:
    """Motor pedagógico socrático para la preparación del Examen de Grado en Chile."""

    def __init__(self):
        self.cedulas = CEDULAS_DATA
        self.flashcards = FLASHCARDS_DATA

    def interrogar_socratico(self, materia: str = "civil", dificultad: str = "media") -> Dict[str, Any]:
        """
        Selecciona una pregunta de examen de grado y provee el estándar de respuesta dogmática.
        """
        area = materia.lower()
        if area not in self.cedulas:
            area = "civil"

        subtemas = list(self.cedulas[area].keys())
        subtema_elegido = random.choice(subtemas)
        pregunta_data = random.choice(self.cedulas[area][subtema_elegido])

        # Buscar doctrina complementaria si está disponible
        doctrina_extracto = ""
        if search_doctrina and pregunta_data.get("obra"):
            try:
                res = search_doctrina(pregunta_data["tema"], obra=pregunta_data["obra"], limit=1)
                if res and res.get("resultados"):
                    doctrina_extracto = res["resultados"][0]["texto_fragmento"]
            except Exception:
                pass

        return {
            "id": pregunta_data["id"],
            "area": area.upper(),
            "tema": pregunta_data["tema"],
            "pregunta_socratica": pregunta_data["pregunta"],
            "articulos_vinculados": pregunta_data["articulos"],
            "autor_canonico": pregunta_data["doctrina_autor"],
            "obra_relevante": pregunta_data["obra"],
            "estandar_evaluacion": pregunta_data["criterio_evaluacion"],
            "doctrina_respaldo": doctrina_extracto[:350] + "..." if doctrina_extracto else "Tratado canónico indexado en FTS5."
        }

    def generar_cedula_completa(self, tema: str) -> Dict[str, Any]:
        """
        Desglosa un tema completo de cédula de examen en su estructura canónica de evaluación.
        """
        t = tema.lower()
        # Buscar en cédulas
        encontrados = []
        for area, subareas in self.cedulas.items():
            for sub, lista in subareas.items():
                for item in lista:
                    if t in item["tema"].lower() or t in sub:
                        encontrados.append(item)

        if not encontrados:
            # Fallback a tema general
            encontrados = [self.cedulas["civil"]["obligaciones"][0]]

        base = encontrados[0]
        return {
            "cedula_titulo": base["tema"],
            "interrogantes_principales": [
                base["pregunta"],
                "¿Qué excepciones contempla la ley chilena a esta regla?",
                "¿Cuál es la sanción civil o procesal en caso de infracción?"
            ],
            "normas_legales_involucradas": base["articulos"],
            "autor_doctrinal_obligatorio": base["doctrina_autor"],
            "pauta_de_aprobacion": base["criterio_evaluacion"]
        }

    def get_flashcards(self, area: Optional[str] = None, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna fichas mnemotécnicas filtradas por área (civil/procesal) o tipo (plazo/definicion).
        """
        cards = self.flashcards
        if area:
            cards = [c for c in cards if c["area"] == area.lower()]
        if tipo:
            cards = [c for c in cards if c["tipo"] == tipo.lower()]
        return cards
