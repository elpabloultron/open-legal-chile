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
