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

# Importar configuración y conectores
from config import check_configuration
from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from tdlc_connector import TDLCClient
from ambiental_connector import AmbientalClient
from pjud_connector import PJUDClient

# Prompt Maestro de Especialización en Derecho Chileno
SYSTEM_PROMPT_CHILE = """Eres "Open Legal Chile", un asistente de inteligencia jurídica altamente especializado en el ordenamiento jurídico de la República de Chile (Sistema Romano-Germánico / Civil Law / Derecho Continental Codificado).

PRINCIPIOS FUNDAMENTALES:
1. La LEY es la fuente formal primordial (Art. 1 Código Civil).
2. Jurisprudencia con efecto relativo (Art. 3 inc. 2 Código Civil), pero con valor doctrinal orientador.
3. PROHIBIDO usar conceptos o términos del Common Law estadounidense (como at-will employment, punitive damages, discovery, subpoena, grand jury, Title VII, Delaware C-Corp). Usa terminología procesal y sustantiva chilena (necesidades de la empresa, finiquito, fuero, daño moral, daño emergente, lucro cesante, otrosí, reposición, apelación, casación, SpA, etc.).
4. CITA rigurosamente las fuentes con el formato:
   - [BCN - Código Civil, Art. 1545] o [BCN - Ley N° 21.643, Art. 2]
   - [CPR 1980 - Art. 19 N° X]
   - [Dictamen DT N° XXXX/XX]
   - [Dictamen CGR N° XXXXX]
   - [CS - Rol N° XXX-XXXX] o [C.A. de Santiago - Rol N° XXX-XXXX]
5. Si se detecta un caso de alta trascendencia o inminencia procesal, incluye la advertencia de revisión jurídica por abogado habilitado.
"""

bcn_client = BCNClient()
cgr_client = CGRClient()
dt_client = DTClient()
sma_client = AmbientalClient()
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
                    context_chunks.append(f"• [{it.get('tribunal')} — {it.get('rol')}] {it.get('caratula')}: {it.get('doctrina', '')[:250]}")
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
        "gemini-2.5-pro": "gemini-2.0-flash",
        "gemini-3.7-flash-high": "gemini-2.0-flash",

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
    def call_deepseek(prompt: str, messages: List[Dict[str, str]], api_key: str, model: str = "deepseek-reasoner") -> str:
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def call_anthropic(prompt: str, messages: List[Dict[str, str]], api_key: str, model: str = "claude-3-7-sonnet-20250219") -> str:
        """Llama a la API de Anthropic Claude con soporte para Thinking / Reasoning y tokens de sesión."""
        target_model = LegalChatEngine.resolve_model(model)
        url = "https://api.anthropic.com/v1/messages"
        user_msgs = [m for m in messages if m["role"] != "system"]
        payload = {
            "model": target_model,
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT_CHILE,
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]

    @staticmethod
    def call_gemini(prompt: str, messages: List[Dict[str, str]], api_key: str, model: str = "gemini-2.5-pro") -> str:
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
        
        # Convertir mensajes a formato Gemini
        contents = []
        for m in messages:
            role = "user" if m["role"] in ["user", "system"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT_CHILE}]},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def call_openai(prompt: str, messages: List[Dict[str, str]], api_key: str, model: str = "gpt-4o") -> str:
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def call_ollama(prompt: str, messages: List[Dict[str, str]], host: str = "http://localhost:11434", model: str = "llama3.3") -> str:
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"]

    DEFAULT_MODELS = {
        "anthropic": "claude-3-7-sonnet-20250219",
        "gemini": "gemini-2.0-flash",
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o",
        "ollama": "llama3.3"
    }


    def chat(self, user_message: str, provider: str, api_key: Optional[str] = None, model: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Procesa una consulta jurídica, inyecta contexto en vivo y consulta al proveedor seleccionado."""
        provider = provider.lower().strip()
        history = history or []

        # 1. Recuperar contexto jurídico en tiempo real
        live_context = get_relevant_legal_context(user_message)
        enriched_user_msg = user_message
        if live_context:
            enriched_user_msg = f"{user_message}\n\n[CONTEXTO NORMATIVO Y DOCTRINAL DE OPEN LEGAL CHILE]:\n{live_context}"

        # 2. Construir historial de mensajes con system prompt
        messages = [{"role": "system", "content": SYSTEM_PROMPT_CHILE}]
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": enriched_user_msg})

        # 3. Resolver API Key y Modelo
        key = api_key or os.getenv(f"{provider.upper()}_API_KEY", "")
        chosen_model = model or self.DEFAULT_MODELS.get(provider, "")

        # 4. Enrutar según el proveedor
        try:
            if provider == "deepseek":
                if not key:
                    return {"error": "Falta DEEPSEEK_API_KEY. Configúrala en .env o en la interfaz."}
                reply = self.call_deepseek(user_message, messages, key, chosen_model or "deepseek-reasoner")

            elif provider == "anthropic" or provider == "claude":
                if not key:
                    return {"error": "Falta ANTHROPIC_API_KEY. Configúrala en .env o en la interfaz."}
                reply = self.call_anthropic(user_message, messages, key, chosen_model or "claude-3-7-sonnet-20250219")

            elif provider == "gemini" or provider == "google":
                if not key:
                    return {"error": "Falta GEMINI_API_KEY. Configúrala en .env o en la interfaz."}
                reply = self.call_gemini(user_message, messages, key, chosen_model or "gemini-2.5-pro")

            elif provider == "openai":
                if not key:
                    return {"error": "Falta OPENAI_API_KEY. Configúrala en .env o en la interfaz."}
                reply = self.call_openai(user_message, messages, key, chosen_model or "o3-mini")

            elif provider == "ollama":
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                reply = self.call_ollama(user_message, messages, host, chosen_model or "llama3.3")

            else:
                return {"error": f"Proveedor '{provider}' no reconocido. Opciones: deepseek, anthropic, gemini, openai, ollama."}

            return {
                "provider": provider,
                "model": chosen_model,
                "reply": reply,
                "contextUsed": bool(live_context),
                "liveContext": live_context
            }

        except Exception as e:
            return {"error": f"Error consultando al proveedor '{provider}': {str(e)}"}

    def verify_credentials(self, provider: str, api_key: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Prueba de conexión en vivo con la clave o token para verificar validez inmediata."""
        test_messages = [{"role": "user", "content": "Hola, responde únicamente con la palabra 'OK'."}]
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
