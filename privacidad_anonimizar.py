"""Open Legal Chile — Anonimizador Reversible de Datos Personales (Ley N.° 21.719 / Art. 247 CP).

Permite enmascarar de forma determinista y reversible datos personales chilenos (RUT verificado
por Módulo 11, correos electrónicos, teléfonos chilenos, domicilios, cuentas bancarias y nombres
propios en contexto procesal) antes de enviar borradores o expedientes a un LLM en la nube.

Soporta dos motores:
1. Motor nativo determinista chileno (100 % offline, cero descargas, siempre disponible).
2. Motor enriquecido opcional con `presidio-analyzer` + `GLiNER` si el usuario instaló
   `pip install openlegal-chile[privacy]`.

El mapa de reversión puede guardarse localmente bajo `casos/<id>/mapa_pii.json` (carpeta
excluida de Git) para rehidratar el documento Word/OJV final en el equipo del abogado.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

from entes_publicos import validar_rut

# Patrones chilenos de alta precisión (ordenados de más específico a más general)
_RE_RUT = re.compile(r"\b\d{1,2}(?:\.\d{3}){2}-[\dkK]\b|\b\d{7,8}-[\dkK]\b")
_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_TELEFONO_CL = re.compile(r"(?:\+?56\s*9[\s-]?\d{4}[\s-]?\d{4}|\b9\s?\d{4}[\s-]\d{4}\b|\+?56\s*[2-7]\d[\s-]?\d{3,4}[\s-]?\d{4}\b)")
_RE_CUENTA_BANCO = re.compile(
    r"(?i)\b(?:cuenta\s+(?:corriente|vista|rut|de\s+ahorro)\s*(?:N[°º.]*\s*)?)(\d[\d.\-]{5,18}\d)\b"
)
_RE_DOMICILIO = re.compile(
    r"(?i)\b(?:domiciliad[oa]s?\s+en|con\s+domicilio\s+en|ubicad[oa]\s+en)\s+([A-ZÁÉÍÓÚÑ0-9][^,.;\n]{5,90}(?:,\s*(?:comuna\s+de\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]{2,35})?)"
)
_RE_PERSONA_TITULO = re.compile(
    r"\b(?:don|doña|Sr\.|Sra\.|Srta\.|menor)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\b"
)


def is_presidio_available() -> bool:
    """Verifica si Microsoft Presidio está instalado para enriquecimiento NER opcional."""
    try:
        import presidio_analyzer  # noqa: F401
        return True
    except ImportError:
        return False


class ChileanPIIAnonymizer:
    """Motor reversible de anonimización para cumplimiento Ley N.° 21.719 y secreto profesional."""

    def __init__(self, usar_presidio: bool = False):
        self.usar_presidio = bool(usar_presidio and is_presidio_available())
        self._presidio_analyzer: Optional[Any] = None

    def _cargar_presidio(self) -> Optional[Any]:
        if not self.usar_presidio:
            return None
        if self._presidio_analyzer is not None:
            return self._presidio_analyzer
        try:
            from presidio_analyzer import AnalyzerEngine
            self._presidio_analyzer = AnalyzerEngine()
            return self._presidio_analyzer
        except Exception:  # noqa: BLE001 — fallback transparente al motor nativo chileno
            self.usar_presidio = False
            return None

    @staticmethod
    def _registrar_token(
        valor: str,
        categoria: str,
        valor_a_token: Dict[str, str],
        token_a_valor: Dict[str, str],
        contadores: Dict[str, int],
    ) -> str:
        clave = valor.strip()
        if clave in valor_a_token:
            return valor_a_token[clave]
        contadores[categoria] = contadores.get(categoria, 0) + 1
        token = f"[{categoria}_{contadores[categoria]}]"
        valor_a_token[clave] = token
        token_a_valor[token] = clave
        return token

    def anonimizar(
        self,
        texto: str,
        incluir_domicilios: bool = True,
        incluir_personas: bool = True,
        mapa_previo: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Anonimiza el texto devolviendo texto seguro y mapa reversible {token: valor_real}."""
        if not texto:
            return {
                "texto_anonimizado": "",
                "mapa_reversion": dict(mapa_previo or {}),
                "resumen_entidades": {},
                "total_reemplazos": 0,
                "motor": "nativo_cl",
            }

        token_a_valor: Dict[str, str] = dict(mapa_previo or {})
        valor_a_token: Dict[str, str] = {v: k for k, v in token_a_valor.items()}
        contadores: Dict[str, int] = {}
        for tok in token_a_valor:
            m_cat = re.match(r"^\[([A-Z_]+)_(\d+)\]$", tok)
            if m_cat:
                cat, num = m_cat.group(1), int(m_cat.group(2))
                contadores[cat] = max(contadores.get(cat, 0), num)

        resumen: Dict[str, int] = {}
        resultado = texto

        def _contar(cat: str) -> None:
            resumen[cat] = resumen.get(cat, 0) + 1

        # 1. RUTs chilenos válidos (Módulo 11)
        def _rep_rut(m: re.Match[str]) -> str:
            candidato = m.group(0)
            check = validar_rut(candidato)
            if not check.get("valido"):
                return candidato
            _contar("RUT")
            return self._registrar_token(candidato, "RUT", valor_a_token, token_a_valor, contadores)

        resultado = _RE_RUT.sub(_rep_rut, resultado)

        # 2. Correos electrónicos
        def _rep_email(m: re.Match[str]) -> str:
            _contar("EMAIL")
            return self._registrar_token(m.group(0), "EMAIL", valor_a_token, token_a_valor, contadores)

        resultado = _RE_EMAIL.sub(_rep_email, resultado)

        # 3. Teléfonos chilenos
        def _rep_tel(m: re.Match[str]) -> str:
            _contar("TELEFONO")
            return self._registrar_token(m.group(0), "TELEFONO", valor_a_token, token_a_valor, contadores)

        resultado = _RE_TELEFONO_CL.sub(_rep_tel, resultado)

        # 4. Cuentas bancarias
        def _rep_cta(m: re.Match[str]) -> str:
            num = m.group(1)
            _contar("CUENTA_BANCARIA")
            tok = self._registrar_token(num, "CUENTA_BANCARIA", valor_a_token, token_a_valor, contadores)
            return m.group(0).replace(num, tok, 1)

        resultado = _RE_CUENTA_BANCO.sub(_rep_cta, resultado)

        # 5. Domicilios particulares
        if incluir_domicilios:
            def _rep_dom(m: re.Match[str]) -> str:
                addr = m.group(1).strip()
                if addr.startswith("["):
                    return m.group(0)
                _contar("DOMICILIO")
                tok = self._registrar_token(addr, "DOMICILIO", valor_a_token, token_a_valor, contadores)
                return m.group(0).replace(addr, tok, 1)

            resultado = _RE_DOMICILIO.sub(_rep_dom, resultado)

        # 6. Nombres propios precedidos por tratamientos forenses (don/doña/Sr./Sra./menor)
        if incluir_personas:
            def _rep_per(m: re.Match[str]) -> str:
                nom = m.group(1).strip()
                if nom.startswith("["):
                    return m.group(0)
                _contar("PERSONA")
                tok = self._registrar_token(nom, "PERSONA", valor_a_token, token_a_valor, contadores)
                return m.group(0).replace(nom, tok, 1)

            resultado = _RE_PERSONA_TITULO.sub(_rep_per, resultado)

        # 7. Enriquecimiento opcional con Presidio si fue solicitado e instalado
        motor_usado = "nativo_cl"
        analyzer = self._cargar_presidio()
        if analyzer is not None and incluir_personas:
            try:
                hallazgos = analyzer.analyze(text=resultado, language="es", entities=["PERSON", "LOCATION"])
                spans: List[Tuple[int, int, str]] = sorted(
                    ((h.start, h.end, h.entity_type) for h in hallazgos if getattr(h, "score", 0) >= 0.65),
                    key=lambda x: x[0],
                    reverse=True,
                )
                for ini, fin, etype in spans:
                    frag = resultado[ini:fin]
                    if "[" in frag or "]" in frag or len(frag.strip()) < 3:
                        continue
                    cat = "PERSONA" if etype == "PERSON" else "UBICACION"
                    _contar(cat)
                    tok = self._registrar_token(frag, cat, valor_a_token, token_a_valor, contadores)
                    resultado = resultado[:ini] + tok + resultado[fin:]
                motor_usado = "presidio+nativo_cl"
            except Exception:  # noqa: BLE001
                motor_usado = "nativo_cl"

        return {
            "texto_anonimizado": resultado,
            "mapa_reversion": token_a_valor,
            "resumen_entidades": resumen,
            "total_reemplazos": sum(resumen.values()),
            "motor": motor_usado,
            "nota_seguridad": (
                "Guarda mapa_reversion únicamente en disco local (carpeta casos/, excluida de Git). "
                "Cumplimiento preventivo Ley N.° 21.719 y Art. 247 Código Penal."
            ),
        }

    @staticmethod
    def desanonimizar(texto_anonimizado: str, mapa_reversion: Dict[str, str]) -> str:
        """Restaura las identidades originales localmente a partir del mapa de reversión."""
        salida = texto_anonimizado or ""
        # Ordenar por longitud de token descendente para evitar colisiones parciales ([RUT_1] vs [RUT_10])
        for tok in sorted(mapa_reversion.keys(), key=len, reverse=True):
            salida = salida.replace(tok, str(mapa_reversion[tok]))
        return salida

    @staticmethod
    def guardar_mapa_local(mapa_reversion: Dict[str, str], ruta_destino: str) -> str:
        """Guarda el mapa de reversión con permisos restrictivos (0600 en POSIX)."""
        destino = pathlib.Path(ruta_destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(mapa_reversion, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            destino.chmod(0o600)
        except OSError:
            pass
        return str(destino)


def anonimizar_texto(
    texto: str,
    incluir_domicilios: bool = True,
    incluir_personas: bool = True,
    usar_presidio: bool = False,
    mapa_previo: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Atajo funcional para anonimizar texto jurídico chileno."""
    return ChileanPIIAnonymizer(usar_presidio=usar_presidio).anonimizar(
        texto,
        incluir_domicilios=incluir_domicilios,
        incluir_personas=incluir_personas,
        mapa_previo=mapa_previo,
    )


def desanonimizar_texto(texto_anonimizado: str, mapa_reversion: Dict[str, str]) -> str:
    """Atajo funcional para revertir tokens PII localmente."""
    return ChileanPIIAnonymizer.desanonimizar(texto_anonimizado, mapa_reversion)
