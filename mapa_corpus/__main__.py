"""CLI del constructor del mapa: `python -m mapa_corpus <estado|construir|validar|publicar|puntero|actualizar|verificar-puntero>`.

`--trabajo` es la carpeta de trabajo (plan.json, base/, mapa/, reporte). Nunca debe quedar
dentro de `data/` del repo: el publicador de catálogos sube `data/` entero a HF.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from mapa_corpus import REPO_ID, RUTA_HF, constructor, inventario, particiones, publicador

log = logging.getLogger("mapa_corpus")
REPO_RAIZ = Path(__file__).resolve().parent.parent
CURADO = REPO_RAIZ / "data" / "legal_knowledge_graph.json"
MOVIMIENTO_MINUTOS = 45


def _token() -> Optional[str]:
    try:
        from online_library_sync import resolver_token_hf
        return resolver_token_hf()
    except Exception:  # noqa: BLE001 — sin token se lee anónimo (el dataset es público)
        return None


def _trabajo(ruta: str) -> Path:
    p = Path(ruta).resolve()
    if (REPO_RAIZ / "data") in p.parents or p == REPO_RAIZ / "data":
        raise SystemExit("--trabajo no puede estar dentro de data/ (se subiría a HF con el catálogo)")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _salida_github(ruta: Optional[str], valores: Dict[str, Any]) -> None:
    if not ruta:
        return
    with open(ruta, "a", encoding="utf-8") as f:
        for k, v in valores.items():
            f.write(f"{k}={v}\n")


def _filtrar(inv: Dict[str, inventario.Archivo], prefijos: Optional[List[str]]) -> Dict[str, inventario.Archivo]:
    if not prefijos:
        return inv
    return {r: a for r, a in inv.items() if r.startswith(tuple(prefijos)) or r == constructor.INDICE_CS}


def _bajar_base_hf(destino: Path, revision: str, token: Optional[str]) -> Optional[Dict[str, Any]]:
    """El último mapa publicado (estado + entradas) a `destino`, o None si no hay."""
    import requests
    s = requests.Session()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    url = f"{inventario.ENDPOINT}/datasets/{REPO_ID}/resolve/{revision}/{RUTA_HF}/estado.json"
    r = s.get(url, timeout=60)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "estado.json").write_bytes(r.content)
    estado = json.loads(r.content)
    for rel, meta in particiones.archivos_de(estado).items():
        if not rel.startswith("entradas/"):
            continue
        datos = s.get(f"{inventario.ENDPOINT}/datasets/{REPO_ID}/resolve/{revision}/{RUTA_HF}/{rel}", timeout=120)
        datos.raise_for_status()
        if particiones.sha256(datos.content) != meta["sha256_gz"]:
            raise RuntimeError(f"la base publicada {rel} no calza con su estado")
        (destino / rel).parent.mkdir(parents=True, exist_ok=True)
        (destino / rel).write_bytes(datos.content)
    return constructor.leer_mapa(str(destino))


def cmd_estado(a: argparse.Namespace) -> int:
    trabajo = _trabajo(a.trabajo)
    token = _token()
    sha, modificado = inventario.sha_main(token=token, revision=a.sha) if a.sha else inventario.sha_main(token=token)
    inv = _filtrar(inventario.inventario(sha, token=token), a.prefijos)
    base: Optional[Dict[str, Any]] = None
    origen_base = None
    if a.base_dir:
        base, origen_base = constructor.leer_mapa(a.base_dir), f"local:{a.base_dir}"
    elif not a.sin_base:
        # La base, fijada a la misma revisión que el inventario: publicar exige que siga siendo esa.
        base = _bajar_base_hf(trabajo / "base", sha, token)
        origen_base = "hf:main" if base else None
    reglas = constructor.version_reglas()
    huella = inventario.huella(inv.values(), reglas)
    motivo, cambio, puntero_pendiente = "", True, False
    if base is None and getattr(a, "requiere_base", False):
        cambio, motivo = False, "sin mapa publicado: la primera construcción se lanza a mano (modo completo)"
    elif base and base["estado"].get("huella_fuente") == huella and \
            base["estado"].get("curado", {}).get("sha256") == _sha_curado():
        cambio, motivo = False, "huella y grafo curado iguales a lo publicado"
        # El mapa ya está en HF pero el PR de su puntero no llegó (sin token, cerrado…): se rehace.
        puntero_pendiente = _puntero_desactualizado(trabajo / "base" / "estado.json")
        if puntero_pendiente:
            motivo += "; el puntero del repo no apunta a él"
    elif modificado and not a.ignorar_movimiento:
        edad = (datetime.now(timezone.utc) - datetime.fromisoformat(modificado.replace("Z", "+00:00"))).total_seconds()
        if edad < MOVIMIENTO_MINUTOS * 60:
            cambio, motivo = False, f"fuente en movimiento (último commit hace {int(edad // 60)} min)"
    if cambio:
        modo = "completo" if not base or base["estado"].get("version_reglas") != reglas else "delta"
        prev = {f["ruta"]: str(f.get("blob", "")) for f in (base or {}).get("filas", []) if f.get("ruta")}
        altas, mods, bajas = inventario.delta(prev, inv) if modo == "delta" else (sorted(inv), [], [])
        motivo = f"{modo}: +{len(altas)} ~{len(mods)} -{len(bajas)}"
    plan = {"sha": sha, "modificado": modificado, "base": origen_base, "sin_base": bool(a.sin_base),
            "cambio": cambio, "motivo": motivo, "huella": huella, "prefijos": a.prefijos or [],
            "puntero_pendiente": puntero_pendiente}
    (trabajo / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("estado: %s", plan)
    modo_plan = motivo.split(":", 1)[0] if cambio else ""
    _salida_github(a.github_output, {"cambio": str(cambio).lower(), "sha_fuente": sha, "motivo": motivo,
                                     "modo": modo_plan, "puntero": str(puntero_pendiente).lower()})
    return 0


def _sha_curado() -> str:
    import hashlib
    return hashlib.sha256(CURADO.read_bytes()).hexdigest() if CURADO.exists() else ""


def _puntero_desactualizado(estado_publicado: Path) -> bool:
    if not estado_publicado.exists():
        return False
    try:
        actual = json.loads(publicador.PUNTERO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        actual = {}
    return bool(actual.get("sha256_estado") != particiones.sha256(estado_publicado.read_bytes()))


def cmd_puntero(a: argparse.Namespace) -> int:
    """El puntero al mapa ya publicado (el de la base del plan), cuando el PR que lo llevaba no llegó."""
    trabajo = _trabajo(a.trabajo)
    plan = json.loads((trabajo / "plan.json").read_text(encoding="utf-8"))
    estado_bytes = (trabajo / "base" / "estado.json").read_bytes()
    puntero = publicador.escribir_puntero(estado_bytes, plan["sha"])
    (trabajo / "reporte.md").write_text(
        f"## Mapa del corpus — puntero\n\nEl mapa de la fuente `{str(puntero['sha_fuente'])[:8]}` ya está publicado "
        f"en HF (revisión `{plan['sha']}`), pero el PR de su puntero no se fusionó: este lo rehace.\n",
        encoding="utf-8")
    _salida_github(a.github_output, {"publicado": "true", "revision_mapa": plan["sha"],
                                     "sha_fuente": puntero.get("sha_fuente") or ""})
    return 0


def cmd_construir(a: argparse.Namespace) -> int:
    trabajo = _trabajo(a.trabajo)
    plan = json.loads((trabajo / "plan.json").read_text(encoding="utf-8"))
    token = _token()
    inv = _filtrar(inventario.inventario(plan["sha"], token=token), plan.get("prefijos") or None)
    base = None
    if a.modo == "delta":
        if plan.get("base", "") and str(plan["base"]).startswith("local:"):
            base = constructor.leer_mapa(str(plan["base"])[6:])
        elif (trabajo / "base" / "estado.json").exists():
            base = constructor.leer_mapa(str(trabajo / "base"))
    t0 = time.time()
    descargador = inventario.Descargador(plan["sha"], token=token)
    resultado = constructor.construir(inv, plan["sha"], descargador, a.curado or str(CURADO), base=base)
    resultado["estado"]["fecha_fuente"] = plan.get("modificado") or None
    estado = constructor.escribir(resultado, str(trabajo / "mapa"), (base or {}).get("estado"))
    reporte = {**resultado["reporte"], "segundos": int(time.time() - t0), "peticiones": descargador.peticiones,
               "conteos": estado["conteos"], "calidad": estado["calidad"]}
    (trabajo / "reporte.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.podar_cache:
        log.info("caché de fuentes: %d blobs fuera del inventario borrados", descargador.podar(inv.values()))
    if a.reporte:
        Path(a.reporte).write_text(_reporte_md(plan, reporte), encoding="utf-8")
    log.info("construido: %s", json.dumps(reporte, ensure_ascii=False))
    return 0


def _reporte_md(plan: Dict[str, Any], r: Dict[str, Any]) -> str:
    lineas = [f"## Mapa del corpus — fuente `{plan['sha'][:8]}`", "",
              f"- Delta: +{r['altas']} ~{r['modificados']} -{r['bajas']} · descargados {r['descargados']} "
              f"· {r['segundos']} s · {r['peticiones']} peticiones", "", "### Conteos", ""]
    lineas += [f"- {k}: {v}" for k, v in r["conteos"].items()]
    lineas += ["", "### Calidad", ""] + [f"- {k}: {v}" for k, v in r["calidad"].items()]
    return "\n".join(lineas)[:60000] + "\n"


def cmd_validar(a: argparse.Namespace) -> int:
    trabajo = _trabajo(a.trabajo)
    plan = json.loads((trabajo / "plan.json").read_text(encoding="utf-8"))
    inv = _filtrar(inventario.inventario(plan["sha"], token=_token()), plan.get("prefijos") or None)
    base = constructor.leer_mapa(str(trabajo / "base")) if (trabajo / "base" / "estado.json").exists() else None
    problemas = constructor.validar(str(trabajo / "mapa"), inv, base)
    for p in problemas:
        log.error("validación: %s", p)
    return 1 if problemas else 0


def cmd_publicar(a: argparse.Namespace) -> int:
    trabajo = _trabajo(a.trabajo)
    plan = json.loads((trabajo / "plan.json").read_text(encoding="utf-8"))
    if plan.get("prefijos"):
        raise SystemExit("un mapa parcial (--prefijos) no se publica")
    token = _token()
    # Lo publicado AHORA es la base del commit (parent_commit = este HEAD: si main se mueve de aquí
    # al commit, HF lo rechaza). Si el plan se hizo contra el mapa de HF y ese mapa ya no es el
    # mismo (otra publicación entretanto), el delta calculado es inválido: la corrida queda superada.
    head, _ = inventario.sha_main(token=token)
    remoto_bytes = _bajar_estado(head, token)
    if not str(plan.get("base") or "").startswith("local:") and not plan.get("sin_base"):
        base_ruta = trabajo / "base" / "estado.json"
        if remoto_bytes != (base_ruta.read_bytes() if base_ruta.exists() else None):
            log.error("superado: el mapa publicado cambió durante la corrida (la próxima lo rehace)")
            return 3
    remoto = json.loads(remoto_bytes) if remoto_bytes else None
    res = publicador.publicar(str(trabajo / "mapa"), remoto, head, token,
                              dry_run=a.dry_run, forzar_versiones=a.forzar_versiones)
    log.info("publicación: %s", json.dumps({k: v for k, v in res.items() if k != "puntero"}, ensure_ascii=False)[:2000])
    _salida_github(a.github_output, {"publicado": str(res.get("publicado")).lower(),
                                     "revision_mapa": res.get("revision_mapa", ""),
                                     "sha_fuente": (res.get("puntero") or {}).get("sha_fuente") or ""})
    return 0


def _bajar_estado(revision: str, token: Optional[str]) -> Optional[bytes]:
    """Los bytes de `estado.json` del mapa en `revision` (None si no hay mapa publicado)."""
    import requests
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{inventario.ENDPOINT}/datasets/{REPO_ID}/resolve/{revision}/{RUTA_HF}/estado.json",
                     headers=h, timeout=60)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return bytes(r.content)


def cmd_actualizar(a: argparse.Namespace) -> int:
    if cmd_estado(a):
        return 1
    plan = json.loads((Path(a.trabajo).resolve() / "plan.json").read_text(encoding="utf-8"))
    if not plan["cambio"]:
        log.info("sin cambios: %s", plan["motivo"])
        return 0
    a.modo = "delta" if plan["motivo"].startswith("delta") else "completo"
    for paso in (cmd_construir, cmd_validar, cmd_publicar):
        codigo = paso(a)
        if codigo:
            return codigo
    return 0


def cmd_verificar_puntero(a: argparse.Namespace) -> int:
    """Verifica que el puntero apunte a un mapa publicado íntegro (lectura pública, sin token)."""
    puntero = json.loads(Path(a.puntero).read_text(encoding="utf-8"))
    if not puntero.get("revision_mapa"):
        log.info("puntero sin revisión (mapa aún no publicado): nada que verificar")
        return 0
    from mapa_corpus.verificacion import verificar_puntero
    problemas = verificar_puntero(puntero)
    for p in problemas:
        log.error("puntero: %s", p)
    return 1 if problemas else 0


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stderr)
    p = argparse.ArgumentParser(prog="python -m mapa_corpus")
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--trabajo", required=True)
        sp.add_argument("--github-output", default=None)

    sp = sub.add_parser("estado")
    comunes(sp)
    sp.add_argument("--sha", default=None, help="fijar la revisión fuente (por defecto: main)")
    sp.add_argument("--base-dir", default=None, help="mapa local como base (en vez del publicado)")
    sp.add_argument("--sin-base", action="store_true", help="ignorar el mapa publicado (construcción completa)")
    sp.add_argument("--prefijos", nargs="*", default=None, help="solo para pruebas: limitar el inventario")
    sp.add_argument("--ignorar-movimiento", action="store_true")
    sp.add_argument("--requiere-base", action="store_true",
                    help="sin mapa publicado no se construye (corridas programadas)")
    sp.set_defaults(fn=cmd_estado)

    sp = sub.add_parser("construir")
    comunes(sp)
    sp.add_argument("--modo", choices=["delta", "completo"], default="delta")
    sp.add_argument("--curado", default=None)
    sp.add_argument("--reporte", default=None)
    sp.add_argument("--podar-cache", action="store_true", help="borrar de la caché los blobs que ya no existen")
    sp.set_defaults(fn=cmd_construir)

    sp = sub.add_parser("validar")
    comunes(sp)
    sp.set_defaults(fn=cmd_validar)

    sp = sub.add_parser("publicar")
    comunes(sp)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--forzar-versiones", action="store_true")
    sp.set_defaults(fn=cmd_publicar)

    sp = sub.add_parser("puntero", help="rehacer el puntero al mapa ya publicado (si su PR no llegó)")
    comunes(sp)
    sp.set_defaults(fn=cmd_puntero)

    sp = sub.add_parser("actualizar")
    comunes(sp)
    sp.add_argument("--sha", default=None)
    sp.add_argument("--base-dir", default=None)
    sp.add_argument("--sin-base", action="store_true")
    sp.add_argument("--prefijos", nargs="*", default=None)
    sp.add_argument("--ignorar-movimiento", action="store_true")
    sp.add_argument("--curado", default=None)
    sp.add_argument("--reporte", default=None)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--forzar-versiones", action="store_true")
    sp.add_argument("--modo", default="delta")
    sp.add_argument("--podar-cache", action="store_true")
    sp.set_defaults(fn=cmd_actualizar)

    sp = sub.add_parser("verificar-puntero")
    sp.add_argument("--puntero", default=str(publicador.PUNTERO))
    sp.set_defaults(fn=cmd_verificar_puntero)

    args = p.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
