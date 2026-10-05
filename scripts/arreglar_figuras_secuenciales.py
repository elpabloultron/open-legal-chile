import re
from pathlib import Path

p = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")
content = p.read_text(encoding="utf-8")

# Corregir la duplicación en Sección 4 (reemplazar la segunda Figura 3 por Figura 4)
# En Sección 4 debe ir Cuadro 2: Arquitectura Modular
sec4_erronea = """![Figura 3](figuras/cuadro1_principios_arquitectonicos.png)

*Figura 3. Los cuatro pilares axiológicos y arquitectónicos fundamentales de Open Legal Chile. Fuente: Elaboración propia a partir de la especificación técnica de Open Legal Chile v1.12.0.*"""

sec4_correcta = """![Figura 4](figuras/cuadro2_arquitectura_modular.png)

*Figura 4. Distribución y flujo operativo de las seis capas funcionales del ecosistema Open Legal Chile. Fuente: Elaboración propia a partir de la arquitectura modular de Open Legal Chile v1.12.0.*"""

# Reemplazar la segunda ocurrencia
partes = content.split(sec4_erronea)
if len(partes) == 3:
    # La primera ocurrencia está en Sec 3 (dejarla como Figura 3)
    # La segunda ocurrencia está en Sec 4 (cambiarla a Figura 4)
    content = partes[0] + sec4_erronea + partes[1] + sec4_correcta + partes[2]
    print("Sec 4 corregida con éxito.")
else:
    print(f"Ocurrencias encontradas: {len(partes)-1}")

# En Sección 4.5: La figura de LegalCanvas pasa de Figura 5 a Figura 6
content = content.replace(
    "![Figura 5](figuras/figura5_dashboard_legalcanvas.png)",
    "![Figura 6](figuras/figura5_dashboard_legalcanvas.png)"
)
content = content.replace(
    "*Figura 5. Micro-UI forense de LegalCanvas:",
    "*Figura 6. Micro-UI forense de LegalCanvas:"
)

# En Sección 5.1: El timeline laboral pasa de Figura 6 a Figura 7
content = content.replace(
    "![Figura 6](figuras/figura4_timeline_laboral_art168.png)",
    "![Figura 7](figuras/figura4_timeline_laboral_art168.png)"
)
content = content.replace(
    "*Figura 6. Cómputo de días hábiles judiciales",
    "*Figura 7. Cómputo de días hábiles judiciales"
)

# En Sección 6.1: Los benchmarks pasan de Figura 7 a Figura 8
content = content.replace(
    "![Figura 7](figuras/figura6_latencias_benchmarks.png)",
    "![Figura 8](figuras/figura6_latencias_benchmarks.png)"
)
content = content.replace(
    "*Figura 7. Desempeño computacional en milisegundos y aseguramiento SAST 360°.*",
    "*Figura 8. Desempeño computacional en milisegundos y aseguramiento SAST 360°.*"
)

p.write_text(content, encoding="utf-8")
words = len(re.findall(r'\b\w+\b', content))
print(f"Total palabras: {words}")
