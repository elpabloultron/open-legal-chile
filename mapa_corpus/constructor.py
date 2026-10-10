"""Construcción del mapa: completa o incremental (solo altas, modificaciones y bajas).

Flujo (`python -m mapa_corpus`):
  estado    → sha de main, base publicada, delta y `plan.json`.
  construir → descarga solo lo necesario (fijado al sha del plan), extrae, recalcula entidades y
              la capa del grafo, y escribe las particiones en `<trabajo>/mapa/`.
  validar   → integridad y consultas de humo antes de publicar.

Invariante: con el mismo (sha fuente, grafo curado, versión de reglas) la construcción
incremental y la completa producen exactamente los mismos bytes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from citas_legales import etiqueta_norma
from mapa_corpus import ESQUEMA, REPO_ID, RUTA_HF, extractores, grafo, ids, particiones
from mapa_corpus.inventario import Archivo, Descargador, delta, huella

log = logging.getLogger("mapa_corpus")

VERSION_CONSTRUCTOR = "1.0.0"
INDICE_CS = "data/jurisprudencia/cs_sentencias_2anios.jsonl"
# Límite de tamaño por archivo a bajar; las excepciones se bajan siempre.
MAX_BYTES = 20 * 1024 * 1024
EXCEPCIONES_TAMANO = {INDICE_CS}
TANDA = 64  # fuentes descargadas y extraídas por vuelta (memoria acotada)


def version_reglas() -> str:
    """Hash del código que decide el contenido de las filas: si cambia, se reconstruye todo."""
    h = hashlib.sha256()
    base = Path(__file__).resolve().parent
    # Todo lo que decide el contenido: extracción, IDs, entidades/colisiones y serialización.
    for nombre in ("extractores.py", "ids.py", "texto.py", "grafo.py", "constructor.py", "particiones.py"):
        h.update((base / nombre).read_bytes())
    h.update((base.parent / "citas_legales.py").read_bytes())
    h.update(f"{VERSION_CONSTRUCTOR}|{extractores.VERSION_EXTRACTORES}|{ESQUEMA}".encode())
    return h.hexdigest()[:16]


# ── Entidades ─────────────────────────────────────────────────────────────────────────────
def _mas_frecuente(c: Counter) -> str:
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else ""


def entidades(filas: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    normas: Dict[str, Counter] = defaultdict(Counter)
    autores: Dict[str, Dict[str, Any]] = {}
    revistas: Dict[str, Dict[str, Any]] = {}
    ministros: Dict[str, Dict[str, Any]] = {}
    salas: Counter = Counter()
    tribunales: Dict[str, Counter] = defaultdict(Counter)
    recursos: Dict[str, Counter] = defaultdict(Counter)
    for f in filas:
        col = f.get("col", "")
        for norma, n in f.get("normas", []):
            normas[norma][col] += int(n)
        if col == "doc":
            for txt in f.get("autores_txt", []):
                aid = ids.autor_id(txt)
                if not aid:
                    continue
                a = autores.setdefault(aid, {"nombres": Counter(), "docs": 0, "revistas": Counter()})
                a["nombres"][txt] += 1
                a["docs"] += 1
                if f.get("revista"):
                    a["revistas"][f["revista"]] += 1
            if f.get("revista"):
                r = revistas.setdefault(f["revista"], {"nombres": Counter(), "docs": 0, "anios": []})
                if f.get("revista_txt"):
                    r["nombres"][f["revista_txt"]] += 1
                r["docs"] += 1
                if f.get("anio"):
                    r["anios"].append(int(f["anio"]))
        if col in ("cs", "ta"):
            nombres = f.get("ministros_txt", []) if col == "cs" else []
            for txt in nombres:
                mid = ids.ministro_id(txt)
                if mid:
                    m = ministros.setdefault(mid, {"nombres": Counter(), "cs": 0, "ta": 0})
                    m["nombres"][" ".join(txt.split())] += 1
            for mid in f.get("ministros", []) + ([f["redactor"]] if f.get("redactor") else []):
                m = ministros.setdefault(mid, {"nombres": Counter(), "cs": 0, "ta": 0})
                m[col] += 1
        if col == "cs":
            if f.get("sala"):
                salas[f["sala"]] += 1
            if f.get("origen"):
                tribunales[f["origen"]][f.get("origen_txt", "")] += 1
            if f.get("recurso"):
                recursos[f["recurso"]][f.get("recurso_txt", "")] += 1
    salida: Dict[str, List[Dict[str, Any]]] = {
        "normas": [{"id": k, "tipo": "norma", "label": etiqueta_norma(k), "citas": dict(sorted(v.items()))}
                   for k, v in normas.items()],
        "autores": [{"id": k, "tipo": "autor", "label": _mas_frecuente(v["nombres"]), "docs": v["docs"],
                     "revistas": sorted(v["revistas"])} for k, v in autores.items()],
        "revistas": [{"id": k, "tipo": "revista", "label": _mas_frecuente(v["nombres"]) or k[8:].upper(),
                      "docs": v["docs"], "desde": min(v["anios"]) if v["anios"] else None,
                      "hasta": max(v["anios"]) if v["anios"] else None} for k, v in revistas.items()],
        "ministros": [{"id": k, "tipo": "ministro",
                       "label": _mas_frecuente(v["nombres"]) or k[9:].replace("-", " ").title(),
                       "fallos_cs": v["cs"], "sentencias_ta": v["ta"]} for k, v in ministros.items()],
        "salas": [{"id": k, "tipo": "sala", "label": k[5:].replace("cs-", "Corte Suprema, sala ").title(),
                   "fallos_cs": v} for k, v in salas.items()],
        "tribunales": [{"id": k, "tipo": "tribunal", "label": _mas_frecuente(v), "fallos_cs": sum(v.values())}
                       for k, v in tribunales.items()],
        "recursos": [{"id": k, "tipo": "recurso", "label": _mas_frecuente(v), "fallos_cs": sum(v.values())}
                     for k, v in recursos.items()],
    }
    for lista in salida.values():
        for e in lista:
            for k in [k for k, v in e.items() if v in (None, "", [], {})]:
                del e[k]
        lista.sort(key=lambda e: e["id"])
    return salida


# ── Colisiones de IDs ─────────────────────────────────────────────────────────────────────
def resolver_colisiones(filas: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Dos archivos con el mismo ID: gana el principal (no síntesis) y, a igualdad, la ruta menor;
    los demás reciben el sufijo del nombre de archivo y guardan su `id_base`.

    Se resuelve siempre desde los IDs base: en un delta, una fila que heredó un sufijo de la corrida
    anterior vuelve a competir por su ID (si el archivo que lo tenía desapareció, lo recupera), igual
    que en una reconstrucción completa."""
    grupos: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in filas:
        if f.get("id_base"):
            f = dict(f)
            f["id"] = f.pop("id_base")
            marcas = [c for c in f.get("calidad", []) if c != "id_compartido"]
            if marcas:
                f["calidad"] = marcas
            else:
                f.pop("calidad", None)
        grupos[f["id"]].append(f)
    salida: List[Dict[str, Any]] = []
    colisiones = 0
    usados = set(grupos)
    for _, grupo in sorted(grupos.items()):
        grupo.sort(key=lambda f: (f.get("tipo") == "sintesis", f.get("ruta", "")))
        salida.append(grupo[0])
        for f in grupo[1:]:
            colisiones += 1
            f = dict(f)
            ruta = f.get("ruta", "")
            sufijo = "sintesis" if f.get("tipo") == "sintesis" else ids.slug(ruta.rsplit("/", 1)[-1][:-3])
            # El mismo rol en dos meses (…/03/1-2024.md y …/05/1-2024.md) o dos síntesis de una
            # causa darían el mismo sufijo: entonces va la ruta entera y, en último caso, un número.
            nuevo = f"{f['id']}:{sufijo}"
            if nuevo in usados:
                nuevo = f"{f['id']}:{ids.slug(ruta.rsplit('.', 1)[0])}"
            candidato, n = nuevo, 2
            while candidato in usados:
                candidato, n = f"{nuevo}-{n}", n + 1
            usados.add(candidato)
            f["id_base"] = f["id"]
            f["id"] = candidato
            f["calidad"] = sorted(set(f.get("calidad", [])) | {"id_compartido"})
            salida.append(f)
    return salida, colisiones


# ── Construcción ──────────────────────────────────────────────────────────────────────────
# Contadores que salen de leer el índice de la CS (no de una fila): pasan de corrida en corrida.
_CALIDAD_INDICE_CS = frozenset({"cs_linea_invalida", "cs_indice_sin_ficha_md"})


def _marcar(fila: Dict[str, Any], marca: str) -> Dict[str, Any]:
    """La fila con una marca de calidad más (se cuenta como `fila:<marca>` en el estado)."""
    return {**fila, "calidad": sorted(set(fila.get("calidad", [])) | {marca})}


def _filas_cs(indice: bytes, inv: Dict[str, Archivo]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    from pjud_connector import ruta_hf_corte_suprema
    filas: List[Dict[str, Any]] = []
    calidad: Counter = Counter()
    for linea in indice.decode("utf-8").splitlines():
        if not linea.strip():
            continue
        try:
            registro = json.loads(linea)
        except ValueError:
            calidad["cs_linea_invalida"] += 1
            continue
        ruta = ruta_hf_corte_suprema(registro)
        a = inv.get(ruta or "")
        if a is None:
            calidad["cs_indice_sin_ficha_md"] += 1
            continue
        fila = extractores.fila_cs(registro, a.ruta, a.blob, a.bytes)
        if fila:
            filas.append(fila)
    return filas, dict(calidad)


def construir(inv: Dict[str, Archivo], sha: str, descargador: Descargador, curado_ruta: str,
              base: Optional[Dict[str, Any]] = None, avisar: Callable[[str], None] = log.info) -> Dict[str, Any]:
    """Arma el mapa completo en memoria. `base` = {"estado": …, "filas": [...]} del mapa anterior
    (si está y sus reglas coinciden, solo se procesa el delta).

    Devuelve {"particiones": {nombre: [filas]}, "estado": {...}, "reporte": {...}}.
    """
    reglas = version_reglas()
    usar_base = base is not None and base["estado"].get("version_reglas") == reglas
    previas: Dict[str, Dict[str, Any]] = {}
    if usar_base and base:
        previas = {f["ruta"]: f for f in base["filas"] if f.get("ruta")}
    prev_blobs = {r: str(f.get("blob", "")) for r, f in previas.items()}
    altas, mods, bajas = delta(prev_blobs, inv) if usar_base else (sorted(inv), [], [])
    a_procesar = set(altas) | set(mods)
    avisar(f"delta: +{len(altas)} ~{len(mods)} -{len(bajas)} (base {'sí' if usar_base else 'no'})")

    filas: Dict[str, Dict[str, Any]] = {r: f for r, f in previas.items() if r in inv and r not in a_procesar}
    # La calidad se cuenta sobre las filas finales (marcas `calidad` de cada fila), no sobre lo
    # procesado en esta corrida: así un delta y una reconstrucción completa dan el mismo estado.
    calidad: Counter = Counter()

    # CS: siempre desde su índice cuando algo de la CS (o el índice, también si desapareció) cambió.
    cs_tocada = any(r.startswith("jurisprudencia_cs/") for r in a_procesar | set(bajas)) or \
        INDICE_CS in a_procesar or INDICE_CS in bajas
    if cs_tocada:
        for r in [r for r in filas if r.startswith("jurisprudencia_cs/") and r.split("/")[1].isdigit()]:
            del filas[r]
    if cs_tocada and INDICE_CS in inv:
        avisar("CS: leyendo el índice cs_sentencias_2anios.jsonl")
        cs_filas, cs_calidad = _filas_cs(descargador.obtener(inv[INDICE_CS]), inv)
        calidad.update(cs_calidad)
        for f in cs_filas:
            filas[f["ruta"]] = f
    elif usar_base and base and INDICE_CS in inv:
        # El índice no se releyó: sus contadores son los de la corrida que lo leyó.
        calidad.update({k: v for k, v in base["estado"].get("calidad", {}).items() if k in _CALIDAD_INDICE_CS})
    # Fichas CS sin fila en el índice: se leen del .md.
    faltan_cs = {r for r in inv if r.startswith("jurisprudencia_cs/") and r.split("/")[1].isdigit()
                 and r not in filas}
    a_bajar: List[Archivo] = []
    for r in sorted(set(a_procesar) | faltan_cs):
        if r in filas:
            continue
        a = inv[r]
        solo = extractores.solo_inventario(r)
        if solo:
            filas[r] = extractores.fila_archivo(solo[0], solo[1], r, a.blob, a.bytes)
        elif a.bytes > MAX_BYTES and r not in EXCEPCIONES_TAMANO:
            filas[r] = _marcar(extractores.fila_archivo("arch", "arch", r, a.blob, a.bytes), "omitido_por_tamano")
        else:
            a_bajar.append(a)
    avisar(f"descargando {len(a_bajar)} archivos (fijados a {sha[:8]})")
    # Por tandas: cada fuente se extrae apenas llega y sus bytes se sueltan. Bajar todo primero
    # retenía en memoria los ~650 MB del corpus (RSS de 1,2 GB en la construcción completa).
    for inicio in range(0, len(a_bajar), TANDA):
        tanda = a_bajar[inicio:inicio + TANDA]
        datos = descargador.obtener_varios(tanda)
        for a in tanda:
            try:
                fila = extractores.extraer(a.ruta, datos.pop(a.ruta), a.blob)
            except Exception as exc:  # noqa: BLE001 — un archivo raro no tumba el mapa: queda anotado
                log.warning("no se pudo extraer %s: %s", a.ruta, exc)
                fila = _marcar(extractores.fila_archivo("arch", "arch", a.ruta, a.blob, a.bytes), "error_extraccion")
            fila = fila or extractores.fila_archivo("arch", "arch", a.ruta, a.blob, a.bytes)
            filas[a.ruta] = _marcar(fila, "cs_fuera_del_indice") if a.ruta in faltan_cs else fila
        hechos = inicio + len(tanda)
        if hechos % (TANDA * 4) == 0 or hechos == len(a_bajar):
            avisar(f"  {hechos}/{len(a_bajar)}")

    # En memoria, igual que en disco (NFC): si no, un nombre con tildes descompuestas contaría como
    # otro en las entidades de una construcción completa y no en las de un delta (que lee de disco).
    lista, colisiones = resolver_colisiones([particiones.nfc(f) for f in filas.values()])
    calidad["ids_compartidos"] += colisiones
    for f in lista:
        for marca in f.get("calidad", []):
            calidad[f"fila:{marca}"] += 1

    avisar("entidades y capa del grafo")
    ents = entidades(lista)
    curado = grafo.cargar_curado(curado_ruta)
    capa = grafo.construir_capa(lista, ents, grafo.vias_de(curado))
    alias, puentes = grafo.alias_curados(curado, capa, lista)
    comunidad = grafo.comunidades(curado, capa, alias, puentes)

    partes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in lista:
        partes[particiones.particion_de(f["ruta"])].append(f)
    for nombre, filas_ent in ents.items():
        partes[f"entidades/{nombre}"] = filas_ent
    partes.update(grafo.exportar(capa, alias, puentes, comunidad))

    conteos = Counter(f.get("col", "") for f in lista)
    estado = {
        "esquema": ESQUEMA,
        "repo": REPO_ID,
        "ruta": RUTA_HF,
        "sha_fuente": sha,
        "huella_fuente": huella(inv.values(), reglas),
        "version_reglas": reglas,
        "constructor": VERSION_CONSTRUCTOR,
        "curado": {"sha256": hashlib.sha256(Path(curado_ruta).read_bytes()).hexdigest()},
        "conteos": dict(sorted({**{f"col_{k}": v for k, v in conteos.items() if k},
                                "entradas": len(lista), "nodos": len(capa.nodos),
                                "aristas": len(capa.aristas) + len(puentes), "alias": len(alias),
                                "comunidades": len(set(comunidad.values()))}.items())),
        "calidad": dict(sorted(calidad.items())),
        "excluidos": ["data/mapa/**", ".gitattributes", "jurisprudencia_tc/testrol*"],
    }
    reporte = {"altas": len(altas), "modificados": len(mods), "bajas": len(bajas),
               "descargados": len(a_bajar), "tipos_nodo": grafo.resumen_tipos(capa)}
    return {"particiones": dict(partes), "estado": estado, "reporte": reporte}


def escribir(resultado: Dict[str, Any], destino: str, estado_previo: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Escribe las particiones en `<destino>/` y completa `estado.archivos`.

    Para los archivos cuyo contenido no cambió se conservan `sha256_gz` y `bytes` del estado
    anterior (lo publicado), así otra versión de zlib no hace parecer distinto lo que es igual.
    """
    base = Path(destino)
    previos = particiones.archivos_de(estado_previo or {})
    archivos: Dict[str, Dict[str, Any]] = {}
    for nombre in sorted(resultado["particiones"]):
        filas = resultado["particiones"][nombre]
        crudo = particiones.serializar(filas)
        rel = nombre + particiones.EXTENSION
        sha_c = particiones.sha256(crudo)
        ruta = base / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        anterior = previos.get(rel)
        if anterior and anterior.get("sha256_contenido") == sha_c and ruta.exists():
            archivos[rel] = dict(anterior)
            continue
        gz = particiones.comprimir(crudo)
        tmp = ruta.with_suffix(".tmp")
        tmp.write_bytes(gz)
        os.replace(tmp, ruta)
        archivos[rel] = {"filas": len(filas), "sha256_contenido": sha_c,
                         "sha256_gz": particiones.sha256(gz), "bytes": len(gz)}
        if anterior and anterior.get("sha256_contenido") == sha_c:
            archivos[rel].update({"sha256_gz": anterior["sha256_gz"], "bytes": anterior["bytes"]})
    for viejo in previos:
        if viejo not in archivos and (base / viejo).exists():
            (base / viejo).unlink()
    estado = dict(resultado["estado"])
    estado["archivos"] = archivos
    texto = json.dumps(estado, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    (base / "estado.json").write_bytes(texto.encode("utf-8"))
    return estado


def leer_mapa(dir_mapa: str) -> Dict[str, Any]:
    """{"estado", "filas"} de un mapa en disco (para usarlo como base o validarlo)."""
    base = Path(dir_mapa)
    estado = json.loads((base / "estado.json").read_text(encoding="utf-8"))
    filas: List[Dict[str, Any]] = []
    for rel in sorted(particiones.archivos_de(estado)):
        if rel.startswith("entradas/"):
            filas.extend(particiones.leer((base / rel).read_bytes()))
    return {"estado": estado, "filas": filas}


# ── Validación ────────────────────────────────────────────────────────────────────────────
_RE_ID = re.compile(r"^(?:cs|tc|ta|doc|guia|bib|pub|dato|graphify|arch|csidx|taidx):\S+$")


def _sha_contenido(datos_gz: bytes) -> str:
    try:
        return particiones.sha256(particiones.descomprimir(datos_gz))
    except (OSError, EOFError, zlib.error):
        return ""


def validar(dir_mapa: str, inv: Optional[Dict[str, Archivo]] = None,
            base: Optional[Dict[str, Any]] = None) -> List[str]:
    """Lista de problemas (vacía = válido)."""
    problemas: List[str] = []
    raiz = Path(dir_mapa)
    estado = json.loads((raiz / "estado.json").read_text(encoding="utf-8"))
    filas_por_parte: Dict[str, List[Dict[str, Any]]] = {}
    try:
        archivos = particiones.archivos_de(estado)
    except ValueError as exc:
        return [str(exc)]
    for rel, meta in archivos.items():
        datos = (raiz / rel).read_bytes()
        if particiones.sha256(datos) != meta["sha256_gz"] and _sha_contenido(datos) != meta.get("sha256_contenido"):
            # Un archivo sin cambios recomprimido aquí (otro zlib) conserva el sha256_gz de lo
            # publicado: vale si su contenido es el mismo.
            problemas.append(f"sha256_gz no calza: {rel}")
            continue
        filas = particiones.leer(datos)
        if len(filas) != meta["filas"]:
            problemas.append(f"filas no calzan en {rel}: {len(filas)} != {meta['filas']}")
        filas_por_parte[rel] = filas
    entradas = [f for rel, fs in filas_por_parte.items() if rel.startswith("entradas/") for f in fs]
    ids_entradas = [f["id"] for f in entradas]
    if len(ids_entradas) != len(set(ids_entradas)):
        dup = [k for k, v in Counter(ids_entradas).items() if v > 1][:5]
        problemas.append(f"IDs de entrada repetidos: {dup}")
    malos = [i for i in ids_entradas if not _RE_ID.match(i)][:5]
    if malos:
        problemas.append(f"IDs con forma inválida: {malos}")
    if inv is not None:
        sin_inv = [f["ruta"] for f in entradas if f.get("ruta") not in inv][:5]
        if sin_inv:
            problemas.append(f"rutas fuera del inventario: {sin_inv}")
        rutas = {f.get("ruta") for f in entradas}
        faltan = [r for r in inv if r not in rutas][:5]
        if faltan:
            problemas.append(f"archivos del inventario sin entrada: {faltan}")
    nodos = {n["id"] for rel, fs in filas_por_parte.items() if rel.startswith("grafo/nodos-") for n in fs}
    alias = {a["id"]: a["a"] for a in filas_por_parte.get("grafo/alias" + particiones.EXTENSION, [])}
    for rel, fs in filas_por_parte.items():
        if rel.startswith("grafo/aristas-") and not rel.startswith(("grafo/aristas-mismo_documento",
                                                                     "grafo/aristas-refiere_a")):
            colgando = [a for a in fs if (a["s"] not in nodos or (a["t"] not in nodos and a["t"] not in alias))
                        and not str(a["t"]).startswith("via_")][:3]
            if colgando:
                problemas.append(f"aristas con extremos inexistentes en {rel}: {colgando}")
    comunidades = {c["id"] for c in filas_por_parte.get("grafo/comunidades" + particiones.EXTENSION, [])}
    sin_c = [n for n in nodos if n not in comunidades][:5]
    if sin_c:
        problemas.append(f"nodos sin comunidad: {sin_c}")
    if base:
        for clave, previo in base["estado"].get("conteos", {}).items():
            actual = estado.get("conteos", {}).get(clave, 0)
            if previo and actual < previo * 0.99 and clave.startswith("col_"):
                problemas.append(f"el conteo {clave} cayó de {previo} a {actual}")
    por_id = {f["id"]: f for f in entradas}
    humo = por_id.get("cs:10641-2024")
    if inv is not None and "jurisprudencia_cs/2024/03/10641-2024.md" in inv and \
            (not humo or humo.get("ruta") != "jurisprudencia_cs/2024/03/10641-2024.md"):
        problemas.append("humo: cs:10641-2024 no apunta a jurisprudencia_cs/2024/03/10641-2024.md")
    return problemas
