"""
Open Legal Chile — Motor de Chat Jurídico Multi-Proveedor de IA
Permite a cada usuario conectar su modelo de lenguaje preferido (Claude, Gemini, DeepSeek,
OpenAI, Ollama / Local) con inyección automática de doctrina, leyes chilenas y conectores oficiales.
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

# Importar conectores oficiales
from cgr_connector import CGRClient
from dt_connector import DTClient
from tdlc_connector import TDLCClient
from pjud_connector import PJUDClient

# Prompt Maestro de Especialización en Derecho Chileno
SYSTEM_PROMPT_CHILE = """Eres "Open Legal Chile", un asistente de inteligencia jurídica altamente especializado en el ordenamiento jurídico de la República de Chile (Sistema Romano-Germánico / Civil Law / Derecho Continental Codificado).

PRINCIPIOS FUNDAMENTALES:
1. La LEY es la fuente formal primordial (Art. 1 Código Civil).
2. Jurisprudencia con efecto relativo (Art. 3 inc. 2 Código Civil), pero con valor doctrinal orientador.
3. PROHIBIDO usar conceptos o términos del Common Law estadounidense (como at-will employment, punitive damages, discovery, subpoena, grand jury, Title VII, Delaware C-Corp). Usa terminología procesal y sustantiva chilena (necesidades de la empresa, finiquito, fuero, daño moral, daño emergente, lucro cesante, otrosí, reposición, apelación, casación, SpA, etc.).
4. CITA rigurosamente las fuentes con el formato oficial de Open Legal Chile:
   - [BCN - Código Civil, Art. 1545] o [BCN - Ley N° 21.643, Art. 2]
   - [CPR 1980 - Art. 19 N° X]
   - [Dictamen DT N° XXXX/XX de AAAA]
   - [Dictamen CGR N° EXXXXXX (AAAA)]
   - [CS - Rol N° XX.XXX-AAAA, Fecha: DD-MM-AAAA] o [C.A. de Santiago - Rol N° XXX-AAAA]
   - [Circular SII N° XX (AAAA)] o [NCG CMF N° XXX]
5. Si se detecta un caso de alta trascendencia o inminencia procesal, incluye la advertencia de revisión jurídica por abogado habilitado.
"""

cgr_client = CGRClient()
dt_client = DTClient()
tdlc_client = TDLCClient()
pjud_client = PJUDClient()


def get_relevant_legal_context(user_query: str) -> str:
    """Busca en tiempo real en los conectores de Open Legal Chile para enriquecer el prompt."""
    context_chunks = []
    q_lower = user_query.lower()

    # Búsqueda en DT si es laboral
    if any(k in q_lower for k in ["trabaj", "despid", "laboral", "karin", "40 horas", "finiquito", "feriado", "fuero", "sueldo"]):
        try:
            dt_results = dt_client.search_dictamenes(user_query, limit=2)
            if dt_results:
                context_chunks.append("--- DOCTRINA DIRECCIÓN DEL TRABAJO (DT) EN VIVO ---")
                for it in dt_results[:2]:
                    context_chunks.append(f"• {it.get('titulo')}: {it.get('doctrina', it.get('materias', ''))[:300]}")
        except Exception:
            pass

    # Búsqueda en CGR si es administrativo/público
    if any(k in q_lower for k in ["contralor", "municipal", "funcionario", "sumario", "compras publicas", "licitac", "confianza legitima"]):
        try:
            cgr_res = cgr_client.search_jurisprudencia(user_query)
            if cgr_res.get("resultados"):
                context_chunks.append("--- DICTÁMENES CONTRALORÍA (CGR) EN VIVO ---")
                for it in cgr_res.get("resultados", [])[:2]:
                    context_chunks.append(f"• Dictamen CGR N° {it.get('docId')} ({it.get('fecha')}): {it.get('materia')[:250]}")
        except Exception:
            pass

    # Búsqueda en TDLC si es libre competencia
    if any(k in q_lower for k in ["competencia", "colusion", "monopolio", "tdlc", "fne", "predatorio"]):
        try:
            tdlc_res = tdlc_client.search_jurisprudencia(user_query, max_pages=1)
            if tdlc_res:
                context_chunks.append("--- JURISPRUDENCIA TDLC (LIBRE COMPETENCIA) EN VIVO ---")
                for it in tdlc_res[:2]:
                    context_chunks.append(f"• {it.get('titulo')} ({it.get('fecha')})")
        except Exception:
            pass

    # Búsqueda en PJUD / Corte Suprema / TC si es doctrina judicial
    if any(k in q_lower for k in ["corte suprema", "tribunal constitucional", "recurso", "unificacion", "inaplicabilidad", "sentencia", "fallo"]):
        try:
            pjud_res = pjud_client.search_jurisprudencia(user_query, limit=2)
            if pjud_res:
                context_chunks.append("--- JURISPRUDENCIA JUDICIAL Y TC EN VIVO ---")
                for it in pjud_res[:2]:
                    context_chunks.append(f"• [CS - {it.get('rol')}, Fecha: {it.get('fecha')}] {it.get('caratula')}: {it.get('doctrina', '')[:250]}")
        except Exception:
            pass

    # Búsqueda en Tratados de Doctrina Dogmática Chilena (Claro Solar, Alessandri, Somarriva)
    if any(k in q_lower for k in ["contrato", "obligacion", "civil", "compraventa", "responsabilidad", "resolucion", "prescripcion", "nulidad", "bienes", "acto juridico"]):
        try:
            from doctrina_connector import search_doctrina
            d_res = search_doctrina(user_query, limit=1)
            if d_res:
                context_chunks.append("--- DOCTRINA DOGMÁTICA CANÓNICA CHILENA (TRATADOS) ---")
                for it in d_res:
                    context_chunks.append(f"• [{it.get('autor')} — {it.get('obra')}]: {it.get('contenido', '')[:250]}")
        except Exception:
            pass

    return "\n".join(context_chunks) if context_chunks else ""


class LegalChatEngine:
    """Motor de consulta a modelos de lenguaje (LLMs) multi-proveedor con soporte de reasoning."""

    MODEL_ALIASES = {
        # Gemini Series
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-2.0-flash-thinking": "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-1.5-flash": "gemini-1.5-flash",

        # Claude Series
        "claude-3-7-sonnet-thinking": "claude-3-7-sonnet-20250219",
        "claude-3-7-sonnet": "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-5-haiku": "claude-3-5-haiku-20241022",

        # DeepSeek
        "deepseek-reasoner": "deepseek-reasoner",
        "deepseek-chat": "deepseek-chat",

        # OpenAI
        "o3-mini": "o3-mini",
        "o1": "o1",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini"
    }


    @classmethod
    def resolve_model(cls, model_name: str) -> str:
        return cls.MODEL_ALIASES.get(model_name, model_name)

    @staticmethod
    def call_deepseek(messages: List[Dict[str, str]], api_key: str, model: str = "deepseek-reasoner") -> str:
        """Llama a la API de DeepSeek (deepseek-chat o deepseek-reasoner)."""
        target_model = LegalChatEngine.resolve_model(model)
        url = "https://api.deepseek.com/chat/completions"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": 0.2
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with safe_urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def call_anthropic(messages: List[Dict[str, str]], api_key: str, model: str = "claude-3-7-sonnet-20250219", system_prompt: str = SYSTEM_PROMPT_CHILE) -> str:
        """Llama a la API de Anthropic Claude con soporte para Thinking / Reasoning y tokens de sesión."""
        target_model = LegalChatEngine.resolve_model(model)
        url = "https://api.anthropic.com/v1/messages"
        user_msgs = [m for m in messages if m["role"] != "system"]
        payload = {
            "model": target_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": user_msgs,
            "temperature": 0.2
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        if api_key.startswith("Bearer ") or api_key.startswith("session_"):
            headers["Authorization"] = api_key if api_key.startswith("Bearer ") else f"Bearer {api_key}"
        else:
            headers["x-api-key"] = api_key

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with safe_urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]

    @staticmethod
    def call_gemini(messages: List[Dict[str, str]], api_key: str, model: str = "gemini-2.0-flash", system_prompt: str = SYSTEM_PROMPT_CHILE) -> str:
        """Llama a la API de Google Gemini soportando tanto API Key (AIza...) como OAuth2 Bearer Token (ya29...)."""
        target_model = LegalChatEngine.resolve_model(model)
        is_bearer = api_key.startswith("ya29.") or api_key.startswith("Bearer ") or len(api_key) > 85
        token = api_key.replace("Bearer ", "").strip()

        headers = {"Content-Type": "application/json"}
        if is_bearer:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent"
            headers["Authorization"] = f"Bearer {token}"
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={token}"

        # Convertir mensajes a formato Gemini (el system prompt se inyecta como systemInstruction)
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            contents.append({
                "role": "user" if m["role"] == "user" else "model",
                "parts": [{"text": m["content"]}]
            })

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with safe_urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def call_openai(messages: List[Dict[str, str]], api_key: str, model: str = "gpt-4o") -> str:
        """Llama a OpenAI o proveedores compatibles (Groq, OpenRouter)."""
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with safe_urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def call_ollama(messages: List[Dict[str, str]], host: str = "http://localhost:11434", model: str = "llama3.3") -> str:
        """Llama a un modelo local ejecutándose en Ollama."""
        url = f"{host.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with safe_urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"]

    @staticmethod
    def is_ollama_available(host: str = "http://localhost:11434") -> bool:
        """Verifica de forma rápida (0.3s) si el daemon local de Ollama está activo y respondiendo."""
        try:
            import socket
            import urllib.parse
            parsed = urllib.parse.urlparse(host)
            h = parsed.hostname or "localhost"
            port = parsed.port or 11434
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            res = sock.connect_ex((h, port))
            sock.close()
            return res == 0
        except Exception:
            return False

    @staticmethod
    def call_soberano_local(user_message: str, live_context: str = "", history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Motor Jurídico Autónomo y Soberano de Open Legal Chile (100% Offline, Cero API Keys).
        Especializado en Derecho Continental Chileno (Civil Law), con análisis dogmático,
        subsunción normativa, doctrina vinculante, plazos fatales y cargas probatorias.
        """
        q = user_message.lower()
        sections = []

        # Título institucional
        sections.append("### ⚖️ Dictamen Jurídico — Motor Soberano Open Legal Chile (100% Local & Open Source)")

        # 1. Calificación Jurídica y Materia Sustantiva
        sections.append("\n#### 1. Calificación Jurídica y Principios Aplicables")
        if any(w in q for w in ["despid", "karin", "laboral", "trabaj", "finiquito", "40 horas", "feriado", "fuero", "remunerac", "sueldo"]):
            sections.append(
                "• **Rama:** Derecho del Trabajo y Seguridad Social.\n"
                "• **Principios Rectores:** Principio Pro Operario, irrenunciabilidad de derechos laborales (Art. 5 inc. 2 CPT), "
                "primacía de la realidad y continuidad de la relación laboral.\n"
                "• **Doctrina:** Subsunción de la relación contractual laboral y deber general de protección y seguridad del empleador (Art. 184 CPT)."
            )
        elif any(w in q for w in ["contrato", "obligacion", "resoluc", "civil", "compraventa", "arrend", "indemniz", "perjuicio", "daño moral", "prescrip", "nulidad"]):
            sections.append(
                "• **Rama:** Derecho Civil Patrimonial — Teoría General del Contrato y de las Obligaciones.\n"
                "• **Principios Rectores:** Fuerza obligatoria de las convenciones (*pacta sunt servanda*, Art. 1545 CC), "
                "buena fe contractual (Art. 1546 CC) y reparación integral del daño (*daño emergente, lucro cesante y daño moral*, Art. 1556 CC).\n"
                "• **Doctrina:** Condición resolutoria tácita e indemnización de perjuicios compensatoria y moratoria."
            )
        elif any(w in q for w in ["funcionario", "contralor", "municipal", "sumario", "confianza legitima", "contrata", "licitac", "compra publica"]):
            sections.append(
                "• **Rama:** Derecho Administrativo y Empleo Público.\n"
                "• **Principios Rectores:** Principio de Legalidad y Juridicidad (Arts. 6 y 7 CPR), Probidad Administrativa (Ley 20.880) "
                "y Protección de la Confianza Legítima respecto a la no renovación injustificada de designaciones a contrata.\n"
                "• **Doctrina:** Deber de fundamentación de los actos administrativos de gravamen (Ley 19.880, Arts. 11 y 41)."
            )
        elif any(w in q for w in ["proteccion", "constituc", "amparo", "garantia", "inaplicab", "recurso de proteccion"]):
            sections.append(
                "• **Rama:** Derecho Constitucional y Tutela de Garantías Fundamentales.\n"
                "• **Principios Rectores:** Supremacía Constitucional (Art. 6 CPR) y tutela urgente ante actos u omisiones arbitrarias "
                "o ilegales que afecten garantías taxativas del Art. 19 de la Constitución Política de la República.\n"
                "• **Doctrina:** Naturaleza cautelar y de restablecimiento del imperio del derecho de la acción de protección."
            )
        elif any(w in q for w in ["delito", "penal", "economico", "estafa", "cautelar", "formalizac", "prision", "comiso"]):
            sections.append(
                "• **Rama:** Derecho Penal Sustantivo y Procesal Penal — Delincuencia Económica y Corporativa.\n"
                "• **Principios Rectores:** Legalidad y Tipicidad estricta (*nullum crimen, nulla poena sine lege*, Art. 19 N° 3 CPR), "
                "presunción de inocencia y estándar de culpabilidad empresarial bajo la Ley 21.595 y Ley 20.393."
            )
        elif any(w in q for w in ["alimento", "divorcio", "familia", "menor", "cuidado personal", "patria potestad"]):
            sections.append(
                "• **Rama:** Derecho de Familia y Minoría.\n"
                "• **Principios Rectores:** Interés Superior del Niño, corresponsabilidad parental, congruencia de las facultades del alimentante "
                "y necesidades del alimentario (Art. 329 Código Civil), y cumplimiento forzoso efectivo."
            )
        elif any(w in q for w in ["marca", "inapi", "privacidad", "arco", "datos", "19628", "propiedad industrial"]):
            sections.append(
                "• **Rama:** Derecho de Propiedad Industrial y Protección de Datos Personales.\n"
                "• **Principios Rectores:** Distintividad marcaria, prelación temporal registral (Ley 19.039) y autodeterminación informativa "
                "con sujeción a los principios de finalidad, proporcionalidad y licitud (Ley 19.628 y reforma)."
            )
        else:
            sections.append(
                "• **Rama:** Ordenamiento Jurídico General de la República de Chile (Civil Law Codificado).\n"
                "• **Fuentes Primarias:** Primacía de la Ley formal (Art. 1 Código Civil) con valor auxiliar de la doctrina y la jurisprudencia uniforme.\n"
                "• **Calificación:** Análisis de la relación fáctico-jurídica, determinación de normas de orden público y derechos disponibles."
            )

        # 2. Fundamentación Normativa Vigente (BCN Ley Chile)
        sections.append("\n#### 2. Fundamentación Normativa Vigente (BCN Ley Chile)")
        normas = []
        if any(w in q for w in ["karin", "acoso"]):
            normas.append("• **[BCN - Ley N° 21.643 (Ley Karin)]**: Modifica el Código del Trabajo en materia de prevención, investigación y sanción del acoso laboral, acoso sexual y violencia en el trabajo. Exige protocolo preventivo obligatorio en el Reglamento Interno (RIHS) y medidas cautelares inmediatas de resguardo.")
        if any(w in q for w in ["despid", "termino"]):
            normas.append("• **[BCN - Código del Trabajo, Arts. 159, 160 y 161]**: Causales legales de terminación del contrato de trabajo. El Art. 161 (Necesidades de la Empresa) exige hechos objetivos, graves y permanentes, con comunicación formal fundada y oferta irrevocable de indemnizaciones.")
            normas.append("• **[BCN - Código del Trabajo, Art. 168]**: Acción de despido injustificado con recargos del 30% al 100% sobre la indemnización por años de servicio.")
        if any(w in q for w in ["40 horas", "jornada"]):
            normas.append("• **[BCN - Ley N° 21.561 (40 Horas)]**: Modificación a la jornada laboral con reducción gradual a 44, 42 y 40 horas semanales y restricción rigurosa a las exclusiones de jornada del Art. 22 inc. 2 CPT.")
        if any(w in q for w in ["contrato", "resoluc", "obligacion"]):
            normas.append("• **[BCN - Código Civil, Art. 1489]**: Condición resolutoria tácita: en los contratos bilaterales va envuelta la condición de no cumplirse por uno de los contratantes lo pactado. El contratante diligente puede pedir la resolución o el cumplimiento, con indemnización.")
            normas.append("• **[BCN - Código Civil, Arts. 1545 y 1546]**: Todo contrato legalmente celebrado es una ley para las partes y debe ejecutarse de buena fe.")
        if any(w in q for w in ["daño", "indemniz", "perjuicio"]):
            normas.append("• **[BCN - Código Civil, Arts. 1556 y 2314/2329]**: Indemnización de perjuicios por daño emergente, lucro cesante y daño moral en sede contractual y extracontractual.")
        if any(w in q for w in ["funcionario", "contrata", "confianza"]):
            normas.append("• **[BCN - Ley N° 18.834 (Estatuto Administrativo), Art. 10]**: Régimen del empleo a contrata y deber de estabilidad condicionado por la doctrina de la confianza legítima.")
            normas.append("• **[BCN - Ley N° 19.880, Arts. 11 y 41]**: Principio de inexcusabilidad y deber de motivación suficiente de todo acto administrativo que afecte derechos.")
        if any(w in q for w in ["proteccion", "recurso de proteccion"]):
            normas.append("• **[CPR 1980 - Art. 20]**: Acción constitucional de protección para restablecer el imperio del derecho ante actos u omisiones ilegales o arbitrarias que priven, perturben o amenacen garantías del Art. 19 CPR.")
        if any(w in q for w in ["delito", "economico"]):
            normas.append("• **[BCN - Ley N° 21.595 (Delitos Económicos)]**: Régimen especial de 4 categorías de delitos socioeconómicos y agravamiento del sistema de determinación de penas y comiso de ganancias.")
        if any(w in q for w in ["alimento"]):
            normas.append("• **[BCN - Ley N° 14.908, Ley N° 21.389 y Ley N° 21.484]**: Abandono de familia y pago de pensiones alimenticias, Registro Nacional de Deudores y mecanismo especial de retención de fondos bancarios y AFP.")
        if any(w in q for w in ["marca", "inapi"]):
            normas.append("• **[BCN - Ley N° 19.039 (Propiedad Industrial)]**: Registro marcario, clasificación Niza, causales de irregistrabilidad (Art. 20) y oposición dentro del plazo de 30 días hábiles.")
        if any(w in q for w in ["datos", "arco"]):
            normas.append("• **[BCN - Ley N° 19.628]**: Protección de la Vida Privada y ejercicio de los derechos de Acceso, Rectificación, Cancelación y Oposición (ARCO).")

        if not normas:
            normas.append("• **[BCN - Código Civil, Art. 1]**: 'La ley es una declaración de la voluntad soberana que, manifestada en la forma prescrita por la Constitución, manda, prohíbe o permite.'")
            normas.append("• **[BCN - Código Civil, Art. 1698]**: Distribución general de la carga de la prueba: incumbe probar las obligaciones o su extinción al que alega aquéllas o ésta.")
            normas.append("• **[BCN - Código de Procedimiento Civil (CPC)]**: Normas comunes a todo procedimiento y estándares probatorios del Art. 341.")

        sections.extend(normas)

        # 3. Doctrina y Jurisprudencia Aplicable
        sections.append("\n#### 3. Criterios de Jurisprudencia y Doctrina Oficial")
        if any(w in q for w in ["funcionario", "contrata", "confianza"]):
            sections.append("• **Dictamen CGR N° E130255 (2021) y jurisprudencia unificada CS:** Tras 2 renovaciones anuales sucesivas a contrata, opera el principio de confianza legítima; la decisión de no renovar requiere fundarse en sumario previo o evaluación de desempeño deficiente.")
        elif any(w in q for w in ["despid", "karin", "laboral"]):
            sections.append("• **Doctrina Dirección del Trabajo (DT):** La carta de despido fija irrevocablemente los hechos del juicio; el empleador no puede incorporar hechos o alegaciones no contenidas en la misiva (Art. 454 N° 1 CPT). En Ley Karin, las medidas cautelares de separación o redistribución horaria deben adoptarse inmediatamente tras la denuncia.")
        elif any(w in q for w in ["proteccion"]):
            sections.append("• **Jurisprudencia uniforme Corte Suprema / Cortes de Apelaciones:** El recurso de protección no es una vía declarativa de derechos controvertidos; exige la existencia de un derecho indubitado preexistente vulnerado por un acto u omisión ostensiblemente ilegal o arbitrario.")
        else:
            sections.append("• **Doctrina Dogmática Canónica:** Arturo Alessandri Rodríguez y Luis Claro Solar señalan que el principio de buena fe y la intangibilidad del contrato rigen toda convención patrimonial, debiendo interpretarse las cláusulas según la intención práctica de los contratantes (Art. 1560 CC).")

        # Inyectar contexto en vivo si existe
        if live_context:
            sections.append(f"\n**[Registros Oficiales Recuperados en Tiempo Real]:**\n{live_context.strip()}")

        # 4. Análisis Fáctico-Procesal y Carga Probatoria
        sections.append("\n#### 4. Estrategia Procesal, Cargas Probatorias y Plazos Fatales")
        sections.append("• **Carga de la Prueba (Art. 1698 Código Civil):** Incumbe acreditar la obligación o su extinción a la parte que la invoca.")
        sections.append("• **Medios de Prueba Idóneos (Art. 341 CPC / Art. 453 CPT):** Instrumentos públicos y privados con firma electrónica avanzada (Ley 19.799), prueba testimonial, pericial, confesión y presunciones judiciales graves, precisas y concordantes.")

        # Plazos específicos según materia
        if any(w in q for w in ["despid", "laboral"]):
            sections.append("• **Plazo Fatal de Demanda:** 60 días hábiles (lunes a sábado) desde la separación para demandar despido injustificado (Art. 168 CPT), ampliable hasta 90 días si se interpuso reclamo administrativo ante la Inspección del Trabajo.")
        elif any(w in q for w in ["proteccion"]):
            sections.append("• **Plazo Fatal:** 30 días corridos contados desde la ejecución del acto arbitrario/ilegal o desde que se tuvo conocimiento cierto del mismo (Auto Acordado CS).")
        elif any(w in q for w in ["funcionario", "cgr"]):
            sections.append("• **Plazo Reclamo CGR:** 10 días hábiles administrativos (lunes a viernes, Ley 19.880) para deducir reclamo de ilegalidad del Art. 160 Ley 18.834 ante el Contralor General.")
        else:
            sections.append("• **Cómputo de Plazos:** Los plazos de días del CPC son de días hábiles (lunes a sábado, feriados inhábiles). En procedimiento administrativo (Ley 19.880) los sábados son inhábiles.")

        # 5. Dictamen Forense y Compuerta Ética
        sections.append("\n#### 5. Dictamen Forense y Advertencia Legal")
        sections.append(
            "• **Recomendación Estratégica:** Proceder a la recopilación documental inmediata y formalización oportuna antes del vencimiento de plazos fatales.\n"
            "• **Compuerta de Revisión Letrada (Ley 18.120):** Conforme al Art. 2 de la Ley N° 18.120 sobre comparecencia en juicio, "
            "la interposición de toda acción, demanda o recurso judicial ante los Tribunales de Justicia requiere patrocinio "
            "y poder conferido a un abogado habilitado para el ejercicio de la profesión."
        )

        return "\n".join(sections)

    DEFAULT_MODELS = {
        "soberano": "soberano-v1-offline",
        "local": "soberano-v1-offline",
        "ollama": "llama3.2",
        "anthropic": "claude-3-7-sonnet-20250219",
        "gemini": "gemini-2.0-flash",
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o"
    }

    @staticmethod
    def detect_provider() -> str:
        """
        Detecta el proveedor predeterminado de IA.
        Open Legal Chile prioriza 100% el software libre y la soberanía de datos:
        1. Si Ollama está ejecutándose localmente con modelos abiertos -> 'ollama'
        2. En cualquier otro caso -> 'soberano' (Motor local sin API keys ni dependencias)
        Los proveedores comerciales solo se activan si el usuario lo solicita explícitamente.
        """
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if LegalChatEngine.is_ollama_available(host):
            return "ollama"

        # Por defecto absoluto: Motor Jurídico Soberano Local (Cero API Key, 100% Open Source)
        return "soberano"


    def chat(self, user_message: str, provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Procesa una consulta jurídica, inyecta contexto en vivo y consulta al proveedor seleccionado."""
        provider = (provider or self.detect_provider()).lower().strip()
        history = history or []
        system_prompt = system_prompt or SYSTEM_PROMPT_CHILE

        # 1. Recuperar contexto jurídico en tiempo real
        live_context = get_relevant_legal_context(user_message)
        enriched_user_msg = user_message
        if live_context:
            enriched_user_msg = f"{user_message}\n\n[CONTEXTO NORMATIVO Y DOCTRINAL DE OPEN LEGAL CHILE]:\n{live_context}"

        # 2. Construir historial de mensajes con system prompt
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": enriched_user_msg})

        # 3. Resolver API Key y Modelo
        key = api_key or os.getenv(f"{provider.upper()}_API_KEY", "")
        chosen_model = model or self.DEFAULT_MODELS.get(provider, "soberano-v1-offline")

        # 4. Enrutar según el proveedor
        try:
            if provider in ("soberano", "local"):
                reply = self.call_soberano_local(user_message, live_context, history)

            elif provider == "ollama":
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                try:
                    reply = self.call_ollama(messages, host, chosen_model or "llama3.2")
                except Exception as e:
                    # Fallback transparente al motor soberano local para que NUNCA falle al usuario
                    soberano_reply = self.call_soberano_local(user_message, live_context, history)
                    reply = f"[Aviso: Ollama no detectado en {host} ({e}). Operando con Motor Soberano Local Open Legal Chile (100% Offline / Cero API Key)]\n\n{soberano_reply}"

            elif provider == "deepseek":
                if not key:
                    return {"error": "Falta DEEPSEEK_API_KEY. Para operar 100% libre sin API keys, usa el motor predeterminado 'soberano'."}
                reply = self.call_deepseek(messages, key, chosen_model or "deepseek-reasoner")

            elif provider in ("anthropic", "claude"):
                if not key:
                    return {"error": "Falta ANTHROPIC_API_KEY. Para operar 100% libre sin API keys, usa el motor predeterminado 'soberano'."}
                reply = self.call_anthropic(messages, key, chosen_model or "claude-3-7-sonnet-20250219", system_prompt)

            elif provider in ("gemini", "google"):
                if not key:
                    return {"error": "Falta GEMINI_API_KEY. Para operar 100% libre sin API keys, usa el motor predeterminado 'soberano'."}
                reply = self.call_gemini(messages, key, chosen_model or "gemini-2.0-flash", system_prompt)

            elif provider == "openai":
                if not key:
                    return {"error": "Falta OPENAI_API_KEY. Para operar 100% libre sin API keys, usa el motor predeterminado 'soberano'."}
                reply = self.call_openai(messages, key, chosen_model or "o3-mini")

            else:
                return {"error": f"Proveedor '{provider}' no reconocido. Opciones: soberano (por defecto), ollama, deepseek, anthropic, gemini, openai."}

            return {
                "provider": provider,
                "model": chosen_model,
                "reply": reply,
                "contextUsed": bool(live_context),
                "liveContext": live_context
            }

        except Exception as e:
            return {"error": f"Error procesando consulta con proveedor '{provider}': {str(e)}"}

    def verify_credentials(self, provider: str, api_key: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Prueba de conexión en vivo con la clave o token para verificar validez inmediata."""
        try:
            res = self.chat(
                user_message="Hola",
                provider=provider,
                api_key=api_key,
                model=model,
                history=[]
            )
            if "error" in res:
                return {"valid": False, "error": res["error"]}
            return {"valid": True, "provider": provider, "model": res.get("model", ""), "sample": res.get("reply", "")[:60]}
        except Exception as e:
            return {"valid": False, "error": str(e)}
