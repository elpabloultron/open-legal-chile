#!/usr/bin/env python3
"""
Open Legal Chile — Watchdog y Auto-Reparador de CI de GitHub
Supervisa los workflows de GitHub Actions para el commit actual o rama main,
audita si todos los jobs terminaron en verde y, en caso de fallos detectados
(p. ej. desincronización de skills-lock, formato de linter o red),
ejecuta el diagnóstico y la reparación automática.

Utiliza la herramienta oficial GitHub CLI (gh de cli/cli).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


def _run(cmd: List[str], cwd: Optional[pathlib.Path] = None, check: bool = False) -> Tuple[int, str, str]:
    """Ejecuta un comando en un subproceso y retorna (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, cwd=str(cwd or ROOT_DIR), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"Comando falló ({p.returncode}): {' '.join(cmd)}\n{p.stderr}")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def verificar_gh_instalado() -> bool:
    """Verifica si gh (GitHub CLI) está disponible en el entorno."""
    rc, out, _ = _run(["which", "gh"])
    return rc == 0 and bool(out)


def obtener_head_commit() -> str:
    """Obtiene el hash SHA completo del commit actual en HEAD."""
    rc, out, _ = _run(["git", "rev-parse", "HEAD"])
    if rc != 0 or not out:
        raise RuntimeError("No se pudo determinar el commit actual con git.")
    return out.strip()


def consultar_runs_commit(commit_sha: str) -> List[Dict[str, Any]]:
    """Consulta la API de GitHub mediante gh para obtener los workflows del commit."""
    cmd = [
        "gh", "run", "list",
        "--commit", commit_sha,
        "--json", "databaseId,name,status,conclusion,url,event,headSha"
    ]
    rc, out, err = _run(cmd)
    if rc != 0:
        # Fallback: consultar últimos 15 runs y filtrar por commit
        rc2, out2, _ = _run(["gh", "run", "list", "--limit", "15", "--json", "databaseId,name,status,conclusion,url,event,headSha"])
        if rc2 == 0 and out2:
            try:
                todos = json.loads(out2)
                return [r for r in todos if r.get("headSha", "").startswith(commit_sha[:8])]
            except Exception:
                pass
        raise RuntimeError(f"Error al consultar GitHub Actions con gh: {err}")
    try:
        return json.loads(out) if out else []
    except json.JSONDecodeError:
        return []


def descargar_log_fallado(run_id: int | str) -> str:
    """Descarga el extracto de log fallado para un workflow específico."""
    cmd = ["gh", "run", "view", str(run_id), "--log-failed"]
    _, out, err = _run(cmd)
    return out or err


def clasificar_fallo(log_text: str) -> Dict[str, Any]:
    """Analiza el log de error e identifica la causa raíz y su posible reparación."""
    # 1. Desincronización de skills-lock.json
    m_skill = re.search(r"AssertionError:\s*([\w-]+):\s*lock=([a-f0-9]+)…\s*archivo=([a-f0-9]+)…", log_text)
    if m_skill or "test_el_lock_de_skills_corresponde_a_los_archivos" in log_text:
        skill_nombre = m_skill.group(1) if m_skill else None
        return {
            "tipo": "SKILLS_LOCK",
            "descripcion": f"Desincronización de hash SHA-256 en skills-lock.json (skill: {skill_nombre or 'varias'})",
            "skill": skill_nombre,
            "reparable_automaticamente": True
        }

    # 2. Hallazgos Bandit SAST (p. ej. B108 directorio temporal)
    m_bandit = re.search(r"Issue:\s*\[(B\d+):(\w+)\].*Location:\s*([^\n:]+):(\d+)", log_text, re.DOTALL)
    if m_bandit:
        regla, id_regla, archivo, linea = m_bandit.groups()
        return {
            "tipo": "BANDIT_SAST",
            "descripcion": f"Hallazgo de seguridad Bandit {regla} ({id_regla}) en {archivo}:{linea}",
            "archivo": archivo,
            "linea": linea,
            "reparable_automaticamente": False
        }

    # 3. Errores de formato / linting con Ruff
    m_ruff = re.search(r"Found\s+\d+\s+error.*fixable with", log_text)
    if m_ruff or "Ruff Linter" in log_text and "FAILED" in log_text:
        return {
            "tipo": "RUFF_LINT",
            "descripcion": "Errores de formato o sintaxis detectados por Ruff",
            "reparable_automaticamente": True
        }

    # 4. Error de red / timeout transitorio
    if any(k in log_text.lower() for k in ("connectionerror", "503 service unavailable", "429 too many requests", "operation timed out")):
        return {
            "tipo": "NETWORK_TIMEOUT",
            "descripcion": "Error transitorio de red o timeout conectando a fuentes oficiales",
            "reparable_automaticamente": True
        }

    # 5. Fallo general en prueba unitaria de pytest
    m_pytest = re.search(r"FAILED\s+(tests/[^\s:]+)::(\w+)", log_text)
    if m_pytest:
        return {
            "tipo": "PYTEST_FAIL",
            "descripcion": f"Fallo en prueba {m_pytest.group(1)}::{m_pytest.group(2)}",
            "test_file": m_pytest.group(1),
            "test_name": m_pytest.group(2),
            "reparable_automaticamente": False
        }

    return {
        "tipo": "DESCONOCIDO",
        "descripcion": "Fallo no clasificado en los logs de ejecución",
        "reparable_automaticamente": False
    }


def reparar_skills_lock() -> bool:
    """Recalcula los hashes SHA-256 de todas las skills y actualiza skills-lock.json."""
    lock_file = ROOT_DIR / "skills-lock.json"
    if not lock_file.exists():
        return False
    data = json.loads(lock_file.read_text(encoding="utf-8"))
    skills = data.get("skills", {})
    actualizadas = 0
    for _nombre, entrada in skills.items():
        ruta = ROOT_DIR / entrada["skillPath"]
        if ruta.exists():
            contenido = ruta.read_bytes().replace(b"\r\n", b"\n")
            nuevo_hash = hashlib.sha256(contenido).hexdigest()
            if entrada.get("sha256") != nuevo_hash:
                entrada["sha256"] = nuevo_hash
                actualizadas += 1
    if actualizadas > 0:
        lock_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"🔧 skills-lock.json actualizado ({actualizadas} skills sincronizadas).")
        return True
    return False


def reparar_ruff() -> bool:
    """Ejecuta ruff check --fix para corregir fallos menores de estilo automáticamente."""
    rc, out, _ = _run(["ruff", "check", "--fix", "."])
    return rc == 0


def reintentar_run_fallado(run_id: int | str) -> bool:
    """Reintenta sólo los jobs fallados mediante gh run rerun."""
    cmd = ["gh", "run", "rerun", str(run_id), "--failed"]
    rc, out, _ = _run(cmd)
    return rc == 0


def publicar_reparacion(mensaje_commit: str) -> bool:
    """Confirma los cambios locales reparados y los sube a GitHub pasando la auditoría."""
    print("📦 Confirmando reparación local...")
    _run(["git", "add", "-A"])
    rc, _, err = _run(["git", "commit", "-m", mensaje_commit])
    if rc != 0:
        print(f"⚠️ No hubo cambios para confirmar: {err}")
        return False
    print("🚀 Subiendo reparación a origin/main (ejecutando auditoría pre-push)...")
    rc_push, out_push, err_push = _run(["git", "push", "origin", "main"])
    if rc_push != 0:
        print(f"❌ Error al empujar a origin/main:\n{err_push or out_push}")
        return False
    print("✅ Reparación subida exitosamente a GitHub.")
    return True


def vigilar_y_reparar(commit_sha: Optional[str] = None, watch: bool = True, auto_fix: bool = True, timeout: int = 900) -> int:
    """Bucle principal de supervisión y auto-reparación."""
    if not verificar_gh_instalado():
        print("❌ Error: GitHub CLI ('gh') no está disponible o no está en PATH.")
        print("Instálalo con 'mise use gh' o 'pacman -S github-cli'.")
        return 1

    sha = commit_sha or obtener_head_commit()
    print(f"🔍 Supervisando GitHub Actions para el commit: {sha[:8]}...")
    inicio = time.time()

    while True:
        runs = consultar_runs_commit(sha)
        if not runs:
            # Si no hay runs todavía, puede tardar unos segundos en crearse
            if time.time() - inicio < 45:
                print("⏳ Esperando que GitHub Actions registre los workflows...")
                time.sleep(5)
                continue
            print(f"⚠️ No se encontraron runs activos para el commit {sha[:8]}.")
            return 0

        total = len(runs)
        completados = [r for r in runs if r.get("status") == "completed"]
        fallados = [r for r in completados if r.get("conclusion") in ("failure", "timed_out")]
        exitosos = [r for r in completados if r.get("conclusion") == "success"]
        en_progreso = [r for r in runs if r.get("status") != "completed"]

        print(f"\r📊 Workflows: {len(exitosos)}/{total} verdes | {len(fallados)} fallados | {len(en_progreso)} en curso...", end="", flush=True)

        if fallados:
            print(f"\n\n🚨 SE DETECTARON {len(fallados)} WORKFLOW(S) CON ERROR:")
            for f in fallados:
                run_id = f.get("databaseId")
                if not run_id:
                    continue
                run_id_str = str(run_id)
                nombre = f.get("name")
                print(f" • [{nombre}] ID: {run_id_str} ({f.get('url')})")
                log = descargar_log_fallado(run_id_str)
                analisis = clasificar_fallo(log)
                print(f"   ↳ Diagnóstico: {analisis['descripcion']}")

                if auto_fix and analisis.get("reparable_automaticamente"):
                    tipo = analisis["tipo"]
                    print(f"   🔧 Intentando auto-reparación de tipo '{tipo}'...")
                    reparado = False
                    if tipo == "SKILLS_LOCK":
                        reparado = reparar_skills_lock()
                        if reparado:
                            reparado = publicar_reparacion("fix(ci): autoreparar hash en skills-lock.json")
                    elif tipo == "RUFF_LINT":
                        reparado = reparar_ruff()
                        if reparado:
                            reparado = publicar_reparacion("fix(ci): autoreparar formato y linter ruff")
                    elif tipo == "NETWORK_TIMEOUT":
                        reparado = reintentar_run_fallado(run_id_str)
                        print("   🔄 Reintento disparado en GitHub Actions.")

                    if reparado:
                        print("✨ Reparación completada. Reiniciando supervisión con el nuevo estado...")
                        time.sleep(10)
                        sha = obtener_head_commit()
                        inicio = time.time()
                        break
            if not auto_fix:
                return 1

        if len(completados) == total and not fallados:
            print(f"\n\n🎉 ¡TODO EN VERDE! Todos los workflows de GitHub Actions concluyeron con éxito para {sha[:8]}:")
            for r in exitosos:
                print(f"  ✅ {r.get('name')}")
            return 0

        if not watch:
            break

        if time.time() - inicio > timeout:
            print(f"\n⏱️ Tiempo de espera agotado ({timeout}s) supervisando GitHub Actions.")
            return 1

        time.sleep(10)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Watchdog y Auto-Reparador de CI de GitHub para Open Legal Chile")
    parser.add_argument("--commit", help="Hash SHA del commit a supervisar (por defecto HEAD)")
    parser.add_argument("--no-watch", action="store_true", help="Solo revisa el estado actual sin esperar")
    parser.add_argument("--no-fix", action="store_true", help="No intentar reparar automáticamente los fallos")
    parser.add_argument("--timeout", type=int, default=900, help="Segundos máximos de espera (default: 900s)")

    args = parser.parse_args()
    rc = vigilar_y_reparar(
        commit_sha=args.commit,
        watch=not args.no_watch,
        auto_fix=not args.no_fix,
        timeout=args.timeout
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
