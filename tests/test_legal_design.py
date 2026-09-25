"""
Legal design: los principios de `docs/legal_design.md`, aplicados y verificables.

Estos tests sostienen la capa de diseño del proyecto: que las 18 skills de `.agents/skills/`
existan y declaren su compuerta de revisión y su formato de salida, que el documento de principios y
el checklist existan y tengan contenido, que el README enlace los principios, que no se cuele
terminología de Common Law en texto propio y que `skills-lock.json` no quede desactualizado.

Lo que estos tests **no** pueden probar, y por eso no lo fingen: si un texto es claro de verdad lo
decide una persona leyéndolo con `docs/legal_design_checklist.md`. Acá se comprueba que la regla esté
escrita y que el esqueleto exista, no que esté bien redactado.

Si se edita una skill registrada en `skills-lock.json`, hay que refrescar su hash (lo pide
`CONTRIBUTING.md`):

    sha256sum .agents/skills/<nombre>/SKILL.md     # o Get-FileHash -Algorithm SHA256 en Windows
"""

import hashlib
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = RAIZ / ".agents" / "skills"
DOC_PRINCIPIOS = RAIZ / "docs" / "legal_design.md"
CHECKLIST = RAIZ / "docs" / "legal_design_checklist.md"
LOCK = RAIZ / "skills-lock.json"

CAMPOS_DEL_BLOQUE = (
    "Quién lee",
    "Lenguaje claro",
    "Salida (estructura)",
    "Citas",
    "Compuerta de Revisión",
)

# Figuras del Common Law prohibidas por AGENTS.md §1. `summary judgment` se incluye porque se cita
# como figura local inexistente en Chile (el equivalente es la sentencia definitiva / el juicio
# sumario, no la institución anglosajona).
FIGURAS_FORANEAS = {
    "at-will employment": r"at[-\s]will\s+employment",
    "punitive damages": r"punitive\s+damages",
    "discovery": r"\bdiscovery\b",
    "subpoena": r"\bsubpoenas?\b",
    "grand jury": r"\bgrand\s+jury\b",
    "summary judgment": r"\bsummary\s+judgment\b",
}

# Una mención se considera legítima si la línea entera la está prohibiendo o explicando como foránea.
MARCAS_DE_PROHIBICION = (
    "prohib", "veta", "nunca", "jamás", "common law", "no usar", "no existe", "inexistente",
)

# Archivos que nombran las figuras para detectarlas o para probar que se detectan. No son texto
# propio de la documentación: son el detector, sus casos y este mismo test. El test comprueba que
# sigan existiendo y que sigan nombrando las figuras, para que la exclusión no se convierta en un
# agujero.
ARCHIVOS_QUE_DETECTAN = {
    "critique.py": ('"discovery"', '"punitive damages"', '"grand jury"'),
    "evals/test_cases.json": ('"punitive damages"', '"subpoena"', '"discovery"'),
    "promptfooconfig.yaml": ('"punitive damages"', '"subpoena"', '"discovery"'),
    "tests/test_chat_and_critique.py": ("discovery", "punitive damages"),
    "tests/test_legal_design.py": (
        '"at-will employment"', '"punitive damages"', '"discovery"', '"subpoena"', '"grand jury"',
        '"summary judgment"',
    ),
}

# Carpetas fuera del barrido: corpus de terceros, artefactos generados, cachés de portales y
# entornos. El texto propio del proyecto no vive acá.
CARPETAS_FUERA = {
    ".git", ".venv", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".claude", ".cursor", ".vscode",
    "__pycache__", "node_modules", "build", "dist", "doctrina", "doctrina_raw", "exports",
    "graphify-out", "brag-output", "bcn_spec_files", "envs",
    # Los datos derivados no son escritura del proyecto: el grafo y los índices reproducen lo que
    # dicen las fuentes. Si un manual de la Academia habla de «discovery», eso es contenido suyo,
    # no una figura del Common Law usada por nosotros. La regla mira lo que escribimos nosotros.
    "data",
}
SUFIJOS_REVISADOS = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".html", ".sh", ".cfg", ".ini"}


def _skills():
    """Las 17 skills del repositorio, ordenadas por nombre."""
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def _texto(ruta):
    return ruta.read_text(encoding="utf-8")


def _bloque_de_diseno(texto):
    """El bloque `## 🎨 Presentación y Lenguaje Claro (Legal Design)` de una skill."""
    m = re.search(r"^## 🎨 Presentación y Lenguaje Claro \(Legal Design\)\n(.*?)(?=^## |\Z)",
                  texto, re.S | re.M)
    return m.group(1) if m else ""


def test_existen_las_17_skills_con_su_frontmatter():
    skills = _skills()
    assert len(skills) == 18, f"hay {len(skills)} SKILL.md en .agents/skills/"

    for ruta in skills:
        texto = _texto(ruta)
        cabecera = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
        assert cabecera, f"{ruta.parent.name}: falta el frontmatter o no empieza en '---'"
        assert "name:" in cabecera.group(1), ruta.parent.name
        assert "description:" in cabecera.group(1), ruta.parent.name


def test_toda_skill_declara_compuerta_citacion_y_salida():
    """Las 17 skills presentan su salida y traen compuerta y formato de citación (reglas LD-04, LD-06)."""
    faltantes = []
    for ruta in _skills():
        bloque = _bloque_de_diseno(_texto(ruta))
        if not bloque:
            faltantes.append(f"{ruta.parent.name}: sin bloque de legal design")
            continue
        for campo in CAMPOS_DEL_BLOQUE:
            if campo not in bloque:
                faltantes.append(f"{ruta.parent.name}: sin '{campo}'")
        if "Formato de Citación" not in _texto(ruta):
            faltantes.append(f"{ruta.parent.name}: sin formato de citación")

    assert not faltantes, "\n".join(faltantes)


def test_toda_skill_explica_el_termino_tecnico_entre_parentesis():
    """LD-01: cada skill declara la regla del término técnico con su equivalencia entre paréntesis."""
    sin_ejemplo = [
        ruta.parent.name
        for ruta in _skills()
        if "entre paréntesis" not in _bloque_de_diseno(_texto(ruta))
    ]
    assert not sin_ejemplo, f"skills sin la regla de lenguaje claro: {sin_ejemplo}"


def test_las_skills_de_dominio_legal_llevan_la_compuerta_juridica():
    """LD-06: en las 11 skills de derecho chileno la compuerta no es opcional ni condicional."""
    legales = [r for r in _skills() if r.parent.name.startswith("chilean-")]
    assert len(legales) == 12, [r.parent.name for r in legales]

    for ruta in legales:
        texto = _texto(ruta)
        assert "Compuerta de Revisión Jurídica" in texto, ruta.parent.name
        assert "⚖️" in texto, f"{ruta.parent.name}: la compuerta va con su marca ⚖️"
        assert "listo para presentar" not in texto.lower(), ruta.parent.name


def test_las_skills_de_codigo_acotan_su_compuerta_a_lo_juridico():
    """Las 6 skills ponytail no producen asesoría: su compuerta es explícitamente condicional."""
    de_codigo = [r for r in _skills() if r.parent.name.startswith("ponytail")]
    assert len(de_codigo) == 6, [r.parent.name for r in de_codigo]

    for ruta in de_codigo:
        bloque = _bloque_de_diseno(_texto(ruta))
        assert "aplica solo si" in bloque, (
            f"{ruta.parent.name}: una skill de código no puede declarar compuerta obligatoria"
        )


def test_cada_skill_declara_como_se_ve_su_salida():
    """LD-02 y LD-03: estructura antes que prosa, y la salida se anuncia."""
    for ruta in _skills():
        bloque = _bloque_de_diseno(_texto(ruta))
        m = re.search(r"\*\*Salida \(estructura\):\*\*\s*(.+)", bloque)
        assert m, f"{ruta.parent.name}: falta la línea de estructura de salida"
        assert len(m.group(1).strip()) >= 30, f"{ruta.parent.name}: la salida se describe en dos palabras"


def test_el_documento_de_principios_tiene_las_12_reglas_y_su_fuente():
    assert DOC_PRINCIPIOS.exists(), "falta docs/legal_design.md"
    texto = _texto(DOC_PRINCIPIOS)
    assert len(texto.splitlines()) >= 100, "el documento de principios quedó en esqueleto"

    faltan = [f"LD-{n:02d}" for n in range(1, 13) if f"LD-{n:02d} —" not in texto]
    assert not faltan, f"reglas sin desarrollar: {faltan}"

    assert "legaldesignalliance.org" in texto, "falta la fuente del Legal Design Manifesto"
    assert "Stanford" in texto, "falta la referencia al Stanford Legal Design Lab"
    assert "legal_design_checklist.md" in texto, "el documento no enlaza el checklist"


def test_el_checklist_es_usable_y_tiene_criterios():
    assert CHECKLIST.exists(), "falta docs/legal_design_checklist.md"
    texto = _texto(CHECKLIST)

    casillas = texto.count("[ ]")
    assert casillas >= 12, f"el checklist tiene {casillas} casillas: no cubre las 12 reglas"
    assert "Compuerta de Revisión Jurídica" in texto
    assert "Criterio" in texto, "las casillas van sin criterio: no sirven para revisar"
    assert len(texto.splitlines()) <= 60, "el checklist dejó de caber en una pantalla"


def test_el_readme_declara_y_enlaza_los_principios():
    readme = _texto(RAIZ / "README.md")
    assert "Diseño Legal (Legal Design)" in readme, "el README no declara los principios"
    assert "docs/legal_design.md" in readme, "el README no enlaza el documento de principios"
    assert "docs/legal_design_checklist.md" in readme, "el README no enlaza el checklist"


def test_ningun_archivo_propio_usa_figuras_de_common_law():
    """AGENTS.md §1: las figuras del Common Law solo pueden aparecer para prohibirlas."""
    hallazgos = []

    for ruta in RAIZ.rglob("*"):
        if not ruta.is_file() or ruta.suffix.lower() not in SUFIJOS_REVISADOS:
            continue
        partes = ruta.relative_to(RAIZ).parts
        if any(p in CARPETAS_FUERA for p in partes[:-1]):
            continue
        relativa = "/".join(partes)
        if relativa in ARCHIVOS_QUE_DETECTAN:
            continue

        for numero, linea in enumerate(_texto(ruta).splitlines(), 1):
            minuscula = linea.lower()
            for figura, patron in FIGURAS_FORANEAS.items():
                if re.search(patron, minuscula) and not any(m in minuscula for m in MARCAS_DE_PROHIBICION):
                    hallazgos.append(f"{relativa}:{numero}: '{figura}' sin marcar como prohibida")

    assert not hallazgos, "\n".join(hallazgos)


def test_el_detector_y_los_casos_de_prueba_siguen_nombrando_las_figuras():
    """La exclusión del barrido anterior tiene que seguir teniendo sentido."""
    for relativa, figuras in ARCHIVOS_QUE_DETECTAN.items():
        ruta = RAIZ / relativa
        assert ruta.exists(), f"{relativa} desapareció: el barrido quedó sin detector"
        texto = _texto(ruta)
        for figura in figuras:
            assert figura in texto, f"{relativa} ya no nombra {figura}"


def test_el_lock_de_skills_corresponde_a_los_archivos():
    """CONTRIBUTING.md: al editar una skill registrada hay que refrescar su SHA-256 en el lock."""
    assert LOCK.exists(), "falta skills-lock.json"
    registro = json.loads(_texto(LOCK))["skills"]

    desactualizadas = []
    for nombre, entrada in registro.items():
        ruta = RAIZ / entrada["skillPath"]
        assert ruta.exists(), f"{nombre}: el lock apunta a {entrada['skillPath']}, que no existe"
        # El candado es del contenido, no de cómo quedó el archivo en el disco: en Windows el
        # checkout convierte los saltos de línea a CRLF y el hash cambiaría sin que nadie
        # tocara la skill. Se normaliza antes de comparar.
        real = hashlib.sha256(ruta.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if real != entrada["sha256"]:
            desactualizadas.append(f"{nombre}: lock={entrada['sha256'][:12]}… archivo={real[:12]}…")

    assert not desactualizadas, "\n".join(desactualizadas)


def test_la_regla_de_citas_y_entrega_esta_declarada():
    """AGENTS.md §2 bis: en documentos, citas a pie de página y entrega en Word; en conversación, citas al final."""
    agents = _texto(RAIZ / "AGENTS.md")
    assert "a pie de página" in agents
    assert "informe en derecho" in agents, "no distingue documento de conversación"
    assert "Word (.docx)" in agents, "no declara que los documentos se entregan en Word, no en PDF"
    assert "al final" in agents, "no declara que en la conversación las citas van al final"
    assert "sin fuente verificable" in agents
    assert "Fuentes:" in agents
    readme = _texto(RAIZ / "README.md")
    assert "a pie de página" in readme, "el README no declara la regla de citación"
    assert "Word (.docx)" in readme, "el README no declara la entrega en Word"


def test_citas_en_skills_y_agentes():
    """La regla de citas y entrega es del producto: vive en las skills y en los agentes, no sólo en AGENTS.md."""
    import json

    faltan = []
    for skill in _skills():
        contenido = _texto(skill)
        if "Word (.docx)" not in contenido or "al final" not in contenido:
            faltan.append(str(skill.relative_to(RAIZ)))
    for agente in sorted((RAIZ / "agents").glob("*.json")):
        datos = json.loads(agente.read_text(encoding="utf-8"))
        sp = datos.get("systemPrompt", "")
        if "a pie de página" not in sp or "informe en derecho" not in sp or "Word (.docx)" not in sp:
            faltan.append(str(agente.relative_to(RAIZ)))
    assert not faltan, f"sin la regla de citas y entrega: {faltan}"
