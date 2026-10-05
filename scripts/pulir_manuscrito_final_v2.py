import re
from pathlib import Path

p = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")
content = p.read_text(encoding="utf-8")

# 1. Renumerar figuras cronológicamente
# Figura 1: Brecha en la difusión (Sec 1.2) - ya es Figura 1
# Figura 2: Matriz de privacidad (Sec 2.5.4)
content = content.replace("![Figura 5](figuras/cuadro3_matriz_privacidad_retencion.png)", "![Figura 2](figuras/cuadro3_matriz_privacidad_retencion.png)")
content = content.replace("*Figura 5. Matriz comparativa de soberanía de datos", "*Figura 2. Matriz comparativa de soberanía de datos")

# Figura 3: Principios Arquitectónicos (Sec 3)
content = content.replace("![Figura 6](figuras/cuadro1_principios_arquitectonicos.png)", "![Figura 3](figuras/cuadro1_principios_arquitectonicos.png)")
content = content.replace("*Figura 6. Los cuatro pilares axiológicos", "*Figura 3. Los cuatro pilares axiológicos")

# En Sec 4: La Figura 2 previa de seis capas pasa a ser Figura 4 (el Cuadro 2)
# Reemplazar la referencia previa a Figura 2 si existe
content = content.replace("![Figura 2](figuras/figura2_arquitectura_triada.png)", "")
content = content.replace("*Figura 2. Arquitectura de seis capas y la Tríada Neuro-Simbólica de Open Legal Chile. Fuente: Elaboración propia a partir de la especificación técnica de Open Legal Chile v1.12.0.*", "")
content = content.replace("Como ilustra la Figura 2, la arquitectura organiza el flujo forense asegurando que las decisiones de admisibilidad de plazos fatales y validación algorítmica se ejecuten a nivel de Sistema 1 determinista antes de dar paso a la síntesis discursiva.", "")

content = content.replace("![Figura 7](figuras/cuadro2_arquitectura_modular.png)", "![Figura 4](figuras/cuadro2_arquitectura_modular.png)")
content = content.replace("*Figura 7. Distribución y flujo operativo de las seis capas", "*Figura 4. Distribución y flujo operativo de las seis capas")

# Figura 5: Subgrafo sintético LegalGraphify (Sec 4.4.2)
content = content.replace("![Figura 3](figuras/figura3_subgrafo_ahorro_tokens.png)", "![Figura 5](figuras/figura3_subgrafo_ahorro_tokens.png)")
content = content.replace("*Figura 3. Extracción de subgrafo sintético", "*Figura 5. Extracción de subgrafo sintético")
content = content.replace("La Figura 3 demuestra en términos cuantitativos", "La Figura 5 demuestra en términos cuantitativos")

# Figura 6: Timeline laboral Art 168 (Sec 5.1)
content = content.replace("![Figura 4](figuras/figura4_timeline_laboral_art168.png)", "![Figura 6](figuras/figura4_timeline_laboral_art168.png)")
content = content.replace("*Figura 4. Cómputo de días hábiles judiciales", "*Figura 6. Cómputo de días hábiles judiciales")

# Figura 7: Latencias y benchmarks (Sec 6.1)
content = content.replace("![Figura 6](figuras/figura6_latencias_benchmarks.png)", "![Figura 7](figuras/figura6_latencias_benchmarks.png)")
content = content.replace("*Figura 6. Desempeño computacional en milisegundos y aseguramiento SAST 360°.*", "*Figura 7. Desempeño computacional en milisegundos y aseguramiento SAST 360°.*")

# 2. Retirar Sección 10 Anexos duplicada (las 526 pruebas y SAST ya están detalladas en Sec 6.2 y 6.3)
# Dejar una nota metodológica de 2 líneas al final de Sección 6 o Conclusiones
content = re.sub(r"\n---\n\n## 10\. Anexo: Nota Metodológica.*?\Z", "", content, flags=re.DOTALL)

# Verificar palabras
words = len(re.findall(r'\b\w+\b', content))
chars = len(content)
print(f"Palabras sin anexo duplicado: {words}")
print(f"Caracteres: {chars}")

p.write_text(content, encoding="utf-8")
