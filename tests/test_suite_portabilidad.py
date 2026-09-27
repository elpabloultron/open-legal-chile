"""La suite tiene que correr en Windows, no sólo en Linux.

En Windows el pipe de un proceso hijo decodifica con la codificación local (cp1252) y no con UTF-8:
el banner de la CLI (⚖️, tildes) mata al hilo lector de `subprocess`, `stdout` queda en `None` y la
prueba falla con un `TypeError: argument of type 'NoneType' is not iterable` que no dice nada del
problema real. Pasó en el CI de 1.7.1 (`test_integrar_harness.py`), con los trabajos de Linux en verde.

La regla: toda corrida de un proceso que **decodifique** su salida (`text=True` o
`universal_newlines=True`) declara `encoding="utf-8"`.
"""

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Métodos de subprocess que pueden decodificar la salida del hijo.
METODOS = {"run", "Popen", "check_output", "check_call", "call"}


def _llamadas_de_subprocess(arbol: ast.AST):
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            if nodo.func.attr in METODOS:
                yield nodo


def _esta_activo(valor: ast.expr) -> bool:
    """True sólo si el argumento quedó escrito literalmente como True (no si es una variable)."""
    return isinstance(valor, ast.Constant) and valor.value is True


def test_las_pruebas_que_decodifican_salida_declaran_la_codificacion():
    fallas = []
    for ruta in sorted((RAIZ / "tests").glob("test_*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for llamada in _llamadas_de_subprocess(arbol):
            claves = {k.arg: k.value for k in llamada.keywords if k.arg}
            decodifica = any(_esta_activo(claves[nombre]) for nombre in ("text", "universal_newlines")
                             if nombre in claves)
            if decodifica and "encoding" not in claves:
                fallas.append(f"{ruta.name}:{llamada.lineno}")

    assert not fallas, (
        "estas corridas decodifican con la codificación local (cp1252 en Windows) y van a dejar "
        f"stdout en None: {fallas}"
    )
