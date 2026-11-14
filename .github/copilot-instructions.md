# Open Legal Chile — GitHub Copilot & Commit Instructions (`github/awesome-copilot` + `commit-commands`)

## 1. Filosofía y Jurisdicción
* Este repositorio implementa **Open Legal Chile**, la suite de inteligencia artificial jurídica para el **Derecho Continental Codificado de la República de Chile**.
* Prohibición estricta de términos del *Common Law* (no usar figuras anglosajonas inexistentes en Chile).
* Ortotipografía académica RAE/ASALE (`« »`, `N.°`, mayúsculas con tilde preceptiva) y formato obligatorio de citas `[BCN - ...]`, `[CS - ...]`, `[Doctrina - ...]`, `[Hugging Face - ...]`.

## 2. Protocolo de Commits Atómicos (`Conventional Commits` + `commit-commands`)
Todo commit debe seguir el estándar `<tipo>(<alcance>): <descripción concisa en español>`:
* **Tipos permitidos:** `feat`, `fix`, `perf`, `docs`, `refactor`, `test`, `chore`, `ci`.
* **Alcances frecuentes:** `graphify`, `hf`, `pjud`, `baremo`, `critique`, `skills`, `plugin`, `web`, `conectores`, `forense`, `ci`.
* **Cuerpo del commit:** Explicar qué se hizo, por qué se hizo y qué pruebas/auditorías lo respaldan.

## 3. Compuerta Pre-Commit de 9 Capas (`.github/workflows/audit.yml`)
Antes de ejecutar `git commit` y `git push`, verificar siempre:
1. `skills-lock.json` sincronizado con los hashes SHA-256 de `.agents/skills/*/SKILL.md`.
2. `.venv/bin/ruff check .` (0 errores).
3. `.venv/bin/bandit -r . -x ./tests,./.venv,./doctrina_raw -s B101,B110,B310,B311,B404,B603 -q` (0 alertas).
4. `.venv/bin/vulture . --min-confidence 80 --exclude .venv,tests` (0 código muerto).
5. `.venv/bin/mypy --ignore-missing-imports --explicit-package-bases --exclude '(\.venv|doctrina_raw|brag-output)' .` (0 errores de tipos).
6. `.venv/bin/pytest tests/test_legal_design.py tests/test_empaquetado.py tests/test_web_actualizada.py` (100 % verde).
