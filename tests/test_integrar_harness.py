"""Cada harness recibe su configuración MCP sin editar archivos a mano.

El reclamo era «me da un terminal para usar las herramientas y todo por fuera del harness». Acá la
integración se resuelve por el producto: un comando por cliente, con respaldo y sin pisar los
servidores que la persona ya tenga configurados.
"""

import json
import pathlib
import subprocess
import sys

import integraciones_harness as ih

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_configuracion_claude_code_es_json_valido():
    cfg = ih.configuracion("claude-code")

    assert cfg["ruta"] == ".mcp.json"
    datos = json.loads(cfg["contenido"])
    assert datos["mcpServers"]["open-legal-chile"]["command"] == "openlegal-mcp"


def test_configuracion_vscode_usa_la_clave_servers():
    datos = json.loads(ih.configuracion("vscode")["contenido"])

    assert "servers" in datos
    assert datos["servers"]["open-legal-chile"]["type"] == "stdio"


def test_configuracion_antigravity_reusa_el_formato_mcpservers():
    datos = json.loads(ih.configuracion("antigravity")["contenido"])

    assert datos["mcpServers"]["open-legal-chile"]["command"] == "openlegal-mcp"


def test_configuracion_codex_es_toml_de_mcp_servers():
    cfg = ih.configuracion("codex")

    assert cfg["ruta"].endswith(".toml")
    assert "[mcp_servers.open-legal-chile]" in cfg["contenido"]


def test_configuracion_dsh_es_un_parche_cordis():
    cfg = ih.configuracion("dsh")

    assert cfg["ruta"] == "cordis.patch.yml"
    assert "dsh-mcp-client" in cfg["contenido"]
    assert "open_legal_chile" in cfg["contenido"]


def test_clientes_disponibles():
    assert {"claude-code", "cursor", "vscode", "antigravity", "codex", "dsh", "generic"} <= set(ih.clientes())


def test_cliente_desconocido_lo_dice():
    try:
        ih.configuracion("emacs")
    except ValueError as exc:
        assert "emacs" in str(exc) and "cursor" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("un cliente desconocido no puede pasar en silencio")


def test_escribir_respalda_y_conserva_los_servidores_previos(tmp_path):
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"viejo": {"command": "x"}}}', encoding="utf-8")

    resultado = ih.escribir("claude-code", carpeta_base=tmp_path)

    datos = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert datos["mcpServers"]["viejo"] == {"command": "x"}, "no puede borrar lo que ya estaba"
    assert datos["mcpServers"]["open-legal-chile"]["command"] == "openlegal-mcp"
    respaldo = (tmp_path / ".mcp.json.bak").read_text(encoding="utf-8")
    assert "viejo" in respaldo
    assert resultado["estado"] == "fusionado"
    assert resultado["respaldo"].endswith(".bak")


def test_escribir_es_idempotente(tmp_path):
    ih.escribir("claude-code", carpeta_base=tmp_path)

    segunda = ih.escribir("claude-code", carpeta_base=tmp_path)

    assert segunda["estado"] == "ya_configurado"
    datos = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert list(datos["mcpServers"]) == ["open-legal-chile"]


def test_escribir_dsh_fusiona_el_parche_sin_pisar(tmp_path):
    (tmp_path / "cordis.patch.yml").write_text("- insert:\n    - id: otro-plugin\n", encoding="utf-8")

    ih.escribir("dsh", carpeta_base=tmp_path)

    texto = (tmp_path / "cordis.patch.yml").read_text(encoding="utf-8")
    assert "otro-plugin" in texto, "el parche Cordis se fusiona, no se pisa"
    assert "dsh-mcp-client" in texto


def test_la_cli_lista_clientes_e_integra(tmp_path):
    listado = subprocess.run([sys.executable, str(RAIZ / "openlegal.py"), "integrar"],
                             capture_output=True, text=True, cwd=str(tmp_path))
    assert "claude-code" in listado.stdout and "dsh" in listado.stdout

    escrito = subprocess.run([sys.executable, str(RAIZ / "openlegal.py"), "integrar", "claude-code", "--escribir"],
                             capture_output=True, text=True, cwd=str(tmp_path))
    assert (tmp_path / ".mcp.json").exists(), escrito.stdout + escrito.stderr
    assert "open-legal-chile" in (tmp_path / ".mcp.json").read_text(encoding="utf-8")


def test_detectar_instalados_reconoce_las_carpetas_de_cada_harness(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".dsh").mkdir()

    detectados = ih.detectar_instalados(tmp_path)

    assert {"claude-code", "cursor", "dsh"} <= set(detectados)
    assert "codex" not in detectados


def test_la_cli_integra_todos_los_detectados(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".vscode").mkdir()

    corrida = subprocess.run([sys.executable, str(RAIZ / "openlegal.py"), "integrar", "--todos", "--escribir"],
                             capture_output=True, text=True, cwd=str(tmp_path))

    assert (tmp_path / ".mcp.json").exists(), corrida.stdout + corrida.stderr
    assert (tmp_path / ".vscode" / "mcp.json").exists(), corrida.stdout + corrida.stderr
    assert "claude-code" in corrida.stdout and "vscode" in corrida.stdout


def test_todos_cae_al_home_cuando_el_directorio_no_tiene_pistas(tmp_path, monkeypatch):
    falso_home = tmp_path / "casa"
    (falso_home / ".dsh").mkdir(parents=True)
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: falso_home))
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()

    resultados = ih.escribir_todos(carpeta_base=proyecto)

    assert [r["cliente"] for r in resultados] == ["dsh"]
    assert (falso_home / "cordis.patch.yml").exists(), "la configuración global va a la casa"
