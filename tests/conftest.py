"""Aislamiento de la suite respecto del mapa del corpus de Hugging Face.

Se fija en `pytest_configure`, antes de importar los módulos de prueba, para que ninguna prueba
lea la caché del usuario (`~/.openlegal/mapa`, `~/.cache/openlegal-mapa`) ni descargue el mapa: con
`OPENLEGAL_MAPA=off` el producto se comporta como sin mapa. Las pruebas del mapa lo activan con
sus propios fixtures, sobre directorios temporales y una API de HF falsa.
"""

import os
import shutil
import tempfile

import pytest

_DIRECTORIO = None


def pytest_configure(config):
    global _DIRECTORIO
    _DIRECTORIO = tempfile.mkdtemp(prefix="openlegal-mapa-pruebas-")
    os.environ["OPENLEGAL_MAPA"] = "off"
    os.environ["OPENLEGAL_MAPA_DIR"] = os.path.join(_DIRECTORIO, "mapa")
    os.environ["OPENLEGAL_MAPA_FUENTES"] = os.path.join(_DIRECTORIO, "fuentes")
    os.environ.pop("OPENLEGAL_MAPA_LOCAL", None)


def pytest_unconfigure(config):
    if _DIRECTORIO:
        shutil.rmtree(_DIRECTORIO, ignore_errors=True)


# ── Mapa diminuto para las pruebas de integración ─────────────────────────────────────────────
FILAS_MAPA_MINIMO = [
    {"id": "cs:10641-2024", "col": "cs", "ruta": "jurisprudencia_cs/2024/03/10641-2024.md", "blob": "b" * 40,
     "bytes": 800, "fecha": "2026-03-04", "era": 2024, "rol": "10641-2024", "titulo": "PÉREZ CON FISCO DE CHILE",
     "sala": "sala:cs-3", "recurso": "recurso:proteccion", "recurso_txt": "PROTECCIÓN",
     "resultado": "CONFIRMA", "ministros": ["ministro:maria-gajardo-harboe"],
     "ministros_txt": ["MARÍA GAJARDO HARBOE"]},
    {"id": "cs:1234-2023", "col": "cs", "ruta": "jurisprudencia_cs/2023/05/1234-2023.md", "blob": "c" * 40,
     "bytes": 790, "fecha": "2023-05-10", "era": 2023, "rol": "1234-2023", "titulo": "SOTO CON BANCO",
     "sala": "sala:cs-1", "recurso": "recurso:casacion-en-el-fondo", "recurso_txt": "CASACIÓN FONDO",
     "ministros": ["ministro:maria-gajardo-harboe"], "ministros_txt": ["MARÍA GAJARDO HARBOE"]},
    {"id": "tc:2402", "col": "tc", "ruta": "jurisprudencia_tc/2402-12-INA.md", "blob": "d" * 40, "bytes": 9000,
     "fecha": "2013-05-02", "titulo": "Requerimiento de inaplicabilidad por inconstitucionalidad",
     "resumen": "La indemnización de perjuicios por responsabilidad extracontractual del Estado.",
     "normas": [["norma:cc", 2], ["norma:cc:2314", 3], ["norma:cpr:19:n3", 1]], "cita_cs": ["cs:10641-2024"]},
    {"id": "ta:3ta:r-21-2021", "col": "ta", "ruta": "jurisprudencia_ambiental/3TA/R-21-2021.md", "blob": "e" * 40,
     "bytes": 7000, "fecha": "2021-11-02", "titulo": "Reclamación contra la SMA", "tribunal": "organo:3ta",
     "normas": [["norma:losma:35", 1]], "alias": ["ta:3ta:r-35-2021"],
     "ministros": ["ministro:javier-millar-silva"], "ministros_txt": ["JAVIER MILLAR SILVA"]},
    {"id": "doc:revistas/rchd/2020/responsabilidad", "col": "doc", "sub": "revistas", "revista": "revista:rchd",
     "revista_txt": "Revista Chilena de Derecho",
     "ruta": "doctrina/revistas/rchd/2020/responsabilidad.md", "blob": "f" * 40, "bytes": 5000,
     "titulo": "La responsabilidad extracontractual en la jurisprudencia", "tiene_texto": True,
     "resumen": "Estudio sobre el artículo 2314 del Código Civil y el daño moral.",
     "autores": ["autor:barros_bourie_enrique"], "autores_txt": ["Enrique Barros Bourie"],
     "cita_oficial": "Barros Bourie, Enrique (2020). Revista Chilena de Derecho, 47(1).",
     "normas": [["norma:cc:2314", 2]], "cita_cs": ["cs:1234-2023"]},
]


@pytest.fixture
def fabrica_mapa(tmp_path):
    """Arma en disco un mapa con la forma exacta que publica el constructor (entradas, entidades,
    capa del grafo, alias, comunidades y estado.json), a partir de filas ya extraídas."""
    from mapa_corpus import constructor, grafo, particiones

    def fabricar(filas=None, curado=None, destino=None):
        filas = [dict(f) for f in (filas or FILAS_MAPA_MINIMO)]
        curado = curado or {"nodes": [], "edges": []}
        destino = destino or (tmp_path / "mapa_minimo")
        ents = constructor.entidades(filas)
        capa = grafo.construir_capa(filas, ents, grafo.vias_de(curado))
        alias, puentes = grafo.alias_curados(curado, capa, filas)
        comunidad = grafo.comunidades(curado, capa, alias, puentes)
        partes = {}
        for f in filas:
            partes.setdefault(particiones.particion_de(f["ruta"]), []).append(f)
        for nombre, filas_ent in ents.items():
            partes[f"entidades/{nombre}"] = filas_ent
        partes.update(grafo.exportar(capa, alias, puentes, comunidad))
        estado = {"esquema": 1, "repo": "pablobenavidesj/doctrina-jurisprudencia-chile", "ruta": "data/mapa",
                  "sha_fuente": "9" * 40, "fecha_fuente": "2026-10-01T13:03:51.000Z",
                  "conteos": {"entradas": len(filas)}, "calidad": {}}
        constructor.escribir({"particiones": partes, "estado": estado}, str(destino))
        return destino

    return fabricar


@pytest.fixture
def mapa_activo(fabrica_mapa, tmp_path, monkeypatch):
    """El cliente compartido del mapa, ACTIVO sobre el mapa diminuto (sin red): para probar las
    herramientas «con mapa». Al terminar, el cliente vuelve a quedar apagado."""
    from mapa_corpus import cliente

    destino = fabrica_mapa()
    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    monkeypatch.setenv("OPENLEGAL_MAPA_LOCAL", str(destino))
    monkeypatch.setenv("OPENLEGAL_MAPA_DIR", str(tmp_path / "cache_mapa"))
    cliente.reiniciar_cliente()
    c = cliente.obtener_cliente()
    assert c.asegurar(bloquear=True, timeout=120), c.error
    yield c
    cliente.reiniciar_cliente()
