"""Ingesta del Tribunal Constitucional: el documento oficial se pide por número de rol.

La cosecha anterior armaba el enlace con el id de la ficha (`extended/<id>`), que trae la causa
cuyo rol es ese número: las 965 sentencias del dataset quedaron con la cabecera de una causa y el
texto de otra. Sin red: la API, el PDF y Hugging Face se simulan.
"""

import pathlib
from types import SimpleNamespace

from scripts import cosechar_jurisprudencia_2anios as cosecha
from scripts import subir_tc_hf
from scripts import tc_pdfs_a_md as tc

FX = pathlib.Path(__file__).parent / "fixtures" / "mapa" / "delta"
FICHA_API = {"id": "13336", "codigo": "06a-INA", "folio": "15686", "fecha_sentencia": "2025-06-12 00:00:00",
             "template": {"nombre": "INA-STC"}, "detalle": []}


def test_la_ficha_apunta_al_documento_de_su_rol():
    reg = cosecha.tc_compacto(FICHA_API)
    assert reg["rol"] == "Rol N° 15686-06a-INA"
    assert reg["link_pdf"] == "https://buscador-backend.tcchile.cl/api/extended/15686/download"
    assert reg["ficha_id"] == "13336" and reg["folio"] == "15686"


def test_los_registros_viejos_rehacen_el_enlace_desde_el_rol():
    viejo = {"rol": "Rol N° 15686-06a-INA", "link_pdf": "https://buscador-backend.tcchile.cl/api/extended/13336/download"}
    assert tc.link_oficial(viejo).endswith("/extended/15686/download")


def test_el_documento_tiene_que_nombrar_su_rol():
    assert tc.corresponde("Sentencia\nRol 15.686-24 INA\nSantiago", 15686)
    assert tc.corresponde("Sentencia Rol 15.738-2024 EN EL PROCESO ROL N° 12-2024", 15738)
    assert tc.corresponde("Rol N° 15686-24-INA", 15686)
    assert not tc.corresponde("Comunica Resolución Rol N° 13.336-22-INA", 15686)   # el error de antes
    assert not tc.corresponde("Rol 115.686-24", 15686)
    assert not tc.corresponde("Rol 15.686-24", 0)


def test_un_pdf_de_otra_causa_no_se_escribe(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "DIR_MD", tmp_path)
    monkeypatch.setattr(tc, "DIR_PDF", tmp_path / "pdf")
    (tmp_path / "pdf").mkdir()
    pedidos = []

    def get(url, headers=None, timeout=None):
        pedidos.append(url)
        return SimpleNamespace(content=b"%PDF-1.4 falso", raise_for_status=lambda: None)

    monkeypatch.setattr(tc.requests, "get", get)
    monkeypatch.setattr(tc, "texto_completo", lambda pdf: ("Comunica Resolución Rol N° 13.336-22-INA. " * 20, "pdftotext"))
    reg = {"rol": "Rol N° 15686-06a-INA", "link_pdf": "https://buscador-backend.tcchile.cl/api/extended/13336/download"}
    _, estado = tc.procesar((0, reg))
    assert estado.startswith("error|15686-06a-INA|") and "no es de la causa" in estado
    assert pedidos == ["https://buscador-backend.tcchile.cl/api/extended/15686/download"]
    assert not (tmp_path / "15686-06a-INA.md").exists() and not (tmp_path / "pdf" / "15686-06a-INA.pdf").exists()

    monkeypatch.setattr(tc, "texto_completo", lambda pdf: ("Sentencia Rol 15.686-24 INA. VISTOS: " * 20, "pdftotext"))
    _, estado = tc.procesar((0, reg))
    assert estado.startswith("ok|15686-06a-INA|")
    md = (tmp_path / "15686-06a-INA.md").read_text(encoding="utf-8")
    assert "extended/15686/download" in md and "extended/13336" not in md


def _md_tc(rol, cuerpo, enlace=None, fecha="2025-06-12"):
    return (f"# INA-STC — Rol N° {rol}\n\n- **Tribunal:** Tribunal Constitucional de Chile\n"
            f"- **Rol:** Rol N° {rol}\n- **Fecha:** {fecha}\n"
            f"- **Documento oficial:** https://buscador-backend.tcchile.cl/api/extended/{enlace or rol.split('-')[0]}/download\n\n"
            f"---\n\n{cuerpo}\n")


class _ApiHF:
    """Hugging Face simulado: el árbol de jurisprudencia_tc/, la cabeza de main y los commits."""

    def __init__(self, remotos=(), sin_cambios=False, fallas=()):
        self.remotos = list(remotos)
        self.commits = []
        self.head = "0" * 40
        self.sin_cambios = sin_cambios          # HF no crea commit y devuelve la cabeza actual
        self.fallas = list(fallas)              # excepciones que lanzan los próximos create_commit

    def list_repo_tree(self, repo_id, repo_type=None, path_in_repo=None):
        return [SimpleNamespace(path=f"jurisprudencia_tc/{n}") for n in self.remotos]

    def repo_info(self, repo_id, repo_type=None):
        return SimpleNamespace(sha=self.head)

    def get_paths_info(self, repo_id, paths, repo_type=None):
        return [SimpleNamespace(path=p) for p in paths if p.rsplit("/", 1)[-1] in self.remotos]

    def create_commit(self, **kw):
        if self.fallas:
            raise self.fallas.pop(0)
        if self.sin_cambios:
            return SimpleNamespace(oid=self.head)
        self.commits.append(kw)
        for op in kw["operations"]:
            nombre = op.path_in_repo.rsplit("/", 1)[-1]
            if type(op).__name__ == "CommitOperationDelete":
                self.remotos.remove(nombre)
            elif nombre not in self.remotos:
                self.remotos.append(nombre)
        self.head = str(len(self.commits)) * 40
        return SimpleNamespace(oid=self.head)


def test_solo_se_suben_las_sentencias_con_cabecera_y_texto_de_la_misma_causa(tmp_path):
    (tmp_path / "README.md").write_text("# TC\n", encoding="utf-8")
    # El archivo de la cosecha anterior: cabecera de una causa, texto de otra → no se sube.
    (tmp_path / "15907-06a-INA.md").write_bytes((FX / "tc_15907-06a-INA.md").read_bytes())
    (tmp_path / "15686-06a-INA.md").write_text(
        _md_tc("15686-06a-INA", "Sentencia\nRol 15.686-24 INA\n\nVISTOS: … CONSIDERANDO: …"), encoding="utf-8")
    revision = subir_tc_hf.revisar(tmp_path)
    assert revision == {"validos": ["15686-06a-INA.md"], "rechazados": ["15907-06a-INA.md"]}

    api = _ApiHF()
    res = subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=lambda ruta: b"")
    assert res["subido"] and res["commits"] == ["1" * 40] and res["rechazados"] == ["15907-06a-INA.md"]
    assert res["borrar"] == [] and len(api.commits) == 1               # nada que retirar: sin commit de bajas
    subidos = [op.path_in_repo for op in api.commits[0]["operations"]]
    assert subidos == ["jurisprudencia_tc/README.md", "jurisprudencia_tc/15686-06a-INA.md"]
    assert api.commits[0]["repo_type"] == "dataset"
    assert subir_tc_hf.subir(tmp_path, None, api=_ApiHF(), dry_run=True, bajar=lambda r: b"")["subido"] is False


def test_se_sube_por_lotes_y_se_retiran_los_defectuosos_que_no_se_rehicieron(tmp_path):
    for n in range(5):
        (tmp_path / f"1500{n}-06a-INA.md").write_text(
            _md_tc(f"1500{n}-06a-INA", f"Sentencia Rol 15.00{n}-24 INA VISTOS"), encoding="utf-8")
    viejo = (FX / "tc_15907-06a-INA.md").read_bytes()         # cabecera 15907, texto de 13139
    bueno = _md_tc("14000-06a-INA", "Sentencia Rol 14.000-23 INA VISTOS").encode()
    remotos = {"jurisprudencia_tc/15907-06a-INA.md": viejo, "jurisprudencia_tc/14000-06a-INA.md": bueno,
               "jurisprudencia_tc/15000-06a-INA.md": viejo}
    api = _ApiHF(["README.md", "15000-06a-INA.md", "15907-06a-INA.md", "14000-06a-INA.md", "testrol2-34566.md"])
    pedidos = []

    def bajar(ruta):
        pedidos.append(ruta)
        return remotos[ruta]

    seco = subir_tc_hf.subir(tmp_path, None, api=_ApiHF(api.remotos), bajar=bajar, dry_run=True)
    res = subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=bajar, lote=2, reservadas=["14000-06a-INA.md"])
    # Se retiran el defectuoso que no se rehízo, el resto de prueba y la causa reservada (esta sin
    # descargarla); el 15000 (defectuoso en HF) se reemplaza con el nuevo, no se borra.
    assert res["borrar"] == ["jurisprudencia_tc/14000-06a-INA.md", "jurisprudencia_tc/15907-06a-INA.md",
                             "jurisprudencia_tc/testrol2-34566.md"]
    assert pedidos.count("jurisprudencia_tc/15907-06a-INA.md") == 2 and res["sin_revisar"] == []
    assert pedidos.count("jurisprudencia_tc/14000-06a-INA.md") == 1             # solo en el dry-run
    assert [len(c["operations"]) for c in api.commits] == [2, 2, 1, 3]      # 3 lotes de altas + las bajas
    assert {type(op).__name__ for op in api.commits[-1]["operations"]} == {"CommitOperationDelete"}
    assert seco["subido"] is False and seco["commits"] == [] and len(seco["borrar"]) == 2


def test_lo_que_no_se_puede_leer_de_hf_no_se_borra_y_lo_nuevo_igual_se_sube(tmp_path):
    (tmp_path / "15686-06a-INA.md").write_text(_md_tc("15686-06a-INA", "Sentencia Rol 15.686-24 INA VISTOS"),
                                               encoding="utf-8")
    api = _ApiHF(["15907-06a-INA.md"])

    def bajar(ruta):
        raise subir_tc_hf.requests.ConnectionError("HF no responde")

    res = subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=bajar)
    assert res["subido"] and res["borrar"] == [] and res["sin_revisar"] == ["jurisprudencia_tc/15907-06a-INA.md"]
    assert "15907-06a-INA.md" in api.remotos and "15686-06a-INA.md" in api.remotos


def test_un_lote_sin_cambios_no_cuenta_como_commit_y_un_4xx_no_se_reintenta(tmp_path, monkeypatch):
    (tmp_path / "15686-06a-INA.md").write_text(_md_tc("15686-06a-INA", "Sentencia Rol 15.686-24 INA VISTOS"),
                                               encoding="utf-8")
    res = subir_tc_hf.subir(tmp_path, "hf_x", api=_ApiHF(sin_cambios=True), bajar=lambda r: b"")
    assert res["subido"] is False and res["commits"] == []

    monkeypatch.setattr(subir_tc_hf.time, "sleep", lambda s: None)
    prohibido = Exception("403 Forbidden")
    prohibido.response = SimpleNamespace(status_code=403)
    api = _ApiHF(fallas=[prohibido])
    with __import__("pytest").raises(Exception, match="403"):
        subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=lambda r: b"")
    caido = Exception("502 Bad Gateway")
    caido.response = SimpleNamespace(status_code=502)
    api = _ApiHF(fallas=[caido])
    assert subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=lambda r: b"")["commits"] == ["1" * 40]


def test_el_borrado_no_pide_retirar_lo_que_ya_no_existe(tmp_path):
    api = _ApiHF(["testrol2-34566.md"])
    llamadas = []
    original = api.get_paths_info

    def paths_info(repo_id, paths, repo_type=None):
        llamadas.append(list(paths))
        api.remotos.clear()                         # otro proceso ya lo retiró
        return original(repo_id, paths, repo_type)

    api.get_paths_info = paths_info
    res = subir_tc_hf.subir(tmp_path, "hf_x", api=api, bajar=lambda r: b"")
    assert llamadas == [["jurisprudencia_tc/testrol2-34566.md"]] and api.commits == [] and res["commits"] == []


def test_las_inadmisibilidades_nombran_su_rol_solo_al_pie():
    relleno = "Considerando que el requerimiento no cumple los requisitos. " * 200   # > 8 000 caracteres
    assert tc.corresponde(f"Santiago, veintinueve de octubre de dos mil veinticuatro. {relleno} Rol Nº 15.707-24 INA.", 15707)
    assert not tc.corresponde(f"Santiago. {relleno} Rol Nº 15.708-24 INA.", 15707)
    assert tc.corresponde("Proveído Rol N° 16.615-INA. Santiago", 16615)                # sin año
    assert tc.corresponde("Sentencia Rol 15.713 (15.777)-24 INA", 15777)                # acumuladas
    assert tc.corresponde("Sentencia Roles 11.315/11.317-21-CPT", 11315)                # lista
    assert not tc.corresponde("según la ley 15.686 de 1964", 15686)


def test_el_pdf_con_bytes_antes_de_la_cabecera_se_acepta_y_los_429_se_reintentan(monkeypatch):
    respuestas = [SimpleNamespace(status_code=429, content=b"", raise_for_status=lambda: None),
                  SimpleNamespace(status_code=200, content=b" \n%PDF-1.7 cuerpo", raise_for_status=lambda: None)]
    monkeypatch.setattr(tc.requests, "get", lambda url, headers=None, timeout=None: respuestas.pop(0))
    monkeypatch.setattr(tc.time, "sleep", lambda s: None)
    assert tc.descargar_pdf("https://buscador-backend.tcchile.cl/api/extended/8995/download") == b"%PDF-1.7 cuerpo"


def test_la_ficha_se_corrige_con_el_documento_y_se_ocultan_los_correos(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "DIR_MD", tmp_path)
    monkeypatch.setattr(tc, "DIR_PDF", tmp_path / "pdf")
    (tmp_path / "pdf").mkdir()
    monkeypatch.setattr(tc.requests, "get", lambda url, headers=None, timeout=None:
                        SimpleNamespace(status_code=200, content=b"%PDF-1.4", raise_for_status=lambda: None))
    texto = ("Santiago, veintisiete de agosto de dos mil veintiuno. VISTOS: con fecha 3 de julio de 2021 se "
             "presentó un requerimiento en la causa RIT 2125-2020 del 5° Juzgado de Garantía. " * 3
             + "SE DECLARA INADMISIBLE el requerimiento. Rol N° 11.636-21-INA. "
             + "De: oficina@tcchile.cl Para: abogada.parte@gmail.com Asunto: Comunica resolución")
    monkeypatch.setattr(tc, "texto_completo", lambda pdf: (texto, "pdftotext"))
    reg = {"rol": "Rol N° 11636-06a-INA", "folio": "11636", "fecha": "2021-01-05", "tipo": "INA-STC",
           "caratula": "10° Juzgado de Garantía de Santiago, RIT 4007-2008", "resultado": "None"}
    _, estado = tc.procesar((0, reg), rehacer=True)
    assert estado.startswith("ok|11636-06a-INA|")
    md = (tmp_path / "11636-06a-INA.md").read_text(encoding="utf-8")
    assert md.startswith("# INA-Inadmisibilidad — Rol N° 11636-06a-INA")
    assert "- **Fecha:** 2021-08-27" in md and "- **Fecha en la ficha del buscador:** 2021-01-05" in md
    assert "- **Tipo en la ficha del buscador:** INA-STC" in md
    assert "- **Rol oficial:** Rol N° 11636-21-INA" in md
    assert "Gestión pendiente" not in md and "RIT 4007-2008" not in md        # la gestión era de otra causa
    assert "None" not in md and "@" not in md and md.count("[correo omitido]") == 2
    assert reg["fecha"] == "2021-08-27" and reg["caratula"] == ""             # el índice, con lo verificado


def test_la_gestion_se_escribe_solo_si_aparece_en_el_documento():
    assert tc.gestion_verificada("Causa Rol C-139-2022 del Juzgado de Letras de Talca",
                                 "en los autos Rol C-139-2022 seguidos ante el Juzgado de Talca")
    assert tc.gestion_verificada("RUC N° 2100552184-7, RIT N° 1128-2021", "RUC 2.100.552.184-7") != ""
    assert tc.gestion_verificada("RIT T-3-2020, Juzgado de San Antonio", "en la causa RIT T-13-2020") == ""
    assert tc.gestion_verificada("Juzgado de Garantía de Vallenar", "cualquier texto") == ""


def test_las_reservadas_y_las_fichas_de_prueba_no_se_cosechan(tmp_path, monkeypatch):
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    monkeypatch.setattr(cosecha.time, "sleep", lambda s: None)
    # La cosecha anterior traía la gestión pendiente que la API ya no entrega.
    (tmp_path / "tc_sentencias_2anios.jsonl").write_text(
        '{"rol": "Rol N° 15686-06a-INA", "caratula": "Causa Rol C-1-2024 del Juzgado de Arica"}\n'
        '{"rol": "Rol N° 15700-06a-INA", "caratula": "None"}\n', encoding="utf-8")
    fichas = [dict(FICHA_API), dict(FICHA_API, folio="15700"), dict(FICHA_API, folio="11526", es_reservada=1),
              dict(FICHA_API, folio="1234rolprueba"), dict(FICHA_API, folio="testrol2")]
    monkeypatch.setattr(cosecha, "tc_por_dia", lambda fecha, page, s: {"data": fichas, "meta": {"total": 4, "per_page": 5}})
    salida = cosecha.cosechar_tc("2025-06-12", hasta="2025-06-12")
    filas = [__import__("json").loads(x) for x in salida.read_text(encoding="utf-8").splitlines()]
    assert [f["folio"] for f in filas] == ["15686", "15700"]
    assert filas[0]["caratula"] == "Causa Rol C-1-2024 del Juzgado de Arica"
    assert filas[0]["caratula_origen"] == "cosecha_anterior"
    assert filas[1]["caratula"] == "" and "caratula_origen" not in filas[1]    # el «None» viejo no se hereda


def test_los_dias_sin_respuesta_se_reintentan_y_se_anotan(tmp_path, monkeypatch):
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    monkeypatch.setattr(cosecha.time, "sleep", lambda s: None)
    caidas = {"2025-06-11": 5, "2025-06-10": 99}             # el 11 se recupera al reintentar; el 10 no

    def por_dia(fecha, page, s):
        if caidas.get(fecha, 0) > 0:
            caidas[fecha] -= 1
            raise cosecha.requests.ConnectionError("caída")
        return {"data": [dict(FICHA_API, folio=fecha[-2:] + "1", fecha_sentencia=f"{fecha} 00:00:00")],
                "meta": {"total": 1, "per_page": 5}}

    monkeypatch.setattr(cosecha, "tc_por_dia", por_dia)
    fallidos = tmp_path / "fallidos.txt"
    salida = cosecha.cosechar_tc("2025-06-10", hasta="2025-06-12", fallidos=fallidos)
    folios = sorted(__import__("json").loads(x)["folio"] for x in salida.read_text(encoding="utf-8").splitlines())
    assert folios == ["111", "121"] and fallidos.read_text(encoding="utf-8") == "2025-06-10\n"


def test_limpiar_no_pega_los_numeros_partidos_por_un_salto():
    import ingesta_fuentes
    limpio = ingesta_fuentes._limpiar("la consti-\ntución y el Rol 185-\n2020 y el RUC 2010062802-\n4")
    assert "constitución" in limpio and "185-\n2020" in limpio and "2010062802-\n4" in limpio


def test_la_ampliacion_recorre_todo_el_rango_pedido(tmp_path, monkeypatch):
    # Antes había un tope de 1 200 días: desde 2021 la cosecha se cortaba en 2023 sin avisar.
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    monkeypatch.setattr(cosecha.time, "sleep", lambda s: None)
    dias = []

    def por_dia(fecha, page, s):
        dias.append(fecha)
        if fecha != "2021-01-04":
            return {"data": [], "meta": {"total": 0, "per_page": 5}}
        return {"data": [dict(FICHA_API, folio="9876", fecha_sentencia="2021-01-04 00:00:00")],
                "meta": {"total": 1, "per_page": 5}}

    monkeypatch.setattr(cosecha, "tc_por_dia", por_dia)
    salida = cosecha.cosechar_tc("2021-01-01", hasta="2024-12-31")
    assert len(dias) == 1461 and dias[0] == "2024-12-31" and dias[-1] == "2021-01-01"
    filas = salida.read_text(encoding="utf-8").splitlines()
    assert len(filas) == 1 and "extended/9876/download" in filas[0]


def test_el_rol_cuenta_en_el_encabezado_o_en_el_ultimo_rol_del_pie_y_no_en_un_precedente():
    relleno = "Considerando. " * 300
    assert tc.corresponde("Sentencia Roles N° 16.122-25-INHP y N° 16.138-25-INHP [10 de abril de 2025]", 16138)
    assert tc.corresponde(f"{relleno} como se resolvió en causa Rol N° 16.067-24 INA, c. 7°. "
                          "Comuníquese. Rol N° 16.410-25-INA.", 16410)
    assert not tc.corresponde(f"{relleno} como se resolvió en causa Rol N° 16.067-24 INA, c. 7°. "
                              "Comuníquese. Rol N° 16.410-25-INA.", 16067)              # precedente citado
    assert not tc.corresponde("según la STC (c. 11°, Rol N° 12.338). " + relleno, 12338)
    assert not tc.corresponde("en la causa civil Rol N° C-9240-2024 " + relleno, 9240)


def test_el_tipo_sale_del_documento_sin_confundir_la_palabra_sentencia():
    inadmisible = ("Santiago, nueve de enero de dos mil veinticinco. VISTOS: el precepto impugnado regula la "
                   "citación para sentencia… SE DECLARA: Derechamente inadmisible el requerimiento.")
    assert tc.tipo_documento(inadmisible, "INA-Inadmisibilidad") == "INA-Inadmisibilidad"
    assert tc.tipo_documento("Sentencia Rol 9231-2020 [8 de julio de 2021] … se rechaza", "INA-STC") == "INA-STC"
    assert tc.tipo_documento("Santiago, … se declara improcedente el requerimiento", "INA-STC") == "INA-Inadmisibilidad"


def test_un_proveido_posterior_no_se_publica_como_la_resolucion_de_la_ficha():
    proveido = ("Santiago, catorce de octubre de dos mil veinticinco. Advirtiéndose un error en la incorporación "
                "de un escrito, desglósese. Rol N° 16.450-25-INA.")
    assert "proveído" in tc.documento_de_la_ficha({"tipo": "INA-Inadmisibilidad"}, proveido)
    assert tc.documento_de_la_ficha({"tipo": "INA-STC"}, proveido)
    assert tc.documento_de_la_ficha({"tipo": "INHM-STC"}, proveido) == ""     # resoluciones de sala, sin encabezado
    assert tc.documento_de_la_ficha({"tipo": "INA-STC"}, "Sentencia Rol 15.686-24 INA VISTOS") == ""


def test_la_fecha_del_documento_se_controla_con_las_firmas():
    texto = ("Santiago, veintisiete de marzo de dos mil veinticuatro. VISTOS … Rol N° 16.295-25-INA. "
             "María Angélica Barriga Meza Fecha: 27/03/2025 ABC Fecha: 28/03/2025")
    assert tc.fecha_del_documento(texto, "2025-03-27") == "2025-03-27"           # el año mal escrito no gana
    assert tc.fecha_del_documento(texto, "2024-01-01") == "2025-03-27"           # ni la ficha fuera de rango
    bien = "Sentencia Rol 14.685-23 INA [7 de mayo de 2024] … Fecha: 08/05/2024"
    assert tc.fecha_del_documento(bien, "2024-05-08") == "2024-05-07"
    assert tc.fecha_del_documento("Santiago, 1° de abril de 2025.", "") == "2025-04-01"


def test_los_correos_partidos_por_un_salto_de_linea_tambien_se_ocultan():
    texto = ("Para: GASTON80\n        @GMAIL.COM; mariana26\n @gmail.com\n"
             "CC: CONTACTO@LOGAN-\n   ABOGADOS.CL; raro@@x")
    oculto = tc.ocultar_correos(texto)
    assert "@" not in oculto and "GASTON80" not in oculto and "LOGAN" not in oculto and "mariana26" not in oculto


def test_la_cosecha_se_detiene_si_la_api_no_responde_y_anota_lo_pendiente(tmp_path, monkeypatch):
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    monkeypatch.setattr(cosecha.time, "sleep", lambda s: None)
    pedidos = []

    def caida(fecha, page, s):
        pedidos.append(fecha)
        raise cosecha.requests.ConnectionError("caída")

    monkeypatch.setattr(cosecha, "tc_por_dia", caida)
    fallidos = tmp_path / "fallidos.txt"
    cosecha.cosechar_tc("2025-01-01", hasta="2025-06-30", fallidos=fallidos)
    dias = sorted(set(pedidos))
    assert len(dias) == cosecha.CORTE_DIAS_SEGUIDOS                     # no recorre los 181 días
    lineas = fallidos.read_text(encoding="utf-8").splitlines()
    assert lineas[-1] == "2025-01-01..2025-06-20" and len(lineas) == cosecha.CORTE_DIAS_SEGUIDOS + 1


def test_las_reservadas_quedan_anotadas_para_retirarlas(tmp_path, monkeypatch):
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    fichas = [dict(FICHA_API), dict(FICHA_API, folio="11526", codigo="06a-INA", es_reservada=1)]
    monkeypatch.setattr(cosecha, "tc_por_dia", lambda f, p, s: {"data": fichas, "meta": {"total": 2, "per_page": 5}})
    reservadas = tmp_path / "reservadas.txt"
    cosecha.cosechar_tc("2025-06-12", hasta="2025-06-12", reservadas=reservadas)
    assert reservadas.read_text(encoding="utf-8") == "11526-06a-INA.md\n"
