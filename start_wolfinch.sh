#!/bin/bash
#
# Wolfinch Startup Script
# Starts Docker services and runs Wolfinch
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Wolfinch Trading Bot Startup      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed (v2 or v1)
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo -e "${GREEN}✓ Docker Compose found (${DOCKER_COMPOSE_CMD})${NC}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ docker-compose.yml not found${NC}"
    exit 1
fi

# Start Docker services
echo -e "${YELLOW}► Starting Docker services...${NC}"
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be healthy
echo -e "${YELLOW}► Waiting for services to be ready...${NC}"
sleep 5

# Check Redis
echo -n "  Checking Redis... "
if docker exec wolfinch-redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Redis is not responding. Check logs: $DOCKER_COMPOSE_CMD logs redis${NC}"
    exit 1
fi

# Check InfluxDB
echo -n "  Checking InfluxDB... "
if curl -s http://localhost:8086/health | grep -q "pass"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}InfluxDB is not responding. Check logs: $DOCKER_COMPOSE_CMD logs influxdb${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All services are ready!${NC}"
echo ""

# Show service URLs
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Service URLs:${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "  ${GREEN}Redis:${NC}           localhost:6379"
echo -e "  ${GREEN}InfluxDB:${NC}        http://localhost:8086"
echo -e "  ${GREEN}Grafana:${NC}         http://localhost:3000"
echo -e "  ${GREEN}Redis Commander:${NC} http://localhost:8081"
echo -e "  ${GREEN}Wolfinch UI:${NC}     http://localhost:8089/wolfinch"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}► Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirement.txt
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Check if required Python packages are installed
echo -e "${YELLOW}► Checking Python dependencies...${NC}"
if ! python -c "import redis" &> /dev/null; then
    echo "  Installing redis..."
    pip install redis hiredis
fi

if ! python -c "import influxdb_client" &> /dev/null; then
    echo "  Installing influxdb-client..."
    pip install influxdb-client
fi

echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Ask if user wants to start Wolfinch
echo -e "${YELLOW}► Ready to start Wolfinch Trading Bot${NC}"
echo ""
read -p "Start Wolfinch now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${GREEN}Starting Wolfinch...${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    # Start Wolfinch
    ./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
else
    echo ""
    echo -e "${YELLOW}To start Wolfinch manually:${NC}"
    echo "  source venv/bin/activate"
    echo "  ./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml"
    echo ""
    echo -e "${YELLOW}To stop Docker services:${NC}"
    echo "  $DOCKER_COMPOSE_CMD stop"
    echo ""
fi
