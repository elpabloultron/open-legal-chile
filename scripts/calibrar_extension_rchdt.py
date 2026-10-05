#!/usr/bin/env python3
"""
Calibra la extensión del manuscrito para que quede estrictamente por debajo
del tope máximo de 15.000 palabras de la RChDT (entre 14.800 y 14.950 palabras).
"""
from pathlib import Path
import re

MD_PATH = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Condensar frases redundantes en tablas o anexos
text = text.replace(
    "de manera absolutamente libre, gratuita, irrevocable y sin restricciones",
    "de forma libre y abierta"
)
text = text.replace(
    "en los sistemas operativos Linux (Ubuntu 22.04 LTS, Ubuntu 24.04 LTS) y Microsoft Windows (Windows 10, Windows 11)",
    "en Linux y Windows"
)
text = text.replace(
    "la totalidad de los 257 archivos que componen el repositorio del proyecto",
    "los 257 archivos del repositorio"
)
text = text.replace(
    "con una certeza matemática y criptográfica indubitada",
    "con certeza matemática"
)
text = text.replace(
    "a lo largo y ancho de las diversas regiones y provincias del territorio nacional",
    "en las distintas regiones del país"
)
text = text.replace(
    "en el marco ineludible del Estado Constitucional y Democrático de Derecho",
    "en el Estado de Derecho"
)
text = text.replace(
    "tanto a nivel sustantivo como en el plano estrictamente procesal",
    "a nivel sustantivo y procesal"
)
text = text.replace(
    "de forma rápida, expedita, confiable y segura",
    "de forma rápida y segura"
)

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(text)

words = len(re.findall(r'\b\w+\b', text))
chars = len(text)
print("✓ Manuscrito calibrado con precisión quirúrgica:")
print(f"  - Palabras totales: {words:,} (Tope máximo RChDT: 15.000 palabras)")
print(f"  - Caracteres totales (con espacios): {chars:,}")
assert words <= 15000, f"Aún excede el tope: {words}"
assert words >= 14800, f"Quedó muy corto: {words}"
print("✓ ¡Alineación perfecta con las directrices de la RChDT (entre 14.800 y 15.000 palabras)!")
