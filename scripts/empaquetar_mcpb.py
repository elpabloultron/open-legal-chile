"""Validador y empaquetador de extensión `.mcpb` (Desktop Extension 1-clic) para Open Legal Chile."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import zipfile
from typing import Any, Dict, List, Optional

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MANIFEST_PATH = RAIZ / "mcpb" / "manifest.json"
ARCHIVOS_BUNDLE = ("assets/logo.svg", "README.md", "LICENSE")


def _leer_version_pyproject() -> str:
    txt = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    for linea in txt.splitlines():
        if linea.strip().startswith("version"):
            return linea.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def validar_manifiesto_mcpb(manifest_path: Optional[pathlib.Path] = None) -> List[str]:
    """Valida estructura SEP/MCPB 0.3, coherencia de versión y archivos incluidos."""
    ruta = manifest_path or MANIFEST_PATH
    errores: List[str] = []
    if not ruta.exists():
        return [f"Falta manifiesto MCPB: {ruta}"]

    try:
        data: Dict[str, Any] = json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError as err:
        return [f"JSON inválido en {ruta}: {err}"]

    for campo in ("manifest_version", "name", "version", "description", "author", "server"):
        if not data.get(campo):
            errores.append(f"Campo obligatorio ausente: '{campo}'")

    if str(data.get("manifest_version")) not in ("0.3", "0.4"):
        errores.append(f"manifest_version no soportada: {data.get('manifest_version')}")

    srv = data.get("server") or {}
    mcp_cfg = srv.get("mcp_config") or {}
    if not srv.get("type") or not mcp_cfg.get("command") or not isinstance(mcp_cfg.get("args"), list):
        errores.append("server.type, server.mcp_config.command y server.mcp_config.args son obligatorios")

    ver_py = _leer_version_pyproject()
    ver_m = str(data.get("version") or "")
    if ver_py and ver_m != ver_py:
        errores.append(f"Versión en mcpb/manifest.json ({ver_m}) difiere de pyproject.toml ({ver_py})")

    args_str = " ".join(str(a) for a in (mcp_cfg.get("args") or []))
    if ver_py and f"openlegal-chile=={ver_py}" not in args_str:
        errores.append(f"server.mcp_config.args no apunta a openlegal-chile=={ver_py}")

    for rel in ARCHIVOS_BUNDLE:
        if not (RAIZ / rel).exists():
            errores.append(f"Falta archivo de soporte del bundle: {rel}")

    return errores


def construir_mcpb(out_path: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Empaqueta un archivo `.mcpb` determinista y válido tras validar el manifiesto."""
    errores = validar_manifiesto_mcpb()
    if errores:
        raise ValueError("; ".join(errores))

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    destino = out_path or (RAIZ / "dist" / f"open-legal-chile-{data['version']}.mcpb")
    destino.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(MANIFEST_PATH, arcname="manifest.json")
        for rel in ARCHIVOS_BUNDLE:
            zf.write(RAIZ / rel, arcname=rel)
    return destino


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Empaquetador y validador MCPB para Open Legal Chile.")
    parser.add_argument("--check", action="store_true", help="Solo valida mcpb/manifest.json sin generar archivo")
    parser.add_argument("--out", default="", help="Ruta de salida para el archivo .mcpb")
    args = parser.parse_args(argv)

    errores = validar_manifiesto_mcpb()
    if errores:
        for e in errores:
            sys.stderr.write(f"ERROR MCPB: {e}\n")
        return 1

    if args.check:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        print(f"MCPB OK: open-legal-chile {data['version']}")
        return 0

    out_p = pathlib.Path(args.out) if args.out else None
    bundle = construir_mcpb(out_p)
    print(f"MCPB generado: {bundle} ({bundle.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
