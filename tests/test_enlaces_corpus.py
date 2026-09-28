"""Candado de los enlaces «Véase también» del corpus.

Dos garantías: (1) ningún enlace relativo roto; (2) el bloque es **aditivo** —
el cuerpo original no cambió, y eso se prueba con el sha256 que guarda el marcador.
"""
import hashlib
import pathlib
import re
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MARCADOR = "<!-- enlaces:generado"

CARPETAS = ("doctrina", "corpus_guias_aj", "jurisprudencia_tc", "publicaciones_ambientales",
            "jurisprudencia_cs", "jurisprudencia_ambiental")


def _relativos(texto: str) -> list:
    """Enlaces markdown a un destino relativo (sin URL, sin ancla, sin espacios), ya decodificados."""
    return [urllib.parse.unquote(d) for d in re.findall(r"\]\((?!https?:)([^)#\s]+)", texto)]


def _hashear(texto: str) -> str:
    return hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()


def test_todas_las_obras_tienen_su_bloque_de_enlaces():
    sin_bloque = [p for p in (RAIZ / "doctrina").rglob("*.md")
                  if p.name != "README.md" and MARCADOR not in p.read_text(encoding="utf-8")]
    sin_bloque += [p for p in (RAIZ / "corpus_guias_aj").rglob("*.md")
                   if p.name != "README.md" and MARCADOR not in p.read_text(encoding="utf-8")]
    assert not sin_bloque, f"{len(sin_bloque)} obras sin enlaces: {sin_bloque[:5]}"


def test_no_hay_enlaces_relativos_rotos():
    """Los enlaces que generamos (bloques y índices) apuntan a archivos que existen.

    Sólo se revisa lo generado: el texto legal trae secuencias tipo «](iii)» que no son
    enlaces, y mezclar eso en el candado lo volvería un falso positivo permanente.
    """
    rotos = []
    for carpeta in ("doctrina", "corpus_guias_aj"):
        for p in (RAIZ / carpeta).rglob("*.md"):
            texto = p.read_text(encoding="utf-8")
            corte = texto.find(MARCADOR)
            if corte < 0:
                continue
            for destino in _relativos(texto[corte:]):
                if not (p.parent / destino).resolve().exists():
                    rotos.append(f"{p.relative_to(RAIZ)} → {destino}")

    generados = list((RAIZ / "jurisprudencia_cs").glob("INDICE_*.md"))
    generados.append(RAIZ / "jurisprudencia_cs" / "README.md")
    for p in generados:
        if not p.exists():
            continue
        for destino in _relativos(p.read_text(encoding="utf-8")):
            if not (p.parent / destino).resolve().exists():
                rotos.append(f"{p.relative_to(RAIZ)} → {destino}")
    assert not rotos, rotos[:10]


def test_el_cuerpo_no_cambio():
    """El sha256 del marcador coincide con el contenido que está arriba de él."""
    fallos = []
    for carpeta in CARPETAS:
        for p in (RAIZ / carpeta).rglob("*.md"):
            texto = p.read_text(encoding="utf-8")
            corte = texto.find(MARCADOR)
            if corte < 0:
                continue
            linea = texto[corte:].splitlines()[0]
            esperado = re.search(r"sha256:([0-9a-f]{64})", linea)
            if not esperado:
                fallos.append(f"{p.relative_to(RAIZ)}: marcador sin sha256")
                continue
            if _hashear(texto[:corte]) != esperado.group(1):
                fallos.append(f"{p.relative_to(RAIZ)}: el cuerpo cambió después de generar los enlaces")
    assert not fallos, fallos[:10]


def test_el_bloque_es_aditivo_en_un_ejemplo(tmp_path):
    """Generar el bloque sobre un archivo de prueba no toca ni una línea del original."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "enlazar_corpus", RAIZ / "scripts" / "enlazar_corpus.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    original = "# Obra de prueba\n\nTexto original del autor.\n\n## Sección\n\nMás texto.\n"
    archivo = tmp_path / "obra.md"
    archivo.write_text(original, encoding="utf-8")

    mod.aplicar_bloque(archivo, mod.bloque_para(archivo, [], [], {}))
    texto = archivo.read_text(encoding="utf-8")
    assert texto.startswith(original), "no se tocó nada del original"
    assert MARCADOR in texto and "## Véase también" in texto

    cuerpo, linea = texto.split(MARCADOR, 1)
    hash_en_marcador = re.search(r"sha256:([0-9a-f]{64})", linea)
    assert hash_en_marcador
    assert _hashear(cuerpo) == hash_en_marcador.group(1)

    # Reaplicar (idempotencia): no se duplica el bloque ni cambia el cuerpo
    mod.aplicar_bloque(archivo, mod.bloque_para(archivo, [], [], {}))
    texto2 = archivo.read_text(encoding="utf-8")
    assert texto2.count(MARCADOR) == 1
    assert texto2.startswith(original)

def test_no_revienta_si_el_archivo_vive_en_otro_disco(tmp_path, monkeypatch):
    """Windows real: D: vs C: hacen estallar os.path.relpath. El bloque debe caer a ruta absoluta."""
    import importlib.util
    import os as _os

    spec = importlib.util.spec_from_file_location(
        "enlazar_corpus", RAIZ / "scripts" / "enlazar_corpus.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def relpath_simulado(path, start=None):
        raise ValueError("path is on mount 'D:', start on mount 'C:'")

    monkeypatch.setattr(_os.path, "relpath", relpath_simulado)
    archivo = tmp_path / "obra.md"
    archivo.write_text("# Obra\n\nTexto.\n", encoding="utf-8")
    mod.aplicar_bloque(archivo, mod.bloque_para(archivo, [], [], {}))
    texto = archivo.read_text(encoding="utf-8")
    assert MARCADOR in texto and "## Véase también" in texto
    assert "Publicado en Hugging Face" in texto
