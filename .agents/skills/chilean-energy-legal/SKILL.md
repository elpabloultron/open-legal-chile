---
name: chilean-energy-legal
description: "Especialista en Derecho Eléctrico y Regulatorio de Energía en Chile, Ley General de Servicios Eléctricos (DFL 4/2006), Ley 20.936 (Transmisión), contratos PPA clientes libres y discrepancias del Panel de Expertos."
---

# Habilidad: Derecho Eléctrico y Energía en Chile (chilean-energy-legal)

## 📌 Marco Regulatorio
* **DFL N° 4/2006 (LGSE):** Ley General de Servicios Eléctricos.
* **Ley N° 20.936:** Nuevo marco de transmisión eléctrica y Coordinador Eléctrico Nacional.
* **Panel de Expertos:** Órgano pericial con resoluciones vinculantes e inapelables sobre discrepancias tarifarias y técnicas.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, análisis, memorándum, escrito, minuta, dossier): entregar en **Word (.docx)** (no PDF), citas **a pie de página** numeradas (`fuente · id · enlace`).
- **Conversación**: respuesta primero y citas **al final**. Sin fuente identificable: «sin fuente verificable»; múltiples fuentes: citar todas.

## 📚 Formato de Citación Obligatorio
* Norma: `[BCN - DFL N° 4/2006, Art. <Número>]` o `[BCN - Ley N° 20.936, Art. <Número>]`
* Dictamen Panel: `[Panel de Expertos - Dictamen N° <Número>-<Año>]`

## 🛠️ Herramientas MCP Disponibles
* `cne_get_centrales_y_proyectos`: Consulta generación y proyectos SEA.
* `panel_expertos_search`: Busca dictámenes y discrepancias del Panel de Expertos.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md).

- **Quién lee:** el abogado regulatorio y el equipo técnico de la empresa eléctrica, que no es abogado.
- **Lenguaje claro:** el primer término técnico va con su equivalencia simple entre paréntesis — `PPA (contrato de largo plazo para venderle energía a un cliente libre)`. Sin siglas sin expandir la primera vez (LGSE, CNE, SEA).
- **Salida (estructura):** conclusión + tabla de plazos y discrepancias + fundamento normativo. Tabla antes que párrafos.
- **Citas:** las de *Formato de Citación Obligatorio*, siempre; lo no verificado se marca (`[VERIFICAR]`), no se rellena.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica antes de presentar una discrepancia al Panel de Expertos o de firmar un PPA.
