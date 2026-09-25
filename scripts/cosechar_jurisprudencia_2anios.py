#!/usr/bin/env python3
"""
Open Legal Chile — Cosecha de jurisprudencia de los últimos N años.

Fuentes públicas oficiales:
  · Corte Suprema  → buscador público de juris.pjud.cl (id_buscador 528).
                     Metadatos completos (rol, fecha, sala, recurso, resultado,
                     ministros, carátula). El texto íntegro exige sesión PJUD.
  · Tribunal Constitucional → API de buscador-backend.tcchile.cl.
                     Metadatos + enlace de descarga del PDF oficial.

Uso:
    python scripts/cosechar_jurisprudencia_2anios.py --tribunal cs --desde 2024-09-25
    python scripts/cosechar_jurisprudencia_2anios.py --tribunal tc --desde 2024-09-25
    python scripts/cosechar_jurisprudencia_2anios.py --tribunal ambos
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time

import requests

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "jurisprudencia"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "OpenLegalChile/1.6.5 (Investigacion Juridica Soberana; Universidad de Los Lagos)"}
HDR_HTML = {**UA, "Accept": "text/html,application/xhtml+xml"}

PAUSA = 0.25  # cortesía con los servidores públicos


# ────────────────────────────────────────────────────────────── Corte Suprema

CS_BASE = "https://juris.pjud.cl"
CS_FILTROS = {
    "texto": "", "tipo_norma": "", "codigo_norma": "", "numero_norma": "",
    "numero_articulo": "", "numero_inciso": "", "fec_desde": "", "fec_hasta": "",
    "facetas_seleccionadas": [],
    "palabras": {"todas": "", "algunas": "", "excluir": "", "literal": "", "proximidad": "", "distancia": ""},
    "orden": "fecha_desc", "pagina": 1, "largo_pagina": 50,
}


def cs_sesion() -> tuple[requests.Session, str]:
    s = requests.Session()
    html = s.get(f"{CS_BASE}/busqueda?Corte_Suprema", headers=HDR_HTML, timeout=30).text
    token = re.search(r'name="_token"\s+value="([^"]+)"', html)
    if not token:
        raise RuntimeError("no se pudo obtener el token del buscador de la Corte Suprema")
    return s, token.group(1)


def cs_pagina(s: requests.Session, token: str, offset: int, filas: int = 100) -> list[dict]:
    r = s.post(
        f"{CS_BASE}/busqueda/buscar_sentencias",
        data={
            "_token": token, "id_buscador": "528",
            "filtros": json.dumps(CS_FILTROS, ensure_ascii=False),
            "numero_filas_paginacion": str(filas), "offset_paginacion": str(offset),
            "orden": "fecha_desc", "personalizacion": "",
        },
        headers={**UA, "X-Requested-With": "XMLHttpRequest", "Referer": f"{CS_BASE}/busqueda?Corte_Suprema"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json().get("response", {}).get("docs", [])


def cs_compacto(d: dict) -> dict:
    return {
        "tribunal": "Corte Suprema",
        "sala": (d.get("gls_sala_sup_s") or "").strip(),
        "rol": (d.get("rol_era_sup_s") or "").strip(),
        "era": d.get("era_sup_i"),
        "fecha": (d.get("fec_sentencia_sup_dt") or "")[:10],
        "recurso": (d.get("gls_tip_recurso_sup_s") or "").strip(),
        "resultado": (d.get("resultado_recurso_sup_s") or "").strip(),
        "caratula": (d.get("caratulado_anon_s") or "").strip(),
        "tribunal_origen": (d.get("gls_corte_s") or "").strip(),
        "ministros": (d.get("sent__gls_int_firma_sup_s") or "").strip(),
        "publicacion": (d.get("gls_condicion_publicacion_s") or "").strip(),
        "fallo_anonimizado": (d.get("sent__fallo_anonimizado_s") or "").strip(),
        "reservada": d.get("flg_reserva_i"),
        "documento_id": d.get("sent__crr_documento_i"),
        "id_buscador": 528,
        "link_detalle": f"{CS_BASE}/busqueda?Corte_Suprema",
    }


def cosechar_cs(desde: str, limite_paginas: int = 1500) -> pathlib.Path:
    hoy = dt.date.today().isoformat()
    salida = DATA_DIR / "cs_sentencias_2anios.jsonl"
    print(f"[CS] cosechando de {desde} a {hoy} …")
    s, token = cs_sesion()
    vistos: set[str] = set()
    total = 0
    with open(salida, "w", encoding="utf-8") as f:
        offset = 0
        for pagina in range(limite_paginas):
            docs = cs_pagina(s, token, offset)
            if not docs:
                print(f"[CS] página {pagina + 1}: sin resultados — fin")
                break
            fechas = []
            for d in docs:
                c = cs_compacto(d)
                if not c["fecha"] or c["fecha"] < desde:
                    continue
                clave = c["rol"] or str(d.get("id"))
                if clave in vistos:
                    continue
                vistos.add(clave)
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                total += 1
                fechas.append(c["fecha"])
            f.flush()
            mas_antigua = min(fechas) if fechas else min((x.get("fec_sentencia_sup_dt") or "9999")[:10] for x in docs)
            print(f"[CS] página {pagina + 1:>4} · offset {offset:>6} · +{len(fechas):>3} (total {total:>6}) · más antigua {mas_antigua}")
            if mas_antigua < desde:
                print(f"[CS] se alcanzó {desde} — fin")
                break
            offset += len(docs)
            time.sleep(PAUSA)
    print(f"[CS] listo: {total} sentencias → {salida}")
    return salida


# ─────────────────────────────────────────────────────── Tribunal Constitucional

TC_API = "https://buscador-backend.tcchile.cl/api/buscadorexterno/ficha"
TC_FILTRO = {
    "search": "", "palabra_clave": None, "rol": None, "fecha_sentencia": None,
    "tipo_accion": None, "resultado": None, "competencia": None,
    "articulo_constitucion": None, "ministro": None, "cuerpo_legal": None,
}


def tc_por_dia(dia: str, page: int, sesion: requests.Session) -> dict:
    filtro = dict(TC_FILTRO)
    filtro["fecha_sentencia"] = dia
    params: dict[str, str] = {"filter": json.dumps(filtro, ensure_ascii=False), "page": str(page)}
    r = sesion.get(
        TC_API,
        params=params,
        headers={**UA, "Accept": "application/json"},
        timeout=45,
    )
    r.raise_for_status()
    return r.json()


def tc_compacto(it: dict) -> dict:
    detalles = it.get("detalle", []) or []
    campos: dict[str, str] = {}
    for d in detalles:
        nombre = (d.get("parametro", {}) or {}).get("nombre", "")
        if nombre:
            campos[nombre] = str(d.get("valor", ""))
    doc_id = it.get("id")
    folio, codigo = it.get("folio"), it.get("codigo", "")
    return {
        "tribunal": "Tribunal Constitucional",
        "sala": "Pleno",
        "rol": f"Rol N° {folio}-{codigo}" if folio else "Rol S/N",
        "fecha": (it.get("fecha_sentencia") or "")[:10],
        "tipo": (it.get("template", {}) or {}).get("nombre", ""),
        "caratula": campos.get("Gestión pendiente", "")[:200],
        "precepto": campos.get("Precepto legal", "")[:300],
        "resultado": campos.get("Resultado", ""),
        "ministro": campos.get("Ministro", ""),
        "detalle": campos,
        "link_pdf": f"https://buscador-backend.tcchile.cl/api/extended/{doc_id}/download" if doc_id else "",
    }


def cosechar_tc(desde: str, limite_dias: int = 1200) -> pathlib.Path:
    """La API del TC ordena por ingreso; se consulta día por día con fecha exacta."""
    salida = DATA_DIR / "tc_sentencias_2anios.jsonl"
    fin = dt.date.fromisoformat(desde)
    dia = dt.date.today()
    print(f"[TC] cosechando de {desde} a {dia.isoformat()} (día por día) …")
    s = requests.Session()
    vistos: set[str] = set()
    total = 0
    with open(salida, "w", encoding="utf-8") as f:
        contador_dias = 0
        while dia >= fin and contador_dias < limite_dias:
            page = 1
            while True:
                try:
                    j = tc_por_dia(dia.isoformat(), page, s)
                except Exception:
                    time.sleep(2)
                    try:
                        j = tc_por_dia(dia.isoformat(), page, s)
                    except Exception as e2:
                        print(f"[TC] {dia} página {page}: error {e2} — se salta el día")
                        j = {}
                docs = j.get("data", [])
                if not docs:
                    break
                for it in docs:
                    c = tc_compacto(it)
                    if not c["fecha"] or c["fecha"] < desde or c["rol"] in vistos:
                        continue
                    vistos.add(c["rol"])
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
                    total += 1
                f.flush()
                meta = j.get("meta", {}) or {}
                if page * (meta.get("per_page") or 5) >= (meta.get("total") or 0):
                    break
                page += 1
                time.sleep(PAUSA)
            contador_dias += 1
            if contador_dias % 30 == 0:
                print(f"[TC] … {dia.isoformat()} · van {total} sentencias")
            time.sleep(PAUSA)
            dia -= dt.timedelta(days=1)
    print(f"[TC] listo: {total} sentencias → {salida}")
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description="Cosecha de jurisprudencia de los últimos años (CS y TC).")
    ap.add_argument("--tribunal", choices=("cs", "tc", "ambos"), default="ambos")
    ap.add_argument("--desde", default="2024-09-25", help="fecha de corte (YYYY-MM-DD)")
    ap.add_argument("--limite-paginas", type=int, default=1500)
    args = ap.parse_args()

    if args.tribunal in ("cs", "ambos"):
        cosechar_cs(args.desde, args.limite_paginas)
    if args.tribunal in ("tc", "ambos"):
        cosechar_tc(args.desde)
    return 0


if __name__ == "__main__":
    sys.exit(main())
