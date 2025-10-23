#!/bin/bash
###############################################################################
# Wolfinch AlgoEdge - Start Script
# Starts all required services and the trading bot
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WOLFINCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${WOLFINCH_DIR}/logs"
DATA_DIR="${WOLFINCH_DIR}/data"
PID_FILE="${DATA_DIR}/wolfinch.pid"
CONFIG_FILE="${1:-config/wolfinch_openalgo_nifty.yml}"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${DATA_DIR}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Wolfinch AlgoEdge - Professional Trading System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if already running
if [ -f "${PID_FILE}" ]; then
    PID=$(cat "${PID_FILE}")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Wolfinch is already running (PID: ${PID})${NC}"
        echo -e "${YELLOW}  Use ./stop.sh to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ Removing stale PID file${NC}"
        rm -f "${PID_FILE}"
    fi
fi

# Check Python version
echo -e "${BLUE}[1/6]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION}"

# Check dependencies
echo -e "${BLUE}[2/6]${NC} Checking dependencies..."
if ! python3 -c "import openalgo" 2>/dev/null; then
    echo -e "${YELLOW}⚠ OpenAlgo not found. Installing dependencies...${NC}"
    pip install -r requirement.txt --quiet
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} All dependencies present"
fi

# Start Docker services (Redis, InfluxDB)
echo -e "${BLUE}[3/6]${NC} Starting Docker services..."
if command -v docker-compose &> /dev/null; then
    cd "${WOLFINCH_DIR}"
    docker-compose up -d redis influxdb 2>&1 | grep -v "is up-to-date" || true
    echo -e "${GREEN}✓${NC} Docker services started"

    # Wait for services to be ready
    echo -e "${BLUE}     ${NC} Waiting for services to be ready..."
    sleep 3

    # Check Redis
    if docker-compose ps redis | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} Redis is running"
    else
        echo -e "${RED}✗${NC} Redis failed to start"
    fi

    # Check InfluxDB
    if docker-compose ps influxdb | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} InfluxDB is running"
    else
        echo -e "${RED}✗${NC} InfluxDB failed to start"
    fi
else
    echo -e "${YELLOW}⚠ Docker Compose not found. Make sure Redis and InfluxDB are running${NC}"
fi

# Validate configuration
echo -e "${BLUE}[4/6]${NC} Validating configuration..."
if [ ! -f "${WOLFINCH_DIR}/${CONFIG_FILE}" ]; then
    echo -e "${RED}✗${NC} Configuration file not found: ${CONFIG_FILE}"
    echo -e "${YELLOW}  Available configs:${NC}"
    ls -1 "${WOLFINCH_DIR}/config/"*.yml | xargs -n 1 basename
    exit 1
fi
echo -e "${GREEN}✓${NC} Configuration file: ${CONFIG_FILE}"

# Check OpenAlgo connection
echo -e "${BLUE}[5/6]${NC} Checking OpenAlgo connection..."
OPENALGO_HOST=$(grep -A 5 "hostUrl" "${WOLFINCH_DIR}/config/openalgo.yml" | grep "hostUrl" | cut -d "'" -f 2)
if [ -n "${OPENALGO_HOST}" ]; then
    if curl -s -o /dev/null -w "%{http_code}" "${OPENALGO_HOST}" | grep -q "200\|404"; then
        echo -e "${GREEN}✓${NC} OpenAlgo is reachable at ${OPENALGO_HOST}"
    else
        echo -e "${YELLOW}⚠ Cannot reach OpenAlgo at ${OPENALGO_HOST}${NC}"
        echo -e "${YELLOW}  Make sure OpenAlgo is running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ OpenAlgo host not configured${NC}"
fi

# Start Wolfinch
echo -e "${BLUE}[6/6]${NC} Starting Wolfinch trading bot..."
cd "${WOLFINCH_DIR}"

# Set log file with timestamp
LOG_FILE="${LOG_DIR}/wolfinch_$(date +%Y%m%d_%H%M%S).log"

# Start Wolfinch in background
nohup python3 Wolfinch.py --config "${CONFIG_FILE}" > "${LOG_FILE}" 2>&1 &
WOLFINCH_PID=$!

# Save PID
echo "${WOLFINCH_PID}" > "${PID_FILE}"

# Wait a moment and check if it's still running
sleep 2
if ps -p "${WOLFINCH_PID}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Wolfinch started successfully (PID: ${WOLFINCH_PID})"
    echo -e "${GREEN}✓${NC} Log file: ${LOG_FILE}"
else
    echo -e "${RED}✗${NC} Wolfinch failed to start. Check logs:"
    tail -20 "${LOG_FILE}"
    rm -f "${PID_FILE}"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Wolfinch AlgoEdge Started Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  📊 Dashboard: ${BLUE}http://localhost:8080${NC}"
echo -e "  📝 Logs: ${BLUE}tail -f ${LOG_FILE}${NC}"
echo -e "  ❤️  Health: ${BLUE}./health.sh${NC}"
echo -e "  🛑 Stop: ${BLUE}./stop.sh${NC}"
echo ""
echo -e "${YELLOW}  ⚡ Happy Trading! ⚡${NC}"
echo ""
