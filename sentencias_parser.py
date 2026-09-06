"""
Open Legal Chile — Analizador Estructural de Sentencias Judiciales y Proveídos OJV
Módulo forense para desglosar sentencias judiciales conforme al Art. 170 del Código de Procedimiento Civil (CPC)
y el Auto Acordado de la Corte Suprema de 1907 sobre la forma de las sentencias,
así como interpretar procesalmente decretos y resoluciones de mera tramitación de la Oficina Judicial Virtual.
"""

import re
from typing import Dict, Any, List, Optional


class SentenciaParserEngine:
    """Motor de descomposición analítica de sentencias judiciales chilenas."""

    REQUISITOS_ART_170_CPC = [
        {"num": 1, "mencion": "Designación precisa de las partes litigantes, su domicilio y profesión u oficio"},
        {"num": 2, "mencion": "Enunciación breve de las peticiones o acciones deducidas por el demandante y de sus fundamentos"},
        {"num": 3, "mencion": "Enunciación breve de las excepciones o defensas alegadas por el demandado"},
        {"num": 4, "mencion": "Consideraciones de hecho que sirven de fundamento al fallo y las razones jurídicas que se invocan"},
        {"num": 5, "mencion": "Enunciación de las leyes o principios de equidad con arreglo a los cuales se pronuncia el fallo"},
        {"num": 6, "mencion": "Decisión del asunto controvertido (resolutiva), comprendiendo todas las acciones y excepciones"}
    ]

    def parsear_sentencia(self, texto: str) -> Dict[str, Any]:
        """
        Analiza el texto íntegro de una resolución o sentencia judicial chilena
        y extrae sus partes constitutivas: expositiva, considerativa, resolutiva, disidencias y costas.
        """
        if not texto or not isinstance(texto, str):
            return {"error": "Texto de sentencia vacío o inválido."}

        # 1. Detección de Tribunal, Rol y Fecha en el encabezado
        encabezado_match = re.search(r"^(.*?)(?=(?:VISTOS|CONSIDERANDO|Y\s+TENIENDO\s+PRESENTE))", texto, re.DOTALL | re.IGNORECASE)
        encabezado_raw = encabezado_match.group(1).strip() if encabezado_match else texto[:500].strip()

        rol_match = re.search(r"(?:Rol|Causa|RIT|RUC)\s*(?:N[°ºo]?\s*)?([A-Z0-9\-_/]+)", encabezado_raw, re.IGNORECASE)
        rol = rol_match.group(1).strip() if rol_match else "No identificado"

        tribunal_match = re.search(r"(Corte\s+Suprema|Corte\s+de\s+Apelaciones(?:\s+de\s+[A-Za-z]+)?|[0-9]+[°º]?\s+Juzgado\s+de\s+Letras(?:\s+en\s+lo\s+[A-Za-z]+)?|Tribunal\s+de\s+Juicio\s+Oral|Juzgado\s+de\s+Garant[íi]a|Tribunal\s+Ambiental|Tribunal\s+Tributario)", encabezado_raw, re.IGNORECASE)
        tribunal = tribunal_match.group(1).strip() if tribunal_match else "Tribunal Ordinario / Especial"

        # 2. Segmentación de Secciones: Expositiva (Vistos), Considerativa (Considerando), Resolutiva (Resuelvo / Se declara)
        vistos_match = re.search(r"(?:VISTOS?|RESULTANDO)[:\s]*(.*?)(?=(?:Y\s+TENIENDO\s+PRESENTE|CONSIDERANDO))", texto, re.DOTALL | re.IGNORECASE)
        parte_expositiva = vistos_match.group(1).strip() if vistos_match else ""

        # Considerandos
        considerando_match = re.search(r"(?:CONSIDERANDO|Y\s+TENIENDO\s+PRESENTE)[:\s]*(.*?)(?=(?:Y\s+VISTO|POR\s+ESTAS\s+CONSIDERACIONES|SE\s+RESUELVE|RESUELVO|DECLARO))", texto, re.DOTALL | re.IGNORECASE)
        parte_considerativa_raw = considerando_match.group(1).strip() if considerando_match else ""

        # Resolutiva
        resolutiva_match = re.search(r"(?:POR\s+ESTAS\s+CONSIDERACIONES|SE\s+RESUELVE|RESUELVO|DECLARO|POR\s+TANTO)[,:\s]*(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada\s+por|Redacci[oó]n\s+del|$))", texto, re.DOTALL | re.IGNORECASE)
        parte_resolutiva = resolutiva_match.group(1).strip() if resolutiva_match else ""

        # 3. Extracción atómica de Considerandos individuales
        patron_split = r"(?:^|\n)\s*([0-9]+[°º]?|[A-Z]+[°º]?|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|D[EÉ]CIMO|UND[EÉ]CIMO|DUOD[EÉ]CIMO)[\.:\)\s\-]+(?:Que\s+)?"
        tokens = re.split(patron_split, "\n" + parte_considerativa_raw, flags=re.IGNORECASE)

        considerandos_hecho = []
        considerandos_derecho = []
        considerandos_lista = []

        for i in range(1, len(tokens), 2):
            num_c = tokens[i].strip()
            cuerpo_c = tokens[i+1].strip() if i+1 < len(tokens) else ""
            if len(cuerpo_c) < 10:
                continue

            es_derecho = bool(re.search(r"art[íi]culo|ley|c[oó]digo|jurisprudencia|doctrina|precepto|mandato\s+legal|hermen[eé]utica", cuerpo_c, re.IGNORECASE))
            info_c = {
                "numero": num_c,
                "texto": cuerpo_c[:300] + ("..." if len(cuerpo_c) > 300 else ""),
                "tipo": "DERECHO" if es_derecho else "HECHO"
            }
            considerandos_lista.append(info_c)
            if es_derecho:
                considerandos_derecho.append(info_c)
            else:
                considerandos_hecho.append(info_c)

        # 4. Votos Disidentes y Prevenciones
        disidencia_match = re.search(r"(?:Acordada\s+con\s+el\s+voto\s+en\s+contra|Voto\s+disidente|Disidente|Disiente)(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada|$))", texto, re.DOTALL | re.IGNORECASE)
        prevencion_match = re.search(r"(?:Prevenci[oó]n|Previene|Concurre\s+con\s+la\s+prevenci[oó]n)(.*?)(?=(?:Reg[ií]strese|Notif[ií]quese|Pronunciada|$))", texto, re.DOTALL | re.IGNORECASE)

        tiene_disidencia = bool(disidencia_match)
        texto_disidencia = disidencia_match.group(1).strip() if disidencia_match else ""

        tiene_prevencion = bool(prevencion_match)
        texto_prevencion = prevencion_match.group(1).strip() if prevencion_match else ""

        # 5. Régimen de Costas (Art. 144 CPC)
        sin_motivo = bool(re.search(r"sin\s+motivo\s+plausible", texto, re.IGNORECASE))
        costas_condena = bool(re.search(r"con\s+costas|cond[eé]nase\s+(?:en|al?)\s+costas|con\s+expresa\s+condenaci[oó]n\s+en\s+costas", texto, re.IGNORECASE)) or sin_motivo
        costas_exencion = (bool(re.search(r"sin\s+costas|no\s+se\s+condena\s+en\s+costas|por\s+haber\s+tenido\s+motivo\s+plausible|con\s+motivo\s+plausible|ex[ií]mase\s+de\s+costas", texto, re.IGNORECASE)) and not sin_motivo)

        if costas_condena:
            regimen_costas = "CONDENA EN COSTAS (Art. 144 CPC: parte vencida totalmente sin motivo plausible)."
        elif costas_exencion:
            regimen_costas = "EXENCIÓN DE COSTAS (Art. 144 CPC: se estimó que la parte vencida litigó con motivo plausible)."
        else:
            regimen_costas = "Sin pronunciamiento expreso o condenación estándar de autos."

        # 6. Auditoría Art. 170 CPC
        requisitos_cumplidos = {
            "num_1_partes": bool(re.search(r"demandante|demandado|recurrente|recurrido", parte_expositiva, re.IGNORECASE)) or len(parte_expositiva) > 50,
            "num_2_acciones": bool(re.search(r"demanda|acci[oó]n|solicita|pretensi[oó]n", parte_expositiva, re.IGNORECASE)),
            "num_3_excepciones": bool(re.search(r"excepci[oó]n|defensa|contestaci[oó]n|rebeld[ií]a", parte_expositiva, re.IGNORECASE)),
            "num_4_consideraciones": len(considerandos_lista) > 0 or len(parte_considerativa_raw) > 100,
            "num_5_leyes": bool(re.search(r"visto|ley|art[íi]culo|c[oó]digo", texto, re.IGNORECASE)),
            "num_6_resolutiva": len(parte_resolutiva) > 20
        }

        cumple_art_170 = all(requisitos_cumplidos.values())

        return {
            "rol": rol,
            "tribunal": tribunal,
            "estructura_art_170_cpc": {
                "cumple_requisitos_formales": cumple_art_170,
                "evaluacion_por_numeral": requisitos_cumplidos
            },
            "parte_expositiva_resumen": parte_expositiva[:400] + ("..." if len(parte_expositiva) > 400 else ""),
            "total_considerandos": len(considerandos_lista),
            "considerandos_de_hecho": len(considerandos_hecho),
            "considerandos_de_derecho": len(considerandos_derecho),
            "muestra_considerandos": considerandos_lista[:5],
            "parte_resolutiva": parte_resolutiva[:500] + ("..." if len(parte_resolutiva) > 500 else ""),
            "votos": {
                "hay_disidencia": tiene_disidencia,
                "texto_disidencia": texto_disidencia[:300] + ("..." if len(texto_disidencia) > 300 else ""),
                "hay_prevencion": tiene_prevencion,
                "texto_prevencion": texto_prevencion[:300] + ("..." if len(texto_prevencion) > 300 else "")
            },
            "regimen_costas": regimen_costas
        }


class ProveidosParser:
    """Interpreta proveídos, decretos y resoluciones breves de la tramitación judicial en Chile (OJV)."""

    PROVEIDOS_CATALOGO = [
        {
            "patron": r"t[eé]ngase\s+presente",
            "tipo": "TÉNGASE PRESENTE",
            "efecto": "El tribunal toma conocimiento del hecho, documento o personería señalada por la parte sin dar lugar a un incidente ni trámite ulterior obligatorio."
        },
        {
            "patron": r"como\s+se\s+pide(?:,\s*con\s+citaci[oó]n)?",
            "tipo": "COMO SE PIDE (CON CITACIÓN)",
            "efecto": "Se accede a la petición formulada. Si es 'con citación', rige el Art. 69 CPC: la contraria tiene 3 días fatales para oponerse antes de que la resolución se ejecute."
        },
        {
            "patron": r"traslado",
            "tipo": "TRASLADO",
            "efecto": "Se confiere traslado a la contraparte por el término legal (ordinariamente 3 días fatales, Art. 89 CPC) para que exponga lo que convenga a sus derechos."
        },
        {
            "patron": r"autos\s+para\s+fallo|c[ií]tese\s+para\s+o[ií]r\s+sentencia",
            "tipo": "CITACIÓN PARA OÍR SENTENCIA",
            "efecto": "Cierra el debate. Precluye la posibilidad de alegaciones o probanzas (Art. 433 CPC), quedando la causa en acuerdo o estudio para sentencia definitiva."
        },
        {
            "patron": r"a\s+lo\s+principal,?\s*(?:no\s+ha\s+lugar|estese\s+a\s+lo\s+resuelto)",
            "tipo": "NO HA LUGAR / ESTÉSE A LO RESUELTO",
            "efecto": "Rechazo de la petición principal o remisión a una resolución previa que ya dirimió la solicitud. Habilita recurso de reposición (Art. 181 CPC) si procede."
        },
        {
            "patron": r"of[íi]ciese",
            "tipo": "OFÍCIESE",
            "efecto": "Orden del juez para despachar oficio de información a una entidad pública o privada (Art. 348 CPC o prueba de informes)."
        },
        {
            "patron": r"bajo\s+apercibimiento",
            "tipo": "APERCIBIMIENTO",  # pragma: whitelist secret
            "efecto": "Intimación judicial bajo advertencia de sanción procesal (rebeldía, tener por desistido o multas) si la parte no cumple la orden en el plazo conferido."
        }
    ]

    def interpretar_proveido(self, texto_resolucion: str) -> Dict[str, Any]:
        """Interpreta el significado jurídico y la carga procesal de un proveído judicial chileno."""
        t = texto_resolucion.strip()
        matches = []

        for p in self.PROVEIDOS_CATALOGO:
            if re.search(p["patron"], t, re.IGNORECASE):
                matches.append({
                    "tipo": p["tipo"],
                    "efecto_procesal": p["efecto"]
                })

        if not matches:
            return {
                "texto": t,
                "clasificacion": "Decreto de sustanciación general",
                "efecto": "Providencia ordinaria de mero trámite procesal sin fórmula arquetípica detectada."
            }

        return {
            "texto": t,
            "total_formulas_detectadas": len(matches),
            "interpretaciones": matches
        }
