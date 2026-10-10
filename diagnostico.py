"""Diagnóstico real de la suite: mide lo que hay, no lo que debería haber.

El `check` original imprimía doce líneas con ✅ fijos sin mirar nada, así que mentía en cuanto
faltaba el corpus o el OCR. Este módulo mide de verdad y, cuando algo falta, dice el paso exacto
para resolverlo. Regla de la casa: nada de aquí manda a instalar dependencias por terminal — la
instalación del paquete lleva todo.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
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
    # El plugin de Claude Code y la extensión de Gemini pasan el token por entorno (userConfig).
    if any((os.environ.get(v) or "").strip() for v in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")):
        return {"nombre": "hugging_face", "estado": "ok",
                "detalle": "cliente instalado y token presente en el entorno (HF_TOKEN)"}
    return {"nombre": "hugging_face", "estado": "aviso",
            "detalle": "cliente instalado; sin token local (las descargas van anónimas y con menos cuota)",
            "sugerencia": "guarda tu token en ~/.openlegal/hf_token (permisos 600)"}


def _chequeo_mapa() -> Dict[str, Any]:
    """El mapa del corpus de Hugging Face (índice de las ~80 mil fuentes del dataset), sin red.

    Nunca es un error: sin mapa, las herramientas responden con sus fuentes de siempre. Es aviso
    solo si hay una revisión publicada que todavía no se descargó, o si se usa una caché anterior.
    """
    try:
        from mapa_corpus.cliente import obtener_cliente
        cliente = obtener_cliente()
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "mapa_corpus", "estado": "aviso", "detalle": f"no se pudo revisar ({str(exc)[:120]})"}
    if not cliente.habilitado:
        return {"nombre": "mapa_corpus", "estado": "ok", "detalle": "desactivado (OPENLEGAL_MAPA=off)"}
    breve = cliente.estado_breve()
    if breve.get("activo"):
        conteos = breve.get("conteos") or {}
        detalle = (f"listo: fuente {str(breve.get('sha_fuente') or '')[:8]} del "
                   f"{str(breve.get('fecha_fuente') or '')[:10] or 's/f'} · {conteos.get('entradas', '?')} entradas")
        if breve.get("aviso"):
            return {"nombre": "mapa_corpus", "estado": "aviso", "detalle": f"{detalle} — {breve['aviso']}",
                    "sugerencia": "se actualiza solo en segundo plano; para forzarlo, usa la herramienta suite_instalar"}
        return {"nombre": "mapa_corpus", "estado": "ok", "detalle": detalle}
    if not cliente.puntero.get("revision_mapa") and not cliente.local and cliente.modo != "main":
        return {"nombre": "mapa_corpus", "estado": "ok",
                "detalle": "aún no publicado para esta versión: las herramientas usan el corpus de siempre"}
    detalle = "no descargado todavía" + (f" (último error: {breve['error']})" if breve.get("error") else "")
    if breve.get("descargando"):
        detalle = "descargando en segundo plano"
    return {"nombre": "mapa_corpus", "estado": "aviso", "detalle": detalle,
            "sugerencia": "se descarga solo al iniciar el servidor; para forzarlo, usa la herramienta suite_instalar"}


def _chequeo_recursos() -> Dict[str, Any]:
    """Skills, agentes y protocolo de citación: en el repo o instalados en share/openlegal-chile."""
    try:
        from recursos import ruta_recurso
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "recursos", "estado": "error", "detalle": f"no pude cargar recursos.py ({str(exc)[:120]})"}
    skills = list(ruta_recurso(".agents/skills").glob("*/SKILL.md"))
    agentes = list(ruta_recurso("agents").glob("*.json"))
    protocolo = ruta_recurso("AGENTS.md").exists()
    detalle = f"{len(skills)} skills · {len(agentes)} agentes · protocolo de citación {'presente' if protocolo else 'ausente'}"
    if skills and agentes and protocolo:
        return {"nombre": "recursos", "estado": "ok", "detalle": detalle}
    return {"nombre": "recursos", "estado": "error", "detalle": detalle,
            "sugerencia": "reinstala el paquete: skills, agentes y AGENTS.md viajan en share/openlegal-chile"}


def _chequeo_entorno() -> Dict[str, Any]:
    """Programas externos opcionales: informa qué hay, no degrada el estado."""
    partes = []
    partes.append("uvx " + ("presente" if shutil.which("uvx") else "ausente (lo usan el plugin de Claude Code y la "
                                                                    "extensión de Gemini para lanzar el MCP)"))
    poppler = [b for b in ("pdftotext", "pdfinfo", "pdftoppm") if shutil.which(b)]
    partes.append("poppler " + ("presente" if len(poppler) == 3 else
                                "ausente (solo lo usan las ingestas masivas de PDF; el OCR usa PyMuPDF y RapidOCR)"))
    nlm = shutil.which("nlm") or (pathlib.Path.home() / ".local" / "bin" / "nlm").exists()
    partes.append("nlm " + ("presente" if nlm else "ausente (solo para las herramientas notebooklm_*)"))
    return {"nombre": "entorno", "estado": "ok", "detalle": " · ".join(partes)}


def _chequeo_harness() -> Dict[str, Any]:
    """Qué harness de esta carpeta ya tienen configurado el servidor (informativo)."""
    try:
        import integraciones_harness as ih
    except Exception as exc:  # noqa: BLE001
        return {"nombre": "harness", "estado": "ok", "detalle": f"no se pudo revisar ({str(exc)[:80]})"}
    base = pathlib.Path.cwd()
    configurados = []
    for cliente, ruta in ih._RUTA_PROYECTO.items():
        archivo = base / ruta
        try:
            if archivo.is_file() and ih.SERVIDOR in archivo.read_text(encoding="utf-8", errors="ignore"):
                configurados.append(f"{cliente} ({ruta})")
        except OSError:
            continue
    if configurados:
        return {"nombre": "harness", "estado": "ok", "detalle": "configurado en esta carpeta: " + ", ".join(configurados)}
    return {"nombre": "harness", "estado": "ok",
            "detalle": "sin configuración MCP en esta carpeta (plugin, configuración global o `openlegal integrar`)"}


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
        _chequeo_recursos(),
        _chequeo_hugging_face(),
        _chequeo_mapa(),
        _chequeo_entorno(),
        _chequeo_harness(),
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
