"""Open Legal Chile — Indicadores SII y Calculadoras Forenses Deterministas.

Módulo cargado de manera perezosa (PEP 562) para evitar impacto en el cold start MCP:
1. Indicadores oficiales SII (UF diaria, UTM/UTA e IPC mensual) con caché local e interfaz pura.
2. Calendario oficial de feriados de Chile y cálculo determinista de plazos procesales.
3. Cálculo determinista de finiquito, indemnizaciones laborales (Arts. 163/168/172 CT) y AFC.
4. Cálculo de cuantías legales: días-multa (Leyes N.° 21.595 y 20.393) y alimentos en UTM (Ley N.° 14.908).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from citas_legales import formatear_cita
from config import cache_fresco, pedir_http

_CACHE_DIR_DEFECTO = os.path.join(os.path.expanduser("~"), ".openlegal")
_TTL_INDICADORES_SEGUNDOS = 12 * 3600

_MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_DIAS_SEMANA_ES = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)

# Solsticio de invierno en Chile (Ley N.° 21.357 — Día Nacional de los Pueblos Indígenas)
_PUEBLOS_INDIGENAS = {
    2021: date(2021, 6, 21),
    2022: date(2022, 6, 21),
    2023: date(2023, 6, 21),
    2024: date(2024, 6, 20),
    2025: date(2025, 6, 20),
    2026: date(2026, 6, 21),
    2027: date(2027, 6, 21),
    2028: date(2028, 6, 20),
    2029: date(2029, 6, 20),
    2030: date(2030, 6, 21),
    2031: date(2031, 6, 21),
    2032: date(2032, 6, 20),
}

_GRADOS_DIAS_MULTA_21595: Dict[str, Tuple[int, int, str]] = {
    "prision": (1, 10, "Prisión o delito con solo multa/pena no privativa de libertad"),
    "presidio_menor_minimo": (11, 50, "Presidio o reclusión menor en su grado mínimo"),
    "presidio_menor_medio": (51, 100, "Presidio o reclusión menor en su grado medio"),
    "presidio_menor_maximo": (101, 150, "Presidio o reclusión menor en su grado máximo"),
    "presidio_mayor_minimo": (151, 200, "Presidio o reclusión mayor en su grado mínimo"),
    "presidio_mayor_medio": (201, 250, "Presidio o reclusión mayor en su grado medio"),
    "presidio_mayor_maximo": (251, 300, "Presidio o reclusión mayor en su grado máximo a presidio perpetuo calificado"),
}

_RECARGOS_ART_168: Dict[str, Tuple[float, str]] = {
    "161": (0.30, "Art. 168 letra a) CT: aplicación improcedente del Art. 161 (30 %)"),
    "159": (0.50, "Art. 168 letra b) CT: aplicación injustificada del Art. 159 o sin causal legal (50 %)"),
    "160": (0.80, "Art. 168 letra c) CT: aplicación indebida de las causales del Art. 160 (80 %)"),
    "160_sin_motivo_plausible": (1.00, "Art. 168 inc. 2 CT: Art. 160 N.° 1, 5 o 6 carente de motivo plausible (100 %)"),
    "171_autodespido": (0.50, "Art. 171 CT: despido indirecto base (50 %; puede elevarse a 80 % si se funda en Art. 160 N.° 1 o 5)"),
    "renuncia": (0.0, "Renuncia voluntaria o mutuo acuerdo (Art. 159 N.° 1 o 2 CT): sin indemnización legal por término"),
}


# ---------------------------------------------------------------------------
# 1. Indicadores Oficiales SII (UF, UTM, UTA, IPC) y Conversor Monetario
# ---------------------------------------------------------------------------

def _parsear_numero_chile(texto: str) -> Optional[float]:
    """Convierte un número en formato chileno («41.377,93» o «69.751») a float."""
    limpio = re.sub(r"[\s\xa0$]", "", str(texto or ""))
    if not limpio or not re.search(r"\d", limpio):
        return None
    limpio = limpio.replace(".", "").replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        return None


def parsear_html_uf_sii(html: str, anio: int) -> Dict[str, float]:
    """Extrae la serie diaria UF (`{'YYYY-MM-DD': float}`) desde HTML oficial del SII."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    valores: Dict[str, float] = {}
    for tabla in soup.find_all("table"):
        filas = tabla.find_all("tr")
        if not filas:
            continue
        encabezado = filas[0].get_text(" ", strip=True).lower()
        mes = _MESES_ES.get(encabezado)
        if mes is None:
            continue
        for fila in filas[1:]:
            celdas = [c.get_text(" ", strip=True) for c in fila.find_all(["th", "td"])]
            for i in range(0, len(celdas) - 1, 2):
                dia_txt = celdas[i].strip()
                val = _parsear_numero_chile(celdas[i + 1])
                if dia_txt.isdigit() and val is not None:
                    dia = int(dia_txt)
                    try:
                        f_iso = date(anio, mes, dia).isoformat()
                        valores[f_iso] = val
                    except ValueError:
                        continue
    return dict(sorted(valores.items()))


def parsear_html_utm_sii(html: str, anio: int) -> Dict[int, Dict[str, Any]]:
    """Extrae UTM, UTA e IPC mensual (`{mes: {...}}`) desde HTML oficial del SII."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table", id="table_export")
    if tabla is None:
        tablas = soup.find_all("table")
        tabla = tablas[0] if tablas else None
    if tabla is None:
        return {}

    salida: Dict[int, Dict[str, Any]] = {}
    for fila in tabla.find_all("tr"):
        celdas = [c.get_text(" ", strip=True) for c in fila.find_all(["th", "td"])]
        if len(celdas) < 3:
            continue
        mes = _MESES_ES.get(celdas[0].strip().lower())
        if mes is None:
            continue
        utm_f = _parsear_numero_chile(celdas[1])
        uta_f = _parsear_numero_chile(celdas[2])
        if utm_f is None or uta_f is None:
            continue
        salida[mes] = {
            "anio": anio,
            "mes": mes,
            "mes_nombre": celdas[0].strip(),
            "utm": int(round(utm_f)),
            "uta": int(round(uta_f)),
            "ipc_puntos": _parsear_numero_chile(celdas[3]) if len(celdas) > 3 else None,
            "ipc_mensual": _parsear_numero_chile(celdas[4]) if len(celdas) > 4 else None,
            "ipc_acumulado": _parsear_numero_chile(celdas[5]) if len(celdas) > 5 else None,
            "ipc_12m": _parsear_numero_chile(celdas[6]) if len(celdas) > 6 else None,
        }
    return dict(sorted(salida.items()))


def _resolver_fecha(fecha: Optional[str]) -> Tuple[date, Optional[str]]:
    if not fecha or not str(fecha).strip():
        return date.today(), None
    limpio = str(fecha).strip()
    try:
        return date.fromisoformat(limpio), None
    except ValueError:
        return date.today(), f"Formato de fecha inválido: '{limpio}'. Use YYYY-MM-DD."


def obtener_indicadores_sii(
    anio: Optional[int] = None,
    fecha: Optional[str] = None,
    cache_dir: Optional[str] = None,
    usar_cache: bool = True,
) -> Dict[str, Any]:
    """Obtiene valores oficiales de UF, UTM, UTA e IPC del SII con caché local."""
    f_ref, err_fecha = _resolver_fecha(fecha)
    if err_fecha:
        return {"error": err_fecha, "sin_fuente_verificable": True}
    anio_obj = int(anio) if anio is not None else f_ref.year
    if fecha and anio is not None and f_ref.year != anio_obj:
        anio_obj = f_ref.year

    carpeta = cache_dir or _CACHE_DIR_DEFECTO
    os.makedirs(carpeta, exist_ok=True)
    ruta_cache = os.path.join(carpeta, f"indicadores_sii_{anio_obj}.json")

    url_uf = f"https://www.sii.cl/valores_y_fechas/uf/uf{anio_obj}.htm"
    url_utm = f"https://www.sii.cl/valores_y_fechas/utm/utm{anio_obj}.htm"

    datos_cache: Optional[Dict[str, Any]] = None
    if usar_cache and os.path.exists(ruta_cache):
        try:
            with open(ruta_cache, "r", encoding="utf-8") as fh:
                leido = json.load(fh)
            if isinstance(leido, dict):
                datos_cache = leido
        except Exception:  # noqa: BLE001
            datos_cache = None

    copia_vencida = False
    if datos_cache is not None and cache_fresco(ruta_cache, _TTL_INDICADORES_SEGUNDOS):
        datos = datos_cache
    else:
        try:
            html_uf = pedir_http(url_uf, timeout=10.0).decode("utf-8", errors="ignore")
            html_utm = pedir_http(url_utm, timeout=10.0).decode("utf-8", errors="ignore")
            uf_dias = parsear_html_uf_sii(html_uf, anio_obj)
            utm_meses = parsear_html_utm_sii(html_utm, anio_obj)
            if not uf_dias and not utm_meses:
                raise ValueError("El HTML del SII no devolvió tablas de UF ni UTM")
            datos = {
                "anio": anio_obj,
                "uf_dias": uf_dias,
                "utm_meses": {str(k): v for k, v in utm_meses.items()},
            }
            with open(ruta_cache, "w", encoding="utf-8") as fh:
                json.dump(datos, fh, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            if datos_cache is not None:
                datos = datos_cache
                copia_vencida = True
            else:
                return {
                    "anio": anio_obj,
                    "fecha_consulta": f_ref.isoformat(),
                    "error": f"No se pudieron obtener los indicadores desde el SII ({str(exc)[:140]}).",
                    "sin_fuente_verificable": True,
                    "urls": {"uf": url_uf, "utm": url_utm},
                }

    uf_mapa: Dict[str, float] = dict(datos.get("uf_dias") or {})
    utm_mapa: Dict[str, Dict[str, Any]] = {str(k): v for k, v in (datos.get("utm_meses") or {}).items()}
    f_iso = f_ref.isoformat()
    uf_fecha = uf_mapa.get(f_iso)
    ultima_fecha_uf = max(uf_mapa) if uf_mapa else None
    uf_ultimo = {"fecha": ultima_fecha_uf, "valor": uf_mapa[ultima_fecha_uf]} if ultima_fecha_uf else None
    utm_mes = utm_mapa.get(str(f_ref.month))
    if utm_mes is None and utm_mapa:
        ultimo_mes_k = str(max(int(k) for k in utm_mapa))
        utm_mes = utm_mapa.get(ultimo_mes_k)

    citas = [
        formatear_cita(
            "SII",
            f"Valores UF y UTM {anio_obj}",
            url=url_uf,
            texto=(
                f"UF al {f_iso}: {uf_fecha if uf_fecha is not None else 'no publicada para esa fecha'}"
                + (f" · UTM {utm_mes.get('mes_nombre')}: ${utm_mes.get('utm'):,}".replace(",", ".") if utm_mes else "")
            ),
        )
    ]

    salida: Dict[str, Any] = {
        "anio": anio_obj,
        "fecha_consulta": f_iso,
        "fuente": "Servicio de Impuestos Internos (SII)",
        "urls": {"uf": url_uf, "utm": url_utm},
        "uf_fecha": uf_fecha,
        "uf_ultimo_disponible": uf_ultimo,
        "utm_mes": utm_mes,
        "series_uf_total_dias": len(uf_mapa),
        "meses_utm": len(utm_mapa),
        "citas": citas,
    }
    if copia_vencida:
        salida["copia_local_vencida"] = True
    return salida


def convertir_moneda_legal(
    monto: float,
    desde: str,
    hacia: str,
    fecha: Optional[str] = None,
    uf_override: Optional[float] = None,
    utm_override: Optional[float] = None,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Convierte montos jurídicos chilenos entre CLP, UF, UTM y UTA."""
    origen = str(desde or "").strip().upper()
    destino = str(hacia or "").strip().upper()
    validas = {"CLP", "UF", "UTM", "UTA"}
    if origen not in validas or destino not in validas:
        return {"error": f"Moneda no soportada ({origen} -> {destino}). Use: {sorted(validas)}"}

    necesita_uf = "UF" in (origen, destino)
    necesita_utm = "UTM" in (origen, destino) or "UTA" in (origen, destino)

    uf_val = float(uf_override) if uf_override is not None else None
    utm_val = float(utm_override) if utm_override is not None else None
    citas: List[Dict[str, str]] = []
    fecha_usada = fecha or date.today().isoformat()

    if (necesita_uf and uf_val is None) or (necesita_utm and utm_val is None):
        ind = obtener_indicadores_sii(fecha=fecha, cache_dir=cache_dir)
        if ind.get("error"):
            return ind
        citas = list(ind.get("citas") or [])
        if necesita_uf and uf_val is None:
            uf_raw = ind.get("uf_fecha")
            if uf_raw is None and isinstance(ind.get("uf_ultimo_disponible"), dict):
                uf_raw = ind["uf_ultimo_disponible"].get("valor")
                fecha_usada = str(ind["uf_ultimo_disponible"].get("fecha") or fecha_usada)
            if uf_raw is None:
                return {"error": f"Sin valor UF publicado para {fecha_usada}.", "sin_fuente_verificable": True}
            uf_val = float(uf_raw)
        if necesita_utm and utm_val is None:
            utm_info = ind.get("utm_mes")
            if not isinstance(utm_info, dict) or utm_info.get("utm") is None:
                return {"error": f"Sin valor UTM publicado para {fecha_usada}.", "sin_fuente_verificable": True}
            utm_val = float(utm_info["utm"])

    monto_f = float(monto)
    if origen == "CLP":
        monto_clp = monto_f
    elif origen == "UF":
        monto_clp = monto_f * float(uf_val or 0.0)
    elif origen == "UTM":
        monto_clp = monto_f * float(utm_val or 0.0)
    else:
        monto_clp = monto_f * 12.0 * float(utm_val or 0.0)

    resultado: int | float
    if destino == "CLP":
        resultado = round(monto_clp)
    elif destino == "UF":
        resultado = round(monto_clp / float(uf_val or 1.0), 4)
    elif destino == "UTM":
        resultado = round(monto_clp / float(utm_val or 1.0), 5)
    else:
        resultado = round(monto_clp / (12.0 * float(utm_val or 1.0)), 5)

    return {
        "monto_origen": monto_f,
        "moneda_origen": origen,
        "monto_destino": resultado,
        "moneda_destino": destino,
        "monto_clp_equivalente": round(monto_clp),
        "fecha_valor": fecha_usada,
        "uf_utilizada": uf_val,
        "utm_utilizada": utm_val,
        "citas": citas,
    }


# ---------------------------------------------------------------------------
# 2. Calendario Oficial de Feriados de Chile y Plazos Procesales
# ---------------------------------------------------------------------------

def _domingo_pascua(anio: int) -> date:
    """Algoritmo gregoriano anónimo para calcular el Domingo de Resurrección."""
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    mes = (h + el - 7 * m + 114) // 31
    dia = ((h + el - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _lunes_ley_19668(fecha_base: date) -> date:
    """Traslada feriado al lunes correspondiente conforme a la Ley N.° 19.668."""
    wd = fecha_base.weekday()  # 0=lunes, 1=martes, 2=miércoles, 3=jueves, 4=viernes
    if wd in (1, 2, 3):
        return fecha_base - timedelta(days=wd)
    if wd == 4:
        return fecha_base + timedelta(days=3)
    return fecha_base


def feriados_chile(anio: int, adicionales: Optional[List[str]] = None) -> Dict[date, str]:
    """Retorna el calendario oficial de feriados legales de Chile para un año dado."""
    pascua = _domingo_pascua(anio)
    feriados: Dict[date, str] = {
        date(anio, 1, 1): "Año Nuevo",
        pascua - timedelta(days=2): "Viernes Santo",
        pascua - timedelta(days=1): "Sábado Santo",
        date(anio, 5, 1): "Día Nacional del Trabajo",
        date(anio, 5, 21): "Día de las Glorias Navales",
        _PUEBLOS_INDIGENAS.get(anio, date(anio, 6, 21)): "Día Nacional de los Pueblos Indígenas (Ley N.° 21.357)",
        _lunes_ley_19668(date(anio, 6, 29)): "San Pedro y San Pablo (Ley N.° 19.668)",
        date(anio, 7, 16): "Día de la Virgen del Carmen",
        date(anio, 8, 15): "Asunción de la Virgen",
        date(anio, 9, 18): "Independencia Nacional",
        date(anio, 9, 19): "Día de las Glorias del Ejército",
        _lunes_ley_19668(date(anio, 10, 12)): "Encuentro de Dos Mundos (Ley N.° 19.668)",
        date(anio, 11, 1): "Día de Todos los Santos",
        date(anio, 12, 8): "Inmaculada Concepción",
        date(anio, 12, 25): "Navidad",
    }

    # Ley N.° 20.299: Día de las Iglesias Evangélicas y Protestantes (31 oct; traslado si mar/mié)
    oct_31 = date(anio, 10, 31)
    if oct_31.weekday() == 1:
        feriados[date(anio, 10, 27)] = "Día de las Iglesias Evangélicas y Protestantes (Ley N.° 20.299)"
    elif oct_31.weekday() == 2:
        feriados[date(anio, 11, 2)] = "Día de las Iglesias Evangélicas y Protestantes (Ley N.° 20.299)"
    else:
        feriados[oct_31] = "Día de las Iglesias Evangélicas y Protestantes (Ley N.° 20.299)"

    # Ley N.° 20.215: Feriado adicional de Fiestas Patrias (17 o 20 de septiembre)
    sep_18_wd = date(anio, 9, 18).weekday()
    if sep_18_wd == 1:
        feriados[date(anio, 9, 17)] = "Fiestas Patrias — día adicional (Ley N.° 20.215)"
    elif sep_18_wd in (2, 3):
        feriados[date(anio, 9, 20)] = "Fiestas Patrias — día adicional (Ley N.° 20.215)"

    for f_txt in adicionales or []:
        try:
            feriados[date.fromisoformat(str(f_txt).strip())] = "Feriado adicional declarado"
        except ValueError:
            continue

    return dict(sorted(feriados.items()))


def _normalizar_regimen(regimen: str) -> str:
    r = str(regimen or "judicial_cpc").strip().lower()
    alias = {
        "civil": "judicial_cpc",
        "cpc": "judicial_cpc",
        "judicial": "judicial_cpc",
        "judicial_cpc": "judicial_cpc",
        "laboral": "laboral",
        "trabajo": "laboral",
        "ct": "laboral",
        "administrativo": "administrativo",
        "admin": "administrativo",
        "19880": "administrativo",
        "corridos": "corridos",
        "corrido": "corridos",
        "proteccion": "corridos",
    }
    return alias.get(r, "judicial_cpc")


def _es_habil(fecha: date, regimen: str, feriados: Dict[date, str]) -> bool:
    if regimen == "corridos":
        return True
    if fecha.weekday() == 6 or fecha in feriados:
        return False
    if regimen == "administrativo" and fecha.weekday() == 5:
        return False
    return True


def calcular_plazo_procesal(
    fecha_notificacion: str,
    plazo_dias: int,
    regimen: str = "judicial_cpc",
    dias_suspension_dt: int = 0,
    feriados_adicionales: Optional[List[str]] = None,
    fecha_referencia: Optional[str] = None,
) -> Dict[str, Any]:
    """Calcula vencimiento exacto de plazos en Chile descontando feriados y reglas de caducidad."""
    try:
        f_notif = date.fromisoformat(str(fecha_notificacion).strip())
    except ValueError:
        return {"error": f"Formato de 'fecha_notificacion' inválido: '{fecha_notificacion}'. Use YYYY-MM-DD."}

    try:
        plazo_base = int(plazo_dias)
        susp_dt = max(0, int(dias_suspension_dt))
    except (ValueError, TypeError):
        return {"error": "'plazo_dias' y 'dias_suspension_dt' deben ser enteros válidos."}

    if plazo_base < 0:
        return {"error": "'plazo_dias' no puede ser negativo."}

    reg = _normalizar_regimen(regimen)
    plazo_efectivo = plazo_base
    if reg == "laboral" and susp_dt > 0:
        plazo_efectivo = plazo_base + min(susp_dt, max(0, 90 - plazo_base))

    anios_cubrir = range(f_notif.year, f_notif.year + max(2, plazo_efectivo // 180 + 2))
    feriados: Dict[date, str] = {}
    for yr in anios_cubrir:
        feriados.update(feriados_chile(yr, adicionales=feriados_adicionales))

    feriados_ventana: List[Dict[str, str]] = []
    if plazo_efectivo == 0:
        vencimiento = f_notif
        if reg == "administrativo":
            while not _es_habil(vencimiento, reg, feriados):
                vencimiento += timedelta(days=1)
    else:
        contados = 0
        actual = f_notif
        while contados < plazo_efectivo:
            actual += timedelta(days=1)
            if actual in feriados:
                feriados_ventana.append({"fecha": actual.isoformat(), "nombre": feriados[actual]})
            if _es_habil(actual, reg, feriados):
                contados += 1
        vencimiento = actual

    f_ref, err_ref = _resolver_fecha(fecha_referencia)
    if err_ref:
        return {"error": err_ref}

    dias_restantes = (vencimiento - f_ref).days
    if dias_restantes > 0:
        estado = "EN PLAZO"
    elif dias_restantes == 0:
        estado = "VENCE HOY"
    else:
        estado = "VENCIDO"

    reglas_info = {
        "judicial_cpc": ("Art. 66 CPC (días hábiles lunes a sábado; suspende domingos y feriados)", "Código de Procedimiento Civil, Art. 66"),
        "laboral": ("Arts. 168 y 435 CT (lunes a sábado; suspende domingos y feriados; tope 90 días con reclamo DT)", "Código del Trabajo, Art. 435"),
        "administrativo": ("Art. 25 Ley N.° 19.880 (lunes a viernes; inhábiles sábados, domingos y feriados)", "Ley N° 19.880, Art. 25"),
        "corridos": ("Arts. 48-50 Código Civil / Acta CS N.° 94-2015 (días corridos sin suspensión)", "Código Civil, Art. 50"),
    }
    norma_base, cita_id = reglas_info[reg]

    notas: List[str] = []
    if reg == "corridos" and (vencimiento.weekday() == 6 or vencimiento in feriados):
        notas.append(
            "El vencimiento cae en domingo o feriado legal: en recurso de protección (Acta CS N.° 94-2015) "
            "el plazo de 30 días corridos es fatal y se recomienda presentar a más tardar el día hábil previo si "
            "existen dudas de interpretación."
        )
    if reg == "laboral" and susp_dt > 0:
        notas.append(
            f"Se aplicó suspensión por reclamo ante la Dirección del Trabajo ({susp_dt} días), "
            f"respetando el tope máximo legal de 90 días hábiles del Art. 168 inc. final CT (plazo efectivo: {plazo_efectivo} días)."
        )

    citas = [
        formatear_cita(
            "BCN",
            cita_id,
            url="https://www.bcn.cl/leychile/",
            texto=norma_base,
        )
    ]

    return {
        "fecha_notificacion": f_notif.isoformat(),
        "fecha_inicio_computo": (f_notif + timedelta(days=1)).isoformat(),
        "plazo_dias": plazo_base,
        "plazo_efectivo_dias": plazo_efectivo,
        "regimen": reg,
        "norma_base": norma_base,
        "fecha_vencimiento": vencimiento.isoformat(),
        "dia_semana_vencimiento": _DIAS_SEMANA_ES[vencimiento.weekday()],
        "dias_corridos_totales": (vencimiento - f_notif).days,
        "feriados_en_ventana": feriados_ventana,
        "estado": estado,
        "dias_corridos_restantes": dias_restantes,
        "notas": notas,
        "citas": citas,
    }


# ---------------------------------------------------------------------------
# 3. Finiquito e Indemnizaciones Laborales (Arts. 67, 73, 161-172 CT + Ley 19.728)
# ---------------------------------------------------------------------------

def _diferencia_ymd(inicio: date, fin: date) -> Tuple[int, int, int]:
    """Calcula años, meses y días calendario exactos entre `inicio` y `fin`."""
    anios = fin.year - inicio.year
    meses = fin.month - inicio.month
    dias = fin.day - inicio.day
    if dias < 0:
        meses -= 1
        ultimo_prev = date(fin.year, fin.month, 1) - timedelta(days=1)
        dias += ultimo_prev.day
    if meses < 0:
        anios -= 1
        meses += 12
    return anios, meses, dias


def _dias_corridos_feriado(fecha_termino: date, dias_habiles_pendientes: float) -> float:
    """Proyecta días hábiles de feriado (lun–vie sin festivos) a días corridos conforme DT."""
    if dias_habiles_pendientes <= 0:
        return 0.0
    enteros = int(dias_habiles_pendientes)
    fraccion = dias_habiles_pendientes - enteros
    feriados: Dict[date, str] = {}
    for yr in (fecha_termino.year, fecha_termino.year + 1):
        feriados.update(feriados_chile(yr))
    actual = fecha_termino
    habiles_vistos = 0
    while habiles_vistos < enteros:
        actual += timedelta(days=1)
        if actual.weekday() < 5 and actual not in feriados:
            habiles_vistos += 1
    corridos_base = (actual - fecha_termino).days
    return round(corridos_base + (fraccion * 1.4), 2)


def _ultimo_dia_mes_anterior(fecha: date) -> date:
    return date(fecha.year, fecha.month, 1) - timedelta(days=1)


def calcular_finiquito_laboral(
    fecha_ingreso: str,
    fecha_termino: str,
    remuneracion_mensual_clp: float,
    causal: str = "161",
    aviso_previo_dado: bool = False,
    dias_feriado_pendientes: Optional[float] = None,
    aporte_empleador_afc_clp: float = 0.0,
    aplicar_tope_90_uf: bool = True,
    uf_valor: Optional[float] = None,
    meses_cotizaciones_impagas_ley_bustos: int = 0,
    es_trabajador_anterior_1981: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Liquidación determinista de finiquito e indemnización judicial por despido en Chile."""
    try:
        f_ing = date.fromisoformat(str(fecha_ingreso).strip())
        f_term = date.fromisoformat(str(fecha_termino).strip())
    except ValueError:
        return {"error": "Formato de fechas inválido. Use YYYY-MM-DD para 'fecha_ingreso' y 'fecha_termino'."}

    if f_term < f_ing:
        return {"error": "'fecha_termino' no puede ser anterior a 'fecha_ingreso'."}

    rem = float(remuneracion_mensual_clp)
    if rem <= 0:
        return {"error": "'remuneracion_mensual_clp' debe ser mayor a 0."}

    c_norm = str(causal or "161").strip().lower()
    if c_norm not in _RECARGOS_ART_168:
        return {"error": f"Causal no reconocida: '{causal}'. Opciones: {sorted(_RECARGOS_ART_168)}."}

    anios_comp, meses_rest, dias_rest = _diferencia_ymd(f_ing, f_term)
    if anios_comp < 1:
        anios_brutos = 0
    else:
        fraccion_superior_6m = meses_rest > 6 or (meses_rest == 6 and dias_rest > 0)
        anios_brutos = anios_comp + (1 if fraccion_superior_6m else 0)
    anios_indemnizables = anios_brutos if es_trabajador_anterior_1981 else min(anios_brutos, 11)

    uf_usada: Optional[float] = float(uf_valor) if uf_valor is not None else None
    fecha_uf_ref = _ultimo_dia_mes_anterior(f_term)
    aviso_uf: Optional[str] = None
    citas_extras: List[Dict[str, str]] = []

    if aplicar_tope_90_uf and uf_usada is None:
        ind = obtener_indicadores_sii(fecha=fecha_uf_ref.isoformat(), cache_dir=cache_dir)
        if not ind.get("error"):
            uf_raw = ind.get("uf_fecha")
            if uf_raw is None and isinstance(ind.get("uf_ultimo_disponible"), dict):
                uf_raw = ind["uf_ultimo_disponible"].get("valor")
            if uf_raw is not None:
                uf_usada = float(uf_raw)
            citas_extras.extend(ind.get("citas") or [])
        else:
            aviso_uf = (
                "No pudo consultarse la UF en SII sin conexión; el tope de 90 UF (Art. 172 CT) "
                "no pudo aplicarse automáticamente sin `uf_valor`."
            )

    tope_90_uf_clp = round(90.0 * uf_usada) if uf_usada is not None else None
    if aplicar_tope_90_uf and tope_90_uf_clp is not None:
        base_indem = min(round(rem), tope_90_uf_clp)
        tope_aplicado = round(rem) > tope_90_uf_clp
    else:
        base_indem = round(rem)
        tope_aplicado = False

    if dias_feriado_pendientes is not None:
        dias_hab_feriado = max(0.0, float(dias_feriado_pendientes))
    else:
        # 15 días hábiles anuales => 1,25 días hábiles por mes trabajado desde el último aniversario
        dias_hab_feriado = round((meses_rest + (dias_rest / 30.0)) * 1.25, 2)

    dias_corr_feriado = _dias_corridos_feriado(f_term, dias_hab_feriado)
    feriado_prop_clp = round((rem / 30.0) * dias_corr_feriado)

    # Escenario 1: Finiquito base
    if c_norm == "161":
        aviso_fin = 0 if aviso_previo_dado else base_indem
        ias_fin = base_indem * anios_indemnizables
        afc_fin = min(max(0, round(aporte_empleador_afc_clp)), ias_fin)
    else:
        aviso_fin = 0
        ias_fin = 0
        afc_fin = 0
    total_finiquito = aviso_fin + ias_fin + feriado_prop_clp - afc_fin

    # Escenario 2: Demanda judicial (despido injustificado/indebido/improcedente o autodespido)
    pct_recargo, desc_recargo = _RECARGOS_ART_168[c_norm]
    if c_norm == "renuncia":
        aviso_jud = 0
        ias_jud = 0
        recargo_jud = 0
        restitucion_afc = 0
    else:
        aviso_jud = 0 if (c_norm == "161" and aviso_previo_dado) else base_indem
        ias_jud = base_indem * anios_indemnizables
        recargo_jud = round(ias_jud * pct_recargo)
        restitucion_afc = afc_fin

    meses_bustos = max(0, int(meses_cotizaciones_impagas_ley_bustos))
    bustos_clp = (
        round(rem) * meses_bustos
        if (meses_bustos > 0 and c_norm in ("161", "159", "160", "160_sin_motivo_plausible"))
        else 0
    )
    total_judicial = aviso_jud + ias_jud + recargo_jud + feriado_prop_clp + bustos_clp

    caducidad = calcular_plazo_procesal(f_term.isoformat(), 60, regimen="laboral")

    alertas: List[str] = []
    if tope_aplicado and tope_90_uf_clp is not None:
        alertas.append(f"Se aplicó el tope legal de 90 UF (Art. 172 inc. final CT): $ {tope_90_uf_clp:,}".replace(",", "."))
    if aviso_uf:
        alertas.append(aviso_uf)
    if restitucion_afc > 0:
        alertas.append(
            "Jurisprudencia Cuarta Sala CS: declarado improcedente el despido (Art. 161 CT), "
            f"procede restituir el descuento AFC ($ {restitucion_afc:,}).".replace(",", ".")
        )
    if bustos_clp > 0:
        alertas.append(
            f"Nulidad del despido (Ley Bustos, Art. 162 incs. 5-7 CT): estimación por {meses_bustos} "
            f"meses hasta convalidación = $ {bustos_clp:,}.".replace(",", ".")
        )

    citas = [
        formatear_cita("BCN", "Código del Trabajo, Art. 163", url="https://www.bcn.cl/leychile/navegar?idNorma=207436",
                       texto="Indemnización por años de servicio (30 días por año y fracción superior a 6 meses; límite de 330 días)."),
        formatear_cita("BCN", "Código del Trabajo, Art. 168", url="https://www.bcn.cl/leychile/navegar?idNorma=207436",
                       texto=f"Plazo de caducidad de 60 días hábiles y recargo legal: {desc_recargo}."),
        formatear_cita("BCN", "Código del Trabajo, Art. 172", url="https://www.bcn.cl/leychile/navegar?idNorma=207436",
                       texto="Última remuneración mensual para indemnizaciones y tope máximo de 90 unidades de fomento del último día del mes anterior."),
        *citas_extras,
    ]

    return {
        "causal": c_norm,
        "antiguedad": {
            "fecha_ingreso": f_ing.isoformat(),
            "fecha_termino": f_term.isoformat(),
            "anios_completos": anios_comp,
            "meses_fraccion": meses_rest,
            "dias_fraccion": dias_rest,
            "anios_indemnizables": anios_indemnizables,
        },
        "base_calculo": {
            "remuneracion_mensual_clp": round(rem),
            "uf_valor": uf_usada,
            "fecha_referencia_uf": fecha_uf_ref.isoformat(),
            "tope_90_uf_aplicado": tope_aplicado,
            "tope_90_uf_clp": tope_90_uf_clp,
            "base_indemnizatoria_clp": base_indem,
            "dias_habiles_feriado_pendientes": dias_hab_feriado,
            "dias_corridos_feriado": dias_corr_feriado,
        },
        "finiquito_base": {
            "indemnizacion_sustitutiva_aviso_previo_clp": aviso_fin,
            "indemnizacion_anios_servicio_clp": ias_fin,
            "feriado_proporcional_clp": feriado_prop_clp,
            "descuento_afc_empleador_clp": afc_fin,
            "total_liquido_estimado_clp": total_finiquito,
            "total_uf": round(total_finiquito / uf_usada, 2) if uf_usada else None,
        },
        "escenario_demanda_judicial": {
            "indemnizacion_sustitutiva_aviso_previo_clp": aviso_jud,
            "indemnizacion_anios_servicio_clp": ias_jud,
            "recargo_art_168_porcentaje": int(round(pct_recargo * 100)),
            "recargo_art_168_clp": recargo_jud,
            "restitucion_afc_clp": restitucion_afc,
            "feriado_proporcional_clp": feriado_prop_clp,
            "estimacion_ley_bustos_clp": bustos_clp,
            "total_demanda_estimado_clp": total_judicial,
            "total_demanda_uf": round(total_judicial / uf_usada, 2) if uf_usada else None,
            "diferencia_sobre_finiquito_clp": total_judicial - total_finiquito,
        },
        "caducidad_art_168_ct": {
            "fecha_vencimiento": caducidad.get("fecha_vencimiento"),
            "estado": caducidad.get("estado"),
            "dias_corridos_restantes": caducidad.get("dias_corridos_restantes"),
        },
        "alertas_juridicas": alertas,
        "citas": citas,
    }


# ---------------------------------------------------------------------------
# 4. Cuantías Legales: Días-Multa (Leyes 21.595 / 20.393) y Alimentos en UTM
# ---------------------------------------------------------------------------

def calcular_cuantias_legales(
    tipo: str,
    utm_valor: Optional[float] = None,
    grado_pena: str = "presidio_menor_minimo",
    ingreso_diario_liquido_clp: Optional[float] = None,
    dias_multa: Optional[int] = None,
    valor_dia_utm: Optional[float] = None,
    ventas_linea_clp: Optional[float] = None,
    ganancias_clp: Optional[float] = None,
    numero_hijos: int = 1,
    imm_clp: Optional[float] = None,
    ingreso_liquido_alimentante_clp: Optional[float] = None,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Calcula días-multa (Leyes 21.595 y 20.393) o pensión mínima/máxima de alimentos en UTM."""
    modo = str(tipo or "").strip().lower()
    if modo not in ("dias_multa_natural", "dias_multa_persona_juridica", "alimentos_utm"):
        return {"error": f"Tipo no soportado: '{tipo}'. Use 'dias_multa_natural', 'dias_multa_persona_juridica' o 'alimentos_utm'."}

    utm_usada = float(utm_valor) if utm_valor is not None else None
    citas_utm: List[Dict[str, str]] = []
    if utm_usada is None:
        ind = obtener_indicadores_sii(cache_dir=cache_dir)
        if ind.get("error"):
            return ind
        utm_info = ind.get("utm_mes")
        if not isinstance(utm_info, dict) or utm_info.get("utm") is None:
            return {"error": "Sin valor UTM publicado en SII; proporcione `utm_valor`.", "sin_fuente_verificable": True}
        utm_usada = float(utm_info["utm"])
        citas_utm = list(ind.get("citas") or [])

    if modo == "dias_multa_natural":
        clave_g = str(grado_pena or "").strip().lower()
        if clave_g not in _GRADOS_DIAS_MULTA_21595:
            return {"error": f"Grado inválido '{grado_pena}'. Opciones: {sorted(_GRADOS_DIAS_MULTA_21595)}."}
        d_min, d_max, desc_g = _GRADOS_DIAS_MULTA_21595[clave_g]
        d_sel = max(1, min(300, int(dias_multa))) if dias_multa is not None else None
        if ingreso_diario_liquido_clp is not None:
            val_dia_utm = float(ingreso_diario_liquido_clp) / utm_usada
            val_dia_utm = max(0.5, min(1000.0, val_dia_utm))
            val_dia_clp = round(val_dia_utm * utm_usada)
        else:
            val_dia_utm = 0.5
            val_dia_clp = round(0.5 * utm_usada)
        res_nat: Dict[str, Any] = {
            "tipo": modo,
            "grado_pena": clave_g,
            "descripcion_grado": desc_g,
            "rango_dias_multa": {"min": d_min, "max": d_max, "tope_concurso_art_74_cp": 300},
            "utm_utilizada": utm_usada,
            "valor_dia_multa": {
                "utm": round(val_dia_utm, 4),
                "clp": val_dia_clp,
                "piso_utm": 0.5,
                "techo_utm": 1000.0,
            },
            "multa_rango_clp": {
                "min": round(d_min * val_dia_clp),
                "max": round(d_max * val_dia_clp),
            },
            "citas": [
                formatear_cita("BCN", "Ley N° 21.595, Art. 27", url="https://www.bcn.cl/leychile/navegar?idLey=21595",
                               texto=f"Conversión de grado a días-multa ({desc_g}: {d_min} a {d_max} días-multa)."),
                formatear_cita("BCN", "Ley N° 21.595, Art. 28", url="https://www.bcn.cl/leychile/navegar?idLey=21595",
                               texto="Valor del día-multa: entre 0,5 UTM y 1.000 UTM según ingreso diario promedio líquido del año previo."),
                *citas_utm,
            ],
        }
        if d_sel is not None:
            res_nat["multa_especifica_clp"] = round(d_sel * val_dia_clp)
            res_nat["dias_multa_evaluados"] = d_sel
        return res_nat

    if modo == "dias_multa_persona_juridica":
        d_min, d_max = 2, 400
        d_sel = max(d_min, min(600, int(dias_multa))) if dias_multa is not None else d_min
        v_utm = max(5.0, min(5000.0, float(valor_dia_utm))) if valor_dia_utm is not None else 5.0
        val_dia_clp = round(v_utm * utm_usada)
        tope_alternativo_clp = max(
            round(0.30 * float(ventas_linea_clp)) if ventas_linea_clp else 0,
            round(2.0 * float(ganancias_clp)) if ganancias_clp else 0,
        )
        return {
            "tipo": modo,
            "rango_dias_multa": {"min": 2, "max": 400, "tope_concurso_art_12": 600},
            "dias_multa_evaluados": d_sel,
            "utm_utilizada": utm_usada,
            "valor_dia_multa": {"utm": round(v_utm, 4), "clp": val_dia_clp, "piso_utm": 5.0, "techo_utm": 5000.0},
            "multa_calculada_clp": round(d_sel * val_dia_clp),
            "multa_rango_legal_clp": {"min": round(d_min * val_dia_clp), "max": round(d_max * val_dia_clp)},
            "tope_especial_comiso_imposible_clp": tope_alternativo_clp or None,
            "citas": [
                formatear_cita("BCN", "Ley N° 20.393, Art. 12", url="https://www.bcn.cl/leychile/navegar?idLey=20393",
                               texto="Multa a la persona jurídica: 2 a 400 días-multa (tope concursal 600), cada día entre 5 y 5.000 UTM."),
                *citas_utm,
            ],
        }

    # modo == "alimentos_utm"
    hijos = max(1, int(numero_hijos))
    if imm_clp is None or float(imm_clp) <= 0:
        return {"error": "Para 'alimentos_utm' debe proporcionar 'imm_clp' (Ingreso Mínimo Mensual vigente en CLP)."}
    imm = float(imm_clp)
    pct_min = 0.40 if hijos == 1 else (0.30 * hijos)
    minimo_clp = round(imm * pct_min)
    minimo_utm = round(minimo_clp / utm_usada, 5)
    tope_clp = round(0.50 * float(ingreso_liquido_alimentante_clp)) if ingreso_liquido_alimentante_clp else None
    tope_utm = round(tope_clp / utm_usada, 5) if tope_clp is not None else None

    return {
        "tipo": modo,
        "numero_hijos": hijos,
        "imm_clp": round(imm),
        "utm_utilizada": utm_usada,
        "regla_minimo": "40 % de un IMM (1 hijo)" if hijos == 1 else f"30 % de un IMM por cada hijo ({hijos} hijos = {round(pct_min * 100)} % IMM)",
        "pension_minima": {"clp": minimo_clp, "utm": minimo_utm},
        "tope_50_por_ciento_rentas": {"clp": tope_clp, "utm": tope_utm} if tope_clp is not None else None,
        "nota_registro_deudores": (
            "Conforme a la Ley N.° 14.908 (modificada por Leyes N.° 21.389 y 21.484), las pensiones se "
            "fijan y reajustan en UTM; el no pago de 3 mensualidades continuas o 5 discontinuas habilita "
            "el ingreso al Registro Nacional de Deudores de Pensiones de Alimentos."
        ),
        "citas": [
            formatear_cita("BCN", "Ley N° 14.908, Art. 3", url="https://www.bcn.cl/leychile/navegar?idLey=14908",
                           texto="Mínimos de pensión alimenticia (40 % IMM para un hijo; 30 % IMM por cada uno con dos o más)."),
            formatear_cita("BCN", "Ley N° 14.908, Art. 7", url="https://www.bcn.cl/leychile/navegar?idLey=14908",
                           texto="El tribunal no podrá fijar una pensión que exceda el 50 % de las rentas del alimentante, salvo razones fundadas."),
            *citas_utm,
        ],
    }
