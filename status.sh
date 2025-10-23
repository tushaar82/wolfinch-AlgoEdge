#!/bin/bash
# Wolfinch AlgoEdge - System Status Script
# Quick status check for all services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
}

check_service() {
    local service_name=$1
    local check_command=$2
    
    if eval $check_command > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $service_name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $service_name"
        return 1
    fi
}

clear
print_header "Wolfinch AlgoEdge - System Status"
echo ""

# Check Wolfinch
echo -e "${BLUE}Wolfinch Application:${NC}"
if [ -f "wolfinch.pid" ]; then
    PID=$(cat wolfinch.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Running (PID: $PID)"
        
        # Check metrics endpoint
        if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Metrics endpoint responding"
        else
            echo -e "  ${YELLOW}⚠${NC} Metrics endpoint not responding"
        fi
    else
        echo -e "  ${RED}✗${NC} Not running (stale PID file)"
    fi
elif [ -f "data/wolfinch.pid" ]; then
    PID=$(cat data/wolfinch.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Running (PID: $PID)"
    else
        echo -e "  ${RED}✗${NC} Not running (stale PID file)"
    fi
else
    echo -e "  ${RED}✗${NC} Not running"
fi
echo ""

# Check Docker services
echo -e "${BLUE}Docker Services:${NC}"
check_service "Redis" "redis-cli -h localhost -p 6380 ping"
check_service "PostgreSQL" "docker exec wolfinch-postgres pg_isready -U wolfinch"
check_service "InfluxDB" "curl -s http://localhost:8087/health"
check_service "Kafka" "docker exec wolfinch-kafka kafka-broker-api-versions --bootstrap-server localhost:9092"
check_service "Zookeeper" "docker exec wolfinch-zookeeper nc -z localhost 2181"
check_service "Prometheus" "curl -s http://localhost:9090/-/healthy"
check_service "Grafana" "curl -s http://localhost:3001/api/health"
check_service "Redis Exporter" "curl -s http://localhost:9121/metrics"
check_service "PostgreSQL Exporter" "curl -s http://localhost:9187/metrics"
echo ""

# Check ports
echo -e "${BLUE}Port Status:${NC}"
check_service "Redis (6380)" "nc -z localhost 6380"
check_service "PostgreSQL (5432)" "nc -z localhost 5432"
check_service "InfluxDB (8087)" "nc -z localhost 8087"
check_service "Kafka (9094)" "nc -z localhost 9094"
check_service "Grafana (3001)" "nc -z localhost 3001"
check_service "Prometheus (9090)" "nc -z localhost 9090"
check_service "Wolfinch Metrics (8000)" "nc -z localhost 8000"
echo ""

# Quick stats
echo -e "${BLUE}Quick Statistics:${NC}"

# Docker container count
RUNNING_CONTAINERS=$(docker ps --filter "name=wolfinch-" --format "{{.Names}}" | wc -l)
echo -e "  Running containers: ${GREEN}$RUNNING_CONTAINERS${NC}"

# Disk usage
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
echo -e "  Disk usage: ${YELLOW}$DISK_USAGE${NC}"

# Memory usage
if command -v free &> /dev/null; then
    MEM_USAGE=$(free -h | awk 'NR==2 {print $3 "/" $2}')
    echo -e "  Memory usage: ${YELLOW}$MEM_USAGE${NC}"
fi

echo ""

# Access URLs
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  Grafana:     ${GREEN}http://localhost:3001${NC} (admin/wolfinch2024)"
echo -e "  Prometheus:  ${GREEN}http://localhost:9090${NC}"
echo -e "  Kafka UI:    ${GREEN}http://localhost:8090${NC}"
echo -e "  Metrics:     ${GREEN}http://localhost:8000/metrics${NC}"
echo ""

# Recent logs
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/wolfinch_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo -e "${BLUE}Latest Log File:${NC}"
        echo -e "  $LATEST_LOG"
        echo -e "  Last 5 lines:"
        tail -5 "$LATEST_LOG" 2>/dev/null | sed 's/^/    /'
    fi
fi

echo ""
print_header "Status Check Complete"
