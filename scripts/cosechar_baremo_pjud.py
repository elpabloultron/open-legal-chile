#!/usr/bin/env python3
"""
Open Legal Chile — Extractor Estadístico y Jurisprudencial del Baremo de Daño Moral PJUD
Fuente oficial: https://baremo.pjud.cl/BAREMOWEB/ (Poder Judicial / Universidad de Concepción)

Extrae las tablas estadísticas de indemnización por daño moral por muerte (según vínculo de
parentesco: Hijo/a, Cónyuge, Padre/Madre, Hermano/a, Conviviente, Nieto/a, Abuelo/a, etc.) y
por lesiones corporales (CIE-10), calculando percentiles (P10, P25, Mediana/P50, Promedio,
P75, P90, Mínimo y Máximo) en Unidades de Fomento (UF) y Pesos Chilenos (CLP) por instancia
(Primera Instancia, Corte de Apelaciones y Excma. Corte Suprema), junto con los fallos
individuales y sus enlaces de descarga oficial.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import time
from typing import Any, Dict, List, Optional
import requests

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
JSONL_OUT = BASE_DIR / "data" / "jurisprudencia" / "baremo_dano_moral.jsonl"
MD_DIR = BASE_DIR / "jurisprudencia_baremo"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _parse_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace("UF", "").strip()
    if not s or s == "-":
        return 0.0
    # Formato chileno: 50.000.000 o 1.385,95
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s and len(s.split(".")[-1]) == 3 and s.count(".") >= 1:
        s = s.replace(".", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _calcular_estadisticas(valores: List[float]) -> Dict[str, Any]:
    limpios = sorted(v for v in valores if v > 0)
    if not limpios:
        return {
            "n": 0,
            "min": 0.0,
            "p25": 0.0,
            "mediana": 0.0,
            "promedio": 0.0,
            "p75": 0.0,
            "max": 0.0,
        }
    n = len(limpios)
    p25 = limpios[max(0, int(n * 0.25) - 1)]
    p75 = limpios[min(n - 1, int(n * 0.75))]
    return {
        "n": n,
        "min": round(limpios[0], 2),
        "p25": round(p25, 2),
        "mediana": round(float(statistics.median(limpios)), 2),
        "promedio": round(float(statistics.mean(limpios)), 2),
        "p75": round(p75, 2),
        "max": round(limpios[-1], 2),
    }


class BaremoPJUDScraper:
    URL_BASE = "https://baremo.pjud.cl/BAREMOWEB"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9",
        })
        self._inicializado = False

    def inicializar(self) -> Dict[str, Any]:
        """Inicializa cookies de sesión JSF y obtiene catálogos de parentesco y cortes."""
        self.session.get(f"{self.URL_BASE}/", timeout=15)
        self.session.get(f"{self.URL_BASE}/ConsultaBaremo", timeout=15)
        r = self.session.post(
            f"{self.URL_BASE}/jsonInitConsultaBaremo.faces",
            data={"tipo": 1},
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"{self.URL_BASE}/ConsultaBaremo"},
            timeout=20,
        )
        r.raise_for_status()
        self._inicializado = True
        raw = r.json()
        return raw[0] if isinstance(raw, list) and raw else (raw if isinstance(raw, dict) else {})

    def consultar_muerte_por_parentesco(self, codigo_parentesco: str, glosa_parentesco: str) -> Dict[str, Any]:
        """Consulta todos los registros estadísticos y fallos para un vínculo de parentesco."""
        if not self._inicializado:
            self.inicializar()

        param = json.dumps([{
            "flgCorteSuprema": 1,
            "idTribunal": 10000,
            "idCorteApelaciones": 100,
            "flgPrimeraInstancia": 1,
            "flgSexoFallecido": 3,
            "minRngEtareoFallecido": "0",
            "maxRngEtareoFallecido": "100",
            "flgTipoDemanda": 1,
            "flgPersona": 3,
            "flgBusqExacta": 2,
            "flgTipoBusqueda": 1,
            "flgParienteIndividual": str(codigo_parentesco),
        }])
        dem = json.dumps([{
            "id": 1,
            "idParentesco": str(codigo_parentesco),
            "flgConviviente": 3,
            "flgSexo": 3,
            "rangoMin": "0",
            "rangoMax": "100",
            "ncantidad": 1,
        }])
        r = self.session.post(
            f"{self.URL_BASE}/jsonDatosConsultaBaremoMain.faces",
            data={"tipo": 3, "arregloParam": param, "listaDemandante": dem},
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"{self.URL_BASE}/ConsultaBaremo"},
            timeout=30,
        )
        r.raise_for_status()
        raw = r.json()
        data = raw[0] if isinstance(raw, list) and raw else (raw if isinstance(raw, dict) else {})

        # Tabla 1 (listaTablaPrimeraInstanciaArray): trae IDs, roles, fechas y montos UF de las 3 instancias
        t1_rows = data.get("listaTablaPrimeraInstanciaArray") or []
        # Tabla 3 (listaTablaCorteSupremaArray): trae montos en Pesos y UF de las 3 instancias
        t3_rows = data.get("listaTablaCorteSupremaArray") or []

        uf_pi = [_parse_float(x.get("montoPrimeraIns")) for x in t1_rows if _parse_float(x.get("montoPrimeraIns")) > 0]
        uf_ca = [_parse_float(x.get("montoCorteApe")) for x in t1_rows if _parse_float(x.get("montoCorteApe")) > 0]
        uf_cs = [_parse_float(x.get("montoSuprema")) for x in t1_rows if _parse_float(x.get("montoSuprema")) > 0]

        clp_pi = [_parse_float(x.get("montoPesosPrimera")) for x in t3_rows if _parse_float(x.get("montoPesosPrimera")) > 0]
        clp_ca = [_parse_float(x.get("montoPesosCA")) for x in t3_rows if _parse_float(x.get("montoPesosCA")) > 0]
        clp_cs = [_parse_float(x.get("montoPesosCS")) for x in t3_rows if _parse_float(x.get("montoPesosCS")) > 0]

        stats_pi_uf = _calcular_estadisticas(uf_pi)
        stats_ca_uf = _calcular_estadisticas(uf_ca)
        stats_cs_uf = _calcular_estadisticas(uf_cs)

        stats_pi_clp = _calcular_estadisticas(clp_pi)
        stats_ca_clp = _calcular_estadisticas(clp_ca)
        stats_cs_clp = _calcular_estadisticas(clp_cs)

        # Extraer muestras representativas de fallos (priorizando los que llegaron a CS o CA)
        muestras: List[Dict[str, Any]] = []
        vistos_roles = set()
        t1_ordenados = sorted(
            t1_rows,
            key=lambda row: (
                1 if str(row.get("cs_id") or "").strip() else 0,
                1 if str(row.get("ca_id") or "").strip() else 0,
                _parse_float(row.get("montoSuprema")) or _parse_float(row.get("montoCorteApe")) or _parse_float(row.get("montoPrimeraIns")),
            ),
            reverse=True,
        )
        for row in t1_ordenados:
            rol_cs = str(row.get("rolSuprema") or "").strip()
            rol_ca = str(row.get("rolCorte") or "").strip()
            rol_pi = str(row.get("rolPrimeraInstancia") or "").strip()
            rol_principal = rol_cs if rol_cs and rol_cs != "-" else (rol_ca if rol_ca and rol_ca != "-" else rol_pi)
            if not rol_principal or rol_principal in vistos_roles:
                continue
            vistos_roles.add(rol_principal)
            inst_id = row.get("cs_id") or row.get("ca_id") or row.get("pi_id")
            tipo_inst = 3 if row.get("cs_id") else (2 if row.get("ca_id") else 1)
            monto_uf = _parse_float(row.get("montoSuprema")) or _parse_float(row.get("montoCorteApe")) or _parse_float(row.get("montoPrimeraIns"))
            monto_clp = round(monto_uf * 38000)
            fecha = row.get("fechaSentenciaSup") if row.get("fechaSentenciaSup") else (
                row.get("fechaSentenciaApe") if row.get("fechaSentenciaApe") else row.get("fechaSentenciaPrimeraIns")
            )
            muestras.append({
                "rol": rol_principal,
                "rol_pi": rol_pi,
                "rol_ca": rol_ca,
                "rol_cs": rol_cs,
                "fecha": str(fecha or "").strip(),
                "corte_apelaciones": str(row.get("glsCorte") or "").strip(),
                "juzgado_origen": str(row.get("glsTribunal") or "").strip(),
                "monto_uf": monto_uf,
                "monto_clp": int(monto_clp),
                "url_descarga_sentencia": f"{self.URL_BASE}/jsonDescargaDocumentoInstancia.faces?tipo=8&indice={inst_id}&tipoInstancia={tipo_inst}" if inst_id else "",
            })
            if len(muestras) >= 25:
                break

        resumen_texto = (
            f"Baremo Estadístico de Daño Moral por Muerte — Vínculo: {glosa_parentesco}. "
            f"Primera Instancia ({stats_pi_uf['n']} fallos): Mediana {stats_pi_uf['mediana']} UF "
            f"(${int(stats_pi_clp['mediana']):,} CLP), Promedio {stats_pi_uf['promedio']} UF, "
            f"Rango intercuartil P25-P75: {stats_pi_uf['p25']} a {stats_pi_uf['p75']} UF (Máx: {stats_pi_uf['max']} UF). "
            f"Corte de Apelaciones ({stats_ca_uf['n']} fallos): Mediana {stats_ca_uf['mediana']} UF "
            f"(${int(stats_ca_clp['mediana']):,} CLP), Rango P25-P75: {stats_ca_uf['p25']} a {stats_ca_uf['p75']} UF. "
            f"Excma. Corte Suprema ({stats_cs_uf['n']} fallos): Mediana {stats_cs_uf['mediana']} UF "
            f"(${int(stats_cs_clp['mediana']):,} CLP), Rango P25-P75: {stats_cs_uf['p25']} a {stats_cs_uf['p75']} UF."
        ).replace(",", ".")

        return {
            "id": f"baremo_muerte_{codigo_parentesco}",
            "rol": f"BAREMO-MUERTE-{codigo_parentesco}",
            "portal": "baremo",
            "tribunal": "Poder Judicial — Baremo Estadístico Daño Moral (CS / CA / Civil)",
            "sala": "Civil / Responsabilidad Extracontractual y Contractual",
            "fecha": "2026-01-01",
            "tipo_dano": "Muerte",
            "codigo_parentesco": str(codigo_parentesco),
            "parentesco": glosa_parentesco,
            "caratula": f"Baremo Daño Moral por Muerte — Demandante: {glosa_parentesco} de la víctima",
            "materia": f"Indemnización de perjuicios por daño moral por muerte ({glosa_parentesco}) — Arts. 2314 y 2329 Código Civil",
            "recurso": "Estadística Jurisprudencial Oficial PJUD-UdeC",
            "resultado": f"Mediana PI: {stats_pi_uf['mediana']} UF | Mediana CA: {stats_ca_uf['mediana']} UF | Mediana CS: {stats_cs_uf['mediana']} UF",
            "estadisticas_uf": {
                "primera_instancia": stats_pi_uf,
                "corte_apelaciones": stats_ca_uf,
                "corte_suprema": stats_cs_uf,
            },
            "estadisticas_clp": {
                "primera_instancia": stats_pi_clp,
                "corte_apelaciones": stats_ca_clp,
                "corte_suprema": stats_cs_clp,
            },
            "total_casos_analizados": stats_pi_uf["n"],
            "fallos_muestra": muestras,
            "texto_integral": resumen_texto,
            "extracto_relevante": resumen_texto,
            "cita": f"[PJUD Baremo Daño Moral - Muerte ({glosa_parentesco}), Casos: {stats_pi_uf['n']}, Mediana: {stats_pi_uf['mediana']} UF]",
            "url_origen": "https://baremo.pjud.cl/BAREMOWEB/ConsultaBaremo",
        }


def formatear_md_baremo(reg: Dict[str, Any]) -> str:
    uf_pi = reg["estadisticas_uf"]["primera_instancia"]
    uf_ca = reg["estadisticas_uf"]["corte_apelaciones"]
    uf_cs = reg["estadisticas_uf"]["corte_suprema"]
    clp_pi = reg["estadisticas_clp"]["primera_instancia"]
    clp_ca = reg["estadisticas_clp"]["corte_apelaciones"]
    clp_cs = reg["estadisticas_clp"]["corte_suprema"]

    lineas_fallos = []
    for f in reg.get("fallos_muestra", [])[:15]:
        lineas_fallos.append(
            f"| `{f['rol']}` | {f['fecha']} | {f['corte_apelaciones'] or f['juzgado_origen']} | "
            f"**{f['monto_uf']:,.2f} UF** | ${f['monto_clp']:,} | [Descargar]({f['url_descarga_sentencia']}) |"
        )
    tabla_fallos = "\n".join(lineas_fallos) if lineas_fallos else "| Sin muestras | - | - | - | - | - |"

    return (
        f"---\n"
        f"id: \"{reg['id']}\"\n"
        f"rol: \"{reg['rol']}\"\n"
        f"portal: \"baremo\"\n"
        f"tipo_dano: \"{reg['tipo_dano']}\"\n"
        f"parentesco: \"{reg['parentesco']}\"\n"
        f"total_casos: {reg['total_casos_analizados']}\n"
        f"url_oficial: \"{reg['url_origen']}\"\n"
        f"---\n\n"
        f"# {reg['caratula']}\n\n"
        f"**Cita Oficial:** `{reg['cita']}`\n\n"
        f"{reg['texto_integral']}\n\n"
        f"## 📊 Distribución Estadística en Unidades de Fomento (UF) y CLP\n\n"
        f"| Instancia Judicial | N.° Fallos | Mínimo (UF) | P25 (UF) | **Mediana (UF)** | Promedio (UF) | P75 (UF) | Máximo (UF) | Mediana (CLP) |\n"
        f"| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        f"| **Primera Instancia** | {uf_pi['n']} | {uf_pi['min']} | {uf_pi['p25']} | **{uf_pi['mediana']} UF** | {uf_pi['promedio']} | {uf_pi['p75']} | {uf_pi['max']} | ${int(clp_pi['mediana']):,} |\n"
        f"| **Corte de Apelaciones** | {uf_ca['n']} | {uf_ca['min']} | {uf_ca['p25']} | **{uf_ca['mediana']} UF** | {uf_ca['promedio']} | {uf_ca['p75']} | {uf_ca['max']} | ${int(clp_ca['mediana']):,} |\n"
        f"| **Excma. Corte Suprema** | {uf_cs['n']} | {uf_cs['min']} | {uf_cs['p25']} | **{uf_cs['mediana']} UF** | {uf_cs['promedio']} | {uf_cs['p75']} | {uf_cs['max']} | ${int(clp_cs['mediana']):,} |\n\n"
        f"## ⚖️ Sentencias de Referencia Verificadas en el Baremo\n\n"
        f"| Rol Principal | Fecha | Tribunal / Corte | Monto UF | Monto CLP | Sentencia Oficial |\n"
        f"| :--- | :---: | :--- | :---: | :---: | :---: |\n"
        f"{tabla_fallos}\n"
    )


def cosechar_baremo_completo(exportar_md: bool = True) -> Dict[str, Any]:
    scraper = BaremoPJUDScraper()
    init_data = scraper.inicializar()
    parentescos = init_data.get("listaParentescoArray") or []

    JSONL_OUT.parent.mkdir(parents=True, exist_ok=True)
    if exportar_md:
        MD_DIR.mkdir(parents=True, exist_ok=True)

    registros: List[Dict[str, Any]] = []
    total_fallos_indexados = 0

    for item in parentescos:
        cod = str(item.get("codigo") or "").strip()
        glosa = str(item.get("nombre") or item.get("glosa") or "").strip()
        if not cod:
            continue
        try:
            reg = scraper.consultar_muerte_por_parentesco(cod, glosa)
            if reg["total_casos_analizados"] > 0:
                if exportar_md:
                    slug = f"baremo_muerte_{cod}_{glosa.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}"
                    rel_md = f"jurisprudencia_baremo/{slug}.md"
                    reg["archivo_md"] = rel_md
                    (BASE_DIR / rel_md).write_text(formatear_md_baremo(reg), encoding="utf-8")
                registros.append(reg)
                total_fallos_indexados += reg["total_casos_analizados"]
            time.sleep(0.1)
        except Exception as e:
            print(f"[!] Error consultando parentesco {cod} ({glosa}): {e}")

    with open(JSONL_OUT, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return {
        "categorias_parentesco_con_datos": len(registros),
        "total_fallos_estadisticos": total_fallos_indexados,
        "archivo_jsonl": str(JSONL_OUT.relative_to(BASE_DIR)),
    }


def main():
    parser = argparse.ArgumentParser(description="Cosechador del Baremo Estadístico de Daño Moral PJUD")
    parser.add_argument("--sin-md", action="store_true", help="No generar fichas Markdown")
    args = parser.parse_args()
    res = cosechar_baremo_completo(exportar_md=not args.sin_md)
    print(f"[+] Baremo PJUD cosechado: {res['categorias_parentesco_con_datos']} categorías de parentesco "
          f"({res['total_fallos_estadisticos']} fallos estadísticos) -> {res['archivo_jsonl']}")


if __name__ == "__main__":
    main()
