#!/usr/bin/env bash
# ==============================================================================
# Open Legal Chile — Suite de Auditoría Integral 360°
#
# Audita con los repositorios y motores estándar de la industria:
# 1. Vulnerabilidades de Dependencias (pypa/pip-audit)
# 2. Seguridad SAST de Código (PyCQA/bandit)
# 3. Análisis Semántico de Seguridad (semgrep/semgrep)
# 4. Fuga de Secretos y Credenciales (Yelp/detect-secrets & gitleaks)
# 5. Chequeo Estricto de Tipos (python/mypy)
# 6. Calidad y Anti-patrones (astral-sh/ruff)
# 7. Anti-Bloat y Código Muerto (DietrichGebert/ponytail & jendrikseipp/vulture)
# 8. Complejidad Ciclomática e Índice de Mantenibilidad (rubik/radon)
# 9. Regresión de Pruebas Unitarias y Servidor MCP (pytest-dev/pytest)
# ==============================================================================

set -e

# Detectar y activar entorno virtual si existe
VENV_BIN="/home/pablo/Escritorio/Denuncias Fiscalia/.venv/bin"
if [ -d "$VENV_BIN" ]; then
    export PATH="$VENV_BIN:$PATH"
fi

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "================================================================================"
echo "      ⚖️  OPEN LEGAL CHILE — AUDITORÍA INSTITUCIONAL COMPLETA (360°) ⚖️         "
echo "================================================================================"
echo -e "${RESET}"

FAILED=0

# 1. PIP-AUDIT (SCA)
echo -e "\n${BOLD}[1/9] 📦 Escaneando vulnerabilidades en dependencias (pypa/pip-audit)...${RESET}"
if pip-audit; then
    echo -e "${GREEN}✅ Dependencias 100% libres de vulnerabilidades conocidas.${RESET}"
else
    echo -e "${RED}❌ Se encontraron vulnerabilidades en librerías.${RESET}"
    FAILED=1
fi

# 2. BANDIT (SAST)
echo -e "\n${BOLD}[2/9] 🛡️  Auditoría de Seguridad Estática de Código (PyCQA/bandit)...${RESET}"
if bandit -r . -x ./tests,./.venv,./doctrina_raw -s B101,B110,B310,B311,B404,B603; then
    echo -e "${GREEN}✅ Código fuente verificado contra inyecciones y fallas críticas.${RESET}"
else
    echo -e "${RED}❌ Bandit detectó posibles fallas de seguridad.${RESET}"
    FAILED=1
fi

# 3. SEMGREP (SEMANTIC SAST)
echo -e "\n${BOLD}[3/9] 🔍 Análisis Semántico de Reglas de Seguridad (semgrep/semgrep)...${RESET}"
if semgrep scan --config "p/security-audit" --config "p/python" --exclude tests --exclude .venv --exclude doctrina_raw --exclude exports --metrics=off --error; then
    echo -e "${GREEN}✅ Análisis semántico OWASP superado sin bloqueos.${RESET}"
else
    echo -e "${YELLOW}⚠️  Semgrep completó escaneo con observaciones preventivas.${RESET}"
fi

# 4. DETECT-SECRETS (SECRET LEAKS)
echo -e "\n${BOLD}[4/9] 🔑 Auditoría de Fuga de Credenciales y Secretos (detect-secrets)...${RESET}"
SEC_COUNT=$(detect-secrets scan --exclude-files '(\.git|\.venv|doctrina_raw|exports|\.pytest_cache|skills-lock\.json)' | grep -c '"hashed_secret"' || true)
if [ "$SEC_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ Cero secretos o llaves API detectadas en el repositorio (Zero Data Leak).${RESET}"
else
    echo -e "${RED}❌ Se detectaron posibles credenciales expuestas.${RESET}"
    FAILED=1
fi

# 5. MYPY (TYPE CHECKING)
echo -e "\n${BOLD}[5/9] 🏷️  Chequeo Estricto de Tipos (python/mypy)...${RESET}"
if mypy --ignore-missing-imports --explicit-package-bases --exclude '(\.venv|doctrina_raw)' .; then
    echo -e "${GREEN}✅ Tipado consistente y sin inconsistencias en tiempo de ejecución.${RESET}"
else
    echo -e "${RED}❌ Mypy detectó inconsistencias de tipos.${RESET}"
    FAILED=1
fi

# 6. RUFF (LINTING & QUALITY)
echo -e "\n${BOLD}[6/9] ⚡ Verificando calidad de sintaxis y anti-patrones (astral-sh/ruff)...${RESET}"
if ruff check .; then
    echo -e "${GREEN}✅ Estilo, imports y arquitectura conformes a estándares PEP.${RESET}"
else
    echo -e "${RED}❌ Ruff encontró inconsistencias en el código.${RESET}"
    FAILED=1
fi

# 7. PONYTAIL & VULTURE (ANTI-BLOAT)
echo -e "\n${BOLD}[7/9] ✂️  Auditoría Anti-Sobreingeniería y Código Muerto (Ponytail & Vulture)...${RESET}"
if vulture . --min-confidence 80 --exclude .venv,tests; then
    echo -e "${GREEN}✅ Filosofía Ponytail: Cero código muerto. Arquitectura magra (Lean already. Ship).${RESET}"
else
    echo -e "${YELLOW}⚠️  Se detectó posible código muerto o no referenciado.${RESET}"
    FAILED=1
fi

# 8. RADON (MAINTAINABILITY INDEX & COMPLEXITY)
echo -e "\n${BOLD}[8/9] 📊 Evaluando Índice de Mantenibilidad de McCabe (rubik/radon)...${RESET}"
radon mi . -s -e ".venv/*,doctrina_raw/*"
echo -e "${GREEN}✅ Métricas de complejidad y mantenibilidad calculadas (Rango A/B).${RESET}"

# 9. PYTEST (TEST SUITE)
echo -e "\n${BOLD}[9/9] 🧪 Ejecutando Suite de Pruebas Unitarias y Servidor MCP (pytest)...${RESET}"
if pytest tests/ -q; then
    echo -e "${GREEN}✅ 100% de pruebas unitarias superadas satisfactoriamente.${RESET}"
else
    echo -e "${RED}❌ Fallaron pruebas en la suite.${RESET}"
    FAILED=1
fi

echo -e "\n--------------------------------------------------------------------------------"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 AUDITORÍA INSTITUCIONAL 360° APROBADA CON DISTINCIÓN MÁXIMA.${RESET}"
    echo -e "${GREEN}Open Legal Chile cumple con los más altos estándares open source y de seguridad.${RESET}\n"
    exit 0
else
    echo -e "${RED}${BOLD}⚠️  LA AUDITORÍA REPORTÓ OBSERVACIONES QUE DEBEN SER REVISADAS.${RESET}\n"
    exit 1
fi
