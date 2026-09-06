"""
Open Legal Chile — Sistema de Notificación y Comprobación de Actualizaciones
Comprueba en segundo plano si existe una versión más reciente de la Suite en PyPI o GitHub,
muestra un banner informativo amigable para terminal y agentes de IA,
y proporciona el mecanismo de auto-actualización automática.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
from typing import Dict, Any, Optional, Tuple

CURRENT_VERSION = "1.3.0"
PYPI_URL = "https://pypi.org/pypi/openlegal-chile/json"
GITHUB_RELEASES_URL = "https://api.github.com/repos/elpabloultron/open-legal-chile/releases/latest"
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".update_cache.json")
CACHE_TTL_SECONDS = 86400  # 24 horas


def _parse_version_tuple(v_str: str) -> Tuple[int, ...]:
    """Convierte un string de versión '1.3.0' en una tupla de enteros (1, 3, 0) para comparación segura."""
    try:
        clean = v_str.strip().lstrip("v")
        res = tuple(int(x) for x in clean.split(".") if x.isdigit())
        return res if res else (0, 0, 0)
    except Exception:
        return (0, 0, 0)


def check_for_updates(force: bool = False, timeout: float = 2.0) -> Dict[str, Any]:
    """
    Comprueba si existe una versión más reciente en PyPI o GitHub.
    Usa caché local de 24 horas para no ralentizar el inicio del CLI ni de los agentes.
    """
    now = time.time()

    # Verificar caché salvo que se fuerce
    if not force and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if now - cached.get("timestamp", 0) < CACHE_TTL_SECONDS:
                    return cached.get("data", {
                        "actualizado": True,
                        "version_actual": CURRENT_VERSION,
                        "version_disponible": CURRENT_VERSION,
                        "hay_actualizacion": False
                    })
        except Exception:
            pass

    latest_version = CURRENT_VERSION
    release_notes = ""
    source = "pypi"

    try:
        req = urllib.request.Request(PYPI_URL, headers={"User-Agent": "OpenLegalChile-UpdateChecker"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            info = data.get("info", {})
            latest_version = info.get("version", CURRENT_VERSION)
            release_notes = info.get("summary", "")
    except Exception:
        # Fallback a GitHub Releases
        try:
            req_gh = urllib.request.Request(
                GITHUB_RELEASES_URL,
                headers={"User-Agent": "OpenLegalChile-UpdateChecker", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req_gh, timeout=timeout) as resp_gh:
                data_gh = json.loads(resp_gh.read().decode("utf-8"))
                latest_version = data_gh.get("tag_name", CURRENT_VERSION).lstrip("v")
                release_notes = data_gh.get("name", "")
                source = "github"
        except Exception:
            pass

    curr_tuple = _parse_version_tuple(CURRENT_VERSION)
    latest_tuple = _parse_version_tuple(latest_version)

    hay_actualizacion = latest_tuple > curr_tuple

    res = {
        "version_actual": CURRENT_VERSION,
        "version_disponible": latest_version,
        "hay_actualizacion": hay_actualizacion,
        "fuente": source,
        "notas": release_notes,
        "comando_pip": f"pip install --upgrade openlegal-chile",
        "comando_git": "git pull && pip install -e .",
        "instruccion_ia": "Actualiza la suite Open Legal Chile a la última versión disponible"
    }

    # Guardar en caché
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": now, "data": res}, f)
    except Exception:
        pass

    return res


def format_update_banner(info: Dict[str, Any]) -> Optional[str]:
    """Genera un banner estilizado si existe una versión más reciente."""
    if not info.get("hay_actualizacion"):
        return None

    curr = info.get("version_actual", CURRENT_VERSION)
    disp = info.get("version_disponible", CURRENT_VERSION)

    banner = f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔔 NUEVA VERSIÓN DISPONIBLE: Open Legal Chile Suite v{disp:<10}          │
│    (Versión instalada actualmente: v{curr})                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 👉 Para actualizar en tu terminal ejecuta:                                  │
│    pip install --upgrade openlegal-chile                                    │
│                                                                             │
│ 🤖 O pídele a tu Agente de IA:                                              │
│    "Actualiza la suite Open Legal Chile a la última versión"                │
│                                                                             │
│ ⚡ O ejecuta en la consola:                                                 │
│    openlegal update                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
"""
    return banner.strip()


def run_auto_update() -> Dict[str, Any]:
    """
    Ejecuta la actualización de la suite de manera automática y segura.
    Detecta si el entorno es un repositorio git local o un paquete instalado vía pip.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    is_git_repo = os.path.exists(os.path.join(repo_dir, ".git"))

    python_bin = sys.executable or "python3"

    resultado = {
        "exito": False,
        "metodo": "git" if is_git_repo else "pip",
        "version_previa": CURRENT_VERSION,
        "salida": "",
        "mensaje": ""
    }

    if is_git_repo:
        try:
            cmd_pull = ["git", "-C", repo_dir, "pull", "origin", "main"]
            p1 = subprocess.run(cmd_pull, capture_output=True, text=True, timeout=30)
            cmd_install = [python_bin, "-m", "pip", "install", "-e", repo_dir]
            p2 = subprocess.run(cmd_install, capture_output=True, text=True, timeout=60)

            resultado["salida"] = p1.stdout + "\n" + p2.stdout
            if p1.returncode == 0 and p2.returncode == 0:
                resultado["exito"] = True
                resultado["mensaje"] = "Repositorio local actualizado exitosamente vía git pull y pip install -e ."
            else:
                resultado["mensaje"] = f"Error durante la actualización: {p1.stderr or p2.stderr}"
        except Exception as e:
            resultado["mensaje"] = f"Excepción durante auto-actualización git: {str(e)}"
    else:
        try:
            cmd_upgrade = [python_bin, "-m", "pip", "install", "--upgrade", "openlegal-chile"]
            p = subprocess.run(cmd_upgrade, capture_output=True, text=True, timeout=60)
            resultado["salida"] = p.stdout
            if p.returncode == 0:
                resultado["exito"] = True
                resultado["mensaje"] = "Paquete openlegal-chile actualizado exitosamente vía pip."
            else:
                resultado["mensaje"] = f"Error durante pip install --upgrade: {p.stderr}"
        except Exception as e:
            resultado["mensaje"] = f"Excepción durante auto-actualización pip: {str(e)}"

    # Limpiar caché de actualización
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass

    return resultado
