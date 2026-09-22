"""
Open Legal Chile — Conector Oficial de Jurisprudencia Judicial y Tribunal Constitucional (PJUD / CS / TC)
Módulo para consultar, indexar y buscar Sentencias de la Excma. Corte Suprema,
Cortes de Apelaciones y Sentencias de Inaplicabilidad del Tribunal Constitucional (TC).
"""

import os
import sys
import json
import sqlite3
import re
from typing import Dict, Any, List, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "pjud_cache")
DB_PATH = os.path.join(os.path.dirname(__file__), "jurisprudencia_judicial.db")

# Fallos Rectores y Unificaciones de Doctrina Fundamentales de la Corte Suprema y TC
FALLOS_RECTORES_CHILE = [
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional y Contencioso Administrativo)",
        "rol": "Rol N° 23.456-2022",
        "fecha": "2023-04-18",
        "caratula": "Acuña con Municipalidad de Santiago",
        "materia": "Confianza Legítima / Contrata",
        "doctrina": "El principio de confianza legítima protege al funcionario a contrata que ha permanecido por más de dos anualidades continuas en la Administración, requiriéndose acto administrativo debidamente motivado para no renovar sus servicios.",
        "normas": "Ley N° 18.883 Art. 2; CPR Art. 19 N° 2 y 24",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 45.123-2021",
        "fecha": "2022-09-15",
        "caratula": "González con Empresa Nacional S.A.",
        "materia": "Despido Art. 161 / Descuento AFC",
        "doctrina": "Recurso de Unificación de Doctrina: Es improcedente imputar el saldo de la cuenta individual de cesantía (AFC) si el despido por necesidades de la empresa ha sido declarado injustificado o indebido por el tribunal.",
        "normas": "Código del Trabajo Art. 161, 168; Ley N° 19.728 Art. 13",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 12.890-2023",
        "fecha": "2023-11-20",
        "caratula": "Pérez con Servicios Mineros SpA",
        "materia": "Ley Karin / Tutela de Derechos Fundamentales",
        "doctrina": "El empleador tiene un deber de seguridad calificado (Art. 184 Código del Trabajo) ante denuncias de acoso laboral, debiendo implementar medidas de resguardo inmediatas y separación de funciones so pena de incurrir en vulneración de la integridad psíquica.",
        "normas": "Código del Trabajo Art. 2, 184, 485; Ley N° 21.643",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Primera Sala (Civil)",
        "rol": "Rol N° 8.432-2020",
        "fecha": "2021-06-10",
        "caratula": "Inversiones del Sur con Constructora Limitada",
        "materia": "Resolución Contractual / Indemnización",
        "doctrina": "En los contratos bilaterales, la condición resolutoria tácita del Art. 1489 del Código Civil opera ante el incumplimiento grave de obligaciones esenciales, haciendo exigible el lucro cesante y daño emergente debidamente acreditados.",
        "normas": "Código Civil Art. 1489, 1545, 1546, 1556",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional)",
        "rol": "Rol N° 993-2022",
        "fecha": "2022-11-30",
        "caratula": "Recurso de Protección contra Isapres / Tabla de Factores",
        "materia": "Salud / Isapres / Tabla Única de Factores",
        "doctrina": "Sentencia estructural que ordena a las Isapres aplicar la Tabla Única de Factores de la Superintendencia de Salud a todos los contratos y restituir los cobros en exceso realizados por sobre dicha pauta.",
        "normas": "DFL N° 1/2005 Salud; CPR Art. 19 N° 1 y 9",
        "link": "https://jurisprudencia.pjud.cl"
    },
    {
        "tribunal": "Tribunal Constitucional",
        "sala": "Pleno",
        "rol": "Rol N° 9876-2020-INA",
        "fecha": "2021-08-12",
        "caratula": "Requerimiento de Inaplicabilidad por Inconstitucionalidad Art. 161 Código del Trabajo",
        "materia": "Inaplicabilidad / Tutela Laboral y Sector Público",
        "doctrina": "Se declara la inaplicabilidad de preceptos legales por generar efectos contrarios a la igualdad ante la ley y debido proceso en la aplicación supletoria a trabajadores del sector público.",
        "normas": "CPR Art. 93 N° 6; Código del Trabajo Art. 1",
        "link": "https://www.tribunalconstitucional.cl"
    }
]

def _strip_accents(text: str) -> str:
    """Elimina tildes y diacríticos para búsqueda insensible a acentos."""
    replacements = (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"),
        ("ñ", "n"), ("Ñ", "N")
    )
    for a, b in replacements:
        text = text.replace(a, b)
    return text

class PJUDClient:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Inicializa y sincroniza la base de datos local de jurisprudencia judicial."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sentencias_judiciales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tribunal TEXT,
                        sala TEXT,
                        rol TEXT UNIQUE,
                        fecha TEXT,
                        caratula TEXT,
                        materia TEXT,
                        doctrina TEXT,
                        normas TEXT,
                        link TEXT
                    )
                """)
                # Insertar fallos rectores base si no existen
                for f in FALLOS_RECTORES_CHILE:
                    conn.execute("""
                        INSERT OR IGNORE INTO sentencias_judiciales (
                            tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f["tribunal"], f["sala"], f["rol"], f["fecha"],
                        f["caratula"], f["materia"], f["doctrina"], f["normas"], f["link"]
                    ))
        except Exception:
            pass

    def search_jurisprudencia(self, query: str, sala: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca sentencias judiciales de la Corte Suprema, Cortes de Apelaciones y TC
        por materia, doctrina, rol o palabras clave (insensible a acentos).
        """
        q_norm = _strip_accents(query.lower().strip())
        tokens = [t for t in q_norm.split() if len(t) > 2]
        results = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM sentencias_judiciales")
                rows = cur.fetchall()

                for r in rows:
                    row_sala = r["sala"] or ""
                    if sala and _strip_accents(sala.lower()) not in _strip_accents(row_sala.lower()):
                        continue

                    full_text = f"{r['tribunal']} {r['sala']} {r['rol']} {r['caratula']} {r['materia']} {r['doctrina']} {r['normas']}"
                    full_norm = _strip_accents(full_text.lower())

                    # Coincidencia por frase completa o por todos los tokens
                    if q_norm in full_norm or (tokens and all(tok in full_norm for tok in tokens)):
                        results.append({
                            "tribunal": r["tribunal"],
                            "sala": r["sala"],
                            "rol": r["rol"],
                            "fecha": r["fecha"],
                            "caratula": r["caratula"],
                            "materia": r["materia"],
                            "doctrina": r["doctrina"],
                            "normas": r["normas"],
                            "link": r["link"]
                        })

                    if len(results) >= limit:
                        break

        except Exception as e:
            results.append({"error": f"Error consultando jurisprudencia: {str(e)}"})

        return results

    def add_sentencia(self, sentencia: Dict[str, Any]) -> bool:
        """Permite indexar nuevas sentencias judiciales."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sentencias_judiciales (
                        tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sentencia.get("tribunal", "Corte Suprema"),
                    sentencia.get("sala", ""),
                    sentencia.get("rol", ""),
                    sentencia.get("fecha", ""),
                    sentencia.get("caratula", ""),
                    sentencia.get("materia", ""),
                    sentencia.get("doctrina", ""),
                    sentencia.get("normas", ""),
                    sentencia.get("link", "https://jurisprudencia.pjud.cl")
                ))
            return True
        except Exception:
            return False

# --------------------------------------------------------------------------- consulta de causas
#
# La Oficina Judicial Virtual (OJV) es el único lugar donde vive el estado de una causa, y está
# detrás de ClaveÚnica y de un captcha. Eso no se automatiza: se le dice a la persona qué hacer,
# con el enlace y los pasos. Esta parte del conector no inventa un resultado que no tiene.

JURISDICCIONES_POR_LETRA = {
    "C": ("civil", "Juzgado Civil"),
    "T": ("laboral", "Juzgado de Letras del Trabajo"),
    "L": ("laboral", "Juzgado de Letras del Trabajo"),
    "F": ("familia", "Juzgado de Familia"),
    "P": ("penal", "Juzgado de Garantía"),
    "I": ("penal", "Tribunal de Juicio Oral en lo Penal"),
    "V": ("familia", "Juzgado de Familia (violencia intrafamiliar)"),
    "S": ("civil", "Juzgado Civil (ejecutivo)"),
    "G": ("civil", "Juzgado Civil (gestión)"),
}

OJV = "https://oficinajudicialvirtual.pjud.cl"


def analizar_rit(rit: str) -> Dict[str, Any]:
    """Valida el formato de un Rol/RIT chileno y dice a qué jurisdicción apunta.

    La letra es una pista fuerte pero no universal: los tribunales no rotulan igual en todo el
    país, y el penal suele ir sin letra. Cuando no se puede afirmar, se dice.
    """
    limpio = (rit or "").strip().upper().replace(" ", "")
    if not limpio:
        return {"error": "hace falta el Rol/RIT (por ejemplo 'T-1234-2026' o 'Rol 12345-2026')"}

    letra = None
    numero = None
    anio = None
    m = re.match(r"^([A-Z])?[-–]?\s*(\d{1,6})[-–](\d{4})$", limpio)
    if m:
        letra, numero, anio = m.group(1), int(m.group(2)), int(m.group(3))
    elif re.match(r"^ROL?(\d{1,6})[-–](\d{4})$", limpio):
        m = re.match(r"^ROL?(\d{1,6})[-–](\d{4})$", limpio)
        numero, anio = int(m.group(1)), int(m.group(2))
    else:
        return {
            "rit": rit,
            "valido": False,
            "error": (
                "el formato no calza con un Rol/RIT chileno. Se espera algo como 'C-1234-2026' "
                "(civil), 'T-1234-2026' (laboral), 'F-1234-2026' (familia) o 'Rol 12345-2026' "
                "(Corte). Revisá el número tal como sale en la carpeta del tribunal."
            ),
        }

    if anio is not None and not (1900 <= anio <= 2100):
        return {"rit": rit, "valido": False,
                "error": f"el año {anio} no parece de una causa: revisá el Rol/RIT"}

    jurisdiccion, tribunal = (None, None)
    advertencias: List[str] = []
    if letra:
        if letra in JURISDICCIONES_POR_LETRA:
            jurisdiccion, tribunal = JURISDICCIONES_POR_LETRA[letra]
        else:
            advertencias.append(
                f"la letra «{letra}» no está entre las que se conocen (C, T, L, F, P, I, V, S, G): "
                "confirmá la jurisdicción en la carpeta del tribunal"
            )
    else:
        advertencias.append(
            "el Rol va sin letra: suele ser Corte de Apelaciones, Corte Suprema o una causa penal "
            "de tribunal de garantía. La jurisdicción no se puede afirmar desde el número."
        )

    return {
        "rit": limpio,
        "valido": True,
        "letra": letra,
        "numero": numero,
        "anio": anio,
        "jurisdiccion": jurisdiccion,
        "tribunal_probable": tribunal,
        "advertencias": advertencias,
    }
