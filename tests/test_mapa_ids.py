"""Gramática canónica de normas y roles (`citas_legales`) e IDs del mapa del corpus (`mapa_corpus.ids`).

Los casos unitarios fijan las trampas medidas en el dataset real (CPC≠CC, CPP≠CP, LOC≠CPR,
DFL≠ley, puntos de miles, sufijos, numerales de la CPR, roles sin contexto). El conjunto de
referencia anotado (`tests/fixtures/mapa/referencia_*.jsonl`, fragmentos literales del dataset)
mide precisión y exhaustividad con un piso: la gramática puede mejorar, no empeorar.
"""

import json
from pathlib import Path

import pytest

import citas_legales as c
from mapa_corpus import ids, texto

REFERENCIA = sorted((Path(__file__).parent / "fixtures" / "mapa").glob("referencia_*.jsonl"))


def normas(t):
    return [i for i, _ in c.normas_canonicas(t)]


def roles(t):
    return [i for i, _ in c.roles_canonicos(t)]


# ── Normas ────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("frase, esperado", [
    # El nombre más largo gana: Procedimiento Civil no es el Código Civil, Procesal Penal no es el Penal.
    ("el artículo 170 del Código de Procedimiento Civil", ["norma:cpc:170"]),
    ("el artículo 373 del Código Procesal Penal", ["norma:cpp:373"]),
    ("el artículo 1545 del Código Civil", ["norma:cc:1545"]),
    ("el artículo 391 del Código Penal", ["norma:cp:391"]),
    ("el artículo 500 del Código de Procedimiento Penal", ["norma:cpp1906:500"]),
    # Puntos de miles en artículos y leyes; «art.» abreviado.
    ("art. 1.545 del Código Civil", ["norma:cc:1545"]),
    ("la Ley N° 4.808 sobre Registro Civil", ["norma:ley-4808"]),
    ("Ley N.° 19.300", ["norma:ley-19300"]),
    ("Ley 18,216", ["norma:ley-18216"]),
    # Sufijos latinos y artículos transitorios.
    ("el artículo 372 ter del Código Penal", ["norma:cp:372ter"]),
    ("ARTÍCULO 196 TER, INCISO PRIMERO, DE LA LEY N° 18.290", ["norma:ley-18290:196ter"]),
    ("el art. 1º transitorio de la Ley N° 20.600", ["norma:ley-20600:1-transitorio"]),
    ("la disposición segunda transitoria de la Constitución", ["norma:cpr:2-transitorio"]),
    # Numerales de la CPR, en cifra, lista, palabra o antes del artículo.
    ("el artículo 19 N° 3 de la Constitución Política de la República", ["norma:cpr:19:n3"]),
    ("artículos 19, N°s 3° (inciso sexto) y 2° de la Constitución", ["norma:cpr:19:n2", "norma:cpr:19:n3"]),
    ("el inciso sexto, del numeral tercero, del artículo 19 de la Carta Fundamental", ["norma:cpr:19:n3"]),
    ("artículo 19, literal a) del numeral 7° de la Constitución", ["norma:cpr:19:n7"]),
    ("art. 19 N° 24 CPR", ["norma:cpr:19:n24"]),
    # Fórmula final de los fallos de inaplicabilidad del TC.
    ("lo preceptuado en el artículo 93, incisos primero, N° 6°, y decimoprimero, y en las demás "
     "disposiciones citadas y pertinentes de la Constitución Política de la República", ["norma:cpr:93:n6"]),
    # Listas, con cuerpos distintos y con una cláusula descriptiva en medio.
    ("arts. 1545, 1546 y 1560 del Código Civil", ["norma:cc:1545", "norma:cc:1546", "norma:cc:1560"]),
    ("artículo 3 de la Ley N° 19.880 y 19 de la Constitución", ["norma:cpr:19", "norma:ley-19880:3"]),
    ("ARTÍCULOS 19, INCISOS DÉCIMO, UNDÉCIMO, Y DECIMOTERCERO, DEL D.L. N° 3.500, QUE ESTABLECE NUEVO "
     "SISTEMA DE PENSIONES, Y 22, INCISO TERCERO, DE LA LEY N° 17.322", ["norma:dl-3500:19", "norma:ley-17322:22"]),
    ("ARTÍCULOS 4°, INCISO PRIMERO, SEGUNDA FRASE, DE LA LEY N° 19.886", ["norma:ley-19886:4"]),
    # Letras: «5 A» es otro artículo; «331 a, 331 b» son literales del mismo artículo 331.
    ("artículo 5 A sustitutivo de la Ley N° 17.798", ["norma:ley-17798:5a"]),
    ("los artículos 331 a, 331 b, y 332 del Código Procesal Penal", ["norma:cpp:331", "norma:cpp:332"]),
    ("del artículo 373, letra a), Código Procesal Penal", ["norma:cpp:373"]),
    # El cuerpo antes del artículo.
    ("Código Civil, artículo 1545", ["norma:cc:1545"]),
    ("la Carta Fundamental garantiza en su artículo 19 N°16", ["norma:cpr:19:n16"]),
    ("el Código de Comercio lo regulaba con limitaciones, en sus artículos 617 y 804",
     ["norma:ccom:617", "norma:ccom:804"]),
    # Artículo implícito, solo con un código, la CPR o una sigla inmediatamente después.
    ("en el 19 N°3 de nuestra Carta Fundamental", ["norma:cpr:19:n3"]),
    ("la aplicación del 146 del COT cede frente al fuero", ["norma:cot:146"]),
    ("la reforma del 2005 de la Constitución", ["norma:cpr"]),
    # DFL y DL no son leyes.
    ("el DFL N° 1 de 2005", ["norma:dfl-1"]),
    ("el Decreto Ley N° 2.695", ["norma:dl-2695"]),
    ("D.L. 3.500", ["norma:dl-3500"]),
    # Siglas distintivas; LOSMA es un solo cuerpo.
    ("según la LOSMA", ["norma:losma"]),
    ("el artículo 35 de la LOSMA", ["norma:losma:35"]),
    ("la Ley de Bases Generales del Medio Ambiente", ["norma:ley-19300"]),
    # Reformulación entre paréntesis: una sola mención.
    ("el art. 1º transitorio de la Ley Orgánica Constitucional de Concesiones Mineras (Ley N° 18.097, 1982)",
     ["norma:ley-18097:1-transitorio"]),
    # Llamadas al pie pegadas y timbres de foja del TC.
    ("con la Ley General de Educación Nº 20.370,4 con", ["norma:ley-20370"]),
    ("el Código de Procedimiento Penal24.", ["norma:cpp1906"]),
    ("la misma Ley N° 0000177 CIENTO SETENTA Y SIETE 17.322 y", ["norma:ley-17322"]),
    # Tras «artículos» (plural), un N° singular rige solo a su artículo: el resto son artículos.
    ("en los artículos 17 Nº 4 y 32 de la Ley Nº 20.600", ["norma:ley-20600:17:n4", "norma:ley-20600:32"]),
    ("los Arts. 17 N° 2, 18 Nº2, 20 y 24 de la Ley Nº 20.600",
     ["norma:ley-20600:17:n2", "norma:ley-20600:18:n2", "norma:ley-20600:20", "norma:ley-20600:24"]),
    ("el artículo 19 N° 2, 3 y 24 de la Constitución", ["norma:cpr:19:n2", "norma:cpr:19:n24", "norma:cpr:19:n3"]),
    # Salvo en el artículo 19 de la CPR (26 numerales): lo que pasa de 26 es otro artículo.
    ("los artículos 19 N° 2 y 3 de la CPR", ["norma:cpr:19:n2", "norma:cpr:19:n3"]),
    ("los artículos 19 N° 3 y 76 de la Carta Fundamental", ["norma:cpr:19:n3", "norma:cpr:76"]),
    ("los artículos 19 N° 3, 19 N° 7 y 19 N° 24 de la Constitución",
     ["norma:cpr:19:n24", "norma:cpr:19:n3", "norma:cpr:19:n7"]),
    # El numeral antes del artículo, abreviado o en lista.
    ("el N° 7 del art. 434 del Código de Procedimiento Civil", ["norma:cpc:434:n7"]),
    ("según las reglas de los números 1 y 2 del artículo 61 del Código Penal", ["norma:cp:61:n1", "norma:cp:61:n2"]),
    # OCR de los fallos ambientales: «1a» por «la».
    ("los articulos 17 N° 8, 18 N° 7 de 1a Ley N° 20.600", ["norma:ley-20600:17:n8", "norma:ley-20600:18:n7"]),
    # El artículo seguido de un cuerpo que la gramática no reconoce no hereda el anterior.
    ("del artículo 25 ter de la Ley N° 19.300, artículo 73 y artículo 4° transitorio del Decreto Supremo N° 40",
     ["norma:ley-19300:25ter"]),
])
def test_normas_canonicas(frase, esperado):
    assert normas(frase) == esperado


@pytest.mark.parametrize("frase", [
    "la ley 20 años después",                                    # sin N° y < 3 dígitos
    "el principio de igualdad ante la ley",
    "la Constitución española de 1978",
    "la Comisión de Constitución del Senado",
    "la constitución de la servidumbre",                         # sustantivo común
    "Mensaje N° 1167-362 del Proyecto de Ley iniciado por el Ejecutivo",
    "el CC del contrato",                                        # sigla suelta no distintiva
    "el artículo 1545",                                          # sin cuerpo explícito
    # Derecho comparado: no son los códigos ni la Constitución de Chile.
    "los artículos 253 y 254 del Código Penal español",
    "los artículos 322 a 326 del Código Penal belga de 1867",
    "el artículo 1382 del Código Civil francés",
    "el Código Civil y Comercial de la Nación",
    "la Constitución Política de la República de Guatemala",
])
def test_normas_negativas(frase):
    assert normas(frase) == []


def test_ley_organica_constitucional_no_es_la_cpr():
    assert "norma:cpr" not in normas("la Ley Orgánica Constitucional del Tribunal Constitucional")
    assert normas("la Ley Orgánica Constitucional del Tribunal Constitucional") == ["norma:ley-17997"]


def test_frecuencia_y_orden():
    resultado = c.normas_canonicas("art. 1545 del Código Civil; art. 1545 del Código Civil y la Ley N° 19.300")
    assert resultado == [("norma:cc:1545", 2), ("norma:ley-19300", 1)]


@pytest.mark.parametrize("norma_id", [
    "norma:cc:1545", "norma:cpr:19:n3", "norma:ley-19300:11bis", "norma:dl-3500:19",
    "norma:dfl-1", "norma:losma:35", "norma:cpr:2-transitorio", "norma:ley-20600:1-transitorio",
])
def test_etiqueta_norma_ida_y_vuelta(norma_id):
    assert normas(c.etiqueta_norma(norma_id)) == [norma_id]


def test_detectar_normas_no_cambia():
    """La API previa sigue igual: misma forma de resultado que usan los conectores."""
    r = c.detectar_normas("conforme al artículo 1545 del Código Civil y la Ley 19.300")
    assert isinstance(r, list) and r and all(isinstance(x, dict) for x in r)


# ── Roles ─────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("frase, esperado", [
    ("la Excma. Corte Suprema, en causa Rol N° 29.635-2018", ["cs:29635-2018"]),
    ("sentencia de la Corte Suprema Rol 10641-2024", ["cs:10641-2024"]),
    ("STC Rol N° 2402", ["tc:2402"]),
    ("en las STC Roles N°s 2995, 3053 y 3198", ["tc:2995", "tc:3053", "tc:3198"]),
    ("en la causa 10822-21-INA", ["tc:10822"]),
    ("jurisprudencia del Tribunal Constitucional en las sentencias Roles N°s 2673-14; 2957-16; y 9406-20",
     ["tc:2673", "tc:2957", "tc:9406"]),
    ("R-32-2020 del Segundo Tribunal Ambiental", ["ta:2ta:r-32-2020"]),
    ("las causas R-21-2021, R-35-2021 y D-29-2020 del Tercer Tribunal Ambiental",
     ["ta:3ta:d-29-2020", "ta:3ta:r-21-2021", "ta:3ta:r-35-2021"]),
])
def test_roles_canonicos(frase, esperado):
    assert roles(frase) == esperado


@pytest.mark.parametrize("frase", [
    "la Corte de Apelaciones de Santiago, Rol N° 1234-2023",    # C.A., no CS
    "RIT O-123-2023 del Juzgado de Letras del Trabajo",
    "Rol N° 1234-2023",                                         # sin contexto: ambiguo
    "en el período 2019-2023",
])
def test_roles_sin_contexto_cs(frase):
    assert not [r for r in roles(frase) if r.startswith("cs:")]


@pytest.mark.parametrize("texto_rol, tribunal, esperado", [
    ("Rol N° 29.635-2018", None, "cs:29635-2018"),
    ("10822-21-INA", None, "tc:10822"),
    ("R-32-2020", "2ta", "ta:2ta:r-32-2020"),
    ("R-32-2020", None, None),
    ("2402", "tc", "tc:2402"),
    ("2402", None, None),
])
def test_rol_canonico(texto_rol, tribunal, esperado):
    assert c.rol_canonico(texto_rol, tribunal) == esperado


@pytest.mark.parametrize("consulta, esperado", [
    ("Rol 1234-2023", ["cs:1234-2023"]),
    ("10641-2024", ["cs:10641-2024"]),
    ("STC 2402", ["tc:2402"]),
    ("art. 1545 del Código Civil", ["norma:cc:1545"]),
    ("Ley 19.300", ["norma:ley-19300"]),
    ("2019-2023", []),
    ("Corte de Apelaciones 1234-2023", []),
    ("¿qué es el contrato de arrendamiento?", []),
])
def test_resolver_consulta(consulta, esperado):
    assert c.resolver_consulta(consulta) == esperado


# ── IDs del mapa ──────────────────────────────────────────────────────────────────────────────
def test_autor_id_independiente_del_orden():
    assert ids.autor_id("Guzmán Brito, Alejandro") == ids.autor_id("Alejandro Guzmán Brito")
    assert ids.autor_id("Comité Editorial") is None
    assert ids.autor_id("Revista Chilena de Derecho") is None


@pytest.mark.parametrize("bruto, esperado", [
    ("Guzmán Brito, Alejandro", ["Guzmán Brito, Alejandro"]),
    ("Ana Pérez Soto; Juan Díaz y María Rojas", ["Ana Pérez Soto", "Juan Díaz", "María Rojas"]),
    ("Mella Cabrera,Patricio Eleodoro, Domínguez Montoya,Álvaro Eduardo",
     ["Mella Cabrera,Patricio Eleodoro", "Domínguez Montoya,Álvaro Eduardo"]),
    ("Comité Editorial", []),
])
def test_separar_autores(bruto, esperado):
    assert ids.separar_autores(bruto) == esperado


def test_ministros_y_salas():
    assert ids.ministros("MARÍA GAJARDO HARBOE,Sr. Juan Pérez") == ["ministro:juan-perez",
                                                                     "ministro:maria-gajardo-harboe"]
    assert ids.ministros("—") == []
    assert ids.sala_id("SEGUNDA, PENAL") == "sala:cs-2"
    assert ids.sala_id("Corte Suprema — TERCERA, CONSTITUCIONAL") == "sala:cs-3"
    assert ids.tribunal_id("C.A. de Valparaíso") == "tribunal:ca-valparaiso"
    assert ids.recurso_id("(CRIMEN) APELACIÓN AMPARO") == "recurso:crimen-apelacion-amparo"


def test_ids_de_roles_y_rutas():
    assert ids.id_cs("Rol N° 10.641-2024") == "cs:10641-2024"
    assert ids.id_tc("STC 2402") == "tc:2402"
    assert ids.id_ta("2TA", "R-32-2020") == "ta:2ta:r-32-2020"
    assert ids.id_ruta("doc", "doctrina/revistas/rchd/1979/x.md", "doctrina/") == "doc:revistas/rchd/1979/x"


@pytest.mark.parametrize("bruto, esperado", [
    ("2024-03-04", "2024-03-04"),
    ("4-3-2024", "2024-03-04"),
    ("04/03/2024", "2024-03-04"),
    ("4 de marzo de 2024", "2024-03-04"),
    ("Santiago, 1° de septiembre del 2020", "2020-09-01"),
    ("—", None),
    ("31-02-2024 y luego 1-3-2024", "2024-03-01"),
])
def test_fecha_iso(bruto, esperado):
    assert texto.fecha_iso(bruto) == esperado


def test_front_matter_y_vinetas():
    meta, cuerpo = texto.leer_front_matter('---\ntitulo: "X"\nautores: ["A B", "C D"]\nnormas:\n  - Ley 19.300\n---\ncuerpo')
    assert meta["autores"] == ["A B", "C D"] and meta["normas"] == ["Ley 19.300"] and cuerpo == "cuerpo"
    campos = texto.leer_vinetas("- **Rol:** 10641-2024 · **Fecha:** 2026-03-04\n- **Sala:** SEGUNDA")
    assert campos == {"rol": "10641-2024", "fecha": "2026-03-04", "sala": "SEGUNDA"}


# ── Conjunto de referencia ────────────────────────────────────────────────────────────────────
# Pisos con margen bajo lo medido al fijar la gramática (precisión 0,99 / exhaustividad 0,99 en
# revistas+TC): bajar de aquí es una regresión de la gramática, no ruido.
PISO_PRECISION = 0.95
PISO_EXHAUSTIVIDAD = 0.93


@pytest.mark.skipif(not REFERENCIA, reason="sin conjunto de referencia")
@pytest.mark.parametrize("ruta", REFERENCIA, ids=lambda p: p.stem)
def test_conjunto_de_referencia(ruta):
    tp = fp = fn = 0
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        caso = json.loads(linea)
        esperado = set(caso.get("normas", [])) | set(caso.get("roles", []))
        normas_obt, roles_obt = c.normas_y_roles(caso["texto"])
        obtenido = {i for i, _ in normas_obt} | {i for i, _ in roles_obt}
        tp += len(esperado & obtenido)
        fp += len(obtenido - esperado)
        fn += len(esperado - obtenido)
    precision = tp / (tp + fp) if tp + fp else 1.0
    exhaustividad = tp / (tp + fn) if tp + fn else 1.0
    assert precision >= PISO_PRECISION, f"{ruta.stem}: precisión {precision:.3f} (tp={tp} fp={fp})"
    assert exhaustividad >= PISO_EXHAUSTIVIDAD, f"{ruta.stem}: exhaustividad {exhaustividad:.3f} (fn={fn})"


# ── Conjuntos de evaluación (fallos ambientales y doctrina) ───────────────────────────────────
# Anotados aparte de los de referencia y medidos sin ajustar la gramática a ellos (precisión
# 0,81 / exhaustividad 0,64); después se corrigieron los errores de fondo que mostraron (N° singular
# en listas de artículos, códigos extranjeros, «N° 7 del art. 434»). La precisión es estricta:
# no cuenta como error el cuerpo solo («Ley N° 19.300») cuando la anotación pedía sus artículos y
# la lista no se pudo atribuir: es una cita menos precisa, no una falsa. Medido: 0,98 y 1,00 de
# precisión estricta; 0,667 y 0,726 de exhaustividad.
EVALUACION = sorted((Path(__file__).parent / "fixtures" / "mapa").glob("evaluacion_*.jsonl"))
PISO_PRECISION_ESTRICTA = 0.95
PISO_EXHAUSTIVIDAD_EVALUACION = 0.64


@pytest.mark.skipif(not EVALUACION, reason="sin conjuntos de evaluación")
@pytest.mark.parametrize("ruta", EVALUACION, ids=lambda p: p.stem)
def test_conjunto_de_evaluacion(ruta):
    tp = fp = fn = 0
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        caso = json.loads(linea)
        esperado = set(caso.get("normas", [])) | set(caso.get("roles", []))
        normas_obt, roles_obt = c.normas_y_roles(caso["texto"])
        obtenido = {i for i, _ in normas_obt} | {i for i, _ in roles_obt}
        tp += len(esperado & obtenido)
        fp += sum(1 for i in obtenido - esperado if not any(e.startswith(i + ":") for e in esperado))
        fn += len(esperado - obtenido)
    precision = tp / (tp + fp) if tp + fp else 1.0
    exhaustividad = tp / (tp + fn) if tp + fn else 1.0
    assert precision >= PISO_PRECISION_ESTRICTA, f"{ruta.stem}: precisión {precision:.3f} (tp={tp} fp={fp})"
    assert exhaustividad >= PISO_EXHAUSTIVIDAD_EVALUACION, f"{ruta.stem}: exhaustividad {exhaustividad:.3f} (fn={fn})"
