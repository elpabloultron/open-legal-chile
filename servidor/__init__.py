"""Herramientas del servidor MCP, un módulo por dominio.

Cada módulo expone `TOOLS` (sus esquemas) y `despachar(name, args)` (ejecuta la que le toca;
devuelve None si la herramienta no es suya). Los helpers e instancias compartidas siguen
viviendo en mcp_server.py: cada módulo los trae a su espacio de nombres en cada despacho
(`_refrescar()`), así ve los objetos vivos del servidor —incluidas las sustituciones que
hacen las pruebas con monkeypatch— sin forzar su importación al arrancar."""

from typing import Any, Dict


class _LazyServidor:
    """Proxy liviano que resuelve un símbolo de mcp_server en su primer uso (PEP 562)."""

    __slots__ = ("_nombre",)

    def __init__(self, nombre: str) -> None:
        self._nombre = nombre

    def _real(self) -> Any:
        from config import servidor_actual
        return getattr(servidor_actual(), self._nombre)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._real()(*args, **kwargs)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._real(), attr)

    def __getitem__(self, key: Any) -> Any:
        return self._real()[key]

    def __contains__(self, item: Any) -> bool:
        return item in self._real()

    def __iter__(self) -> Any:
        return iter(self._real())

    def __len__(self) -> int:
        return len(self._real())

    def __bool__(self) -> bool:
        return bool(self._real())

    def __repr__(self) -> str:
        return f"<_LazyServidor({self._nombre!r})>"


def crear_proxies(*nombres: str) -> Dict[str, Any]:
    """Construye un diccionario `{nombre: _LazyServidor(nombre)}` para globals() de un módulo."""
    return {nombre: _LazyServidor(nombre) for nombre in nombres}


def refrescar_globals(g: Dict[str, Any], propios: frozenset, defaults_lazy: Dict[str, Any]) -> None:
    """Restaura proxies perezosos y copia los símbolos ya cargados/parcheados en mcp_server."""
    from config import servidor_actual
    _m = servidor_actual()
    if defaults_lazy:
        g.update(defaults_lazy)
    g.update({k: v for k, v in vars(_m).items() if k not in propios})
