#!/bin/bash
# Wolfinch AlgoEdge - Complete System Startup Script
# This script starts all infrastructure services and the Wolfinch trading application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WOLFINCH_CONFIG="${WOLFINCH_CONFIG:-config/wolfinch_openalgo_nifty.yml}"
VENV_PATH="venv"
LOG_DIR="logs"
MAX_WAIT=120  # Maximum wait time for services (seconds)

# Functions
print_header() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose (both standalone and plugin versions)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
        print_success "Docker Compose is installed (standalone)"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
        print_success "Docker Compose is installed (plugin)"
    else
        print_error "Docker Compose is not installed"
        echo ""
        print_info "Install Docker Compose:"
        echo "  Ubuntu/Debian: sudo apt-get install docker-compose-plugin"
        echo "  Or visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 is installed"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your credentials before running again"
            exit 1
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi
    print_success ".env file exists"
    
    echo ""
}

setup_python_environment() {
    print_header "Setting Up Python Environment"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv $VENV_PATH
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source $VENV_PATH/bin/activate
    print_success "Virtual environment activated"
    
    # Install/upgrade dependencies
    print_info "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirement.txt
    print_success "Python dependencies installed"
    
    echo ""
}

start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    # Stop any existing containers
    print_info "Stopping existing containers..."
    $DOCKER_COMPOSE_CMD down > /dev/null 2>&1 || true
    
    # Start all services
    print_info "Starting Docker services..."
    $DOCKER_COMPOSE_CMD up -d
    
    echo ""
    print_info "Waiting for services to be healthy..."
    sleep 5
    
    # Wait for services
    wait_for_service "Redis" "redis" "redis-cli -h localhost -p 6380 ping" 30
    wait_for_service "PostgreSQL" "postgres" "docker exec wolfinch-postgres pg_isready -U wolfinch" 30
    wait_for_service "InfluxDB" "influxdb" "curl -s http://localhost:8087/health" 30
    wait_for_service "Kafka" "kafka" "docker exec wolfinch-kafka kafka-broker-api-versions --bootstrap-server localhost:9092" 30
    wait_for_service "Prometheus" "prometheus" "curl -s http://localhost:9090/-/healthy" 30
    wait_for_service "Grafana" "grafana" "curl -s http://localhost:3001/api/health" 30
    
    echo ""
}

wait_for_service() {
    local service_name=$1
    local container_name=$2
    local health_check=$3
    local timeout=$4
    local elapsed=0
    
    print_info "Waiting for $service_name..."
    
    while [ $elapsed -lt $timeout ]; do
        if eval $health_check > /dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    print_warning "$service_name is not responding (timeout after ${timeout}s)"
    return 1
}

verify_services() {
    print_header "Verifying Service Health"
    
    # Run health check script if it exists
    if [ -f "scripts/health_check.sh" ]; then
        bash scripts/health_check.sh
    else
        # Manual health checks
        check_service_health "Redis" "redis-cli -h localhost -p 6380 ping"
        check_service_health "PostgreSQL" "docker exec wolfinch-postgres pg_isready -U wolfinch"
        check_service_health "InfluxDB" "curl -s http://localhost:8087/health"
        check_service_health "Kafka" "docker exec wolfinch-kafka kafka-topics --bootstrap-server localhost:9092 --list"
        check_service_health "Prometheus" "curl -s http://localhost:9090/-/healthy"
        check_service_health "Grafana" "curl -s http://localhost:3001/api/health"
    fi
    
    echo ""
}

check_service_health() {
    local service_name=$1
    local health_check=$2
    
    if eval $health_check > /dev/null 2>&1; then
        print_success "$service_name is healthy"
    else
        print_error "$service_name health check failed"
    fi
}

start_wolfinch() {
    print_header "Starting Wolfinch Trading Application"
    
    # Create logs directory if it doesn't exist
    mkdir -p $LOG_DIR
    
    # Check if config file exists
    if [ ! -f "$WOLFINCH_CONFIG" ]; then
        print_error "Configuration file not found: $WOLFINCH_CONFIG"
        print_info "Available configurations:"
        ls -1 config/wolfinch_*.yml 2>/dev/null || echo "  No configurations found"
        exit 1
    fi
    
    print_info "Using configuration: $WOLFINCH_CONFIG"
    
    # Start Wolfinch in background
    print_info "Starting Wolfinch..."
    
    # Activate virtual environment
    source $VENV_PATH/bin/activate
    
    # Start Wolfinch
    nohup python Wolfinch.py --config $WOLFINCH_CONFIG > $LOG_DIR/wolfinch_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    WOLFINCH_PID=$!
    
    echo $WOLFINCH_PID > wolfinch.pid
    print_success "Wolfinch started (PID: $WOLFINCH_PID)"
    
    # Wait a bit and check if it's still running
    sleep 5
    if ps -p $WOLFINCH_PID > /dev/null; then
        print_success "Wolfinch is running"
    else
        print_error "Wolfinch failed to start. Check logs in $LOG_DIR"
        exit 1
    fi
    
    echo ""
}

display_access_info() {
    print_header "System Access Information"
    
    echo -e "${GREEN}Infrastructure Services:${NC}"
    echo "  • Redis:              redis://localhost:6380"
    echo "  • PostgreSQL:         postgresql://localhost:5432/wolfinch"
    echo "  • InfluxDB:           http://localhost:8087"
    echo "  • Kafka:              localhost:9094"
    echo "  • Zookeeper:          localhost:2182"
    echo ""
    
    echo -e "${GREEN}Monitoring & Visualization:${NC}"
    echo "  • Grafana:            http://localhost:3001 (admin/wolfinch2024)"
    echo "  • Prometheus:         http://localhost:9090"
    echo "  • Alertmanager:       http://localhost:9093"
    echo "  • Wolfinch Metrics:   http://localhost:8000/metrics"
    echo ""
    
    echo -e "${GREEN}Management UIs:${NC}"
    echo "  • Redis Commander:    http://localhost:8081"
    echo "  • Kafka UI:           http://localhost:8090"
    echo ""
    
    echo -e "${GREEN}Grafana Dashboards:${NC}"
    echo "  • Trading Dashboard:  http://localhost:3001/d/wolfinch-trading"
    echo "  • System Dashboard:   http://localhost:3001/d/wolfinch-system"
    echo ""
    
    echo -e "${GREEN}Logs:${NC}"
    echo "  • Wolfinch Logs:      $LOG_DIR/wolfinch_*.log"
    echo "  • Docker Logs:        docker-compose logs -f <service>"
    echo ""
    
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo "  • View Wolfinch logs: tail -f $LOG_DIR/wolfinch_*.log"
    echo "  • Stop system:        ./stop.sh"
    echo "  • Health check:       ./scripts/health_check.sh"
    echo "  • View metrics:       curl http://localhost:8000/metrics"
    echo ""
}

display_status() {
    print_header "System Status"
    
    echo -e "${GREEN}Docker Services:${NC}"
    $DOCKER_COMPOSE_CMD ps
    echo ""
    
    if [ -f wolfinch.pid ]; then
        WOLFINCH_PID=$(cat wolfinch.pid)
        if ps -p $WOLFINCH_PID > /dev/null; then
            echo -e "${GREEN}Wolfinch Status:${NC} Running (PID: $WOLFINCH_PID)"
        else
            echo -e "${RED}Wolfinch Status:${NC} Not Running"
        fi
    else
        echo -e "${YELLOW}Wolfinch Status:${NC} Unknown (no PID file)"
    fi
    echo ""
}

# Main execution
main() {
    clear
    
    print_header "Wolfinch AlgoEdge - Complete System Startup"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup Python environment
    setup_python_environment
    
    # Start infrastructure
    start_infrastructure
    
    # Verify services
    verify_services
    
    # Start Wolfinch
    start_wolfinch
    
    # Display status
    display_status
    
    # Display access information
    display_access_info
    
    print_header "System Startup Complete!"
    print_success "All services are running"
    print_info "Monitor the system at: http://localhost:3001 (Grafana)"
    
    echo ""
    print_info "Press Ctrl+C to stop monitoring logs, or run './stop.sh' to stop all services"
    echo ""
    
    # Tail logs
    if [ -f wolfinch.pid ]; then
        LATEST_LOG=$(ls -t $LOG_DIR/wolfinch_*.log | head -1)
        if [ -f "$LATEST_LOG" ]; then
            print_info "Tailing Wolfinch logs (Ctrl+C to stop)..."
            tail -f $LATEST_LOG
        fi
    fi
}

# Run main function
main
