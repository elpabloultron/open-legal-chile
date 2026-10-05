"""
Open Legal Chile — Analizador Anatómico y Citador Canónico de Pronunciamientos Administrativos
(resoluciones_parser.py / dictamenes_parser.py)

Desglosa dictámenes, circulares, resoluciones y acuerdos de CGR, DT, SII, TDLC, CMF, Panel y SMA.
Permite evaluar y rankear consideraciones por tema jurídico controvertido y formatear citas
canónicas oficiales conforme al estándar de AGENTS.md con citas literales exactas («...»).
"""

import os
import re
from typing import Any, Dict, List, Optional


class ResolucionesParserEngine:
    """Motor analítico de resoluciones y dictámenes administrativos del Estado de Chile."""

    STOPWORDS = {
        "de", "la", "el", "en", "un", "una", "unos", "unas", "por", "los", "las", "y", "o",
        "que", "con", "para", "sobre", "del", "al", "se", "su", "sus", "es", "son", "fue",
        "este", "esta", "estos", "estas", "como", "pero", "mas", "a", "ante", "bajo", "cabe"
    }

    def parsear_resolucion(self, texto: str, organismo: str = "CGR") -> Dict[str, Any]:
        """Desglosa anatómicamente el texto de una resolución o dictamen administrativo."""
        if not texto or not isinstance(texto, str):
            return {"error": "Texto de resolución o dictamen vacío o inválido."}

        from resolucion_administrativa2md import segmentar_secciones_administrativas
        secciones = segmentar_secciones_administrativas(texto, organismo=organismo)

        return {
            "organismo": organismo.upper(),
            "antecedentes": secciones["antecedentes"],
            "marco_normativo": secciones["marco_normativo"],
            "total_parrafos": len(secciones["consideraciones"]),
            "todos_parrafos": secciones["consideraciones"],
            "conclusion": secciones["conclusion"]
        }

    def seleccionar_parrafo_relevante(
        self,
        parrafos: List[Dict[str, Any]],
        tema: str
    ) -> Optional[Dict[str, Any]]:
        """
        Rankea y selecciona el párrafo o consideración más pertinente de un dictamen frente
        a un tema controvertido (ej. 'confianza legítima', 'descuento de afc', 'ley karin').
        """
        if not parrafos:
            return None
        if not tema or not tema.strip():
            # Devuelve el último párrafo (suele ser la conclusión/criterio vinculante) o el primero de derecho
            for p in reversed(parrafos):
                if p.get("es_analisis_juridico"):
                    return p
            return parrafos[-1]

        tema_limpio = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+", " ", tema.lower())
        tokens = [t for t in tema_limpio.split() if len(t) > 2 and t not in self.STOPWORDS]

        mejor_p = None
        mejor_score = -1

        for idx, p in enumerate(parrafos):
            texto_p = (p.get("texto") or "").lower()
            score = 0

            # 1. Coincidencia de tokens
            for tok in tokens:
                if tok in texto_p:
                    score += 15

            # 2. Coincidencia de frase exacta
            if tema_limpio.strip() in texto_p:
                score += 60

            # 3. Bonus por ser análisis jurídico
            if p.get("es_analisis_juridico"):
                score += 20

            # 4. Bonus por mención de normas
            if re.search(r"art[íi]culo|ley|c[oó]digo|dictamen|doctrina|cpr|dfl|dl", texto_p):
                score += 15

            # 5. Bonus por posición final (conclusiva)
            if idx >= len(parrafos) - 2:
                score += 10

            if score > mejor_score:
                mejor_score = score
                mejor_p = p

        return mejor_p or parrafos[-1]

    def formatear_cita_canonica(
        self,
        parrafo_o_conclusion: Dict[str, Any],
        doc_info: Dict[str, Any],
        max_longitud: int = 350
    ) -> Dict[str, Any]:
        """
        Construye la cita canónica conforme a los estándares obligatorios de AGENTS.md:
        - CGR: [Dictamen CGR N° E123456 (2024), Fecha: ..., Conclusión: «...»]
        - CGR Auditoría: [CGR - Informe Final N° 123/2024, Fecha: ..., Hallazgo: «...»]
        - DT: [Dictamen DT N° 1234/15 de 2024, Fecha: ..., Doctrina: «...»]
        - SII Circular: [Circular SII N° 45 (2023), Fecha: ..., Instrucción: «...»]
        - SII Oficio: [Oficio SII N° 1234 (2024), Fecha: ..., Criterio: «...»]
        - TDLC: [TDLC - Sentencia N° 180/2022, Fecha: ..., Considerando X: «...»]
        - CMF: [NCG CMF N° 461, Fecha: ..., Norma: «...»]
        - Panel de Expertos: [Panel de Expertos - Dictamen N° 12-2023, Fecha: ..., Determinación: «...»]
        - SMA: [SMA - Expediente SNIFA D-045-2023, Fecha: ..., Cargo: «...»]
        """
        organismo = (doc_info.get("organismo") or "CGR").strip().upper()
        tipo_acto = (doc_info.get("tipo_acto") or "Dictamen").strip()
        ident = str(doc_info.get("identificador") or doc_info.get("numero") or doc_info.get("docId") or "S-N").strip()
        fecha = str(doc_info.get("fecha") or "").strip()
        anio = fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else ""
        link = doc_info.get("link_oficial") or doc_info.get("link") or doc_info.get("url") or doc_info.get("pdfUrl") or ""

        texto = parrafo_o_conclusion.get("texto") or doc_info.get("conclusion") or doc_info.get("materia") or ""

        # Extracto limpio
        extracto = texto.strip()
        if len(extracto) > max_longitud:
            corte_idx = extracto.rfind(".", 0, max_longitud)
            if corte_idx > int(max_longitud * 0.5):
                extracto = extracto[:corte_idx + 1]
            else:
                extracto = extracto[:max_longitud].rstrip() + "..."

        fecha_str = f", Fecha: {fecha}" if fecha else ""
        anio_str = f" ({anio})" if anio else ""

        ident_limpio = re.sub(
            r'^(?:circular|oficio|sentencia|dictamen|resoluci[oó]n|ncg|expediente\s+snifa)\s*(?:n[°ºo\.]*)?\s*',
            '', ident, flags=re.IGNORECASE
        ).strip()

        # Mapeo según AGENTS.md
        if organismo == "CGR":
            if "auditor" in tipo_acto.lower():
                corchete_base = f"[CGR - Informe Final N° {ident_limpio}{fecha_str}]"
                cita_canonica = f"[CGR - Informe Final N° {ident_limpio}{fecha_str}, Hallazgo: «{extracto}»]"
                etiqueta = "Hallazgo"
            else:
                corchete_base = f"[Dictamen CGR N° {ident_limpio}{anio_str}{fecha_str}]"
                cita_canonica = f"[Dictamen CGR N° {ident_limpio}{anio_str}{fecha_str}, Conclusión: «{extracto}»]"
                etiqueta = "Conclusión"

        elif organismo == "DT":
            ident_clean = ident_limpio.replace("ORD.", "").replace("ORD", "").replace("N°", "").strip()
            corchete_base = f"[Dictamen DT N° {ident_clean}{fecha_str}]"
            cita_canonica = f"[Dictamen DT N° {ident_clean}{fecha_str}, Doctrina: «{extracto}»]"
            etiqueta = "Doctrina"

        elif organismo == "SII":
            if "circular" in tipo_acto.lower():
                corchete_base = f"[Circular SII N° {ident_limpio}{anio_str}{fecha_str}]"
                cita_canonica = f"[Circular SII N° {ident_limpio}{anio_str}{fecha_str}, Instrucción: «{extracto}»]"
                etiqueta = "Instrucción"
            else:
                corchete_base = f"[Oficio SII N° {ident_limpio}{anio_str}{fecha_str}]"
                cita_canonica = f"[Oficio SII N° {ident_limpio}{anio_str}{fecha_str}, Criterio: «{extracto}»]"
                etiqueta = "Criterio"

        elif organismo == "TDLC":
            corchete_base = f"[TDLC - {tipo_acto} N° {ident_limpio}{fecha_str}]"
            cita_canonica = f"[TDLC - {tipo_acto} N° {ident_limpio}{fecha_str}, Resolutivo: «{extracto}»]"
            etiqueta = "Resolutivo"

        elif organismo == "CMF":
            if "ncg" in tipo_acto.lower() or "norma" in tipo_acto.lower():
                corchete_base = f"[NCG CMF N° {ident_limpio}{fecha_str}]"
                cita_canonica = f"[NCG CMF N° {ident_limpio}{fecha_str}, Disposición: «{extracto}»]"
                etiqueta = "Disposición"
            else:
                corchete_base = f"[Resolución CMF N° {ident_limpio}{anio_str}{fecha_str}]"
                cita_canonica = f"[Resolución CMF N° {ident_limpio}{anio_str}{fecha_str}, Sanción: «{extracto}»]"
                etiqueta = "Sanción"

        elif organismo == "PANEL":
            corchete_base = f"[Panel de Expertos - Dictamen N° {ident_limpio}{fecha_str}]"
            cita_canonica = f"[Panel de Expertos - Dictamen N° {ident_limpio}{fecha_str}, Determinación: «{extracto}»]"
            etiqueta = "Determinación"

        elif organismo == "SMA":
            corchete_base = f"[SMA - Expediente SNIFA {ident_limpio}{fecha_str}]"
            cita_canonica = f"[SMA - Expediente SNIFA {ident_limpio}{fecha_str}, Infracción: «{extracto}»]"
            etiqueta = "Infracción"

        else:
            corchete_base = f"[{organismo} - {tipo_acto} N° {ident_limpio}{fecha_str}]"
            cita_canonica = f"[{organismo} - {tipo_acto} N° {ident_limpio}{fecha_str}, Doctrina: «{extracto}»]"
            etiqueta = "Doctrina"

        return {
            "corchete": corchete_base,
            "cita_canonica": cita_canonica,
            "organismo": organismo,
            "tipo_acto": tipo_acto,
            "identificador": ident,
            "fecha": fecha,
            "etiqueta_seccion": etiqueta,
            "extracto_literal": extracto,
            "texto_completo": texto,
            "enlace_oficial": link
        }

    def analizar_lote_resoluciones(
        self,
        lista_docs: List[Dict[str, Any]],
        tema_relevante: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza un conjunto de dictámenes o resoluciones regulatorias, segmenta consideraciones
        y selecciona el criterio más relevante para construir una línea doctrinal uniforme.
        """
        resultados = []
        citas_destacadas = []

        for d in lista_docs:
            organismo = d.get("organismo") or "CGR"
            texto_doc = d.get("texto_integral") or d.get("texto") or d.get("documento") or d.get("materia") or ""
            info_parseada = self.parsear_resolucion(texto_doc, organismo=organismo) if texto_doc else {}

            meta = {
                "organismo": organismo,
                "tipo_acto": d.get("tipo_acto") or "Dictamen",
                "identificador": d.get("identificador") or d.get("numero") or d.get("docId") or "S-N",
                "fecha": d.get("fecha") or "",
                "materia": d.get("materia") or d.get("titulo") or "",
                "link_oficial": d.get("link_oficial") or d.get("link") or d.get("url") or d.get("pdfUrl") or ""
            }

            parrafos = info_parseada.get("todos_parrafos") or []
            parrafo_elegido = None
            cita_info = None

            if parrafos:
                parrafo_elegido = self.seleccionar_parrafo_relevante(parrafos, tema_relevante or "")
            elif info_parseada.get("conclusion"):
                parrafo_elegido = {"texto": info_parseada["conclusion"], "es_analisis_juridico": True}

            if parrafo_elegido:
                cita_info = self.formatear_cita_canonica(parrafo_elegido, meta)
                citas_destacadas.append(cita_info)

            resultados.append({
                "metadatos": meta,
                "estructura": {
                    "total_parrafos": len(parrafos),
                    "marco_normativo": info_parseada.get("marco_normativo", []),
                    "conclusion": info_parseada.get("conclusion", "")
                },
                "doctrina_destacada": cita_info
            })

        return {
            "total_documentos_analizados": len(lista_docs),
            "tema_evaluado": tema_relevante or "General / Doctrina Vinculante",
            "citas_destacadas": citas_destacadas,
            "documentos": resultados
        }


# Alias
DictamenesParserEngine = ResolucionesParserEngine
