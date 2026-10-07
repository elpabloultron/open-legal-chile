"""La publicación alcanza al registro oficial de MCP, sin poner en riesgo la de PyPI.

Medido el 07-10-2026: registry.modelcontextprotocol.io listaba io.github.elpabloultron/open-legal-chile
en 1.5.1 («55 herramientas», 13-09-2026) con PyPI ya en 1.13.0. publish-pypi.yml subía el paquete y
creaba el release, pero nunca mandaba server.json. El registro verifica la propiedad en PyPI buscando
`mcp-name: <nombre>` en la descripción del paquete (el README) y concede io.github.<dueño>/* por OIDC.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SERVER = json.loads((RAIZ / "server.json").read_text(encoding="utf-8"))
WORKFLOW = RAIZ / ".github" / "workflows" / "publish-pypi.yml"


def _workflow():
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_server_json_cumple_las_restricciones_del_schema():
    # Del schema 2025-12-11 (static.modelcontextprotocol.io): name con patrón y descripción ≤ 100.
    assert SERVER["$schema"].endswith("/2025-12-11/server.schema.json")
    assert re.fullmatch(r"[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+", SERVER["name"])
    assert SERVER["name"].startswith("io.github.elpabloultron/"), "OIDC solo concede io.github.<dueño>/*"
    assert 1 <= len(SERVER["description"]) <= 100, len(SERVER["description"])
    assert not re.search(r"[\^~<>*]|\bx\b| - |\|\|", SERVER["version"]), "el registro prohíbe rangos"
    paquete = SERVER["packages"][0]
    assert paquete["registryType"] == "pypi" and paquete["identifier"] == "openlegal-chile"
    assert paquete["transport"] == {"type": "stdio"}


def test_el_readme_lleva_la_marca_de_propiedad_que_lee_el_registro():
    tomllib = pytest.importorskip("tomllib", reason="requiere Python 3.11+")
    proyecto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    readme = (RAIZ / proyecto["readme"]).read_text(encoding="utf-8")
    # El token debe cerrar en un límite (espacio, salto o `-->`): pegado a un punto no lo reconoce.
    assert re.search(rf"mcp-name: {re.escape(SERVER['name'])}(\s|-->)", readme)


def test_el_registro_va_en_un_job_aparte_que_no_frena_pypi():
    jobs = _workflow()["jobs"]
    registro = jobs["publish-mcp-registry"]
    assert set(registro["needs"]) == {"detect-version", "build-and-publish"}
    assert registro["continue-on-error"] is True
    assert "!cancelled()" in registro["if"] and "build-and-publish.result != 'failure'" in registro["if"]
    assert registro["permissions"] == {"contents": "read", "id-token": "write"}
    pasos = "\n".join(s.get("run", "") for s in registro["steps"])
    assert "mcp-publisher login github-oidc" in pasos
    assert "mcp-publisher publish server.json" in pasos
    assert "sha256sum --check" in pasos, "el binario se verifica contra el checksums del release"
    assert "secrets." not in json.dumps(registro), "OIDC: el job no necesita secretos"
    assert "mcp-publisher" not in json.dumps(jobs["build-and-publish"]), "PyPI no depende del registro"


def test_el_registro_se_pone_al_dia_aunque_pypi_ya_tenga_la_version():
    detectar = _workflow()["jobs"]["detect-version"]
    assert "registry_publish" in detectar["outputs"]
    paso = next(s for s in detectar["steps"] if s.get("id") == "registro")
    assert "registry.modelcontextprotocol.io/v0.1/servers/" in paso["run"]
    assert '"$CODIGO" = "404"' in paso["run"], "solo un 404 cuenta como versión faltante"
