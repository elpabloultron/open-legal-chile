"""
Open Legal Chile — Gestor Centralizado de Configuración y Claves de API
Carga automáticamente las variables de entorno desde el archivo .env local
o desde las variables del sistema operativo sin dependencias externas.
"""

import os
from typing import Optional


def load_env_file(filepath: Optional[str] = None) -> None:
    """Carga pares clave=valor desde un archivo .env si existe."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(filepath):
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print(f"[Aviso] No se pudo leer el archivo .env: {e}")


# Cargar variables de entorno al importar el módulo
load_env_file()

# Configuraciones y credenciales del Estado
BCN_API_KEY: str = os.getenv("BCN_API_KEY", "")
CNE_EMAIL: str = os.getenv("CNE_EMAIL", "")
CNE_PASSWORD: str = os.getenv("CNE_PASSWORD", "")
PORT: int = int(os.getenv("PORT", "8000"))

# Proveedores de Inteligencia Artificial (BYOK - Bring Your Own Key)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Verificación de credenciales
def check_configuration() -> dict:
    """Verifica el estado de las credenciales configuradas."""
    return {
        "BCN_CONFIGURED": bool(BCN_API_KEY and BCN_API_KEY != "tu_api_key_de_bcn_aqui"),
        "CNE_CONFIGURED": bool(CNE_EMAIL and CNE_PASSWORD and CNE_EMAIL != "tu_correo@ejemplo.cl"),
        "AI_PROVIDERS": {
            "anthropic": bool(ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("tu_")),
            "gemini": bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("tu_")),
            "deepseek": bool(DEEPSEEK_API_KEY and not DEEPSEEK_API_KEY.startswith("tu_")),
            "openai": bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("tu_")),
            "ollama": bool(OLLAMA_HOST)
        }
    }


if __name__ == "__main__":
    status = check_configuration()
    print("\n--- ESTADO DE CONFIGURACIÓN OPEN LEGAL CHILE ---")
    print(f" • BCN Ley Chile API Key: {'✅ Configurada' if status['BCN_CONFIGURED'] else '⚠️ No configurada'}")
    print(f" • CNE Energía Abierta:  {'✅ Configurada' if status['CNE_CONFIGURED'] else '⚠️ No configurada'}")
    print(f" • IA DeepSeek:          {'✅ Configurada' if status['AI_PROVIDERS']['deepseek'] else '⚠️ No configurada'}")
    print(f" • IA Anthropic Claude:  {'✅ Configurada' if status['AI_PROVIDERS']['anthropic'] else '⚠️ No configurada'}")
    print(f" • IA Google Gemini:     {'✅ Configurada' if status['AI_PROVIDERS']['gemini'] else '⚠️ No configurada'}")
    print(f" • IA OpenAI / GPT:      {'✅ Configurada' if status['AI_PROVIDERS']['openai'] else '⚠️ No configurada'}\n")

