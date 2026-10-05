import re
from pathlib import Path

p = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")
content = p.read_text(encoding="utf-8")

# Frases que sabemos que están y podemos acortar
s1 = "Para que el jurista, el litigante y el magistrado puedan evaluar críticamente la incorporación de la inteligencia artificial en el quehacer forense, es indispensable desmitificar la terminología computacional y comprender la mecánica exacta de los componentes que integran el ecosistema:"
r1 = "Para evaluar con rigor la IA forense, es indispensable comprender la mecánica operativa de los componentes del ecosistema:"

s2 = "La confluencia entre la computación jurídica y el movimiento global de Acceso a la Justicia (A2J) cobra un sentido pleno a través de la filosofía del Software Libre y de Código Abierto (FOSS)."
r2 = "La computación jurídica y el Acceso a la Justicia (A2J) se potencian mediante el Software Libre (FOSS)."

s3 = "A la distorsión epistémica descrita se añade un grave problema de justicia distributiva y economía política: la captura y privatización mercantil de las fuentes públicas del derecho por parte de consorcios transnacionales de información jurídica."
r3 = "A dicha distorsión se añade la privatización de las fuentes públicas del derecho por consorcios corporativos."

for orig, nuevo in [(s1, r1), (s2, r2), (s3, r3)]:
    if orig in content:
        content = content.replace(orig, nuevo)
        print("Reemplazo exitoso.")
    else:
        print("No encontrado.")

p.write_text(content, encoding="utf-8")
words = len(re.findall(r'\b\w+\b', content))
chars = len(content)
print(f"Palabras finales: {words}")
print(f"Caracteres finales: {chars}")
assert words <= 15000, f"Aún excede: {words}"
print("✓ ¡Aprobado bajo el límite oficial de 15.000 palabras de la RChDT!")
