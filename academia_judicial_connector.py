"""
Open Legal Chile — Conector e Indexador Oficial Academia Judicial de Chile
Módulo para consultar, descargar, procesar a Markdown e indexar en doctrina.db (FTS5)
las Guías de Buenas Prácticas Judiciales y Materiales de Formación de la Academia Judicial (https://guias.academiajudicial.cl/).
"""

import os
from typing import Dict, Any, List, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "doctrina_raw", "academia_judicial")
DB_PATH = os.path.join(os.path.dirname(__file__), "doctrina.db")

GUIAS_ACADEMIA_JUDICIAL = [
    {
        "id": "aj_determinacion_penas",
        "titulo": "Guía aplicada para la determinación de penas",
        "materia": "Penal",
        "fecha": "2026-07-08",
        "url_pdf": "https://guias.academiajudicial.cl/wp-content/uploads/2026/07/Guia-aplicada-para-la-determinacion-de-penas.pdf",
        "descripcion": "Metodología judicial para el cómputo de marcos penales, circunstancias modificatorias de responsabilidad (Arts. 11 y 12 CP), concurso de delitos y penas sustitutivas (Ley 18.216)."
    },
    {
        "id": "aj_ia_generativa",
        "titulo": "Guía Básica sobre Inteligencia Artificial Generativa para el ejercicio de Juezas y Jueces",
        "materia": "Transversal / IA",
        "fecha": "2026-04-01",
        "url_pdf": "https://ia.academiajudicial.cl/wp-content/uploads/2026/04/Guia_Basica_sobre_Inteligencia_Artificial_Generativa_para_el_ejercicio_de_Juezas_y_Jueces__2026.pdf",
        "descripcion": "Estándares éticos, sesgos algorítmicos, confidencialidad, privacidad de datos y uso asistencial de LLMs en la redacción de considerandos y decretos judiciales."
    },
    {
        "id": "aj_primera_audiencia_penal",
        "titulo": "Guía de conducción de la primera audiencia en el proceso penal",
        "materia": "Penal",
        "fecha": "2025-05-15",
        "url_pdf": "https://guias.academiajudicial.cl/guias/guia_garantia_2025/Guia_conduccion_primera_audiencia_proceso_penal_V2.1.pdf",
        "descripcion": "Control de legalidad de la detención (Art. 131 CPP), formalización de la investigación, discusión de medidas cautelares personales (Art. 140 CPP) y plazo de investigación judicial."
    },
    {
        "id": "aj_apjo_penal",
        "titulo": "Guía para la conducción de la audiencia de preparación de juicio oral (APJO)",
        "materia": "Penal",
        "fecha": "2025-04-10",
        "url_pdf": "https://guias.academiajudicial.cl/guias/preparacion_juicio_oral/Guia_para_la_conduccion_de_la_audiencia_de_preparacion_de_juicio_oral_2025_v1.pdf",
        "descripcion": "Depuración de la acusación, exclusión de pruebas ilícitas o sobreabundantes (Art. 276 CPP), convenciones probatorias y dictación del auto de apertura del juicio oral (Art. 277 CPP)."
    },
    {
        "id": "aj_juicio_oral_penal",
        "titulo": "Guía de conducción de la audiencia de juicio oral en lo penal",
        "materia": "Penal",
        "fecha": "2025-06-20",
        "url_pdf": "https://guias.academiajudicial.cl/guias/oral_en_lo_penal/Gu%c3%ada_conducci%c3%b3n_audiencia_de_juicio_oral.pdf",
        "descripcion": "Apertura del juicio, orden de rendición de la prueba testimonial y pericial, objeciones y contraexámenes, alegatos de clausura y deliberación del veredicto."
    },
    {
        "id": "aj_procedimiento_abreviado",
        "titulo": "Guía de Procedimiento Abreviado en Juzgados de Garantía",
        "materia": "Penal",
        "fecha": "2025-03-01",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_de_garantia/Guia_Procedimiento_Abreviado_2025_v1.1.pdf",
        "descripcion": "Presupuestos de procedencia (Art. 406 CPP), consentimiento informado del imputado, aceptación de hechos de la acusación y limitación de la pena imponible (Art. 412 CPP)."
    },
    {
        "id": "aj_procedimiento_simplificado",
        "titulo": "Guía de Procedimiento Simplificado en Juzgados de Garantía",
        "materia": "Penal",
        "fecha": "2025-03-01",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_de_garantia/Guia_Procedimiento_Simplificado_2025_v1.1.pdf",
        "descripcion": "Tramitación de requerimientos por faltas o simples delitos con penas que no excedan de presidio menor en su grado mínimo (Art. 388 CPP) y audiencia de admisión de responsabilidad."
    },
    {
        "id": "aj_procedimiento_monitorio_penal",
        "titulo": "Guía de Procedimiento Monitorio Penal",
        "materia": "Penal",
        "fecha": "2025-03-01",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_de_garantia/Guia_Procedimiento_Monitorio_2025_v1.1.pdf",
        "descripcion": "Cobro de multas por faltas (Art. 392 CPP), requerimiento fiscal, imposición directa de pena pecuniaria y derecho de reclamación del imputado."
    },
    {
        "id": "aj_audiencia_preparatoria_laboral",
        "titulo": "Guía para la Audiencia Preparatoria Laboral",
        "materia": "Laboral",
        "fecha": "2025-02-15",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_laborales/Guia_Audiencia_Preparatoria-v1.pdf",
        "descripcion": "Ratificación de demanda y contestación, llamado a conciliación obligatoria, fijación de hechos controvertidos sustanciales y ofrecimiento/admisión de prueba (Art. 453 Código del Trabajo)."
    },
    {
        "id": "aj_juicio_oral_laboral",
        "titulo": "Guía para la Audiencia de Juicio Oral Laboral",
        "materia": "Laboral",
        "fecha": "2025-02-15",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_laborales/Guia_Audiencia_Juicio_Oral_Laboral.pdf",
        "descripcion": "Rendición de prueba bajo sana crítica (Art. 456 CT), absolución de posiciones de representantes legales, interrogatorio de testigos y sentencia oral o diferida (Art. 457 CT)."
    },
    {
        "id": "aj_conciliacion_laboral",
        "titulo": "Guía de Audiencia de Conciliación Laboral",
        "materia": "Laboral",
        "fecha": "2025-02-15",
        "url_pdf": "https://guias.academiajudicial.cl/guias/juzgados_laborales/Guia_Audiencia_Conciliacion_Laboral_v2.1.pdf",
        "descripcion": "Técnicas de negociación judicial, propuesta de bases de arreglo y resguardo de derechos laborales irrenunciables (Art. 5 inc. 2 CT)."
    },
    {
        "id": "aj_audiencias_familia",
        "titulo": "Guía para la conducción de audiencias de familia (Preparatoria, Reservada, Conciliación y Juicio)",
        "materia": "Familia",
        "fecha": "2025-05-10",
        "url_pdf": "https://guias.academiajudicial.cl/guias/audiencias_de_familia/guia_para_la_conduccion_de_las_audiencias_de_familia_preparatoria_reservada_conciliacion_y_juicio_oral_2025_v1.1.pdf",
        "descripcion": "Conducción de audiencias bajo los principios de oralidad, inmediación, interés superior del niño y colaboración procesal (Ley N° 19.968)."
    },
    {
        "id": "aj_proteccion_familia",
        "titulo": "Guía para el procedimiento de medidas de protección en tribunales de familia",
        "materia": "Familia",
        "fecha": "2025-05-25",
        "url_pdf": "https://guias.academiajudicial.cl/guias/audiencia_de_proteccion/Guia_procedimiento_de_proteccion_30525.pdf",
        "descripcion": "Medidas cautelares de urgencia (Art. 71 Ley 19.968), derecho a ser oído de NNA, informe de consejeros técnicos y evaluación de vulneración de derechos."
    },
    {
        "id": "aj_responsabilidad_penal_adolescente",
        "titulo": "Guía para audiencias de Responsabilidad Penal Adolescente (RPA)",
        "materia": "Penal / RPA",
        "fecha": "2025-04-18",
        "url_pdf": "https://guias.academiajudicial.cl/guias/responsabilidad_penal_adolecente/Guia_para_la_conduccion_de_las_Audiencias_de_Casos_de_Responsabilidad_Penal_Adolecente_2025_v1.1.pdf",
        "descripcion": "Especialidad del sistema penal juvenil conforme a la Ley N° 20.084 y Servicio Nacional de Reinserción Social Juvenil (Ley N° 21.527)."
    },
    {
        "id": "aj_etica_judicial",
        "titulo": "Guía de Buenas Prácticas Judiciales en Temas Éticos",
        "materia": "Ética Judicial",
        "fecha": "2026-07-10",
        "url_pdf": "https://guias.academiajudicial.cl/guias/guia_etica/Guia_Etica_10jul_2026.pdf",
        "descripcion": "Principios de independencia, imparcialidad, integridad, diligencia debida, secreto profesional y deber de abstención y recusación en el ejercicio jurisdiccional."
    }
]


class AcademiaJudicialClient:
    """Cliente para buscar, consultar e indexar las Guías de la Academia Judicial de Chile."""

    def __init__(self, cache_dir: str = CACHE_DIR, db_path: str = DB_PATH):
        self.cache_dir = cache_dir
        self.db_path = db_path
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_todas_las_guias(self) -> List[Dict[str, Any]]:
        """Retorna el catálogo completo de las Guías Oficiales de la Academia Judicial de Chile."""
        return GUIAS_ACADEMIA_JUDICIAL

    def search_guias(self, query: str, materia: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca en el catálogo de guías de la Academia Judicial por término o materia jurídica."""
        def _norm(txt: str) -> str:
            t = txt.lower()
            for o, d in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')]:
                t = t.replace(o, d)
            return t

        q_norm = _norm(query.strip())
        matches = []

        for g in GUIAS_ACADEMIA_JUDICIAL:
            if materia and _norm(materia) not in _norm(g["materia"]):
                continue

            texto_completo = _norm(f"{g['titulo']} {g['descripcion']} {g['materia']}")
            if q_norm in texto_completo or all(pal in texto_completo for pal in q_norm.split()):
                matches.append(g)

        return matches
