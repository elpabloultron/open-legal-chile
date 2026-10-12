#!/usr/bin/env python3
"""
Open Legal Chile — Purga el historial del dataset de Hugging Face.

Retirar un archivo de `main` no lo borra de HF: las revisiones anteriores lo siguen sirviendo por su
sha (`resolve/<sha>/…`). Así quedaron accesibles las causas reservadas del TC y los correos de las
versiones previas de sus sentencias. Este script, en este orden:

1. lista las referencias del dataset (ramas, tags y PRs de HF);
2. borra los tags, que mantienen vivas revisiones viejas (`mapa-<n>`);
3. con `--retirar-mapa`, borra `data/mapa/`: el mapa publicado se armó con la fuente vieja y también
   trae las filas retiradas. Se vuelve a publicar después de la purga, sobre la revisión nueva;
4. aplasta `main` en un solo commit (`super_squash_history`): las revisiones anteriores dejan de existir;
5. comprueba que las revisiones viejas ya no se sirvan.

Es IRREVERSIBLE: exige `--confirmar <repo_id>`. Los PRs de HF (refs/pr/*) también fijan revisiones
viejas y la API no los borra: si hay alguno, no se purga (ciérrelos y bórrelos en la web de HF).

Uso: HF_TOKEN=… python scripts/purgar_historial_hf.py --confirmar pablobenavidesj/doctrina-jurisprudencia-chile \\
         [--retirar-mapa] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Callable, Dict, List, Optional

import requests

REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
RUTA_MAPA = "data/mapa"
MENSAJE = "Historial purgado: se retiran las revisiones con causas reservadas y correos de notificación"


def _servida(repo_id: str, revision: str) -> bool:
    """La revisión todavía existe en HF (consulta pública, sin token)."""
    r = requests.get(f"{ENDPOINT}/api/datasets/{repo_id}/revision/{revision}", timeout=30)
    return r.status_code == 200


def _hay_carpeta(api: Any, repo_id: str, ruta: str) -> bool:
    try:
        return next(iter(api.list_repo_tree(repo_id, path_in_repo=ruta, repo_type="dataset")), None) is not None
    except Exception as e:  # noqa: BLE001 — EntryNotFoundError (404): la carpeta no existe
        if getattr(getattr(e, "response", None), "status_code", None) == 404 or type(e).__name__ == "EntryNotFoundError":
            return False
        raise


def purgar(api: Any, repo_id: str, retirar_mapa: bool = False, dry_run: bool = False,
           servida: Optional[Callable[[str, str], bool]] = None) -> Dict[str, Any]:
    servida = servida or _servida
    refs = api.list_repo_refs(repo_id, repo_type="dataset", include_pull_requests=True)
    tags = sorted(str(t.name) for t in (refs.tags or []))
    prs = sorted(str(p.ref) for p in (getattr(refs, "pull_requests", None) or []))
    viejas = [str(c.commit_id) for c in api.list_repo_commits(repo_id, repo_type="dataset")]
    res: Dict[str, Any] = {"tags": tags, "prs": prs, "commits_antes": len(viejas), "mapa_retirado": False,
                           "purgado": False, "commit": "", "revisiones_aun_servidas": []}
    if prs:
        res["error"] = "hay PRs de HF que fijan revisiones viejas: ciérrelos y bórrelos en la web antes de purgar"
        return res
    if dry_run:
        return res
    for tag in tags:
        api.delete_tag(repo_id, tag=tag, repo_type="dataset")
    if retirar_mapa and _hay_carpeta(api, repo_id, RUTA_MAPA):
        from huggingface_hub import CommitOperationDelete
        api.create_commit(repo_id=repo_id, repo_type="dataset",
                          operations=[CommitOperationDelete(path_in_repo=f"{RUTA_MAPA}/", is_folder=True)],
                          commit_message="Se retira el mapa armado con la fuente vieja (se vuelve a publicar)")
        res["mapa_retirado"] = True
    api.super_squash_history(repo_id=repo_id, repo_type="dataset", branch="main", commit_message=MENSAJE)
    despues = [str(c.commit_id) for c in api.list_repo_commits(repo_id, repo_type="dataset")]
    res.update(purgado=len(despues) == 1, commit=despues[0] if despues else "",
               revisiones_aun_servidas=[v for v in viejas[:5] if v not in despues and servida(repo_id, v)])
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="Purga el historial del dataset de HF (irreversible).")
    ap.add_argument("--repo", default=REPO_ID)
    ap.add_argument("--confirmar", default="", help="el repo_id, escrito de nuevo, para confirmar")
    ap.add_argument("--retirar-mapa", action="store_true", help=f"borrar {RUTA_MAPA}/ antes de aplastar")
    ap.add_argument("--dry-run", action="store_true", help="solo listar referencias y commits")
    args = ap.parse_args()
    if args.confirmar != args.repo:
        print(f"Para purgar, repita el repo con --confirmar {args.repo}", file=sys.stderr)
        return 2
    token = os.environ.get("HF_TOKEN") or None
    if not token:
        print("Falta HF_TOKEN (token con escritura en el dataset).", file=sys.stderr)
        return 2
    from huggingface_hub import HfApi
    res = purgar(HfApi(token=token), args.repo, retirar_mapa=args.retirar_mapa, dry_run=args.dry_run)
    lineas: List[str] = [f"### Purga del historial de HF{' (simulada)' if args.dry_run else ''}", "",
                         f"- commits antes: {res['commits_antes']}",
                         f"- tags borrados: {', '.join(res['tags']) or '—'}",
                         f"- PRs de HF: {', '.join(res['prs']) or '—'}",
                         f"- mapa retirado: {'sí' if res['mapa_retirado'] else 'no'}",
                         f"- historial aplastado: {'sí, commit ' + res['commit'][:10] if res['purgado'] else 'no'}",
                         f"- revisiones viejas que aún se sirven: {', '.join(r[:10] for r in res['revisiones_aun_servidas']) or '—'}"]
    if res.get("error"):
        lineas.append(f"- error: {res['error']}")
    print("\n".join(lineas))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
    if res.get("error") or (not args.dry_run and (not res["purgado"] or res["revisiones_aun_servidas"])):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
