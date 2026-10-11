# Tribunal Constitucional de Chile — sentencias en Markdown

Texto íntegro de las sentencias y resoluciones del Tribunal Constitucional, descargadas desde su
buscador oficial (`buscador.tcchile.cl`) y convertidas a Markdown.

- **Cobertura:** desde 2024 (el TC publica en su buscador con meses de rezago). Se actualiza cada
  semana con la Action «Ingesta TC» del repositorio Open Legal Chile.
- **Cada archivo:** `<rol>.md`, con ficha de cita (rol, rol oficial, fecha, sala, gestión pendiente,
  documento oficial) y el texto completo del documento.
- **Verificación:** el documento oficial se pide por número de rol y solo se publica si su texto
  nombra ese rol. La fecha y el tipo salen del propio documento (si la ficha del buscador dice otra
  cosa, queda anotado). La gestión pendiente se escribe solo si sus RIT/RUC/Rol aparecen en el texto.
- **Privacidad:** los correos electrónicos de las notificaciones se reemplazan por «[correo omitido]»
  y no se publican las causas que el TC marca como reservadas.
- **Reproducible:** `python scripts/cosechar_jurisprudencia_2anios.py --tribunal tc --desde AAAA-MM-DD`,
  `python scripts/tc_pdfs_a_md.py --rehacer` y `python scripts/subir_tc_hf.py`.

**Cita:** `[Hugging Face - jurisprudencia_tc/<rol>.md]`; para citar la sentencia, el rol oficial:
`[TC - Rol N° 15686-24-INA, Fecha: 12-06-2025]`.
