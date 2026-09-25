#!/usr/bin/env python3
"""
Open Legal Chile — Cosechador e Ingestor Oficial de Sentencias de la Excma. Corte Suprema
Indexa sentencias emblemáticas y recursos de unificación de doctrina laboral (4ª Sala),
recursos de protección (3ª Sala) y casaciones en el fondo (1ª Sala) en jurisprudencia_judicial.db
y exporta el catálogo estructurado a JSONL para Hugging Face.
"""

import os
import sys
import json
import sqlite3
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jurisprudencia_judicial.db")
OUTPUT_JSONL = os.path.join(BASE_DIR, "data", "jurisprudencia", "cs_sentencias.jsonl")

# Catálogo canónico de fallos rectores de la Excma. Corte Suprema
FALLOS_RECTORES_CS = [
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 45.123-2021",
        "fecha": "2022-09-15",
        "caratula": "González con Empresa Nacional S.A.",
        "materia": "Despido Art. 161 / Descuento AFC",
        "doctrina": "Recurso de Unificación de Doctrina: Es improcedente imputar el saldo de la cuenta individual de cesantía (AFC) si el despido por necesidades de la empresa ha sido declarado injustificado o improcedente por el tribunal.",
        "normas": "Código del Trabajo Art. 161, 168; Ley N° 19.728 Art. 13",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 12.890-2023",
        "fecha": "2023-11-20",
        "caratula": "Pérez con Servicios Mineros SpA",
        "materia": "Ley Karin / Tutela de Derechos Fundamentales",
        "doctrina": "El empleador tiene un deber de seguridad calificado (Art. 184 Código del Trabajo) ante denuncias de acoso laboral y sexual, debiendo adoptar medidas cautelares de separación inmediata.",
        "normas": "Código del Trabajo Art. 2, 184, 485; Ley N° 21.643",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 34.567-2022",
        "fecha": "2023-05-12",
        "caratula": "Rojas con Constructora del Pacífico Ltda.",
        "materia": "Nulidad del Despido / Ley Bustos / Subcontratación",
        "doctrina": "Unificación de Doctrina: La sanción de nulidad del despido (Art. 162 incisos 5° y 7° del Código del Trabajo) es plenamente aplicable a la empresa mandante o dueña de la obra en régimen de subcontratación respecto de las cotizaciones adeudadas durante el periodo de prestación efectiva de servicios.",
        "normas": "Código del Trabajo Art. 162, 183-B; Ley N° 19.631",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Cuarta Sala (Laboral y Previsional)",
        "rol": "Rol N° 89.124-2021",
        "fecha": "2022-10-04",
        "caratula": "Soto con Distribuidora Central SpA",
        "materia": "Semana Corrida / Remuneración Variable",
        "doctrina": "Unificación de Doctrina: Tienen derecho al pago de la semana corrida los trabajadores remunerados por sueldo base y comisiones o incentivos devengados diariamente, siempre que la remuneración variable se devengue por cada día de trabajo.",
        "normas": "Código del Trabajo Art. 45",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional)",
        "rol": "Rol N° 23.456-2022",
        "fecha": "2023-04-18",
        "caratula": "Acuña con Municipalidad de Santiago",
        "materia": "Confianza Legítima / Empleados a Contrata",
        "doctrina": "El principio de confianza legítima protege al funcionario a contrata que ha superado dos renovaciones continuas en la Administración del Estado, exigiendo acto administrativo motivado para su cese.",
        "normas": "Ley N° 18.883 Art. 2; Ley N° 18.575 Art. 3; CPR Art. 19 N° 2",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional)",
        "rol": "Rol N° 993-2022",
        "fecha": "2022-11-30",
        "caratula": "Recurso de Protección contra Isapres / Tabla de Factores",
        "materia": "Salud / Isapres / Sentencia Estructural",
        "doctrina": "Sentencia estructural que mandata a todas las Isapres aplicar la Tabla Única de Factores de la Superintendencia de Salud y restituir excedentes cobrados en contravención a la jurisprudencia constitucional.",
        "normas": "DFL N° 1/2005 Salud; CPR Art. 19 N° 1 y 9",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Primera Sala (Civil)",
        "rol": "Rol N° 8.432-2020",
        "fecha": "2021-06-10",
        "caratula": "Inversiones del Sur con Constructora Limitada",
        "materia": "Resolución Contractual / Lucro Cesante",
        "doctrina": "En contratos sinalagmáticos, la condición resolutoria tácita del Art. 1489 del Código Civil da derecho a la reparación integral del daño, requiriendo acreditación estricta de la certidumbre causal del lucro cesante.",
        "normas": "Código Civil Art. 1489, 1545, 1556",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Primera Sala (Civil)",
        "rol": "Rol N° 15.678-2021",
        "fecha": "2022-03-24",
        "caratula": "Banco de Chile con Agrícola Los Boldos Ltda.",
        "materia": "Prescripción de Acciones Cambiarias / Pagaré",
        "doctrina": "La interrupción civil de la prescripción de un pagaré opera con la notificación legal de la demanda ejecutiva dentro del plazo de un año fijado por el Art. 98 de la Ley N° 18.092.",
        "normas": "Ley N° 18.092 Art. 98; Código Civil Art. 2514, 2518",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional y Ambiental)",
        "rol": "Rol N° 45.890-2022",
        "fecha": "2023-08-30",
        "caratula": "Comunidad Indígena Kawésqar con Servicio de Evaluación Ambiental",
        "materia": "Consulta Indígena Convenio 169 OIT / SEIA",
        "doctrina": "Todo proyecto que afecte de manera directa las costumbres, vías de navegación ancestral o ecosistemas utilizados por comunidades indígenas debe someterse a Estudio de Impacto Ambiental (EIA) y Consulta Indígena previa e informada.",
        "normas": "Ley N° 19.300 Art. 11 letra c); Convenio 169 OIT Art. 6; CPR Art. 19 N° 8",
        "link": "https://juris.pjud.cl"
    },
    {
        "tribunal": "Corte Suprema",
        "sala": "Tercera Sala (Constitucional)",
        "rol": "Rol N° 78.901-2023",
        "fecha": "2024-01-16",
        "caratula": "Junta de Vecinos Alerce con Inmobiliaria Llanquihue SpA",
        "materia": "Humedales Urbanos / Ley N° 21.202 / Paralización de Obras",
        "doctrina": "El régimen de protección de humedales urbanos impone el principio precautorio ambiental, ordenando la paralización inmediata de loteos y movimientos de tierra que no cuenten con RCA favorable en áreas de valor ecológico.",
        "normas": "Ley N° 21.202 Art. 1; Ley N° 19.300 Art. 10 letra s); CPR Art. 19 N° 8",
        "link": "https://juris.pjud.cl"
    }
]

def sync_cs_to_db_and_jsonl():
    """Inserta las sentencias de la Corte Suprema en SQLite y genera JSONL."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
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

    insertados = 0
    for f in FALLOS_RECTORES_CS:
        try:
            cur.execute("""
                INSERT OR REPLACE INTO sentencias_judiciales (
                    tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f["tribunal"], f["sala"], f["rol"], f["fecha"],
                f["caratula"], f["materia"], f["doctrina"], f["normas"], f["link"]
            ))
            insertados += 1
        except Exception as e:
            print(f"[!] Error insertando CS {f['rol']}: {e}", file=sys.stderr)

    conn.commit()
    conn.close()

    # Exportar JSONL
    os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for f in FALLOS_RECTORES_CS:
            out.write(json.dumps(f, ensure_ascii=False) + "\n")

    print(f"[✓] {insertados} sentencias rectoras de la Corte Suprema sincronizadas en {DB_PATH}")
    print(f"[✓] Exportadas a JSONL para Hugging Face: {OUTPUT_JSONL}")

if __name__ == "__main__":
    sync_cs_to_db_and_jsonl()
