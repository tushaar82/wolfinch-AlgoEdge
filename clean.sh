#!/bin/bash
###############################################################################
# Wolfinch AlgoEdge - Clean Script
# Cleans up logs, temporary files, and optionally database
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WOLFINCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${WOLFINCH_DIR}/logs"
DATA_DIR="${WOLFINCH_DIR}/data"
CLEAN_DB="${1:-no}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Wolfinch AlgoEdge - Cleanup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Wolfinch is running
if [ -f "${DATA_DIR}/wolfinch.pid" ]; then
    PID=$(cat "${DATA_DIR}/wolfinch.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} Wolfinch is running. Stop it first with ./stop.sh"
        exit 1
    fi
fi

echo -e "${YELLOW}⚠ This will clean up temporary files and logs${NC}"
if [ "${CLEAN_DB}" = "yes" ] || [ "${CLEAN_DB}" = "y" ]; then
    echo -e "${RED}⚠ WARNING: This will also DELETE all database data!${NC}"
fi
echo ""
read -p "Are you sure? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

# Clean logs
echo -e "${BLUE}[1/4]${NC} Cleaning logs..."
if [ -d "${LOG_DIR}" ]; then
    # Keep last 5 log files
    LOG_COUNT=$(ls -1 "${LOG_DIR}"/*.log 2>/dev/null | wc -l)
    if [ "$LOG_COUNT" -gt 5 ]; then
        ls -1t "${LOG_DIR}"/*.log | tail -n +6 | xargs rm -f
        echo -e "${GREEN}✓${NC} Removed $((LOG_COUNT - 5)) old log files"
    else
        echo -e "${GREEN}✓${NC} No old logs to clean"
    fi
else
    echo -e "${YELLOW}⚠ Log directory not found${NC}"
fi

# Clean temporary files
echo -e "${BLUE}[2/4]${NC} Cleaning temporary files..."
find "${WOLFINCH_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${WOLFINCH_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC} Python cache files cleaned"

# Clean PID file
echo -e "${BLUE}[3/4]${NC} Cleaning PID files..."
rm -f "${DATA_DIR}/wolfinch.pid"
echo -e "${GREEN}✓${NC} PID files removed"

# Clean database if requested
echo -e "${BLUE}[4/4]${NC} Database cleanup..."
if [ "${CLEAN_DB}" = "yes" ] || [ "${CLEAN_DB}" = "y" ]; then
    echo -e "${YELLOW}  Cleaning database data...${NC}"

    # Stop and remove Docker volumes
    if command -v docker-compose &> /dev/null; then
        cd "${WOLFINCH_DIR}"
        docker-compose down -v
        echo -e "${GREEN}✓${NC} Docker volumes removed"
    fi

    # Clean local database files
    rm -rf "${DATA_DIR}/"*.db 2>/dev/null || true
    rm -rf "${DATA_DIR}/"*.sqlite 2>/dev/null || true
    rm -f "${DATA_DIR}/risk_state.json" 2>/dev/null || true

    echo -e "${GREEN}✓${NC} Database cleaned"
else
    echo -e "${GREEN}✓${NC} Database preserved (use './clean.sh yes' to clean)"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Cleanup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
