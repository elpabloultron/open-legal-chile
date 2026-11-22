"""Candado anti-fugas de privacidad y casos de clientes en el repositorio público Git.

Verifica sobre todos los archivos versionados (`git ls-files`) que:
1. Nunca se versionen archivos bajo `casos/` (salvo `casos/.gitkeep`) ni scripts de informes
   de casos concretos (`scripts/generar_informe_*.py`).
2. Ningún archivo de código/configuración contenga rutas personales de disco (`/home/<usuario>`).
3. Ningún archivo de código/scripts/docs propios contenga RUTs personales reales fuera de la
   lista explícita de RUTs ficticios de prueba.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# RUTs ficticios reconocidos de ejemplo/prueba (no corresponden a clientes reales)
RUTS_FICTICIOS_PERMITIDOS = frozenset({
    "12.345.678-5",
    "12.345.678-9",
    "12.345.678-K",
    "11.111.111-1",
    "11.222.333-4",
    "15.123.456-7",
    "33.333.333-3",
    "76.123.456-7",
    "76.543.210-K",
    "99.999.999-9",
    "1.111.111-1",
    "10.000.000-0",
    "22.222.222-2",
    # Ejemplos sintéticos de docs/index.html (buscador/calculadora)
    "3.015.555-3",
    "1.305.765-1",
    "1.305.465-2",
})

_RE_RUT = re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b")
_RE_HOME_PERSONAL = re.compile(r"(?:/home/pablo/|/Users/pablo/|C:\\\\Users\\\\pablo\\\\)", re.IGNORECASE)

_PREFIJOS_CORPUS_TERCEROS = (
    "doctrina/",
    "jurisprudencia",
    "publicaciones_ambientales/",
    "corpus_guias_aj/",
    "graphify-out/",
    "data/",
)


def _archivos_versionados() -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files"],
        cwd=str(RAIZ),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_ningun_caso_de_cliente_esta_versionado_en_git():
    """`casos/` y `scripts/generar_informe_*.py` nunca pueden subir a GitHub."""
    prohibidos = []
    for rel in _archivos_versionados():
        if rel.startswith("casos/") and rel != "casos/.gitkeep":
            prohibidos.append(rel)
        if re.match(r"^scripts/generar_informe_.*\.py$", rel):
            prohibidos.append(rel)
    assert not prohibidos, f"Archivos de casos privados detectados en Git: {prohibidos}"


def test_ningun_codigo_o_script_versionado_contiene_rut_real():
    """Bloquea cualquier RUT real filtrado en código, scripts o documentación propia."""
    hallazgos = []
    for rel in _archivos_versionados():
        if rel.startswith(_PREFIJOS_CORPUS_TERCEROS) or rel.startswith("tests/"):
            continue
        if not rel.endswith((".py", ".md", ".json", ".yaml", ".yml", ".html", ".sh", ".toml")):
            continue
        ruta = RAIZ / rel
        if not ruta.exists() or ruta.stat().st_size > 2_000_000:
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        ruts = [r for r in sorted(set(_RE_RUT.findall(texto))) if r not in RUTS_FICTICIOS_PERMITIDOS]
        if ruts:
            hallazgos.append(f"{rel}: {ruts[:5]}")
    assert not hallazgos, f"Posibles RUTs reales detectados en archivos versionados: {hallazgos}"


def test_ningun_codigo_o_script_versionado_contiene_ruta_personal():
    """Bloquea rutas de disco personales (/home/pablo/...) en archivos de código y scripts."""
    hallazgos = []
    for rel in _archivos_versionados():
        if rel.startswith(_PREFIJOS_CORPUS_TERCEROS) or rel in ("docs/auditoria-e2e.md", "tests/test_empaquetado.py", "tests/test_privacidad_repo.py"):
            continue
        if not rel.endswith((".py", ".json", ".yaml", ".yml", ".sh", ".toml")):
            continue
        ruta = RAIZ / rel
        if not ruta.exists() or ruta.stat().st_size > 2_000_000:
            continue
        if _RE_HOME_PERSONAL.search(ruta.read_text(encoding="utf-8", errors="ignore")):
            hallazgos.append(rel)
    assert not hallazgos, f"Rutas personales detectadas en archivos versionados: {hallazgos}"
