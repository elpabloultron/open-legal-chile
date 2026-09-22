"""Mesa de entrada: de un caso a un plan de herramientas.

Entra una carpeta de expediente, un texto pegado o una consulta en lenguaje natural, y sale un
PLAN: de qué se trata, qué herramientas usar y en qué orden, y qué falta para poder avanzar.

La decisión de la materia y del plan es **código, no modelo**: reglas, patrones de Rol/RIT y
palabras clave del derecho chileno. Así no depende de que el modelo tenga un buen día, se puede
probar, y el modelo queda para lo que sí sabe hacer: narrar, repreguntar y redactar.

Dos reglas de la casa, acá más que en ninguna parte:

* **Avisar, no inventar.** Si no alcanza la información para decidir la materia, se dice «no
  alcanza» y se enumeran los datos que faltan; no se elige la materia más parecida.
* **Una señal no basta.** La letra del RIT es una pista fuerte pero no universal (los tribunales
  no rotulan igual en todo el país), así que se pide concordancia entre letra, palabras clave e
  instituciones antes de afirmar una materia.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- señales

# Letra del RIT/Rol y su materia habitual. Es una pista, no una verdad revelada: en varios
# tribunales el penal no lleva letra y el Rol de Corte tampoco. Por eso el peso.
LETRAS_RIT: Dict[str, str] = {
    "C": "civil",
    "T": "laboral",
    "L": "laboral",
    "F": "familia",
    "P": "penal",
    "I": "penal",
    "V": "familia",       # violencia intrafamiliar, en los tribunales que la rotulan así
    "S": "civil",         # ejecutivo
    "G": "civil",         # gestión
}

PATRONES_ROL = [
    # C-1234-2026 / T-1234-2026 / RIT 1234-2026 / Rol 12345-2026 / ROL C-1234-2026
    re.compile(r"(?i)\b(?:RIT|ROL)\b"),
    re.compile(r"\b([A-Z])[-–]\s?(\d{1,6})[-–]\s?(\d{4})\b"),
    re.compile(r"\b(\d{1,6})[-–]\s?(\d{4})\b"),
]

INSTITUCIONES: Dict[str, Dict[str, Any]] = {
    "CMF": {
        "claves": ("cmf", "comisión para el mercado financiero", "ncg", "mercado de valores",
                   "banco", "aseguradora", "riesgo operacional"),
        "herramientas": ["cmf_search_normativa", "cmf_buscar_sanciones"],
        "etiqueta": "Comisión para el Mercado Financiero",
    },
    "SII": {
        "claves": ("sii", "servicio de impuestos internos", "renta", "iva", "impuesto",
                   "fiscalización", "giro", "tributario"),
        "herramientas": ["sii_search_circulares", "sii_buscar_resoluciones_y_oficios"],
        "etiqueta": "Servicio de Impuestos Internos",
    },
    "CGR": {
        "claves": ("contraloría", "contraloria", "cgr", "dictamen", "probidad administrativa",
                   "sumario administrativo", "municipalidad"),
        "herramientas": ["cgr_search_jurisprudencia", "cgr_search_auditorias",
                         "entes_consultar_organo"],
        "etiqueta": "Contraloría General de la República",
    },
    "DT": {
        "claves": ("dirección del trabajo", "direccion del trabajo", "dt", "dictamen dt",
                   "inspección del trabajo", "fiscalizadora"),
        "herramientas": ["dt_search_doctrina"],
        "etiqueta": "Dirección del Trabajo",
    },
    "SMA": {
        "claves": ("sma", "superintendencia del medio ambiente", "snifa", "rca",
                   "sanción ambiental", "seia", "eia", "dia"),
        "herramientas": ["sma_search_sancionatorios", "ambiental_buscar_jurisprudencia"],
        "etiqueta": "Superintendencia del Medio Ambiente",
    },
    "TDLC": {
        "claves": ("tdlc", "libre competencia", "fne", "colusión", "colusion",
                   "competencia desleal"),
        "herramientas": ["tdlc_search_jurisprudencia", "tdlc_buscar_icg_y_dictamenes"],
        "etiqueta": "Tribunal de Defensa de la Libre Competencia",
    },
    "CNE": {
        "claves": ("cne", "comisión nacional de energía", "panel de expertos", "tarifa eléctrica",
                   "generación", "distribución eléctrica", "dfl 4"),
        "herramientas": ["cne_get_centrales_y_proyectos", "panel_expertos_search"],
        "etiqueta": "Comisión Nacional de Energía",
    },
    "PJUD": {
        "claves": ("corte suprema", "corte de apelaciones", "pjud", "ojv", "oficina judicial"),
        "herramientas": ["pjud_search_jurisprudencia"],
        "etiqueta": "Poder Judicial",
    },
    "BCN": {
        "claves": ("bcn", "ley chile", "ley 21", "ley nº", "ley n°", "código", "codigo"),
        "herramientas": ["bcn_get_codigo", "bcn_get_ley"],
        "etiqueta": "Biblioteca del Congreso Nacional",
    },
    "INAPI": {
        "claves": ("inapi", "marca", "registro de marca", "propiedad industrial",
                   "propiedad intelectual", "cese y desistimiento"),
        "herramientas": ["inapi_evaluar_marca", "inapi_cease_and_desist"],
        "etiqueta": "Instituto Nacional de Propiedad Industrial",
    },
}

# Materias: señales, herramientas base y fuero probable. El orden de la lista importa: cuando
# hay empate de puntaje, se prefiere la primera (las más frecuentes en un estudio chico).
MATERIAS: List[Dict[str, Any]] = [
    {
        "clave": "laboral",
        "etiqueta": "laboral",
        "fuero": "Juzgado de Letras del Trabajo",
        "claves": ("despido", "finiquito", "fuero", "acoso laboral", "remuneración", "remuneracion",
                   "jornada", " horas extras", "indemnización por años", "aviso previo",
                   "necesidades de la empresa", "tutela laboral", "ley karin", "sindicato",
                   "negociación colectiva", "contrato de trabajo"),
        "herramientas": ["dt_search_doctrina", "bcn_get_codigo"],
        "argumentos": {"bcn_get_codigo": {"codigo": "trabajo"}},
    },
    {
        "clave": "familia",
        "etiqueta": "familia",
        "fuero": "Juzgado de Familia",
        "claves": ("divorcio", "pensión de alimentos", "pension de alimentos", "cuidado personal",
                   "tuición", "tuicion", "filiación", "filiacion", "violencia intrafamiliar",
                   "vif", "mediación familiar", "regimen comunicacional", "compensación económica"),
        "herramientas": ["bcn_get_codigo", "pjud_search_jurisprudencia"],
        "argumentos": {"bcn_get_codigo": {"codigo": "civil"}},
    },
    {
        "clave": "penal",
        "etiqueta": "penal",
        "fuero": "Juzgado de Garantía / Tribunal Oral en lo Penal",
        "claves": ("imputado", "querella", "delito", "fiscalía", "fiscalia", "prisión preventiva",
                   "prision preventiva", "violación", "robo", "hurto", "estafa", "lesiones",
                   "ministerio público", "defensoría penal"),
        "herramientas": ["bcn_get_codigo", "pjud_search_jurisprudencia"],
        "argumentos": {"bcn_get_codigo": {"codigo": "penal"}},
    },
    {
        "clave": "inmobiliario",
        "etiqueta": "inmobiliario y registral",
        "fuero": "Juzgado Civil (si hay litigio) · Conservador de Bienes Raíces",
        "claves": ("título", "titulo", "inscripción", "inscripcion", "conservador", "cbr",
                   "hipoteca", "usufructo", "servidumbre", "escritura pública", "escritura publica",
                   "posesión efectiva", "dominio", "gravamen", "prohibición de enajenar"),
        "herramientas": ["cbr_estudio_titulos", "cbr_checklist_documentos", "cpc_validar_mandato"],
        "argumentos": {},
    },
    {
        "clave": "ambiental",
        "etiqueta": "ambiental",
        "fuero": "Tribunal Ambiental · SMA",
        "claves": ("ambiental", "seia", "rca", "sma", "snifa", "medio ambiente", "eia", "dia",
                   "sanción ambiental", "sancion ambiental", "programa de cumplimiento"),
        "herramientas": ["sma_search_sancionatorios", "ambiental_buscar_jurisprudencia"],
        "argumentos": {},
    },
    {
        "clave": "competencia",
        "etiqueta": "libre competencia",
        "fuero": "Tribunal de Defensa de la Libre Competencia",
        "claves": ("libre competencia", "colusión", "colusion", "fne", "tdlc", "monopolio",
                   "competencia desleal", "abuso de posición dominante"),
        "herramientas": ["tdlc_search_jurisprudencia", "tdlc_buscar_icg_y_dictamenes"],
        "argumentos": {},
    },
    {
        "clave": "energia",
        "etiqueta": "eléctrico y energía",
        "fuero": "Panel de Expertos · Corte de Apelaciones",
        "claves": ("cne", "panel de expertos", "tarifa", "generadora", "distribuidora",
                   "transmisión eléctrica", "transmision electrica", "dfl 4", "ppa"),
        "herramientas": ["cne_get_centrales_y_proyectos", "panel_expertos_search"],
        "argumentos": {},
    },
    {
        "clave": "administrativo",
        "etiqueta": "administrativo y probidad",
        "fuero": "Contraloría · Juzgado Civil (si se impugna el acto)",
        "claves": ("municipalidad", "patente", "licitación", "licitacion", "sumario administrativo",
                   "contraloría", "contraloria", "probidad", "acto administrativo", "bases de licitación",
                   "compras públicas", "municipal"),
        "herramientas": ["cgr_search_jurisprudencia", "entes_consultar_organo"],
        "argumentos": {},
    },
    {
        "clave": "tributario",
        "etiqueta": "tributario",
        "fuero": "Tribunal Tributario y Aduanero (TTA)",
        "claves": ("sii", "impuesto", "iva", "renta", "f29", "f22", "giro", "fiscalización",
                   "fiscalizacion", "timbraje", "boleta electrónica"),
        "herramientas": ["sii_search_circulares", "sii_buscar_resoluciones_y_oficios",
                         "bcn_get_codigo"],
        "argumentos": {"bcn_get_codigo": {"codigo": "tributario"}},
    },
    {
        "clave": "consumidor",
        "etiqueta": "consumidor",
        "fuero": "Juzgado de Policía Local / Juzgado Civil",
        "claves": ("consumidor", "sernac", "publicidad engañosa", "publicidad engañosa",
                   "garantía legal", "garantia legal", "cláusula abusiva", "clausula abusiva"),
        "herramientas": ["bcn_get_ley"],
        "argumentos": {"bcn_get_ley": {"numero": "19496"}},
    },
    {
        "clave": "proteccion",
        "etiqueta": "constitucional (protección y amparo)",
        "fuero": "Corte de Apelaciones",
        "claves": ("recurso de protección", "recurso de proteccion", "garantías constitucionales",
                   "garantias constitucionales", "art. 20", "amparo constitucional", "cpr"),
        "herramientas": ["pjud_search_jurisprudencia", "recurso_proteccion_generar"],
        "argumentos": {},
    },
    {
        "clave": "datos",
        "etiqueta": "datos personales",
        "fuero": "Agencia de Protección de Datos (2026) · Tribunales Civiles",
        "claves": ("datos personales", "19.628", "19628", "21.719", "21719", "arco", "habeas data",
                   "tratamiento de datos", "privacidad", "brecha de datos"),
        "herramientas": ["bcn_get_ley"],
        "argumentos": {"bcn_get_ley": {"numero": "19628"}},
    },
    {
        "clave": "propiedad_industrial",
        "etiqueta": "propiedad industrial",
        "fuero": "INAPI · Corte de Apelaciones (apelación)",
        "claves": ("inapi", "registro de marca", "nulidad de marca", "oposición de marca",
                   "oposicion de marca", "patente", "cese y desistimiento"),
        "herramientas": ["inapi_evaluar_marca", "inapi_cease_and_desist"],
        "argumentos": {},
    },
    {
        "clave": "civil",
        "etiqueta": "civil y ejecutivo",
        "fuero": "Juzgado Civil",
        "claves": ("contrato", "arriendo", "mutuo", "cobro", "pagaré", "pagare", "letra",
                   "indemnización de perjuicios", "prescripción", "obligación de dar",
                   "responsabilidad civil", "daño emergente", "lucro cesante", "daño moral",
                   "compraventa", "mandato"),
        "herramientas": ["bcn_get_codigo", "bcn_get_codigo", "pjud_search_jurisprudencia"],
        "argumentos": {"bcn_get_codigo": {"codigo": "civil"}},
    },
]

# Palabras que en los expedientes chilenos nombran el contenido de un documento.
TIPOS_DOCUMENTO: Dict[str, tuple] = {
    "demanda": ("demanda", "requerimiento"),
    "contestacion": ("contestación", "contestacion", "respuesta"),
    "resolucion": ("resolución", "resolucion", "proveído", "proveido", "decreto", "auto"),
    "sentencia": ("sentencia", "fallo", "la corte", "considerando"),
    "escritura": ("escritura", "notaría", "notaria", "protocolización"),
    "contrato": ("contrato", "convenio", "acuerdo", "finiquito", "pagaré", "pagare"),
    "informe": ("informe", "peritaje", "dictamen", "auditoría", "auditoria"),
    "certificado": ("certificado", "inscripción", "inscripcion", "cbr"),
    "escrito": ("escrito", "presentación", "presentacion", "otrosí", "otro si"),
}

EXTENSIONES_TEXTO = {".txt", ".md", ".csv", ".json", ".html", ".xml"}
EXTENSIONES_DOCUMENTO = {".pdf", ".docx", ".doc", ".rtf", ".odt", ".xlsx", ".pptx"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# Cuántas señales distintas hacen falta para afirmar una materia sin advertencia.
SEÑALES_PARA_AFIRMAR = 2

# Herramientas que buscan por texto: si el paso no trae una consulta, hay que dársela, porque
# llamarlas con la consulta vacía devuelve nada y eso no es un resultado, es un silencio.
HERRAMIENTAS_DE_BUSQUEDA = (
    "pjud_search_jurisprudencia", "cgr_search_jurisprudencia", "cgr_search_auditorias",
    "dt_search_doctrina", "cmf_search_normativa", "sii_search_circulares",
    "sii_buscar_resoluciones_y_oficios", "tdlc_search_jurisprudencia",
    "tdlc_buscar_icg_y_dictamenes", "ambiental_buscar_jurisprudencia",
    "sma_search_sancionatorios", "panel_expertos_search", "doctrina_search",
)


# --------------------------------------------------------------------------- detección

def _texto_de(entrada: str, tipo: Optional[str] = None) -> tuple[str, List[str], List[Dict[str, Any]]]:
    """Devuelve (texto, notas, documentos). Si la entrada es una carpeta, junta su contenido.

    Un archivo que no se puede leer no se saltea en silencio: queda anotado, porque el plan que
    se arme después no puede prometer que analizó algo que no abrió.
    """
    notas: List[str] = []
    documentos: List[Dict[str, Any]] = []
    ruta = pathlib.Path(entrada).expanduser()

    if tipo == "carpeta" or (ruta.is_dir() and tipo is None):
        if not ruta.is_dir():
            return "", [f"no existe la carpeta: {entrada}"], []
        archivos = sorted(p for p in ruta.rglob("*") if p.is_file()
                          and ".git" not in p.parts and not p.name.startswith("."))
        if not archivos:
            notas.append(f"la carpeta {ruta.name} no tiene archivos")
        for archivo in archivos[:200]:
            sufijo = archivo.suffix.lower()
            entrada_doc = {
                "ruta": str(archivo),
                "nombre": archivo.name,
                "tipo": _tipo_de_documento(archivo.name),
                "extension": sufijo,
                "bytes": archivo.stat().st_size,
            }
            documentos.append(entrada_doc)
        # El texto que se analiza son los nombres de archivo: es lo que hay sin OCR (el OCR lo
        # corre `caso_ejecutar`, que es otro paso y se demora).
        texto = " ".join(d["nombre"] for d in documentos)
        if len(archivos) > 200:
            notas.append(f"la carpeta tiene {len(archivos)} archivos: se miraron los primeros 200")
        return texto, notas, documentos

    if tipo == "texto" or (ruta.is_file() and tipo is None):
        if not ruta.is_file():
            # No es un archivo: se trata como texto pegado, que es el uso normal.
            return entrada, notas, []
        sufijo = ruta.suffix.lower()
        documentos.append({"ruta": str(ruta), "nombre": ruta.name,
                           "tipo": _tipo_de_documento(ruta.name), "extension": sufijo,
                           "bytes": ruta.stat().st_size})
        if sufijo in EXTENSIONES_TEXTO:
            try:
                return ruta.read_text(encoding="utf-8", errors="replace"), notas, documentos
            except OSError as err:
                return "", [f"no pude leer {ruta.name}: {err}"], documentos
        if sufijo in EXTENSIONES_DOCUMENTO or sufijo in EXTENSIONES_IMAGEN:
            notas.append(
                f"{ruta.name} no es texto plano: hay que extraerlo (OCR o parseo), y eso lo "
                "hace el paso de ejecución del plan"
            )
            return "", notas, documentos
        notas.append(f"extensión no reconocida ({sufijo or 'sin extensión'}): se analiza el nombre")
        return ruta.name, notas, documentos

    return str(entrada), notas, []


def _tipo_de_documento(nombre: str) -> str:
    minuscula = nombre.lower()
    for tipo, claves in TIPOS_DOCUMENTO.items():
        if any(clave in minuscula for clave in claves):
            return tipo
    return "documento"


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def detectar(entrada: str, tipo: Optional[str] = None) -> Dict[str, Any]:
    """Lee la entrada y devuelve las señales encontradas, con su evidencia.

    No decide todavía: junta evidencia. La decisión la toma `planear`, y queda a la vista para
    que cualquiera pueda discutirla (esa es la mitad del valor de que sea determinista).
    """
    texto, notas, documentos = _texto_de(entrada, tipo)
    plano = _normalizar(texto)
    minuscula = plano.lower()

    # Rol/RIT
    roles: List[str] = []
    for patron in PATRONES_ROL[1:]:
        for m in patron.finditer(plano):
            roles.append(m.group(0).strip())
    letras: List[str] = []
    for m in re.finditer(r"\b([A-Z])[-–]\s?\d{1,6}[-–]\s?\d{4}\b", plano):
        letra = m.group(1).upper()
        if letra in LETRAS_RIT:
            letras.append(letra)

    if re.search(r"(?i)\bRIT\b|\bROL\b", plano) and not roles:
        notas.append("menciona un Rol/RIT pero el número no se pudo leer: no se usa para decidir")

    # Palabras clave por materia, con la evidencia de qué palabra apareció.
    puntajes: Dict[str, List[str]] = {}
    for materia in MATERIAS:
        encontradas = [clave.strip() for clave in materia["claves"] if clave in minuscula]
        if encontradas:
            puntajes[materia["clave"]] = encontradas[:6]

    # La letra suma como señal, y su materia queda anotada aparte.
    por_letra = [LETRAS_RIT[letra] for letra in letras]
    for materia_clave in por_letra:
        puntajes.setdefault(materia_clave, [])
        puntajes[materia_clave].append(f"letra del Rol: {letras[por_letra.index(materia_clave)]}")

    # Instituciones
    instituciones: List[str] = []
    for sigla, datos in INSTITUCIONES.items():
        if any(clave in minuscula for clave in datos["claves"]):
            instituciones.append(sigla)

    # Fechas y montos: sirven para saber qué falta
    fechas = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", plano)
    montos = re.findall(r"\$\s?\d[\d.]{3,}|\b\d[\d.]{4,}\s?(?:pesos|clp)\b", plano, re.IGNORECASE)
    rut_mencionados = re.findall(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b", plano)

    return {
        "texto_analizado": len(plano),
        "roles": sorted(set(roles))[:10],
        "letras": sorted(set(letras)),
        "puntajes": puntajes,
        "instituciones": instituciones,
        "documentos": documentos,
        "tipos_de_documento": sorted({d["tipo"] for d in documentos}),
        "fechas": sorted(set(fechas))[:10],
        "montos": sorted(set(montos))[:10],
        "ruts": sorted(set(rut_mencionados))[:10],
        "notas": notas,
    }


# --------------------------------------------------------------------------- el plan

def _materia_de(deteccion: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], List[str]]:
    """Elige la materia con la evidencia disponible. Si no alcanza, lo dice."""
    advertencias: List[str] = []
    puntajes = {clave: list(palabras) for clave, palabras in deteccion["puntajes"].items()}
    if not puntajes:
        return None, ["no se pudo determinar la materia con lo que hay: faltan señales"]

    ordenadas = []
    for materia in MATERIAS:
        if materia["clave"] in puntajes:
            ordenadas.append((len(puntajes[materia["clave"]]), materia))
    ordenadas.sort(key=lambda par: -par[0])
    mejor_puntaje, mejor = ordenadas[0]

    if mejor_puntaje < SEÑALES_PARA_AFIRMAR:
        advertencias.append(
            f"la materia «{mejor['etiqueta']}» sale de una sola señal: conviene confirmarla antes "
            "de usar ese encuadre en un escrito"
        )
    empatadas = [m["etiqueta"] for p, m in ordenadas if p == mejor_puntaje and m is not mejor]
    if empatadas:
        advertencias.append(
            "hay señales de más de una materia (también " + ", ".join(empatadas) +
            "): el plan cubre la principal, revisá si el caso es mixto"
        )
    return mejor, advertencias


def _herramientas_de_materia(materia: Dict[str, Any]) -> List[Dict[str, Any]]:
    pasos = []
    for herramienta in materia["herramientas"]:
        argumentos = dict(materia.get("argumentos", {}).get(herramienta, {}))
        pasos.append({
            "herramienta": herramienta,
            "argumentos": argumentos,
            "por_que": f"aporta el marco de la materia {materia['etiqueta']}",
        })
    return pasos


def planear(deteccion: Dict[str, Any], consulta: str = "") -> Dict[str, Any]:
    """Arma el plan ordenado: qué usar, con qué argumentos y por qué."""
    materia, advertencias = _materia_de(deteccion)
    faltantes: List[str] = []

    for institucion in deteccion["instituciones"]:
        for herramienta in INSTITUCIONES[institucion]["herramientas"]:
            deteccion.setdefault("_pasos_institucion", []).append({
                "herramienta": herramienta,
                "argumentos": {},
                "por_que": f"el caso menciona {INSTITUCIONES[institucion]['etiqueta']} ({institucion})",
            })

    if not deteccion["roles"]:
        faltantes.append("el Rol/RIT de la causa: sin él no se puede buscar en el Poder Judicial")
    if not deteccion["fechas"]:
        faltantes.append("las fechas relevantes (notificación, resolución, plazo): sin ellas no hay cómputo posible")
    if not deteccion["documentos"] and not consulta:
        faltantes.append("los documentos del caso (o su relato): se analizó sólo el texto disponible")
    if not deteccion["ruts"]:
        faltantes.append("el RUT de las partes, si hay que presentar algo en el tribunal")
    if materia is None:
        faltantes.append("la materia: conviene decir en una frase de qué se trata el caso")

    pasos: List[Dict[str, Any]] = []
    # Si el caso trae Rol/RIT, ese es el dato más valioso que hay: se busca la causa y la
    # jurisprudencia por ahí antes que por palabras sueltas.
    if deteccion["roles"]:
        # Primero el RIT en sí: validarlo y dejar armada la consulta del estado de la causa. La
        # suite no consulta el expediente (la OJV pide clave y captcha), así que acá se entrega
        # lo que sí se puede: el RIT revisado, la sección exacta y el enlace.
        con_letra = next((r for r in deteccion["roles"] if re.match(r"^[A-Z][-–]", r)), None)
        pasos.append({
            "herramienta": "pjud_consultar_causa",
            "argumentos": {"rit": con_letra or deteccion["roles"][0]},
            "por_que": (
                "valida el Rol/RIT y deja armados los pasos y el enlace para consultar la causa en "
                "la Oficina Judicial Virtual (la consulta la hace la persona: el portal pide clave "
                "y captcha)"
            ),
        })
        # El buscador del Poder Judicial es literal: con una frase larga no encuentra nada. Se le
        # da la palabra más distintiva de la materia (dos o tres palabras cortas es lo que mejor
        # responde), y la frase completa queda para la doctrina, que sí entiende de frases.
        corta = ""
        if materia:
            corta = next((c for c in materia["claves"] if c.strip() and " " not in c.strip()), "")
            corta = corta or materia["clave"].replace("_", " ")
        pasos.append({
            "herramienta": "pjud_search_jurisprudencia",
            "argumentos": {"query": corta or deteccion["roles"][0], "limite": 5},
            "por_que": (
                "busca fallos del Poder Judicial relacionados con el caso. Ojo: esta herramienta "
                "consulta jurisprudencia, no el expediente; el estado de la causa por su Rol/RIT "
                "se pide en la Oficina Judicial Virtual, y la suite todavía no tiene conector para eso"
            ),
        })
    if materia:
        pasos.extend(_herramientas_de_materia(materia))
    pasos.extend(deteccion.pop("_pasos_institucion", []))

    # Lo que va siempre, en este orden.
    pasos.append({
        "herramienta": "doctrina_search",
        "argumentos": {"query": consulta or " ".join(deteccion["letras"]) or "caso"},
        "por_que": "encuadre dogmático en la doctrina chilena indexada",
    })
    pasos.append({
        "herramienta": "graphify_consulta_subgrafo",
        "argumentos": {},
        "por_que": "relación entre las instituciones del caso, sin gastar tokens de más",
    })
    if deteccion["documentos"]:
        pasos.append({
            "herramienta": "ocr_extract_pdf" if any(
                d["extension"] in EXTENSIONES_DOCUMENTO or d["extension"] in EXTENSIONES_IMAGEN
                for d in deteccion["documentos"]
            ) else "doctrina_ingestar_documento",
            "argumentos": {},
            "por_que": "los documentos hay que leerlos: los escaneados por OCR, los de texto directo",
        })
        pasos.append({
            "herramienta": "compile_legal_dossier",
            "argumentos": {},
            "por_que": "arma el expediente A4 con separadores, foliado y marcadores",
        })

    # A cada paso que busca por texto le llega una consulta armada: la del abogado si la dio, y
    # si no, la materia y sus señales. Un paso sin consulta es un paso que no trae nada.
    for paso in pasos:
        if paso["herramienta"] in HERRAMIENTAS_DE_BUSQUEDA and not paso["argumentos"].get("query"):
            if paso["herramienta"] == "pjud_search_jurisprudencia":
                paso["argumentos"]["query"] = " ".join(consulta.split()[:3]) or "caso"
            else:
                paso["argumentos"]["query"] = (
                    consulta
                    or " ".join((materia["clave"].replace("_", " ") if materia else "").split())
                    or " ".join(deteccion["letras"]) or "caso"
                )
            paso["por_que"] += " (la consulta la armó la mesa de entrada con lo detectado)"

    return {
        "materia": materia["clave"] if materia else None,
        "materia_etiqueta": materia["etiqueta"] if materia else None,
        "fuero_probable": materia["fuero"] if materia else None,
        "instituciones": deteccion["instituciones"],
        "plan": pasos,
        "faltantes": faltantes,
        "advertencias": advertencias,
    }


def _resumen(analisis: Dict[str, Any]) -> str:
    """El plan contado en castellano, para leerlo sin descifrar un JSON."""
    lineas = ["MESA DE ENTRADA", "=" * 15, ""]
    if analisis["materia"]:
        lineas.append(f"Materia: {analisis['materia_etiqueta']} (fuero probable: {analisis['fuero_probable']})")
    else:
        lineas.append("Materia: no se pudo determinar con lo que hay")
    if analisis["instituciones"]:
        lineas.append("Instituciones mencionadas: " + ", ".join(
            INSTITUCIONES[i]["etiqueta"] for i in analisis["instituciones"]))
    if analisis["deteccion"]["roles"]:
        lineas.append("Rol/RIT: " + ", ".join(analisis["deteccion"]["roles"][:5]))
    if analisis["deteccion"]["documentos"]:
        lineas.append(f"Documentos: {len(analisis['deteccion']['documentos'])} "
                      f"({', '.join(analisis['deteccion']['tipos_de_documento'])})")
    lineas.append("")
    lineas.append(f"Plan ({len(analisis['plan'])} pasos):")
    for i, paso in enumerate(analisis["plan"], 1):
        argumentos = f" {paso['argumentos']}" if paso["argumentos"] else ""
        lineas.append(f"  {i}. {paso['herramienta']}{argumentos} — {paso['por_que']}")
    if analisis["faltantes"]:
        lineas.append("")
        lineas.append("Falta para poder avanzar:")
        for falta in analisis["faltantes"]:
            lineas.append(f"  · {falta}")
    if analisis["advertencias"]:
        lineas.append("")
        for aviso in analisis["advertencias"]:
            lineas.append(f"  AVISO: {aviso}")
    lineas.append("")
    lineas.append("Compuerta de revisión jurídica: este plan lo armó un sistema; todo escrito que "
                  "salga de acá lo tiene que validar un abogado habilitado antes de su firma o "
                  "presentación.")
    return "\n".join(lineas)


def caso_analizar(entrada: str, tipo: Optional[str] = None, consulta: str = "") -> Dict[str, Any]:
    """Punto de entrada: de un caso a un plan. No modifica nada, sólo lee y propone."""
    if not entrada or not str(entrada).strip():
        return {"error": "hace falta algo que analizar: una carpeta, un texto o una consulta",
                "resumen": "MESA DE ENTRADA\n\nNo hay nada que analizar."}

    deteccion = detectar(str(entrada), tipo)
    planeado = planear(deteccion, consulta=str(consulta or ""))
    analisis = {
        "entrada": str(entrada),
        "tipo_entrada": tipo or ("carpeta" if pathlib.Path(str(entrada)).expanduser().is_dir() else
                                 "archivo" if pathlib.Path(str(entrada)).expanduser().is_file() else "texto"),
        "fecha_analisis": dt.date.today().isoformat(),
        "deteccion": deteccion,
        **planeado,
    }
    analisis["resumen"] = _resumen(analisis)
    return analisis


# --------------------------------------------------------------------------- ejecución

def caso_ejecutar(entrada: str = "", tipo: Optional[str] = None, pasos: Optional[List[int]] = None,
                  limite_pasos: int = 12) -> Dict[str, Any]:
    """Ejecuta los pasos del plan. Cada paso deja su resultado o su error, y nada se inventa."""
    import mcp_server  # import perezoso: mcp_server importa este módulo al registrarlo

    analisis = caso_analizar(entrada, tipo)
    if "error" in analisis:
        return {"error": analisis["error"], "resumen": analisis["resumen"]}

    plan = analisis["plan"]
    if pasos:
        elegidos = [plan[i - 1] for i in pasos if 0 < i <= len(plan)]
    else:
        elegidos = plan[:limite_pasos]

    resultados: List[Dict[str, Any]] = []
    for numero, paso in enumerate(elegidos, 1):
        herramienta = paso["herramienta"]
        argumentos = dict(paso["argumentos"])
        # Los argumentos que faltan se completan con lo que se pudo detectar, y si no alcanza
        # el paso se saltea con su motivo: es mejor un plan a medias declarado que uno "completo"
        # que en realidad inventó datos.
        if herramienta in ("doctrina_search",) and "query" not in argumentos:
            argumentos["query"] = analisis["deteccion"]["roles"] and analisis["deteccion"]["roles"][0] \
                or (analisis["materia_etiqueta"] or "caso")
        if herramienta in ("ocr_extract_pdf",) and "pdf_path" not in argumentos:
            candidatos = [d for d in analisis["deteccion"]["documentos"]
                          if d["extension"] in EXTENSIONES_DOCUMENTO | EXTENSIONES_IMAGEN]
            if not candidatos:
                resultados.append({"paso": numero, "herramienta": herramienta,
                                   "estado": "salteado",
                                   "motivo": "no hay documentos que se puedan leer por OCR"})
                continue
            argumentos["pdf_path"] = candidatos[0]["ruta"]
        if herramienta in ("compile_legal_dossier", "graphify_consulta_subgrafo") and not argumentos:
            resultados.append({"paso": numero, "herramienta": herramienta, "estado": "salteado",
                               "motivo": "el plan no trae los parámetros: los define el abogado"})
            continue
        if herramienta == "bcn_get_codigo" and not argumentos:
            argumentos = {"codigo": "civil"}
        try:
            salida = mcp_server.handle_tool_call(herramienta, argumentos)
            resultados.append({"paso": numero, "herramienta": herramienta, "estado": "ok",
                               "largo": len(str(salida)), "salida": salida})
        except Exception as err:  # noqa: BLE001 — un paso que falla no tumba la mesa
            resultados.append({"paso": numero, "herramienta": herramienta, "estado": "error",
                               "motivo": f"{type(err).__name__}: {err}"})

    hechos = [r for r in resultados if r["estado"] == "ok"]
    fallados = [r for r in resultados if r["estado"] == "error"]
    salteados = [r for r in resultados if r["estado"] == "salteado"]
    return {
        "analisis": {k: analisis[k] for k in ("materia", "materia_etiqueta", "fuero_probable",
                                              "instituciones", "faltantes", "advertencias")},
        "resultados": resultados,
        "resumen": (
            f"Ejecutados {len(hechos)} de {len(resultados)} pasos.\n"
            + (f"  fallaron {len(fallados)}: " + ", ".join(r["herramienta"] for r in fallados) + "\n"
               if fallados else "")
            + (f"  salteados {len(salteados)}: " + ", ".join(r["herramienta"] for r in salteados) + "\n"
               if salteados else "")
            + "\nCompuerta de revisión jurídica: lo que salió de acá lo valida un abogado habilitado "
            "antes de usarse."
        ),
    }
