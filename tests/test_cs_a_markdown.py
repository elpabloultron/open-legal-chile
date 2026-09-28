"""Candado del conversor de fichas de la Corte Suprema a Markdown.

Regla del producto: la ficha trae metadatos y enlace oficial; los campos ausentes se
escriben como «—» y **nunca** se inventa texto que la fuente no traiga.
"""
import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _ficha_base() -> dict:
    return {
        "tribunal": "Corte Suprema", "sala": "SEGUNDA, PENAL", "rol": "50838-2026", "era": 2026,
        "fecha": "2026-09-24", "recurso": "(CRIMEN) APELACIÓN AMPARO", "resultado": "RECHAZADO",
        "caratula": "SERVICIO DE SALUD c/ OTRO", "tribunal_origen": "C.A. DE SANTIAGO",
        "ministros": "A, B", "publicacion": "2026-09-24", "fallo_anonimizado": "NO ANONIMIZABLE",
        "reservada": False, "documento_id": "x", "id_buscador": "y",
        "link_detalle": "https://juris.pjud.cl/busqueda?Corte_Suprema",
    }


def test_convierte_una_ficha_a_markdown(tmp_path):
    origen = tmp_path / "fichas.jsonl"
    origen.write_text(json.dumps(_ficha_base(), ensure_ascii=False) + "\n", encoding="utf-8")

    corrida = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "cs_a_markdown.py"),
         "--origen", str(origen), "--destino", str(tmp_path / "salida")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")

    assert corrida.returncode == 0, corrida.stderr
    generado = tmp_path / "salida" / "2026" / "50838-2026.md"
    assert generado.exists()
    texto = generado.read_text(encoding="utf-8")
    assert "# SERVICIO DE SALUD c/ OTRO" in texto
    assert "[50838-2026](https://juris.pjud.cl" in texto
    assert "Corte Suprema" in texto and "2026-09-24" in texto
    assert "Hugging Face - jurisprudencia_cs/2026/50838-2026.md" in texto


def test_no_inventa_datos_que_faltan(tmp_path):
    origen = tmp_path / "fichas.jsonl"
    origen.write_text(json.dumps({"rol": "1-2024", "era": 2024}, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "cs_a_markdown.py"),
                    "--origen", str(origen), "--destino", str(tmp_path / "salida")],
                   check=True, capture_output=True)
    texto = (tmp_path / "salida" / "2024" / "1-2024.md").read_text(encoding="utf-8")
    assert "—" in texto, "los campos ausentes se marcan con «—», nunca con texto inventado"


def test_indices_por_era(tmp_path):
    origen = tmp_path / "fichas.jsonl"
    filas = [
        {**_ficha_base(), "rol": "100-2026", "caratula": "UNO c/ DOS", "era": 2026},
        {**_ficha_base(), "rol": "200-2026", "caratula": "TRES c/ CUATRO", "era": 2026},
    ]
    origen.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas),
                      encoding="utf-8")
    corrida = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "cs_a_markdown.py"),
         "--origen", str(origen), "--destino", str(tmp_path / "salida"), "--indices"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert corrida.returncode == 0, corrida.stderr
    indice = tmp_path / "salida" / "INDICE_2026.md"
    assert indice.exists()
    contenido = indice.read_text(encoding="utf-8")
    assert "100-2026" in contenido and "[UNO c/ DOS](2026/100-2026.md)" in contenido
    assert "200-2026" in contenido
