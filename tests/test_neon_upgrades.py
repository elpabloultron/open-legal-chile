"""Pruebas unitarias e integración para las mejoras End-to-End (Neon):
1. Perfil MCP `router` + `descubrir_herramientas` + `invocar_herramienta` (-85 % MCP Tools Tax).
2. Anonimizador reversible Ley N.° 21.719 (`privacidad_anonimizar_documento`).
3. Verificador post-redacción de citas y Common Law (`verificar_citas_escrito`).
4. Diff intertemporal de leyes BCN (`bcn_comparar_versiones`).
5. Motor vectorial con soporte `sqlite-vec` (`vec0`) + `fastembed` (`vector_engine.py`).
6. Hook opcional IBM Docling (`forensic_ocr.py`).
7. Modo Goldfish real con LLM externo en `critique.py` + degradación honesta CNE.
"""

from __future__ import annotations

import json
import unittest.mock as mock

import mcp_server


def test_perfil_router_reduce_drasticamente_tamano_esquema():
    full_json = json.dumps(mcp_server.TOOLS, ensure_ascii=False)
    router_tools = mcp_server.get_active_tools("router")
    router_json = json.dumps(router_tools, ensure_ascii=False)

    assert len(router_tools) == 9
    assert len(router_json) < len(full_json) * 0.25, "el perfil router debe ahorrar >75 % de tokens"
    nombres = {t["name"] for t in router_tools}
    assert {"consulta_maestra", "cita_texto", "descubrir_herramientas", "invocar_herramienta"} <= nombres


def test_descubrir_e_invocar_herramienta_dinamicamente():
    desc = mcp_server.handle_tool_call("descubrir_herramientas", {"consulta": "estudio de títulos CBR hipoteca", "limite": 5})
    assert "herramientas" in desc
    nombres = [h["name"] for h in desc["herramientas"]]
    assert "cbr_estudio_titulos" in nombres
    assert all("inputSchema" in h for h in desc["herramientas"])

    inv = mcp_server.handle_tool_call(
        "invocar_herramienta",
        {"nombre": "rut_validar_chile", "argumentos": {"rut": "12.345.678-5"}},
    )
    assert inv["valido"] is True

    rec = mcp_server.handle_tool_call("invocar_herramienta", {"nombre": "invocar_herramienta"})
    assert "error" in rec


def test_privacidad_anonimizar_y_desanonimizar_reversible():
    original = (
        "Comparece don Juan Pérez González, RUT 12.345.678-5, domiciliado en "
        "Av. Providencia 1234, comuna de Providencia, correo juan.perez@estudio.cl, "
        "teléfono +56 9 8765 4321, titular de cuenta corriente N° 81500086581."
    )
    res = mcp_server.handle_tool_call("privacidad_anonimizar_documento", {"texto": original})
    anon = res["texto_anonimizado"]
    mapa = res["mapa_reversion"]

    assert "12.345.678-5" not in anon
    assert "juan.perez@estudio.cl" not in anon
    assert "8765 4321" not in anon
    assert "81500086581" not in anon
    assert "Juan Pérez González" not in anon
    assert res["total_reemplazos"] >= 5

    rest = mcp_server.handle_tool_call(
        "privacidad_anonimizar_documento",
        {"texto": anon, "accion": "desanonimizar", "mapa_reversion": mapa},
    )
    assert rest["texto_restaurado"] == original


def test_verificar_citas_escrito_atrapa_articulos_imposibles_y_common_law():
    borrador = (
        "EN LO PRINCIPAL: Demanda por punitive damages conforme al Art. 9999 del Código Civil "  # figura prohibida Common Law
        "y Art. 1545 del Código Civil, causa Rol C-1234-2025."
    )
    res = mcp_server.handle_tool_call("verificar_citas_escrito", {"texto": borrador, "consultar_bcn": False})
    assert res["estado"] == "OBSERVADO"
    assert "punitive damages" in res["common_law_prohibido"]  # verifica rechazo de Common Law prohibida
    assert any("9999" in x for x in res["articulos_imposibles"])
    assert any("C-1234-2025" in r for r in res["roles_detectados"])


def test_bcn_comparar_versiones_genera_diff_y_alerta_intertemporal(monkeypatch):
    monkeypatch.setattr(
        mcp_server.bcn,
        "get_codigo_historico",
        lambda cod, fecha, articulo=None: {
            "texto": "Art. 2. Las relaciones laborales deberán siempre fundarse en un trato compatible con la dignidad."
        },
    )
    monkeypatch.setattr(
        mcp_server.bcn,
        "get_codigo",
        lambda cod, articulo=None: {
            "texto": "Art. 2. Las relaciones laborales deberán siempre fundarse en un trato libre de violencia, compatible con la dignidad (Ley Karin).",
            "fechaVersion": "2024-08-01",
        },
    )
    res = mcp_server.handle_tool_call(
        "bcn_comparar_versiones",
        {"norma": "trabajo", "fecha_a": "2020-01-01", "articulo": "2"},
    )
    assert res["hubo_cambios"] is True
    assert "ALERTA INTERTEMPORAL" in res["alerta_intertemporal"]
    assert "Ley Karin" in res["diff_unificado"]


def test_vector_engine_usa_sqlite_vec_cuando_esta_instalado(tmp_path):
    import vector_engine

    db = str(tmp_path / "vec_test.db")
    eng = vector_engine.VectorLegalEngine(db_path=db, use_fastembed=False)
    n = eng.indexar_cuerpo_legal(
        "civil",
        {
            "1545": "Todo contrato legalmente celebrado es una ley para los contratantes.",
            "2314": "El que ha cometido un delito o cuasidelito que ha inferido daño a otro es obligado a la indemnización.",
        },
        "Código Civil",
    )
    assert n == 2
    hits = eng.buscar_hibrido("contrato ley contratantes", top_k=2)
    assert hits and hits[0]["articulo_id"] == "1545"
    if vector_engine.is_sqlite_vec_available():
        assert eng.usa_sqlite_vec is True
        v_hits = eng.buscar_vectorial("delito cuasidelito indemnización daño", top_k=2)
        assert v_hits and v_hits[0]["articulo_id"] == "2314"
        assert "sqlite-vec" in v_hits[0].get("motor_vectorial", "")


def test_critique_goldfish_externo_usa_goldfish_prompt():
    from critique import GOLDFISH_SYSTEM_PROMPT, LegalCritiqueEngine

    eng = LegalCritiqueEngine()
    with mock.patch.object(eng.chat_engine, "chat", return_value={"reply": "OK", "provider": "gemini", "model": "mock"}) as m_chat:
        res = eng.critique("Demanda de prueba", provider="gemini", modo="goldfish")
        assert res["modo"] == "goldfish"
        kwargs = m_chat.call_args.kwargs
        assert kwargs["system_prompt"] == GOLDFISH_SYSTEM_PROMPT


def test_cne_degradacion_honesta_sin_credenciales(monkeypatch):
    monkeypatch.setattr(mcp_server.cne, "get_capacidad_instalada", lambda: [])
    monkeypatch.setattr(mcp_server.cne, "get_proyectos_sea", lambda: [])
    monkeypatch.setattr(mcp_server.cne, "tiene_credenciales", lambda: False)
    res = mcp_server.handle_tool_call("cne_get_centrales_y_proyectos", {"region": "Atacama"})
    assert res["estado"] == "sin_credenciales"
    assert res.get("faltantes")


def test_forensic_ocr_docling_hook_degrada_limpio():
    from forensic_ocr import ForensicOCREngine

    eng = ForensicOCREngine()
    if not eng.is_docling_available():
        res = eng.extract_with_docling("inexistente.pdf")
        assert res["motor"] == "docling_no_disponible"
        assert "docling" in res["error"].lower()
