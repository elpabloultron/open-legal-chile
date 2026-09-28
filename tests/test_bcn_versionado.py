"""Con LeyChile intermitente, una lista de versiones vencida se usa cuando todavía puede responder.

El servicio Consulta/get_versiones falla seguido; antes, con la copia de la lista vencida en disco,
la consulta histórica igual se caía. Una lista de ayer sirve más que un error: la fecha pedida
decide más arriba si la lista alcanza (y si no, el error avisa que el servicio viene intermitente).
"""

import json
import os
import time

import pytest

from bcn_connector import BCNClient


def _cache_vencida(tmp_path, id_norma=1234):
    versiones = [{"@vigenteDesde": "2020-01-01", "@vigenteHasta": "2021-01-01"}]
    ruta = tmp_path / f"versiones_{id_norma}.json"
    ruta.write_text(json.dumps(versiones), encoding="utf-8")
    viejo = time.time() - 200_000
    os.utime(ruta, (viejo, viejo))
    return versiones


def test_lista_vencida_se_usa_si_el_servicio_falla(tmp_path, monkeypatch):
    cliente = BCNClient(cache_dir=str(tmp_path))
    _cache_vencida(tmp_path)

    def _sin_red(*a, **k):
        raise RuntimeError("sin red")
    monkeypatch.setattr(cliente, "_fetch_json_servicios", _sin_red)

    versiones = cliente._versiones_de(1234)   # no debe lanzar

    assert versiones and versiones[0]["@vigenteDesde"] == "2020-01-01"
    assert cliente._versiones_degradadas is True


def test_sin_copia_el_error_sigue_siendo_error(tmp_path, monkeypatch):
    cliente = BCNClient(cache_dir=str(tmp_path))

    def _sin_red(*a, **k):
        raise RuntimeError("sin red")
    monkeypatch.setattr(cliente, "_fetch_json_servicios", _sin_red)

    with pytest.raises(RuntimeError):
        cliente._versiones_de(1234)
