"""
Pruebas del registro estatal perezoso (`_RegistroEstatalLazy`) y caché SQLite de `busqueda_universal`.
"""

import mcp_server


def test_registro_estatal_lazy_no_instancia_hasta_acceder():
    reg = mcp_server._RegistroEstatalLazy()
    # Verificar que es un atributo válido sin disparar importación previa de conectores no pedidos
    assert isinstance(mcp_server._registro_estatal(), mcp_server._RegistroEstatalLazy)
    assert reg.db_path.endswith("openlegal_cache.db")


def test_registro_estatal_cache_sqlite_ida_y_vuelta(tmp_path):
    reg = mcp_server._RegistroEstatalLazy(db_path=str(tmp_path / "cache.db"))
    payload = {"query": "ley karin", "dt": [{"titulo": "Dictamen N° 1"}]}
    assert reg._get_cached("all", "ley karin") is None
    reg._set_cached("all", "ley karin", payload)
    assert reg._get_cached("all", "ley karin") == payload


def test_busqueda_universal_registro_lazy(monkeypatch):
    class _RegMock:
        def search_all(self, consulta):
            return {"query": consulta, "dt": [{"titulo": "ORD. 123", "url": "https://dt.gob.cl/123"}]}

    monkeypatch.setattr(mcp_server, "_registro_estatal", lambda: _RegMock())
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", lambda q, lim=3: {"resultados": [], "citas": []})

    res = mcp_server.handle_tool_call("busqueda_universal", {"consulta": "Ley Karin"})
    assert res["resultados"]["query"] == "Ley Karin"
    assert res["citas"][0]["formato"] == "[DT - ORD. 123]"
