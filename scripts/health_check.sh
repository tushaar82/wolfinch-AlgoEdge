#!/bin/bash
# Comprehensive health check for all Wolfinch services

echo "=== Wolfinch Health Check ==="
echo ""

# Check Docker services
echo "Checking Docker services..."
docker-compose ps

# Check Redis
echo ""
echo "Checking Redis..."
redis-cli -h localhost -p 6380 ping 2>/dev/null && echo "✓ Redis is healthy" || echo "✗ Redis not responding"

# Check InfluxDB
echo ""
echo "Checking InfluxDB..."
curl -s http://localhost:8087/health 2>/dev/null && echo "✓ InfluxDB is healthy" || echo "✗ InfluxDB not responding"

# Check PostgreSQL
echo ""
echo "Checking PostgreSQL..."
PGPASSWORD=wolfinch2024 psql -h localhost -p 5432 -U wolfinch -d wolfinch -c "SELECT 1;" >/dev/null 2>&1 && echo "✓ PostgreSQL is healthy" || echo "✗ PostgreSQL not responding"

# Check Kafka
echo ""
echo "Checking Kafka..."
docker exec wolfinch-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >/dev/null 2>&1 && echo "✓ Kafka is healthy" || echo "✗ Kafka not responding"

# Check Prometheus
echo ""
echo "Checking Prometheus..."
curl -s http://localhost:9090/-/healthy 2>/dev/null && echo "✓ Prometheus is healthy" || echo "✗ Prometheus not responding"

# Check Grafana
echo ""
echo "Checking Grafana..."
curl -s http://localhost:3001/api/health 2>/dev/null && echo "✓ Grafana is healthy" || echo "✗ Grafana not responding"

# Check Wolfinch metrics endpoint
echo ""
echo "Checking Wolfinch metrics..."
curl -s http://localhost:8000/metrics 2>/dev/null | head -n 5 >/dev/null && echo "✓ Wolfinch metrics available" || echo "✗ Wolfinch metrics not available"

echo ""
echo "=== Health Check Complete ==="
