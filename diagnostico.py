"""Diagnóstico real de la suite: mide lo que hay, no lo que debería haber.

El `check` original imprimía doce líneas con ✅ fijos sin mirar nada, así que mentía en cuanto
faltaba el corpus o el OCR. Este módulo mide de verdad y, cuando algo falta, dice el paso exacto
para resolverlo. Regla de la casa: nada de aquí manda a instalar dependencias por terminal — la
instalación del paquete lleva todo.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List

BASE_DIR = pathlib.Path(__file__).resolve().parent

ESTADOS = ("ok", "aviso", "error", "omitido")


def _version_instalada() -> str:
    """La versión que el usuario tiene delante: primero la del paquete instalado con pip.

    El wheel no lleva pyproject.toml, así que leerlo desde BASE_DIR solo sirve en el repo; en una
    instalación normal tiene que salir de los metadatos del paquete.
    """
    try:
        from importlib.metadata import version as version_paquete

        return version_paquete("openlegal-chile")
    except Exception:  # noqa: BLE001 - sin metadatos seguimos con las otras fuentes
        pass
    try:
        import tomllib

        datos = tomllib.loads((BASE_DIR / "pyproject.toml").read_text(encoding="utf-8"))
        return datos["project"]["version"]
    except Exception:  # noqa: BLE001
        pass
    try:
        from update_checker import CURRENT_VERSION

        return CURRENT_VERSION
    except Exception:  # noqa: BLE001
        return "desconocida"


def _chequeo_version() -> Dict[str, Any]:
    return {"nombre": "version", "estado": "ok", "detalle": f"openlegal-chile {_version_instalada()}"}


def _chequeo_ocr() -> Dict[str, Any]:
    try:
        from forensic_ocr import ForensicOCREngine
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "ocr", "estado": "error",
                "detalle": f"no pude cargar el motor de OCR ({str(exc)[:120]})",
                "sugerencia": "reinstala el paquete: el OCR viaja en la instalación"}

    motor = ForensicOCREngine()
    motores = motor.get_available_engines()
    estado = "ok"
    detalle = f"motores: {', '.join(motores)}"
    if "rapidocr" not in motores:
        estado = "aviso"
        detalle += " · falta RapidOCR (el motor robusto para fotos, incluido en la instalación)"
    try:
        idiomas = motor.get_available_languages() or []
    except Exception:  # noqa: BLE001
        idiomas = []
    if idiomas:
        detalle += f" · idiomas: {', '.join(idiomas)}"
    if "spa" not in idiomas:
        # El español puede vivir fuera del TESSDATA del sistema (típico en Linux:
        # ~/.local/share/tessdata), y ahí se usa exportando TESSDATA_PREFIX.
        alterno = pathlib.Path.home() / ".local/share/tessdata" / "spa.traineddata"
        if alterno.exists():
            detalle += " · 'spa' presente en ~/.local/share/tessdata (se activa con TESSDATA_PREFIX)"
        else:
            estado = "aviso"
            detalle += " (sin 'spa' el OCR pierde las palabras acentuadas)"
    return {"nombre": "ocr", "estado": estado, "detalle": detalle}


def _chequeo_corpus() -> Dict[str, Any]:
    obras = list((BASE_DIR / "doctrina").rglob("*.md"))
    if not obras:
        return {"nombre": "corpus", "estado": "error",
                "detalle": "no encontré obras doctrinales empaquetadas",
                "sugerencia": "reinstala el paquete (lleva el corpus) o copia las obras en doctrina/"}
    return {"nombre": "corpus", "estado": "ok",
            "detalle": f"{len(obras)} obras doctrinales empaquetadas"}


def _chequeo_grafo() -> Dict[str, Any]:
    ruta = BASE_DIR / "data" / "legal_knowledge_graph.json"
    if not ruta.exists():
        return {"nombre": "grafo", "estado": "error",
                "detalle": "falta data/legal_knowledge_graph.json",
                "sugerencia": "reinstala el paquete o baja el grafo del dataset de Hugging Face"}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "grafo", "estado": "error",
                "detalle": f"el grafo no se pudo leer ({str(exc)[:120]})"}
    nodos = len(datos.get("nodes", []))
    aristas = len(datos.get("edges", []))
    return {"nombre": "grafo", "estado": "ok" if nodos else "error",
            "detalle": f"{nodos} nodos · {aristas} aristas"}


def _chequeo_indices() -> Dict[str, Any]:
    db = BASE_DIR / "doctrina.db"
    if not db.exists():
        # Normal en una instalación nueva: el índice se arma solo en la primera búsqueda. No es
        # una falla, así que no degrada el estado (antes el doctor gritaba «degradado» al instalar).
        return {"nombre": "indices", "estado": "ok",
                "detalle": "el índice FTS de doctrina se construye en la primera búsqueda"}
    try:
        import sqlite3

        conn = sqlite3.connect(str(db))
        filas = conn.execute("SELECT COUNT(*) FROM doctrina_instituciones").fetchone()[0]
        conn.close()
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "indices", "estado": "aviso",
                "detalle": f"el índice existe pero no se pudo contar ({str(exc)[:100]})"}
    return {"nombre": "indices", "estado": "ok" if filas else "aviso",
            "detalle": f"{filas} fichas indexadas para búsqueda FTS"}


def _chequeo_citas() -> Dict[str, Any]:
    formulada = "[BCN - Código Civil, Art. 1438]"
    try:
        from citas_legales import detectar_normas, formatear_cita

        cita = formatear_cita("BCN", "Código Civil, Art. 1438", url="https://www.bcn.cl/x", texto="Contrato…")
        detectadas = detectar_normas("según el artículo 1438 del Código Civil")
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "citas", "estado": "error",
                "detalle": f"el formateador de citas falló ({str(exc)[:120]})"}
    ok = cita["formato"] == formulada and detectadas
    return {"nombre": "citas", "estado": "ok" if ok else "error",
            "detalle": f"corchete oficial {cita['formato']} · detector de normas {'activo' if detectadas else 'caído'}"}


def _chequeo_herramientas_mcp() -> Dict[str, Any]:
    try:
        import mcp_server

        nombres = [t["name"] for t in mcp_server.TOOLS]
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "herramientas_mcp", "estado": "error",
                "detalle": f"el servidor MCP no se pudo importar ({str(exc)[:120]})"}
    minimas = ("consulta_maestra", "cita_texto", "huggingface_search_dataset")
    faltan = [n for n in minimas if n not in nombres]
    if faltan:
        return {"nombre": "herramientas_mcp", "estado": "error",
                "detalle": f"{len(nombres)} herramientas · faltan {', '.join(faltan)}"}
    return {"nombre": "herramientas_mcp", "estado": "ok",
            "detalle": f"{len(nombres)} herramientas, con consulta_maestra (paso 0) y cita_texto"}


def _chequeo_hugging_face() -> Dict[str, Any]:
    token = pathlib.Path.home() / ".openlegal" / "hf_token"
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        return {"nombre": "hugging_face", "estado": "error",
                "detalle": "huggingface-hub no está importable en este entorno",
                "sugerencia": "reinstala el paquete: es dependencia base"}
    if token.exists():
        return {"nombre": "hugging_face", "estado": "ok",
                "detalle": "cliente instalado y token local presente"}
    return {"nombre": "hugging_face", "estado": "aviso",
            "detalle": "cliente instalado; sin token local (las descargas van anónimas y con menos cuota)",
            "sugerencia": "guarda tu token en ~/.openlegal/hf_token (permisos 600)"}


def diagnostico_completo() -> Dict[str, Any]:
    """Corre los chequeos locales (sin red) y resume el estado de la suite."""
    chequeos: List[Dict[str, Any]] = [
        _chequeo_version(),
        _chequeo_ocr(),
        _chequeo_corpus(),
        _chequeo_grafo(),
        _chequeo_indices(),
        _chequeo_citas(),
        _chequeo_herramientas_mcp(),
        _chequeo_hugging_face(),
    ]
    if any(c["estado"] == "error" for c in chequeos):
        estado = "error"
    elif any(c["estado"] == "aviso" for c in chequeos):
        estado = "degradado"
    else:
        estado = "ok"
    return {"estado": estado, "chequeos": chequeos}


if __name__ == "__main__":  # pragma: no cover
    resumen = diagnostico_completo()
    iconos = {"ok": "✅", "aviso": "⚠️", "error": "❌", "omitido": "⚪"}
    print(f"Doctor de Open Legal Chile — estado: {resumen['estado'].upper()}")
    for chequeo in resumen["chequeos"]:
        print(f" {iconos.get(chequeo['estado'], '•')} {chequeo['nombre']:<18} {chequeo['detalle']}")
        if chequeo.get("sugerencia"):
            print(f"    ↳ {chequeo['sugerencia']}")
