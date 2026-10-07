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


def _es_openlegal_mcp(comando: str) -> bool:
    """El comando es openlegal-mcp, a secas o con su ruta absoluta (las apps de escritorio no
    heredan el PATH de la terminal, por eso se escribe la ruta completa cuando se conoce)."""
    return pathlib.Path(comando).name in ("openlegal-mcp", "openlegal-mcp.exe")


def _correr_cli(*argumentos: str, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    """Corre la CLI como la corre el usuario, leyendo su salida en UTF-8.

    En Windows el pipe decodifica con cp1252 por defecto: el banner (⚖️, tildes) mata al hilo lector,
    `stdout` queda en None y la prueba falla con un TypeError que no dice nada
    («argument of type 'NoneType' is not iterable»). La codificación se declara acá, igual que en el
    punto de entrada del producto (openlegal.py reconfigura su stdout a UTF-8).
    """
    return subprocess.run(
        [sys.executable, str(RAIZ / "openlegal.py"), *argumentos],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd),
    )


def test_configuracion_claude_code_es_json_valido():
    cfg = ih.configuracion("claude-code")

    assert cfg["ruta"] == ".mcp.json"
    datos = json.loads(cfg["contenido"])
    assert _es_openlegal_mcp(datos["mcpServers"]["open-legal-chile"]["command"])


def test_configuracion_vscode_usa_la_clave_servers():
    datos = json.loads(ih.configuracion("vscode")["contenido"])

    assert "servers" in datos
    assert datos["servers"]["open-legal-chile"]["type"] == "stdio"


def test_configuracion_antigravity_reusa_el_formato_mcpservers():
    datos = json.loads(ih.configuracion("antigravity")["contenido"])

    assert _es_openlegal_mcp(datos["mcpServers"]["open-legal-chile"]["command"])


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
    assert {"claude-code", "claude-desktop", "cursor", "vscode", "gemini", "antigravity", "windsurf", "codex",
            "opencode", "dsh", "generic"} <= set(ih.clientes())


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
    assert _es_openlegal_mcp(datos["mcpServers"]["open-legal-chile"]["command"])
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
    listado = _correr_cli("integrar", cwd=tmp_path)
    assert "claude-code" in listado.stdout and "dsh" in listado.stdout

    escrito = _correr_cli("integrar", "claude-code", "--escribir", cwd=tmp_path)
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

    corrida = _correr_cli("integrar", "--todos", "--escribir", cwd=tmp_path)

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


def test_configuracion_gemini_cli_usa_settings_json():
    cfg = ih.configuracion("gemini")
    assert cfg["ruta"] == ".gemini/settings.json"
    assert _es_openlegal_mcp(json.loads(cfg["contenido"])["mcpServers"]["open-legal-chile"]["command"])


def test_configuracion_opencode_usa_la_clave_mcp_con_comando_en_lista():
    datos = json.loads(ih.configuracion("opencode")["contenido"])
    servidor = datos["mcp"]["open-legal-chile"]
    assert servidor["type"] == "local" and servidor["enabled"] is True
    assert isinstance(servidor["command"], list) and _es_openlegal_mcp(servidor["command"][0])


def test_claude_desktop_y_windsurf_son_globales():
    for cliente, final in (("claude-desktop", "claude_desktop_config.json"), ("windsurf", "mcp_config.json")):
        ruta = pathlib.Path(ih.configuracion(cliente)["ruta"])
        assert ruta.is_absolute() and ruta.name == final, ruta


def test_vscode_global_va_a_la_carpeta_de_usuario_de_code():
    ruta = pathlib.Path(ih.configuracion("vscode", global_=True)["ruta"])
    assert ruta.parts[-3:] == ("Code", "User", "mcp.json"), ruta


def test_modo_uvx_no_requiere_el_paquete_instalado():
    servidor = json.loads(ih.configuracion("cursor", uvx=True)["contenido"])["mcpServers"]["open-legal-chile"]
    assert servidor["command"] == "uvx"
    assert servidor["args"][0] == "--from" and servidor["args"][1].startswith("openlegal-chile")
    assert servidor["args"][-1] == "openlegal-mcp"


def test_codex_toml_escapa_rutas_de_windows():
    tomllib = __import__("pytest").importorskip("tomllib")
    original = ih.comando_servidor
    try:
        ih.comando_servidor = lambda: r"C:\Users\Ana\venv\Scripts\openlegal-mcp.exe"
        datos = tomllib.loads(ih.configuracion("codex")["contenido"])
    finally:
        ih.comando_servidor = original
    servidor = datos["mcp_servers"]["open-legal-chile"]
    assert servidor["command"].endswith("openlegal-mcp.exe") and servidor["env"]["PYTHONUNBUFFERED"] == "1"


def test_alias_de_clientes():
    assert ih.configuracion("gemini-cli")["cliente"] == "gemini"
    assert ih.configuracion("claude")["cliente"] == "claude-code"


def test_claude_code_global_se_registra_con_el_cli(tmp_path, monkeypatch):
    """El alcance de usuario de Claude Code vive en ~/.claude.json: se registra con `claude mcp add -s user`."""
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(ih.shutil, "which", lambda nombre: None if nombre == "claude" else None)
    resultado = ih.escribir("claude-code", carpeta_base=tmp_path)
    assert resultado["estado"] == "manual"
    assert "claude mcp add -s user" in resultado["nota"]
    assert not (tmp_path / ".mcp.json").exists(), "~/.mcp.json no es el alcance de usuario de Claude Code"
