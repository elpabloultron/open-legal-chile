"""Herramientas del servidor MCP, un módulo por dominio.

Cada módulo expone `TOOLS` (sus esquemas) y `despachar(name, args)` (ejecuta la que le toca;
devuelve None si la herramienta no es suya). Los helpers e instancias compartidas siguen
viviendo en mcp_server.py: cada módulo los trae a su espacio de nombres en cada despacho
(`_refrescar()`), así ve los objetos vivos del servidor —incluidas las sustituciones que
hacen las pruebas con monkeypatch— y los bloques movidos no cambiaron su lógica."""
