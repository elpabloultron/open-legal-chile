"""
Open Legal Chile — Espacios de Trabajo de Caso (case_workspace.py)
Crea y gestiona la estructura local y privada de cada caso o consulta procesal.
Convierte antecedentes a Markdown canónico (RAE/ASALE y BCN), consulta y enriquece
con Hugging Face, y sincroniza el subgrafo ontológico dinámico con LegalGraphify.
"""

from __future__ import annotations

import os
import re
import json
import shutil
import datetime as dt
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from case_graph import CaseGraphEngine
from doc2md_ingestor import extract_text_from_source, clean_unwanted_hyphens_and_breaks, apply_ortotipografia_rae_chile, standardize_legal_citations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASES_BASE_DIR = Path(os.environ.get("OPENLEGAL_CASES_DIR") or os.path.join(BASE_DIR, "casos"))


def slugify(texto: str, max_palabras: int = 4) -> str:
    """Genera un slug breve y limpio en minúsculas para nombres de directorio."""
    limpio = re.sub(r"[^\w\s-]", "", (texto or "").lower()).strip()
    palabras = [p for p in re.split(r"[\s_]+", limpio) if p and len(p) > 2]
    if not palabras:
        return "caso-general"
    return "-".join(palabras[:max_palabras])


def generar_id_caso(entrada: str, roles: Optional[List[str]] = None, materia: Optional[str] = None) -> str:
    """Genera un identificador intuitivo y breve para el caso (prioriza Rol/RIT; si no, fecha + materia)."""
    # 1. Si hay roles explícitos o detectables
    roles_candidatos = list(roles or [])
    if not roles_candidatos and entrada:
        m = re.search(r"\b([A-Z])[-–]\s?(\d{1,6})[-–]\s?(\d{4})\b", entrada)
        if m:
            roles_candidatos.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        else:
            m_num = re.search(r"\b(\d{1,6})[-–]\s?(\d{4})\b", entrada)
            if m_num:
                roles_candidatos.append(f"{m_num.group(1)}-{m_num.group(2)}")

    if roles_candidatos:
        r = roles_candidatos[0].lower().replace(" ", "").replace("–", "-")
        # Si la entrada decía expresamente "rol" o la letra es típica de rol civil (C-)
        if "rol" in entrada.lower() or re.match(r"^[c]-", r):
            return f"rol-{r}"
        elif re.match(r"^[tosmfl]-", r):
            return f"rit-{r}"
        return f"rol-{r}"

    # 2. Si no hay Rol/RIT: fecha de hoy + slug de materia o consulta
    hoy = dt.date.today().isoformat()
    slug = slugify(materia or entrada or "caso")
    return f"{hoy}-{slug}"


class CaseWorkspace:
    """Manejador del espacio de trabajo local de un caso procesal."""

    def __init__(self, workspace_path: Path | str, id_caso: Optional[str] = None):
        self.path = Path(workspace_path)
        self.id_caso = id_caso or self.path.name
        self.raw_dir = self.path / "documentos_raw"
        self.md_dir = self.path / "markdown"
        self.grafo_dir = self.path / "grafo"
        self.salidas_dir = self.path / "salidas"
        self.meta_file = self.path / "caso.json"

        self._asegurar_estructura()
        self.graph_engine = CaseGraphEngine(self.path)

    def _asegurar_estructura(self) -> None:
        """Crea los directorios del caso si no existen."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.md_dir.mkdir(parents=True, exist_ok=True)
        self.grafo_dir.mkdir(parents=True, exist_ok=True)
        self.salidas_dir.mkdir(parents=True, exist_ok=True)

    def guardar_metadatos(self, meta: Dict[str, Any]) -> None:
        """Escribe o actualiza los metadatos en caso.json."""
        existente = self.leer_metadatos()
        existente.update(meta)
        existente["id_caso"] = self.id_caso
        existente["fecha_actualizacion"] = dt.date.today().isoformat()
        if "fecha_creacion" not in existente:
            existente["fecha_creacion"] = dt.date.today().isoformat()
        self.meta_file.write_text(json.dumps(existente, ensure_ascii=False, indent=2), encoding="utf-8")

    def leer_metadatos(self) -> Dict[str, Any]:
        """Lee los metadatos de caso.json si existe."""
        if self.meta_file.exists():
            try:
                return json.loads(self.meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"id_caso": self.id_caso}

    def agregar_documento(self, ruta_origen: str | Path, nombre_destino: Optional[str] = None) -> Dict[str, Any]:
        """
        Copia un documento original a documentos_raw/, lo transforma a Markdown canónico
        (limpieza RAE/ASALE y extracción de citas BCN) en markdown/, y actualiza el subgrafo.
        """
        origen = Path(ruta_origen).expanduser().resolve()
        if not origen.exists() or not origen.is_file():
            raise FileNotFoundError(f"No existe el documento en '{ruta_origen}'")

        nombre_archivo = nombre_destino or origen.name
        destino_raw = self.raw_dir / nombre_archivo
        shutil.copy2(origen, destino_raw)

        # Extracción y conversión a Markdown canónico
        texto_crudo = extract_text_from_source(str(destino_raw))
        texto_limpio = clean_unwanted_hyphens_and_breaks(texto_crudo)
        texto_normalizado = standardize_legal_citations(apply_ortotipografia_rae_chile(texto_limpio))

        stem = destino_raw.stem
        destino_md = self.md_dir / f"{stem}.md"
        cabecera = f"# Documento: {destino_raw.name}\n\n**Fecha de ingesta:** {dt.date.today().isoformat()}\n\n---\n\n"
        destino_md.write_text(cabecera + texto_normalizado, encoding="utf-8")

        # Actualizar subgrafo ontológico del caso
        resumen_grafo = self.actualizar_grafo()

        return {
            "documento_raw": str(destino_raw),
            "documento_md": str(destino_md),
            "caracteres": len(texto_normalizado),
            "grafo": resumen_grafo,
        }

    def enriquecer_con_huggingface(self, consulta: str, materia: Optional[str] = None, max_fuentes: int = 4) -> Dict[str, Any]:
        """
        Consulta en el dataset canónico de Hugging Face (doctrina, guías AJ y jurisprudencia unificada)
        y almacena las citas y extractos en markdown/fuentes_hf.md, actualizando el subgrafo.
        """
        from online_library_sync import consultar_huggingface_dataset

        termino_busqueda = consulta or materia or self.leer_metadatos().get("materia", "derecho")
        try:
            resultados = consultar_huggingface_dataset(termino_busqueda, limit=max_fuentes)
        except Exception as e:
            resultados = {"resultados": [], "citas": [], "error": str(e)}

        fuentes_md = self.md_dir / "fuentes_hf.md"
        bloques = [f"# Fuentes Doctrinales y Jurisprudenciales — Hugging Face\n\n**Término de consulta:** {termino_busqueda}\n**Fecha:** {dt.date.today().isoformat()}\n\n---\n"]

        # Con el mapa del corpus, cada archivo se cita con la URL fijada a la revisión de la fuente
        # que se leyó (la vigente puede cambiar después).
        urls = {str(i.get("archivo") or ""): str(i.get("url_huggingface") or "")
                for i in resultados.get("resultados", []) if i.get("url_huggingface")}
        # Las citas de la consulta traen la URL (fijada) y no el archivo: se recupera por la URL.
        archivo_de_url = {url: archivo for archivo, url in urls.items()}
        citas_registradas = []
        for extracto in resultados.get("citas", []):
            cita = extracto.get("formato") or extracto.get("cita", "[Hugging Face]")
            archivo = extracto.get("archivo") or archivo_de_url.get(str(extracto.get("url") or ""), "")
            texto = (extracto.get("texto") or "").strip()
            registro = {"cita": cita, "archivo": archivo}
            if urls.get(archivo):
                registro["url"] = urls[archivo]
            citas_registradas.append(registro)
            enlace = f"\n*URL fijada:* {urls[archivo]}" if urls.get(archivo) else ""
            bloques.append(f"### {cita}\n\n*Archivo:* `{archivo}`{enlace}\n\n> {texto}\n\n---\n")

        for item in resultados.get("resultados", []):
            cita_est = item.get("cita_estandar") or item.get("cita", "[Hugging Face]")
            if not any(c["cita"] == cita_est for c in citas_registradas):
                arch = item.get("archivo", "")
                registro = {"cita": cita_est, "archivo": arch}
                if item.get("url_huggingface"):
                    registro["url"] = item["url_huggingface"]
                citas_registradas.append(registro)
                enlace = f"\n*URL fijada:* {item['url_huggingface']}" if item.get("url_huggingface") else ""
                bloques.append(f"### {cita_est}\n\n*Archivo:* `{arch}`{enlace}\n\n---\n")

        fuentes_md.write_text("\n".join(bloques), encoding="utf-8")

        # Guardar en caso.json
        meta = self.leer_metadatos()
        meta["fuentes_huggingface"] = citas_registradas
        mapa = resultados.get("mapa") or {}
        if mapa.get("activo"):
            # Qué revisión del corpus respaldó estas fuentes: deja el caso reproducible.
            meta["corpus_huggingface"] = {k: mapa.get(k) for k in ("revision", "sha_fuente", "fecha_fuente")}
        self.guardar_metadatos(meta)

        # Actualizar subgrafo con las nuevas fuentes
        resumen_grafo = self.actualizar_grafo()

        return {
            "archivo_md": str(fuentes_md),
            "total_fuentes": len(citas_registradas),
            "citas": [c["cita"] for c in citas_registradas],
            "grafo": resumen_grafo,
        }

    def actualizar_grafo(self) -> Dict[str, Any]:
        """Sincroniza el grafo ontológico local del caso a partir de markdown/."""
        meta = self.leer_metadatos()
        return self.graph_engine.construir_o_actualizar(meta)

    def obtener_resumen(self) -> Dict[str, Any]:
        """Entrega un resumen completo del estado del workspace."""
        meta = self.leer_metadatos()
        docs_raw = [f.name for f in self.raw_dir.iterdir() if f.is_file()]
        docs_md = [f.name for f in self.md_dir.iterdir() if f.is_file()]
        resumen_grafo = self.graph_engine._guardar_y_resumir() if (self.grafo_dir / "grafo_caso.json").exists() else self.actualizar_grafo()

        return {
            "id_caso": self.id_caso,
            "ruta_workspace": str(self.path),
            "metadatos": meta,
            "documentos_raw": docs_raw,
            "documentos_markdown": docs_md,
            "grafo": resumen_grafo,
        }


def crear_o_cargar_caso(entrada: str, consulta: str = "", metadatos: Optional[Dict[str, Any]] = None,
                        directorio_base: Optional[Path] = None) -> CaseWorkspace:
    """Punto de entrada principal para crear o abrir el espacio de trabajo local de un caso."""
    base = Path(directorio_base or CASES_BASE_DIR)
    base.mkdir(parents=True, exist_ok=True)

    meta = dict(metadatos or {})
    roles = meta.get("roles") or []
    materia = meta.get("materia") or ""

    id_caso = meta.get("id_caso") or generar_id_caso(entrada, roles=roles, materia=materia)
    workspace_path = base / id_caso

    ws = CaseWorkspace(workspace_path, id_caso=id_caso)
    meta.setdefault("id_caso", id_caso)
    meta.setdefault("entrada_original", entrada[:300])
    if consulta:
        meta.setdefault("consulta", consulta)
    ws.guardar_metadatos(meta)

    # Si la entrada es un archivo o directorio existente, ingestar sus documentos automáticamente
    p_entrada = Path(entrada).expanduser()
    if p_entrada.exists():
        if p_entrada.is_file():
            try:
                ws.agregar_documento(p_entrada)
            except Exception:
                pass
        elif p_entrada.is_dir():
            for f in sorted(p_entrada.glob("*")):
                if f.is_file() and f.suffix.lower() in {".pdf", ".docx", ".txt", ".md"}:
                    try:
                        ws.agregar_documento(f)
                    except Exception:
                        pass

    # Enriquecer automáticamente con Hugging Face
    try:
        ws.enriquecer_con_huggingface(consulta=consulta or entrada, materia=materia)
    except Exception:
        pass

    ws.actualizar_grafo()
    return ws

