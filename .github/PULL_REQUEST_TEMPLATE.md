## Descripción

<!-- Resumen claro del cambio y el problema que resuelve. Vincula el issue si existe: Closes #N -->

## Tipo de cambio

- [ ] 🐞 Fix de bug
- [ ] ✨ Nueva funcionalidad (herramienta MCP / conector / skill / agente)
- [ ] 📚 Documentación
- [ ] 🧪 Tests
- [ ] ⚙️ CI / Packaging

## Checklist

- [ ] `python -m pytest tests/ -v` en verde (21 tests)
- [ ] Citas conforme al estándar oficial de [AGENTS.md](../../AGENTS.md); sin terminología de Common Law
- [ ] Conectores nuevos documentados en `CONNECTORS.md` y `openlegal.manifest.json`
- [ ] Skills nuevas registradas en `skills-lock.json` (con SHA-256), `AGENTS.md` y `README.md`
- [ ] Prompt o skill evaluado con `python evals/benchmark.py` ≥ 7.0/10 sin penalizaciones
- [ ] Sin secretos en el diff (`.env`, claves de API)
- [ ] Código autoexplicativo, docstrings en español, sin dependencias nuevas salvo justificación

## Evidencia

<!-- Salida de tests, comandos de verificación o capturas relevantes -->

> ⚖️ **Compuerta de Revisión Jurídica:** todo contenido legal generado es borrador de asistencia técnica y debe validarse por un abogado habilitado antes de su uso.
