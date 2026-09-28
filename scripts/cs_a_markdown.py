#!/usr/bin/env python3
"""Fichas de la Corte Suprema (JSONL) → un Markdown por sentencia, con su enlace oficial.

No inventa texto: la ficha trae metadatos y el enlace al buscador del Poder Judicial.
Los campos ausentes se escriben como «—». El texto íntegro de las CS exige sesión PJUD,
así que esta colección es un índice navegable, no el fallo completo.

Uso:
  python scripts/cs_a_markdown.py --muestra 20     # ensayo: 20 archivos
  python scripts/cs_a_markdown.py --indices        # todo + INDICE_<era>.md + README.md
  python scripts/cs_a_markdown.py --era 2026       # una sola era
Verificación: ls jurisprudencia_cs/2026 | wc -l    # 26.527
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Base pública del corpus en Hugging Face (el derivado no se versiona; el README lo enlaza ahí).
BASE_HF = "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main/jurisprudencia_cs"
ORIGEN_POR_DEFECTO = RAIZ / "data" / "jurisprudencia" / "cs_sentencias_2anios.jsonl"
DESTINO_POR_DEFECTO = RAIZ / "jurisprudencia_cs"

PLANTILLA = """# {caratula}

- **Tribunal:** {tribunal} — {sala}
- **Rol:** {rol} · **Era:** {era} · **Fecha:** {fecha}
- **Recurso:** {recurso}
- **Resultado:** {resultado}
- **Tribunal de origen:** {tribunal_origen}
- **Ministros:** {ministros}
- **Publicación:** {publicacion}
- **Fallo anonimizado:** {fallo_anonimizado}

> Ficha de jurisprudencia: la sentencia se consulta íntegra en el buscador del Poder Judicial.
> Este documento no reemplaza el texto oficial.

**Fuente oficial:** [{rol}]({link})

---
Cita: `[Hugging Face - jurisprudencia_cs/{ruta_rel}]`
"""

README = """# Jurisprudencia de la Corte Suprema (fichas)

Una ficha por sentencia, con metadatos y enlace oficial al buscador del Poder Judicial.
El texto íntegro de cada fallo exige sesión en PJUD, por lo que esta colección es un
**índice navegable** y citable: {total} fichas.

- Índice por era: {indices}
- Cita: `[Hugging Face - jurisprudencia_cs/<era>/<rol>.md]`
- Fuente: datos oficiales del buscador de jurisprudencia del Poder Judicial de Chile.
"""


def valor(dato: dict, campo: str) -> str:
    """Devuelve el campo como texto legible; los ausentes se marcan «—», nunca se inventan."""
    v = dato.get(campo)
    if v in (None, "", [], {}):
        return "—"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def nombre_archivo(rol: str) -> str:
    limpio = re.sub(r"[^0-9A-Za-z._-]+", "-", rol).strip("-.")
    return f"{limpio or 'sin-rol'}.md"


def ficha_a_markdown(dato: dict) -> tuple[str, pathlib.Path]:
    era = str(dato.get("era") or "sin-era")
    mes = "sin-fecha"
    fecha = str(dato.get("fecha") or "")
    coincidencia = re.match(r"\d{4}-(\d{2})", fecha)
    if coincidencia:
        mes = coincidencia.group(1)
    archivo = nombre_archivo(valor(dato, "rol"))
    texto = PLANTILLA.format(
        caratula=valor(dato, "caratula"), tribunal=valor(dato, "tribunal"),
        sala=valor(dato, "sala"), rol=valor(dato, "rol"), era=era,
        fecha=valor(dato, "fecha"), recurso=valor(dato, "recurso"),
        resultado=valor(dato, "resultado"), tribunal_origen=valor(dato, "tribunal_origen"),
        ministros=valor(dato, "ministros"), publicacion=valor(dato, "publicacion"),
        fallo_anonimizado=valor(dato, "fallo_anonimizado"),
        link=dato.get("link_detalle") or "https://juris.pjud.cl/",
        ruta_rel=f"{era}/{mes}/{archivo}")
    return texto, pathlib.Path(era) / mes / archivo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", type=pathlib.Path, default=ORIGEN_POR_DEFECTO)
    parser.add_argument("--destino", type=pathlib.Path, default=DESTINO_POR_DEFECTO)
    parser.add_argument("--muestra", type=int, default=0, help="convierte sólo N fichas (ensayo)")
    parser.add_argument("--era", type=str, default="", help="filtra por era")
    parser.add_argument("--indices", action="store_true",
                        help="además escribe INDICE_<era>.md y el README de la colección")
    args = parser.parse_args()

    escritos = 0
    duplicados = 0
    por_era: dict[str, list[str]] = {}
    vistas: set[pathlib.Path] = set()

    with args.origen.open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            dato = json.loads(linea)
            era = str(dato.get("era") or "sin-era")
            if args.era and era != args.era:
                continue
            texto, relativo = ficha_a_markdown(dato)
            destino = args.destino / relativo
            if destino in vistas:
                # rol repetido en la misma era: no se pisa, se desambigua de forma determinista
                duplicados += 1
                destino = destino.with_name(f"{destino.stem}-dup{duplicados}.md")
                relativo = relativo.with_name(destino.name)
            vistas.add(destino)
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8")
            escritos += 1
            por_era.setdefault(era, []).append(
                f"- [{valor(dato, 'caratula')}]({relativo.as_posix()}) · "
                f"{valor(dato, 'fecha')} · {valor(dato, 'resultado')}")
            if args.muestra and escritos >= args.muestra:
                break

    print(f"fichas escritas: {escritos} en {args.destino} · duplicadas desambiguadas: {duplicados}")

    if args.indices:
        eras = []
        for era, lineas in sorted(por_era.items(), reverse=True):
            indice = args.destino / f"INDICE_{era}.md"
            indice.write_text(
                f"# Índice — Corte Suprema, era {era}\n\n"
                f"{len(lineas)} fichas. Formato: carátula · fecha · resultado.\n\n"
                + "\n".join(lineas) + "\n", encoding="utf-8")
            # Los índices viven en Hugging Face (el corpus derivado no se versiona): el README los
            # enlaza por URL absoluta para que el enlace valga en el repositorio y en la web.
            eras.append(f"[{era}]({BASE_HF}/INDICE_{era}.md) ({len(lineas)})")
            print(f"  índice {indice.name}: {len(lineas)} entradas")
        readme = args.destino / "README.md"
        readme.write_text(README.format(total=escritos, indices=" · ".join(eras)), encoding="utf-8")
        print(f"  README escrito con {escritos} fichas")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
