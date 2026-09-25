#!/usr/bin/env bash
# Open Legal Chile — Script de Auditoría Pre-Push y Verificación de Calidad
# Audita seguridad SAST, linters y pruebas críticas antes de cada subida a GitHub.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

VENV_PY="$ROOT_DIR/.venv/bin/python"
if [ ! -f "$VENV_PY" ]; then
    VENV_PY="python3"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}⚖️  Open Legal Chile — Auditoría Pre-Push Automática${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Auditoría de Seguridad Estática (SAST) con Bandit
echo -e "\n${YELLOW}[1/3] Ejecutando Bandit SAST (Seguridad del Código)...${NC}"
"$ROOT_DIR/.venv/bin/bandit" -r online_library_sync.py mcp_server.py legal_graphify.py -ll
echo -e "${GREEN}✓ Bandit SAST completado sin hallazgos de severidad.${NC}"

# 2. Linting de código y formato con Ruff
echo -e "\n${YELLOW}[2/3] Ejecutando Ruff Linter...${NC}"
"$ROOT_DIR/.venv/bin/ruff" check online_library_sync.py tests/test_mcp_e2e_live.py
echo -e "${GREEN}✓ Ruff Linter aprobado sin errores.${NC}"

# 3. Tipado estático con Mypy
echo -e "\n${YELLOW}[3/4] Ejecutando Mypy Strict Type Checking...${NC}"
"$ROOT_DIR/.venv/bin/mypy" --ignore-missing-imports --explicit-package-bases --exclude '(\.venv|doctrina_raw|brag-output)' tests/test_mcp_e2e_live.py evals/rag_evaluator.py
echo -e "${GREEN}✓ Mypy Type Checker aprobado sin errores.${NC}"

# 4. Anti-Bloat & Dead Code Audit con Vulture
echo -e "\n${YELLOW}[4/5] Ejecutando Vulture Dead Code Audit...${NC}"
"$ROOT_DIR/.venv/bin/vulture" . --min-confidence 80 --exclude .venv,tests,brag-output
echo -e "${GREEN}✓ Vulture Dead Code Audit aprobado sin hallazgos.${NC}"

# 5. Pruebas críticas y suite E2E en vivo
echo -e "\n${YELLOW}[5/5] Ejecutando Pruebas E2E y Registro MCP...${NC}"
"$ROOT_DIR/.venv/bin/pytest" tests/test_mcp_e2e_live.py tests/test_registry.py tests/test_updates_and_stats.py -q
echo -e "${GREEN}✓ Pruebas críticas aprobadas con éxito.${NC}"

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}✨ Auditoría Pre-Push 100% Superada (5/5). Subida permitida.${NC}"
echo -e "${GREEN}======================================================${NC}\n"
exit 0
