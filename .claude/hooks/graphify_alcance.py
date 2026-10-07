"""Alcance de la guardia PreToolUse de graphify: ¿esta llamada cae dentro del grafo de CÓDIGO?

`graphify hook-guard` empuja a consultar el grafo ante cualquier Read, Grep, Glob o Bash sobre
.py, .md o .txt del proyecto. Pero el grafo de código excluye el corpus jurídico (.graphifyignore),
así que ese aviso mandaría a un agente que estudia doctrina a un grafo que no la contiene, contra
el protocolo consulta_maestra / cita_texto. Este módulo decide, sin subprocess ni red, si la
llamada toca una carpeta excluida (la guardia calla) o código (la guardia deja avisar).

Medido el 07-10-2026 con graphify 0.9.79 sobre la primera versión de la guardia, que buscaba
`(^|["/ ])carpeta/` en todo el JSON con grep: no callaba con Grep{path: '<raíz>/doctrina'} (la
herramienta manda la carpeta sin barra final), ni con Grep{path: 'doctrina'}, ni con
Glob{path: '<raíz>/corpus_guias_aj'}, ni con `rg -n x doctrina`, ni con rutas de Windows (`\\`);
las cuatro formas recibían «MANDATORY: You MUST run graphify». Al revés, buscaba también en la
`description` del Bash, así que un comando de código quedaba mudo si su descripción nombraba
`data/`. Por eso aquí solo se leen los campos que son rutas, se normaliza `\\` y se compara por
prefijo de carpeta, con o sin barra final.

Además del alcance, avisa una vez por sesión y por tipo: el aviso de graphify pesa ~100 tokens por
Read y ~47 por Grep (400 y 190 caracteres, medidos en 0.9.79), y una sesión de 150 Read y 100 Grep
repetiría ~20.000 tokens. La marca vive en graphify-out/.guardia/<sesión>-<tipo>; la crea
graphify-guardia.sh solo cuando hubo aviso, y graphify-sesion.sh la borra en cada SessionStart.

Códigos de salida de `main`: 0 = no avisar (fuera del grafo o ya avisado); 1 = avisar (imprime la
ruta de la marca, si hay session_id); 2 = error (la guardia falla abierta y no dice nada).
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import sys
from pathlib import Path
from typing import Any, Sequence

# Regla de carpeta de .graphifyignore: «nombre/», sin comodines, negaciones ni comentarios.
REGLA_CARPETA = re.compile(r"^[^#!*?\s][^*?\s]*/$")
# Un «argumento» de una línea de Bash: corta en espacios, comillas, redirecciones y operadores.
TOKEN = re.compile(r"[^\s\"'=;|&()<>`]+")
_SANEAR = re.compile(r"[^A-Za-z0-9_-]")


def carpetas_excluidas(texto: str) -> list[str]:
    """Carpetas que excluye .graphifyignore, sin la barra final. Es la única fuente de verdad."""
    carpetas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if REGLA_CARPETA.match(linea):
            carpetas.append(linea[:-1])
    return carpetas


def _normalizar(valor: str) -> str:
    """`\\` pasa a `/` y se quitan las comillas y los `./` iniciales (rutas de Windows y de Bash)."""
    valor = valor.replace("\\", "/").strip().strip("\"'")
    while valor.startswith("./"):
        valor = valor[2:]
    return valor


def _relativa(valor: str, raiz: str) -> str:
    """Ruta relativa a la raíz del proyecto, sin `..` ni barra final. Fuera de la raíz, intacta."""
    valor = _normalizar(valor)
    raiz = _normalizar(raiz).rstrip("/")
    ignorar_mayusculas = os.name == "nt"  # NTFS no distingue mayúsculas de minúsculas
    comparable = valor.casefold() if ignorar_mayusculas else valor
    base = raiz.casefold() if ignorar_mayusculas else raiz
    if raiz and comparable == base:
        valor = ""
    elif raiz and comparable.startswith(base + "/"):
        valor = valor[len(raiz) + 1:]
    return posixpath.normpath(valor) if valor else ""


def candidatos(entrada: dict[str, Any]) -> list[str]:
    """Textos del tool_input que son rutas. Nunca `description` ni el `pattern` de Grep (regex)."""
    datos = entrada.get("tool_input")
    if not isinstance(datos, dict):
        return []
    herramienta = entrada.get("tool_name")
    salida: list[str] = []
    campos = ["file_path", "path", "glob"] + (["pattern"] if herramienta == "Glob" else [])
    for campo in campos:
        valor = datos.get(campo)
        if isinstance(valor, str) and valor:
            salida.append(valor)
    comando = datos.get("command")
    if herramienta == "Bash" and isinstance(comando, str):
        salida.extend(TOKEN.findall(comando.replace("\\", "/")))
    return salida


def fuera_del_grafo(entrada: dict[str, Any], raiz: str, carpetas: Sequence[str]) -> bool:
    """True si algún candidato es una carpeta excluida o está dentro de una."""
    if not carpetas:
        return False
    ignorar_mayusculas = os.name == "nt"
    excluidas = [c.casefold() if ignorar_mayusculas else c for c in carpetas]
    for valor in candidatos(entrada):
        relativa = _relativa(valor, raiz)
        if not relativa:
            continue
        if ignorar_mayusculas:
            relativa = relativa.casefold()
        for carpeta in excluidas:
            if relativa == carpeta or relativa.startswith(carpeta + "/"):
                return True
    return False


def ruta_de_marca(entrada: dict[str, Any], tipo: str, raiz: str) -> Path | None:
    """graphify-out/.guardia/<sesión>-<tipo>, o None si el evento no trae session_id."""
    sesion = entrada.get("session_id")
    if not isinstance(sesion, str):
        return None
    sesion = _SANEAR.sub("", sesion)[:80]
    tipo = _SANEAR.sub("", tipo)[:20]
    if not sesion or not tipo:
        return None
    return Path(raiz) / "graphify-out" / ".guardia" / f"{sesion}-{tipo}"


def _leer_stdin() -> str:
    # Claude Code manda JSON en UTF-8; en Windows el stdin de texto usaría la página de códigos.
    binario = getattr(sys.stdin, "buffer", None)
    if binario is not None:
        return binario.read().decode("utf-8", errors="replace")
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    tipo = argumentos[0] if argumentos else "search"
    try:
        entrada = json.loads(_leer_stdin())
        if not isinstance(entrada, dict):
            return 2
        raiz = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        try:
            texto = (Path(raiz) / ".graphifyignore").read_text(encoding="utf-8")
        except OSError:
            texto = ""
        if fuera_del_grafo(entrada, raiz, carpetas_excluidas(texto)):
            return 0
        marca = ruta_de_marca(entrada, tipo, raiz)
        if marca is not None and marca.exists():
            return 0
        if marca is not None:
            print(marca.as_posix())
        return 1
    except Exception:  # la guardia falla abierta: ante cualquier error no dice nada
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
