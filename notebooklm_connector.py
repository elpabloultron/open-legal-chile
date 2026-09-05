"""
Open Legal Chile — Conector Oficial con Google NotebookLM
Permite a Open Legal Chile y a cualquier agente crear cuadernos de investigación jurídica,
cargar fuentes documentales (PDFs, escritos, sentencias) y realizar consultas fundamentadas
directamente sobre la base de conocimiento de NotebookLM.
"""

import os
import sys
import json
import re
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


class NotebookLMConnector:
    def __init__(self, nlm_bin: Optional[str] = None):
        which_nlm = shutil.which("nlm")
        if nlm_bin and (os.path.exists(nlm_bin) or shutil.which(nlm_bin)):
            self.nlm_bin = nlm_bin
        elif which_nlm:
            self.nlm_bin = which_nlm
        elif os.path.exists("/home/pablo/.local/bin/nlm"):
            self.nlm_bin = "/home/pablo/.local/bin/nlm"
        else:
            self.nlm_bin = "nlm"

    def is_available(self) -> bool:
        """Verifica si el binario de la CLI nlm está disponible en el sistema."""
        if not self.nlm_bin:
            return False
        if os.path.isabs(self.nlm_bin):
            return os.path.exists(self.nlm_bin) and os.access(self.nlm_bin, os.X_OK)
        return bool(shutil.which(self.nlm_bin))

    def _extract_json(self, text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """Extrae de forma tolerante un bloque JSON de la salida de la CLI (omitiendo avisos de versión)."""
        if not text:
            return None
        # Buscar el bloque JSON delimitado por [ ... ] o { ... }
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return None

    def _run_nlm(self, args: List[str], timeout: int = 45) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": f"Binario nlm no encontrado o no ejecutable: {self.nlm_bin}"}
        cmd = [self.nlm_bin] + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "code": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout ({timeout}s) ejecutando comando nlm: {' '.join(args)}"}
        except Exception as e:
            return {"error": str(e)}

    def list_notebooks(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Lista los cuadernos activos en la cuenta de NotebookLM con sus metadatos estructurados."""
        res = self._run_nlm(["notebook", "list", "--json"], timeout=timeout)
        if not res.get("success"):
            # Si falló con --json, intentar sin --json
            res = self._run_nlm(["notebook", "list"], timeout=timeout)
            if not res.get("success"):
                return [{"error": res.get("stderr") or res.get("error") or "Error listando cuadernos"}]

        stdout = res.get("stdout", "")
        parsed = self._extract_json(stdout)
        if parsed and isinstance(parsed, list):
            return parsed

        # Fallback a parseo de texto por líneas
        items = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line or "Update available" in line or line.startswith("ID") or line.startswith("──"):
                continue
            parts = [p.strip() for p in line.split("  ") if p.strip()]
            if len(parts) >= 2:
                items.append({
                    "id": parts[0],
                    "title": parts[1],
                    "raw": line
                })
        return items if items else [{"raw_output": stdout}]

    def create_notebook(self, title: str, timeout: int = 45) -> Dict[str, Any]:
        """Crea un nuevo cuaderno de investigación en NotebookLM y retorna su ID y URL."""
        if not title or not title.strip():
            return {"error": "El título del cuaderno no puede estar vacío."}

        title_clean = title.strip()
        res = self._run_nlm(["notebook", "create", title_clean, "--json"], timeout=timeout)
        stdout = res.get("stdout", "")

        # Intentar extraer JSON estructurado
        parsed = self._extract_json(stdout)
        notebook_id = None
        if parsed and isinstance(parsed, dict):
            notebook_id = parsed.get("id") or parsed.get("notebook_id")

        if not notebook_id:
            for line in stdout.splitlines():
                if "notebook_id:" in line or "id:" in line.lower():
                    notebook_id = line.split(":", 1)[1].strip()
                    break

        if not res.get("success") and not notebook_id:
            return {"error": res.get("stderr") or res.get("error") or "No se pudo crear el cuaderno"}

        return {
            "title": title_clean,
            "notebook_id": notebook_id,
            "url": f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else None,
            "raw": stdout
        }

    def add_source(self, notebook_id: str, file_path: str, title: Optional[str] = None, wait: bool = True, timeout: int = 120) -> Dict[str, Any]:
        """Agrega un archivo local (PDF, Markdown, texto) como fuente en un cuaderno."""
        if not notebook_id:
            return {"error": "El 'notebook_id' es requerido."}
        if not file_path:
            return {"error": "El 'file_path' es requerido."}

        p = Path(file_path)
        if not p.exists():
            return {"error": f"Archivo local no encontrado: {file_path}"}

        args = ["source", "add", str(notebook_id), "--file", str(p.resolve())]
        if title:
            args.extend(["--title", str(title)])
        if wait:
            args.append("--wait")

        res = self._run_nlm(args, timeout=timeout)
        success = res.get("success", False)
        out = res.get("stdout") or res.get("stderr")
        return {
            "notebook_id": notebook_id,
            "file": p.name,
            "success": success,
            "output": out
        }

    def query(self, notebook_id: str, prompt: str, timeout: int = 90) -> Dict[str, Any]:
        """Realiza una consulta fundada (grounded query) con citas sobre las fuentes del cuaderno."""
        if not notebook_id:
            return {"error": "El 'notebook_id' es requerido."}
        if not prompt or not prompt.strip():
            return {"error": "El 'prompt' de consulta no puede estar vacío."}

        args = ["query", "notebook", str(notebook_id), prompt.strip()]
        res = self._run_nlm(args, timeout=timeout)
        success = res.get("success", False)
        response_text = res.get("stdout") or res.get("stderr") or ""
        return {
            "notebook_id": notebook_id,
            "prompt": prompt,
            "success": success,
            "response": response_text
        }


if __name__ == "__main__":
    nlm = NotebookLMConnector()
    print("NLM disponible:", nlm.is_available())
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(nlm.list_notebooks())
