"""
Open Legal Chile — Pruebas Unitarias para el Generador de Recursos de Protección
y Compilador de Expedientes OJV (Auto Acordado CS Acta N.° 94-2015).
"""

import os
import pytest
import pymupdf
from datetime import date, timedelta
from recurso_proteccion import RecursoProteccionEngine
from exporters import LegalDocumentExporter
from pdf_dossier_compiler import LegalDossierCompiler
from mcp_server import handle_tool_call, TOOLS


def test_compute_deadline_tempestivo():
    """Verifica el cómputo exacto del plazo fatal de 30 días corridos (Numeral 1.° Auto Acordado)."""
    fecha_acto = "2026-09-01"
    fecha_interp = "2026-09-14"
    res = RecursoProteccionEngine.compute_deadline(fecha_acto, fecha_interp)

    assert res["es_tempestivo"] is True
    assert res["es_extemporaneo"] is False
    assert res["dias_transcurridos"] == 13
    assert "treinta días corridos" in res["clausula_plazo"]
    assert "Numeral 1.°" in res["clausula_plazo"]
    assert "Acta N.° 94-2015" in res["clausula_plazo"]
    assert "13 días corridos" in res["clausula_plazo"]
    assert "septiembre" in res["clausula_plazo"]  # Mes en minúscula según RAE


def test_compute_deadline_extemporaneo():
    """Verifica advertencia procesal cuando han transcurrido más de 30 días corridos."""
    fecha_acto = "2026-07-01"
    fecha_interp = "2026-09-14"
    res = RecursoProteccionEngine.compute_deadline(fecha_acto, fecha_interp)

    assert res["es_tempestivo"] is False
    assert res["es_extemporaneo"] is True
    assert res["dias_transcurridos"] > 30
    assert "ADVERTENCIA PROCESAL DE EXTEMPORANEIDAD" in res["clausula_plazo"]


def test_presuma_anti_collapse_ojv():
    """Verifica que la presuma y suma no colapsen en un solo párrafo y usen saltos discretos."""
    presuma = RecursoProteccionEngine.format_presuma_recurso_proteccion(
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        recurrente_nombre="Constanza Valdés",
        recurrente_run="16.789.012-3",
        recurrente_domicilio="Calle Los Alerces N.° 450, Ñuñoa",
        recurrente_email="constanza@correo.cl",
        recurrido_nombre="Club Deportivo Social y Cultural Oriente",
        recurrido_rut=None,  # Rut desconocido
        recurrido_domicilio="Av. Grecia 1234",
        recurrido_email="directiva@club.cl",
        representante_legal="Juan Pérez (Presidente de facto no regularizado)",
        representado_nombre="Matías Valdés",
        representado_run="25.678.901-2",
        quinto_otrosi_titulo="REPRESENTA FALTA DE PERSONERÍA DE LA RECURRIDA"
    )

    # Verificación en texto plano
    txt = presuma["plain_text"]
    assert "TRIBUNAL : Ilustrísima Corte de Apelaciones de Santiago" in txt
    assert "MATERIA  : RECURSO DE PROTECCIÓN" in txt
    assert "CONSTANZA VALDÉS (por sí y en representación legal de MATÍAS VALDÉS)" in txt
    assert "Se desconoce / No consta" in txt
    assert "Presidente de facto no regularizado" in txt
    assert "EN LO PRINCIPAL: RECURSO DE PROTECCIÓN;" in txt
    assert "EN EL SEGUNDO OTROSÍ: ORDEN DE NO INNOVAR;" in txt
    assert "TERCER OTROSÍ: SOLICITUD QUE INDICA" in txt
    assert "CUARTO OTROSÍ: SOLICITA OFICIOS" in txt
    assert "QUINTO OTROSÍ: REPRESENTA FALTA DE PERSONERÍA DE LA RECURRIDA;" in txt

    # Verificación en HTML (saltos de línea discretos para evitar colapso en PDF)
    html_p = presuma["html"]
    assert "<br/>" in html_p
    assert "border: 1.5px solid #4a5568" in html_p or "border:" in html_p
    assert "white-space: pre-wrap" in html_p or "line-height:" in html_p


def test_comparecencia_personal_garantizada():
    """Verifica comparecencia personal sin abogado (Numeral 2.° Auto Acordado y Art. 20 CPR)."""
    brief = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de Valparaíso",
        recurrente={
            "nombre": "Carlos Mendoza",
            "run": "14.567.890-1",
            "domicilio": "Plaza Sotomayor 50, Valparaíso",
            "email": "carlos.mendoza@correo.cl"
        },
        recurrido={
            "nombre": "Empresa Portuaria Valparaíso",
            "rut": "61.987.654-3"
        },
        acto_lesivo="Clausura intempestiva e ilegal de acceso al muelle de pescadores artesanales",
        fecha_acto="2026-09-08",
        hechos=["1. Con fecha 8 de septiembre se impidió el acceso por vías de hecho."],
        garantias=["19_16", "19_21", "19_24"],
        fecha_interposicion="2026-09-14"
    )

    # Verificar Tercer Otrosí de comparecencia personal
    otrosies = {ot["numero"]: ot for ot in brief["otrosies"]}
    assert "TERCER OTROSÍ" in otrosies
    ot3 = otrosies["TERCER OTROSÍ"]["contenido"]
    assert "artículo 20 de la Constitución Política" in ot3
    assert "Numeral 2.° del Auto Acordado" in ot3
    assert "sin requerir patrocinio de abogado ni mandato judicial" in ot3
    assert "carlos.mendoza@correo.cl" in ot3


def test_orden_de_no_innovar_copulativa():
    """Verifica formulación técnica obligatoria de la ONI (Numeral 3.° inc. final)."""
    brief = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        recurrente={
            "nombre": "Ana Morales",
            "run": "13.234.567-8",
            "domicilio": "Av. Matta 120, Santiago",
            "email": "ana.morales@correo.cl"
        },
        recurrido={"nombre": "Inmobiliaria Los Robles SpA"},
        acto_lesivo="Corte arbitrario del suministro de agua potable y energía eléctrica",
        fecha_acto="2026-09-10",
        hechos=["El corte se ejecutó mediante vías de hecho sin resolución judicial."],
        garantias=["19_1", "19_24"],
        oni_data={
            "solicita": True,
            "fumus_boni_iuris": "Acreditado con comprobantes de pago de servicios.",
            "periculum_in_mora": "Riesgo vital por privación de agua potable a persona electrodependiente.",
            "medida_suspension": "El restablecimiento inmediato de los suministros básicos."
        },
        fecha_interposicion="2026-09-14"
    )

    otrosies = {ot["numero"]: ot for ot in brief["otrosies"]}
    assert "SEGUNDO OTROSÍ" in otrosies
    ot2 = otrosies["SEGUNDO OTROSÍ"]["contenido"]
    assert "Numeral 3.° inciso final" in ot2
    assert "fumus boni iuris" in ot2.lower()
    assert "periculum in mora" in ot2.lower()
    assert "restablecimiento inmediato" in ot2


def test_preferencia_fallo_numeral_10():
    """Verifica petición automática de fallo preferente al invocar Art. 19 N.° 1 o N.° 3 inc. 5.°."""
    # Caso con preferencia (19 N.° 1)
    b_pref = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        recurrente={"nombre": "Test", "run": "1.1.1-1", "domicilio": "X", "email": "a@a.cl"},
        recurrido={"nombre": "Rdo"},
        acto_lesivo="Acto lesivo contra integridad",
        fecha_acto="2026-09-10",
        hechos=["Hecho 1"],
        garantias=["19_1"],
        fecha_interposicion="2026-09-14"
    )
    assert b_pref["preferente"] is True
    assert "tramitación y fallo preferente en un plazo fatal de dos días hábiles" in b_pref["por_tanto"]
    assert "Numeral 10.°" in b_pref["por_tanto"]

    # Caso sin preferencia (19 N.° 21 actividad económica)
    b_nopref = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        recurrente={"nombre": "Test", "run": "1.1.1-1", "domicilio": "X", "email": "a@a.cl"},
        recurrido={"nombre": "Rdo"},
        acto_lesivo="Acto contra comercio",
        fecha_acto="2026-09-10",
        hechos=["Hecho 1"],
        garantias=["19_21"],
        fecha_interposicion="2026-09-14"
    )
    assert b_nopref["preferente"] is False
    assert "Numeral 10.°" not in b_nopref["por_tanto"]


def test_integracion_estatutos_especiales():
    """Verifica integración dogmática de Leyes 21.430, 21.545, 19.712 y Arts. 175-176 CPP."""
    brief = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de San Miguel",
        recurrente={"nombre": "Padre", "run": "2.2.2-2", "domicilio": "Y", "email": "b@b.cl"},
        recurrido={"nombre": "Colegio"},
        acto_lesivo="Expulsión discriminatoria de alumno autista",
        fecha_acto="2026-09-08",
        hechos=["El colegio expulsó sin ajustes razonables."],
        garantias=["19_2", "19_10"],
        estatutos_especiales=["ninez_21430", "tea_21545", "denuncia_cpp"],
        fecha_interposicion="2026-09-14"
    )

    der = brief["derecho"]
    assert "Ley N.° 21.430" in der
    assert "interés superior" in der
    assert "Ley N.° 21.545" in der
    assert "neurodivergencia" in der
    assert "ajustes razonables" in der
    assert "Código Procesal Penal" in der


def test_dossier_compilation_with_toc_bookmarks(tmp_path):
    """Verifica compilación de expediente PDF con marcadores TOC y carátula divisoria elegante."""
    compiler = LegalDossierCompiler()
    assert compiler.is_available() is True

    # 1. Crear documento anexo temporal
    anx_doc = pymupdf.open()
    anx_doc.new_page().insert_text((50, 100), "Texto de prueba del informe psicológico anexo.")
    anx_path = str(tmp_path / "anexo_prueba.pdf")
    anx_doc.save(anx_path)
    anx_doc.close()

    # 2. Markdown del escrito
    md_content = """# RECURSO DE PROTECCIÓN
## I. LOS HECHOS (CRONOLOGÍA FUNDANTE)
Hecho 1 ocurrido con fecha reciente...
## II. EL DERECHO Y GARANTÍAS CONSTITUCIONALES AFECTADAS
Se invoca el Art. 19 N.° 1...
## POR TANTO,
Pido acoger...
## PRIMER OTROSÍ: ACOMPAÑA DOCUMENTOS
Acompaña informe...
"""

    out_pdf = str(tmp_path / "Expediente_Consolidado.pdf")
    main_pdf = str(tmp_path / "Escrito_Solo_Caratula.pdf")

    res = compiler.compile(
        markdown_content=md_content,
        output_pdf_path=out_pdf,
        main_pdf_path=main_pdf,
        annexes=[
            {
                "num": "ANEXO N.° 1",
                "title": "Informe Clínico Psicológico Pericial",
                "desc": "Acredita afectación psíquica severa conforme al Art. 19 N.° 1 CPR",
                "path": anx_path
            }
        ],
        title="Recurso de Protección — Iltma. Corte de Apelaciones de Santiago"
    )

    assert "error" not in res
    assert res["total_pages"] == 3  # 1 página escrito + 1 separador elegante + 1 anexo
    assert res["main_pages"] == 1
    assert res["annexes_count"] == 1
    assert os.path.exists(out_pdf)
    assert os.path.exists(main_pdf)

    # 3. Validar marcadores nativos TOC
    doc_final = pymupdf.open(out_pdf)
    toc = doc_final.get_toc()
    assert len(toc) >= 3
    # Debe contener marcador para el anexo
    titulos_toc = [item[1] for item in toc]
    assert any("Informe Clínico" in t for t in titulos_toc)
    assert any("ANEXO N.° 1" in t for t in titulos_toc)
    doc_final.close()


def test_mcp_tool_recurso_proteccion_generar(tmp_path):
    """Verifica invocación de la herramienta MCP recurso_proteccion_generar."""
    anx_doc = pymupdf.open()
    anx_doc.new_page().insert_text((50, 100), "Certificado de Alumno Regular")
    anx_path = str(tmp_path / "anexo_cert.pdf")
    anx_doc.save(anx_path)
    anx_doc.close()

    res = handle_tool_call("recurso_proteccion_generar", {
        "tribunal": "Ilustrísima Corte de Apelaciones de Santiago",
        "recurrente": {
            "nombre": "Rodrigo Silva",
            "run": "12.876.543-2",
            "domicilio": "Av. Apoquindo 3000, Las Condes",
            "email": "rodrigo.silva@correo.cl"
        },
        "recurrido": {
            "nombre": "Club de Polo y Equitación San Cristóbal",
            "domicilio": "Av. San Josemaría Escrivá de Balaguer 5551, Vitacura"
        },
        "acto_lesivo": "Suspensión unilateral de derechos societarios sin debido proceso",
        "fecha_acto": "2026-09-02",
        "hechos": ["1. La directiva suspendió la membresía por acuerdo informal."],
        "garantias": ["19_2", "19_3_5", "19_24"],
        "anexos": [
            {"num": "ANEXO N.° 1", "title": "Certificado de Membresía", "desc": "Acredita calidad de socio", "path": anx_path}
        ],
        "compilar_pdf": True
    })

    assert isinstance(res, dict)
    assert "error" not in res
    assert "markdownPath" in res
    assert "htmlPath" in res
    assert "textPath" in res
    assert "jsonPath" in res
    assert res["deadline_info"]["es_tempestivo"] is True
    assert res["preferente"] is True  # Invocó 19_3_5
    assert "pdf_compilation" in res
    assert os.path.exists(res["pdf_compilation"]["output_pdf"])
    assert os.path.exists(res["pdf_compilation"]["main_only_pdf"])

    # Limpieza
    for ext in [".md", ".html", ".txt", ".json"]:
        p = os.path.join(res["exportsDir"], f"{res['filename']}{ext}")
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(res["pdf_compilation"]["output_pdf"]):
        os.remove(res["pdf_compilation"]["output_pdf"])
    if os.path.exists(res["pdf_compilation"]["main_only_pdf"]):
        os.remove(res["pdf_compilation"]["main_only_pdf"])


def test_ortotipografia_rae_asale():
    """Verifica el cumplimiento estricto de las normas RAE/ASALE en la redacción forense."""
    brief = RecursoProteccionEngine.generate_full_brief(
        tribunal="Ilustrísima Corte de Apelaciones de Santiago",
        recurrente={"nombre": "Juan", "run": "12.345.678-9", "domicilio": "D", "email": "j@j.cl"},
        recurrido={"nombre": "Colegio"},
        acto_lesivo="Expulsión",
        fecha_acto="2026-09-01",
        hechos=[{"texto": "Notificación", "anexo": "Anexo 1"}],
        garantias=["19_1", "19_2"],
        anexos=[{"num": "ANEXO N.° 1", "title": "Certificado", "desc": "Prueba"}],
        fecha_interposicion="2026-09-14"
    )

    md = brief["markdown_full"]
    # 1. Comillas latinas obligatorias
    assert "«" in md and "»" in md
    # 2. Abreviatura oficial de número
    assert "N.°" in md
    # 3. Abreviatura de artículo
    assert "Art." in md
    # 4. RUN chileno con puntos y guion
    assert "12.345.678-9" in md
    # 5. Puntuación fuera de comillas en citas
    # (No debe haber ," ni ." en el texto generado)
    assert ',"' not in md
    assert '."' not in md
