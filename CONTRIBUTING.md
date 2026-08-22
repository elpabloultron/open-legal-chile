# 🤝 Guía de Contribución — Open Legal Chile

¡Gracias por tu interés en contribuir a **Open Legal Chile**! Nuestro objetivo es construir la plataforma de inteligencia jurídica y el ecosistema agéntico más riguroso, abierto y accesible para el Derecho Continental de la República de Chile.

---

## 🏛️ 1. Principios Jurídicos Inquebrantables

* **Sistema de Derecho Continental (*Civil Law*):** Todas las contribuciones deben respetar la primacía de la Ley (Art. 1 Código Civil) y el efecto relativo de las sentencias (Art. 3 inc. 2 Código Civil).
* **Prohibición de Extrapolación de Términos de Common Law:** Rechazamos terminología foránea inexistente en Chile (*at-will*, *punitive damages*, *discovery*, *subpoena*, etc.).
* **Sistema de Citación Obligatorio:** Toda cita debe cumplir el formato oficial `[BCN - ...]`, `[Dictamen DT ...]`, `[CS - Rol ...]`, `[Dictamen CGR ...]`.

---

## 💻 2. Entorno de Desarrollo Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/elpabloultron/open-legal-chile.git
cd open-legal-chile

# 2. Instalar dependencias de desarrollo
pip install -e .[dev]

# 3. Ejecutar la suite de pruebas
python -m pytest tests/ -v

# 4. Probar el servidor MCP
python openlegal.py mcp
```

---

## 🧪 3. Requisitos para Pull Requests

1. **Pruebas Automatizadas:** Todo nuevo conector o herramienta MCP debe incluir tests en `tests/`.
2. **Cero Mocks:** No se aceptan respuestas simuladas en conectores oficiales.
3. **Puntuación en Benchmark:** Las modificaciones a los motores de prompt deben pasar las evaluaciones en `evals/benchmark.py` con una nota superior a 7.0/10.0.
