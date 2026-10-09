"""IDs canónicos de las entradas y entidades del mapa.

Las normas y los roles citados se canonizan en `citas_legales` (una sola gramática para todo el
producto); aquí viven los IDs de lo que el mapa inventaría: fichas, documentos, autores,
ministros, salas, tribunales, recursos y revistas.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional

from citas_legales import rol_canonico

# Palabras que delatan que un «autor» no es una persona (pies de imprenta, comités, facultades).
_NO_PERSONA = re.compile(
    r"\b(?:revista|comit[eé]|editorial|editor(?:es)?|facultad|universidad|division|department|consejo|"
    r"instituto|escuela|centro|direcci[oó]n|redacci[oó]n|anonimo|an[oó]nimo|varios|s/a|n/a|academia|poder|"
    r"ministerio|corte|tribunal|fiscal[ií]a|defensor[ií]a|biblioteca|congreso|senado|c[aá]mara|servicio|"
    r"superintendencia|contralor[ií]a|organizaci[oó]n|naciones|comisi[oó]n|asociaci[oó]n|fundaci[oó]n|"
    r"colegio|sociedad|grupo|programa|observatorio|gobierno|rep[uú]blica)\b",
    re.IGNORECASE)
_HONORIFICOS = re.compile(r"\b(?:ministr[oa]s?|sr\.?|sra\.?|srta\.?|don|do[ñn]a|abogad[oa]|suplente|"
                          r"titular|integrante|presidente|presidenta|redactor[a]?|fiscal)\b\.?", re.IGNORECASE)
_SALAS = {"primera": "cs-1", "segunda": "cs-2", "tercera": "cs-3", "cuarta": "cs-4", "quinta": "cs-5",
          "pleno": "cs-pleno"}


def ascii_min(texto: str) -> str:
    """Minúsculas sin tildes (NFKD → ASCII); la ñ queda como n."""
    t = unicodedata.normalize("NFKD", texto or "")
    return t.encode("ascii", "ignore").decode("ascii").lower()


def slug(texto: str) -> str:
    """«C.A. de Valparaíso» → «c-a-de-valparaiso». Determinista y sin dependencias."""
    return re.sub(r"[^a-z0-9]+", "-", ascii_min(texto)).strip("-")


def id_cs(rol: str) -> Optional[str]:
    return rol_canonico(rol, "cs")


def id_tc(rol: str) -> Optional[str]:
    return rol_canonico(rol, "tc")


def id_ta(tribunal: str, rol: str) -> Optional[str]:
    return rol_canonico(rol, tribunal.lower())


def id_ruta(prefijo: str, ruta: str, raiz: str) -> str:
    """`doc:revistas/rchd/1979/x` desde `doctrina/revistas/rchd/1979/x.md` (raíz `doctrina/`)."""
    rel = ruta[len(raiz):] if raiz and ruta.startswith(raiz) else ruta
    if rel.endswith(".md"):
        rel = rel[:-3]
    # «apuntes_orrego/Contrato de Arrendamiento.md»: un ID no lleva espacios (la ruta sí, aparte).
    return prefijo + ":" + re.sub(r"\s+", "_", rel.strip())


def _tokens_persona(nombre: str) -> List[str]:
    limpio = re.sub(r"\([^)]*\)", " ", nombre)
    toks = re.findall(r"[a-z0-9]+", ascii_min(limpio))
    # Iniciales sueltas («Diego I», «J. Pérez») no identifican: fuera.
    return [t for t in toks if len(t) > 1]


def es_persona(nombre: str) -> bool:
    return bool(_tokens_persona(nombre)) and not _NO_PERSONA.search(nombre)


def autor_id(nombre: str) -> Optional[str]:
    """Tokens del nombre ordenados: «Guzmán Brito, Alejandro» = «Alejandro Guzmán Brito»."""
    if not es_persona(nombre):
        return None
    return "autor:" + "_".join(sorted(_tokens_persona(nombre)))


def separar_autores(texto: str) -> List[str]:
    """Separa una lista de autores tal como viene en el YAML de las revistas.

    «A; B» → por punto y coma. «Apellidos, Nombres» (una coma, después ≤ 2 palabras, o coma sin
    espacio) es UNA persona. «Nombre Apellido, Nombre Apellido» (cada lado con ≥ 3 palabras o más
    de una coma) son varias. Después, « y » separa.
    """
    texto = " ".join(str(texto or "").split())
    if not texto:
        return []
    bloques = [b.strip() for b in texto.split(";")] if ";" in texto else [texto]
    partes: List[str] = []
    for bloque in bloques:
        for trozo in (p.strip() for p in re.split(r"\s+(?:y|e|&)\s+", bloque)):
            if re.search(r",[^\s,]", trozo):
                # «Apellidos,Nombres, Apellidos,Nombres»: la coma pegada separa apellido y nombre;
                # la coma con espacio separa personas.
                partes.extend(p.strip() for p in re.split(r",\s+", trozo))
                continue
            comas = [c.strip() for c in trozo.split(",")]
            if len(comas) == 2 and (len(comas[1].split()) <= 2 or ", " not in trozo):
                partes.append(trozo)
            elif len(comas) >= 2:
                partes.extend(comas)
            else:
                partes.append(trozo)
    return [p for p in partes if p and es_persona(p)]


def ministro_id(nombre: str) -> Optional[str]:
    """Mismo espacio de IDs para la Corte Suprema y los tribunales ambientales."""
    limpio = _HONORIFICOS.sub(" ", nombre or "")
    s = slug(limpio)
    return f"ministro:{s}" if s and len(s) > 3 else None


def ministros(texto: str) -> List[str]:
    """La lista «NOMBRE APELLIDO,NOMBRE APELLIDO» de la CS (o «—» / vacío) → IDs ordenados."""
    if not texto or texto.strip() in ("—", "-", "–"):
        return []
    ids = {ministro_id(p) for p in re.split(r"\s*[,;]\s*|\s+y\s+", texto)}
    return sorted(i for i in ids if i)


def sala_id(sala: str) -> Optional[str]:
    """«SEGUNDA, PENAL» → `sala:cs-2`; «Corte Suprema — TERCERA, CONSTITUCIONAL» → `sala:cs-3`."""
    s = ascii_min(sala or "")
    if "—" in (sala or ""):
        s = ascii_min(sala.split("—", 1)[1])
    s = s.strip()
    if not s:
        return None
    primera = re.split(r"[\s,]+", s)[0]
    if re.search(r"\bpleno\b", s):  # «TRIBUNAL PLENO», «Pleno»
        return "sala:cs-pleno"
    if primera in _SALAS:
        return f"sala:{_SALAS[primera]}"
    return f"sala:cs-{slug(s)}"


def tribunal_id(nombre: str) -> Optional[str]:
    """«C.A. de Valparaíso» → `tribunal:ca-valparaiso`."""
    s = ascii_min(nombre or "").strip()
    if not s:
        return None
    s = re.sub(r"^c\.?\s*a\.?\s+de\s+", "ca-", s)
    s = re.sub(r"^corte\s+de\s+apelaciones\s+de\s+", "ca-", s)
    return f"tribunal:{slug(s)}"


def recurso_id(recurso: str) -> Optional[str]:
    """«(CRIMEN) APELACIÓN AMPARO» → `recurso:crimen-apelacion-amparo`."""
    s = slug(recurso or "")
    return f"recurso:{s}" if s else None


def revista_id(sigla: str) -> str:
    return f"revista:{slug(sigla)}"
