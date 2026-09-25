"""
Open Legal Chile — Bridge de Integración para Promptfoo E2E (Nivel 2)
Conecta el framework de evaluación Promptfoo directamente con LegalChatEngine.
"""

import os
import sys
from typing import Dict, Any, Optional

# Asegurar que la raíz del repositorio esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from chat_engine import LegalChatEngine

_engine = LegalChatEngine()


def call_api(prompt: str, options: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Punto de entrada invocado por el runner de Promptfoo."""
    try:
        resp = _engine.chat(user_message=prompt)
        return {
            "output": resp.get("reply", ""),
        }
    except Exception as e:
        return {
            "error": str(e),
        }
