"""Extrae artículos clave de las leyes de educación superior (SES y CNA) desde la BCN.

Leyes N° 21.091 (Educación Superior), N° 20.129 (Aseguramiento de la Calidad / CNA) y
N° 21.094 (Universidades del Estado). El resultado se escribe en exports/, que está fuera del
control de versiones: es material de trabajo de un caso, no parte del producto.

Uso:
  python scripts/extraer_normas_educacion_superior.py [--salida exports/extractos_normativos_denuncias.txt]
"""

import argparse
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

LEYES = (
    (21091, "LEY N° 21.091 (SUPERINTENDENCIA DE EDUCACIÓN SUPERIOR)",
     ["18", "19", "21", "22", "34", "35", "36", "38", "39", "40", "41", "42", "48", "63"]),
    (20129, "LEY N° 20.129 (COMISIÓN NACIONAL DE ACREDITACIÓN - CNA)",
     ["1", "2", "6", "15", "16", "17", "18", "21", "22", "23", "27"]),
    (21094, "LEY N° 21.094 (UNIVERSIDADES DEL ESTADO)", ["2", "3", "4", "39", "41"]),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", default=str(RAIZ / "exports" / "extractos_normativos_denuncias.txt"))
    args = parser.parse_args()

    from bcn_connector import BCNClient

    client = BCNClient()
    salida = pathlib.Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8") as out:
        out.write("=====================================================\n")
        out.write("EXTRACTOS NORMATIVOS CLAVE PARA SES Y CNA\n")
        out.write("=====================================================\n\n")
        for indice, (numero, titulo, articulos) in enumerate(LEYES, start=1):
            print(f"--> Consultando Ley N° {numero}...")
            ley = client.get_ley(numero)
            print(f"Título: {ley.get('titulo')} · artículos extraídos: {len(ley.get('articulos', {}))}")
            out.write(f"\n### {indice}. {titulo}\n\n")
            for art_num in articulos:
                art_txt = ley.get("articulos", {}).get(art_num)
                if art_txt:
                    out.write(f"--- ARTÍCULO {art_num} ---\n{art_txt}\n\n")
    print(f"\n✓ Extractos normativos guardados en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
