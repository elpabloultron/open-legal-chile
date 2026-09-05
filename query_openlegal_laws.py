import sys, os
sys.path.append("/home/pablo/Escritorio/Ultimaprensa/open-legal-chile")
from bcn_connector import BCNClient

client = BCNClient()

print("--> Consultando Ley N° 21.091 (Educación Superior)...")
ley_21091 = client.get_ley(21091)
print(f"Título: {ley_21091.get('titulo')}")
print(f"Total artículos extraídos: {len(ley_21091.get('articulos', {}))}")

print("\n--> Consultando Ley N° 20.129 (Aseguramiento de la Calidad / CNA)...")
ley_20129 = client.get_ley(20129)
print(f"Título: {ley_20129.get('titulo')}")
print(f"Total artículos extraídos: {len(ley_20129.get('articulos', {}))}")

print("\n--> Consultando Ley N° 21.094 (Universidades Estatales)...")
ley_21094 = client.get_ley(21094)
print(f"Título: {ley_21094.get('titulo')}")
print(f"Total artículos extraídos: {len(ley_21094.get('articulos', {}))}")

# Guardar un extracto temático para estructurar las denuncias
with open("extractos_normativos_denuncias.txt", "w", encoding="utf-8") as out:
    out.write("=====================================================\n")
    out.write("EXTRACTOS NORMATIVOS CLAVE PARA SES Y CNA\n")
    out.write("=====================================================\n\n")

    out.write("### 1. LEY N° 21.091 (SUPERINTENDENCIA DE EDUCACIÓN SUPERIOR)\n\n")
    for art_num in ["18", "19", "21", "22", "34", "35", "36", "38", "39", "40", "41", "42", "48", "63"]:
        art_txt = ley_21091.get('articulos', {}).get(art_num)
        if art_txt:
            out.write(f"--- ARTÍCULO {art_num} ---\n{art_txt}\n\n")

    out.write("\n### 2. LEY N° 20.129 (COMISIÓN NACIONAL DE ACREDITACIÓN - CNA)\n\n")
    for art_num in ["1", "2", "6", "15", "16", "17", "18", "21", "22", "23", "27"]:
        art_txt = ley_20129.get('articulos', {}).get(art_num)
        if art_txt:
            out.write(f"--- ARTÍCULO {art_num} ---\n{art_txt}\n\n")

    out.write("\n### 3. LEY N° 21.094 (UNIVERSIDADES DEL ESTADO)\n\n")
    for art_num in ["2", "3", "4", "39", "41"]:
        art_txt = ley_21094.get('articulos', {}).get(art_num)
        if art_txt:
            out.write(f"--- ARTÍCULO {art_num} ---\n{art_txt}\n\n")

print("\n✓ Extractos normativos guardados exitosamente en 'extractos_normativos_denuncias.txt'")
