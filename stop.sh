#!/bin/bash
###############################################################################
# Wolfinch AlgoEdge - Stop Script
# Gracefully stops the trading bot and optionally Docker services
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
DATA_DIR="${WOLFINCH_DIR}/data"
PID_FILE="${DATA_DIR}/wolfinch.pid"
STOP_DOCKER="${1:-no}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Wolfinch AlgoEdge - Graceful Shutdown${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if PID file exists
if [ ! -f "${PID_FILE}" ]; then
    echo -e "${YELLOW}⚠ Wolfinch is not running (no PID file)${NC}"
    PID=0
else
    PID=$(cat "${PID_FILE}")

    # Check if process is actually running
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Wolfinch process not found (PID: ${PID})${NC}"
        rm -f "${PID_FILE}"
        PID=0
    fi
fi

# Stop Wolfinch if running
if [ "$PID" -gt 0 ]; then
    echo -e "${BLUE}[1/2]${NC} Stopping Wolfinch (PID: ${PID})..."

    # Send SIGTERM for graceful shutdown
    kill -TERM "$PID" 2>/dev/null || true

    # Wait for process to exit (max 30 seconds)
    WAIT_TIME=0
    while ps -p "$PID" > /dev/null 2>&1 && [ $WAIT_TIME -lt 30 ]; do
        sleep 1
        WAIT_TIME=$((WAIT_TIME + 1))
        echo -ne "${YELLOW}  Waiting for graceful shutdown... ${WAIT_TIME}s${NC}\r"
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "\n${YELLOW}⚠ Forcefully killing process...${NC}"
        kill -KILL "$PID" 2>/dev/null || true
        sleep 1
    fi

    # Verify process stopped
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓${NC} Wolfinch stopped successfully"
        rm -f "${PID_FILE}"
    else
        echo -e "\n${RED}✗${NC} Failed to stop Wolfinch"
        exit 1
    fi
else
    echo -e "${BLUE}[1/2]${NC} Wolfinch is not running"
fi

# Stop Docker services if requested
echo -e "${BLUE}[2/2]${NC} Docker services..."
if [ "${STOP_DOCKER}" = "yes" ] || [ "${STOP_DOCKER}" = "y" ]; then
    if command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}  Stopping Docker services...${NC}"
        cd "${WOLFINCH_DIR}"
        docker-compose down
        echo -e "${GREEN}✓${NC} Docker services stopped"
    else
        echo -e "${YELLOW}⚠ Docker Compose not found${NC}"
    fi
else
    echo -e "${GREEN}✓${NC} Keeping Docker services running (use './stop.sh yes' to stop)"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Wolfinch AlgoEdge Stopped${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
