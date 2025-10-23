#!/bin/bash
###############################################################################
# Wolfinch AlgoEdge - Health Check Script
# Monitors system health and displays status
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
WOLFINCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${WOLFINCH_DIR}/data"
LOG_DIR="${WOLFINCH_DIR}/logs"
PID_FILE="${DATA_DIR}/wolfinch.pid"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Wolfinch AlgoEdge - Health Check${NC}"
echo -e "${BLUE}  ${TIMESTAMP}${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

HEALTH_SCORE=0
MAX_SCORE=6

# [1] Check Wolfinch Process
echo -e "${CYAN}[1/6] Wolfinch Process${NC}"
if [ -f "${PID_FILE}" ]; then
    PID=$(cat "${PID_FILE}")
    if ps -p "$PID" > /dev/null 2>&1; then
        UPTIME=$(ps -p "$PID" -o etime= | tr -d ' ')
        MEM=$(ps -p "$PID" -o rss= | awk '{printf "%.1f MB", $1/1024}')
        CPU=$(ps -p "$PID" -o %cpu= | tr -d ' ')
        echo -e "  ${GREEN}✓${NC} Running (PID: ${PID})"
        echo -e "    Uptime: ${UPTIME} | Memory: ${MEM} | CPU: ${CPU}%"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        echo -e "  ${RED}✗${NC} Not running (stale PID: ${PID})"
    fi
else
    echo -e "  ${RED}✗${NC} Not running (no PID file)"
fi
echo ""

# [2] Check Docker Services
echo -e "${CYAN}[2/6] Docker Services${NC}"
if command -v docker-compose &> /dev/null; then
    cd "${WOLFINCH_DIR}"

    # Check Redis
    if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
        REDIS_UPTIME=$(docker-compose ps redis | grep "Up" | awk '{print $4, $5, $6}')
        echo -e "  ${GREEN}✓${NC} Redis: Running (${REDIS_UPTIME})"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        echo -e "  ${RED}✗${NC} Redis: Not running"
    fi

    # Check InfluxDB
    if docker-compose ps influxdb 2>/dev/null | grep -q "Up"; then
        INFLUX_UPTIME=$(docker-compose ps influxdb | grep "Up" | awk '{print $4, $5, $6}')
        echo -e "  ${GREEN}✓${NC} InfluxDB: Running (${INFLUX_UPTIME})"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        echo -e "  ${RED}✗${NC} InfluxDB: Not running"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Docker Compose not available"
fi
echo ""

# [3] Check OpenAlgo Connection
echo -e "${CYAN}[3/6] OpenAlgo Connection${NC}"
if [ -f "${WOLFINCH_DIR}/config/openalgo.yml" ]; then
    OPENALGO_HOST=$(grep -A 5 "hostUrl" "${WOLFINCH_DIR}/config/openalgo.yml" | grep "hostUrl" | cut -d "'" -f 2)
    if [ -n "${OPENALGO_HOST}" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${OPENALGO_HOST}" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
            echo -e "  ${GREEN}✓${NC} Reachable: ${OPENALGO_HOST} (HTTP ${HTTP_CODE})"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo -e "  ${RED}✗${NC} Unreachable: ${OPENALGO_HOST} (HTTP ${HTTP_CODE})"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} OpenAlgo host not configured"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} OpenAlgo config not found"
fi
echo ""

# [4] Check Disk Space
echo -e "${CYAN}[4/6] Disk Space${NC}"
DISK_USAGE=$(df -h "${WOLFINCH_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h "${WOLFINCH_DIR}" | awk 'NR==2 {print $4}')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "  ${GREEN}✓${NC} Available: ${DISK_AVAIL} (${DISK_USAGE}% used)"
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "  ${YELLOW}⚠${NC} Available: ${DISK_AVAIL} (${DISK_USAGE}% used) - Running low"
else
    echo -e "  ${RED}✗${NC} Available: ${DISK_AVAIL} (${DISK_USAGE}% used) - Critical!"
fi
echo ""

# [5] Check Recent Logs
echo -e "${CYAN}[5/6] Recent Logs${NC}"
if [ -d "${LOG_DIR}" ]; then
    LATEST_LOG=$(ls -t "${LOG_DIR}"/*.log 2>/dev/null | head -1)
    if [ -n "${LATEST_LOG}" ]; then
        LOG_SIZE=$(du -h "${LATEST_LOG}" | cut -f1)
        LOG_ERRORS=$(grep -i "error\|critical\|fatal" "${LATEST_LOG}" 2>/dev/null | wc -l)
        LOG_WARNINGS=$(grep -i "warning" "${LATEST_LOG}" 2>/dev/null | wc -l)

        echo -e "  ${GREEN}✓${NC} Latest: $(basename "${LATEST_LOG}") (${LOG_SIZE})"
        if [ "$LOG_ERRORS" -eq 0 ]; then
            echo -e "    Errors: ${GREEN}0${NC} | Warnings: ${YELLOW}${LOG_WARNINGS}${NC}"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo -e "    Errors: ${RED}${LOG_ERRORS}${NC} | Warnings: ${YELLOW}${LOG_WARNINGS}${NC}"
        fi

        echo -e "\n  ${CYAN}Last 3 log entries:${NC}"
        tail -3 "${LATEST_LOG}" | sed 's/^/    /'
    else
        echo -e "  ${YELLOW}⚠${NC} No log files found"
    fi
else
    echo -e "  ${RED}✗${NC} Log directory not found"
fi
echo ""

# [6] Check Risk Management Status
echo -e "${CYAN}[6/6] Risk Management${NC}"
RISK_STATE_FILE="${DATA_DIR}/risk_state.json"
if [ -f "${RISK_STATE_FILE}" ]; then
    DAILY_PNL=$(jq -r '.daily_pnl' "${RISK_STATE_FILE}" 2>/dev/null || echo "N/A")
    OPEN_POSITIONS=$(jq -r '.open_positions | length' "${RISK_STATE_FILE}" 2>/dev/null || echo "N/A")
    BLOCKED=$(jq -r '.blocked' "${RISK_STATE_FILE}" 2>/dev/null || echo "false")

    if [ "$BLOCKED" = "false" ]; then
        echo -e "  ${GREEN}✓${NC} Trading: Active"
    else
        BLOCK_REASON=$(jq -r '.block_reason' "${RISK_STATE_FILE}" 2>/dev/null || echo "Unknown")
        echo -e "  ${RED}✗${NC} Trading: Blocked (${BLOCK_REASON})"
    fi

    echo -e "    Daily P&L: ₹${DAILY_PNL} | Open Positions: ${OPEN_POSITIONS}"
else
    echo -e "  ${YELLOW}⚠${NC} Risk state file not found"
fi
echo ""

# Calculate health percentage
HEALTH_PERCENT=$((HEALTH_SCORE * 100 / MAX_SCORE))

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Health Score: ${HEALTH_SCORE}/${MAX_SCORE} (${HEALTH_PERCENT}%)${NC}"

if [ "$HEALTH_PERCENT" -ge 80 ]; then
    echo -e "${GREEN}  Status: HEALTHY ✓${NC}"
elif [ "$HEALTH_PERCENT" -ge 50 ]; then
    echo -e "${YELLOW}  Status: DEGRADED ⚠${NC}"
else
    echo -e "${RED}  Status: CRITICAL ✗${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

exit 0
