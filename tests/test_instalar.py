"""`openlegal instalar`: un solo comando deja el harness configurado y verificado."""
import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _cli(*args, cwd):
    return subprocess.run([sys.executable, str(RAIZ / "openlegal.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd))


def test_instalar_escribe_la_config_del_harness_detectado(tmp_path):
    (tmp_path / ".claude").mkdir()
    corrida = _cli("instalar", "--json", cwd=tmp_path)
    datos = json.loads(corrida.stdout[corrida.stdout.index("{"):])
    assert datos["harnesses"] == ["claude-code"]
    assert (tmp_path / ".mcp.json").exists()
    assert datos["doctor"]["estado"] in ("ok", "degradado")
    assert datos["verificacion"].startswith("openlegal doctor")


def test_instalar_sin_harness_lo_dice_y_no_falla(tmp_path):
    corrida = _cli("instalar", "--json", cwd=tmp_path)
    assert corrida.returncode == 0
    assert "no se detectó ningún harness" in corrida.stdout.lower()
