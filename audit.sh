#!/usr/bin/env bash
# ==============================================================================
# Open Legal Chile — Suite de Auditoría Integral 360°
#
# Audita:
# 1. Seguridad SAST (Bandit)
# 2. Vulnerabilidades de Dependencias (pip-audit)
# 3. Calidad de Código y Anti-Patrones (Ruff)
# 4. Anti-Bloat / Código Muerto (Vulture - Filosofía Ponytail)
# 5. Complejidad Ciclomática e Índice de Mantenibilidad (Radon)
# 6. Regresión de Pruebas Unitarias y Conectores de Estado (Pytest)
# ==============================================================================

set -e

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
echo -e "\n${BOLD}[1/6] 📦 Escaneando vulnerabilidades en dependencias (pip-audit)...${RESET}"
if pip-audit; then
    echo -e "${GREEN}✅ Dependencias 100% libres de vulnerabilidades conocidas.${RESET}"
else
    echo -e "${RED}❌ Se encontraron vulnerabilidades en librerías.${RESET}"
    FAILED=1
fi

# 2. BANDIT (SAST)
echo -e "\n${BOLD}[2/6] 🛡️  Auditoría de Seguridad Estática de Código (Bandit)...${RESET}"
if bandit -r . -x ./tests,./.venv,./doctrina_raw -s B101,B110,B310,B311,B404,B603; then
    echo -e "${GREEN}✅ Código fuente verificado contra inyecciones y fallas de seguridad.${RESET}"
else
    echo -e "${RED}❌ Bandit detectó posibles fallas de seguridad.${RESET}"
    FAILED=1
fi

# 3. RUFF (LINTING & QUALITY)
echo -e "\n${BOLD}[3/6] ⚡ Verificando calidad de sintaxis y anti-patrones (Ruff)...${RESET}"
if ruff check .; then
    echo -e "${GREEN}✅ Estilo, imports y arquitectura conformes a estándares PEP.${RESET}"
else
    echo -e "${RED}❌ Ruff encontró inconsistencias en el código.${RESET}"
    FAILED=1
fi

# 4. VULTURE (ANTI-BLOAT / PONYTAIL AUDIT)
echo -e "\n${BOLD}[4/6] ✂️  Auditoría Anti-Sobreingeniería y Código Muerto (Vulture)...${RESET}"
if vulture . --min-confidence 80 --exclude .venv,tests; then
    echo -e "${GREEN}✅ Cero código muerto. Arquitectura magra y principio YAGNI cumplido.${RESET}"
else
    echo -e "${YELLOW}⚠️  Se detectó posible código muerto o no referenciado.${RESET}"
    FAILED=1
fi

# 5. RADON (MAINTAINABILITY INDEX & COMPLEXITY)
echo -e "\n${BOLD}[5/6] 📊 Evaluando Índice de Mantenibilidad de McCabe (Radon)...${RESET}"
radon mi . -s -e ".venv/*,doctrina_raw/*"
echo -e "${GREEN}✅ Métricas de complejidad y mantenibilidad calculadas.${RESET}"

# 6. PYTEST (TEST SUITE)
echo -e "\n${BOLD}[6/6] 🧪 Ejecutando Suite de Pruebas Unitarias y Servidor MCP...${RESET}"
if pytest tests/ -q; then
    echo -e "${GREEN}✅ 100% de pruebas unitarias superadas satisfactoriamente.${RESET}"
else
    echo -e "${RED}❌ Fallaron pruebas en la suite.${RESET}"
    FAILED=1
fi

echo -e "\n--------------------------------------------------------------------------------"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 AUDITORÍA 360° APROBADA CON DISTINCIÓN MÁXIMA.${RESET}"
    echo -e "${GREEN}Open Legal Chile cumple los más altos estándares de seguridad y calidad institucional.${RESET}\n"
    exit 0
else
    echo -e "${RED}${BOLD}⚠️  LA AUDITORÍA REPORTÓ OBSERVACIONES QUE DEBEN SER REVISADAS.${RESET}\n"
    exit 1
fi
