"""Rutas de las Actions: upload-artifact, download-artifact y cache rechazan «..».

La primera publicación del mapa construyó y validó todo (34 min) y murió al entregar el mapa al
job de publicación: la carpeta de trabajo era `${{ github.workspace }}/../mapa-trabajo`.
"""

import pathlib

import yaml

WORKFLOWS = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"
ACCIONES_CON_RUTA = ("actions/upload-artifact", "actions/download-artifact", "actions/cache")


def _cargar(nombre):
    return yaml.safe_load((WORKFLOWS / nombre).read_text(encoding="utf-8"))


def _envs(wf):
    yield "workflow", wf.get("env") or {}
    for nombre, job in (wf.get("jobs") or {}).items():
        yield nombre, job.get("env") or {}
        for paso in job.get("steps") or []:
            yield f"{nombre}/{paso.get('name') or paso.get('uses')}", paso.get("env") or {}


def test_ninguna_ruta_de_artefacto_ni_variable_usa_dos_puntos():
    malas = []
    for archivo in sorted(WORKFLOWS.glob("*.yml")):
        wf = _cargar(archivo.name)
        for donde, env in _envs(wf):
            malas += [f"{archivo.name}:{donde}:{k}" for k, v in env.items() if ".." in str(v)]
        for nombre, job in (wf.get("jobs") or {}).items():
            for paso in job.get("steps") or []:
                if str(paso.get("uses", "")).startswith(ACCIONES_CON_RUTA):
                    ruta = str((paso.get("with") or {}).get("path", ""))
                    if ".." in ruta:
                        malas.append(f"{archivo.name}:{nombre}:{paso['uses']}")
    assert not malas, malas


def test_cada_job_del_mapa_define_sus_carpetas_antes_de_usarlas():
    wf = _cargar("mapa-hf.yml")
    for nombre, job in wf["jobs"].items():
        if "TRABAJO" not in yaml.safe_dump(job["steps"]):
            continue
        primero = job["steps"][0].get("run", "")
        assert 'TRABAJO=$RUNNER_TEMP/' in primero, nombre
        assert 'OPENLEGAL_MAPA_FUENTES=$RUNNER_TEMP/' in primero, nombre
