# Docker Setup for Wolfinch

Complete Docker-based setup with Redis, InfluxDB, and optional monitoring tools.

---

## 🚀 **Quick Start (2 Minutes)**

```bash
# 1. Start all services
cd ~/Projects/wolfinch
docker-compose up -d

# 2. Verify services are running
docker-compose ps

# 3. Install Python dependencies
source venv/bin/activate
pip install redis hiredis influxdb-client

# 4. Run Wolfinch
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

---

## 📦 **What's Included**

| Service | Port | Purpose | UI |
|---------|------|---------|-----|
| **Redis** | 6379 | High-speed cache | Redis Commander (8081) |
| **InfluxDB** | 8086 | Time-series database | Web UI (8086) |
| **Grafana** | 3000 | Visualization | Web UI (3000) |
| **Redis Commander** | 8081 | Redis GUI | Web UI (8081) |

---

## 🛠️ **Services Details**

### **Redis**
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Data**: Persisted in `redis-data` volume
- **Config**: AOF persistence enabled
- **Purpose**: Cache indicators, positions, recent candles

### **InfluxDB**
- **Image**: `influxdb:2.7-alpine`
- **Port**: 8086
- **Data**: Persisted in `influxdb-data` volume
- **Credentials**:
  - Username: `admin`
  - Password: `wolfinch2024`
  - Token: `wolfinch-super-secret-token-change-in-production`
  - Org: `wolfinch`
  - Bucket: `trading`
- **Purpose**: Primary database for all candle data

### **Grafana** (Optional)
- **Image**: `grafana/grafana:latest`
- **Port**: 3000
- **Credentials**:
  - Username: `admin`
  - Password: `admin`
- **Purpose**: Visualize trading data

### **Redis Commander** (Optional)
- **Image**: `rediscommander/redis-commander:latest`
- **Port**: 8081
- **Purpose**: Browse Redis data visually

---

## 📋 **Commands**

### **Start Services**

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d redis
docker-compose up -d influxdb

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f influxdb
```

### **Stop Services**

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop redis

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (⚠️ deletes data!)
docker-compose down -v
```

### **Restart Services**

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart influxdb
```

### **Check Status**

```bash
# List running containers
docker-compose ps

# Check health
docker-compose ps | grep healthy

# View resource usage
docker stats
```

---

## 🔧 **Configuration**

### **Default Configuration**

The `config/cache_db.yml` is pre-configured for Docker services:

```yaml
redis:
  enabled: true
  host: 'localhost'  # Change to 'redis' if Wolfinch runs in Docker
  port: 6379

influxdb:
  enabled: true
  url: 'http://localhost:8086'  # Change to 'http://influxdb:8086' if in Docker
  token: 'wolfinch-super-secret-token-change-in-production'
  org: 'wolfinch'
  bucket: 'trading'
```

### **Change InfluxDB Token**

Edit `docker-compose.yml`:

```yaml
influxdb:
  environment:
    - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=your-new-token-here
```

Then update `config/cache_db.yml`:

```yaml
influxdb:
  token: 'your-new-token-here'
```

### **Change Redis Password**

Edit `docker-compose.yml`:

```yaml
redis:
  command: redis-server --appendonly yes --requirepass yourpassword
```

Then update `config/cache_db.yml`:

```yaml
redis:
  password: 'yourpassword'
```

---

## 🌐 **Access Web UIs**

### **InfluxDB UI**
```
URL: http://localhost:8086
Username: admin
Password: wolfinch2024
```

**What you can do:**
- View stored candles
- Query data with Flux
- Monitor database size
- Create dashboards

### **Grafana**
```
URL: http://localhost:3000
Username: admin
Password: admin
```

**Setup InfluxDB Data Source:**
1. Configuration → Data Sources → Add data source
2. Select InfluxDB
3. Query Language: Flux
4. URL: `http://influxdb:8086`
5. Organization: `wolfinch`
6. Token: `wolfinch-super-secret-token-change-in-production`
7. Default Bucket: `trading`
8. Save & Test

### **Redis Commander**
```
URL: http://localhost:8081
```

**What you can do:**
- Browse Redis keys
- View cached indicators
- Monitor memory usage
- Delete specific keys

---

## 📊 **Verify Data Storage**

### **Check Redis**

```bash
# Connect to Redis
docker exec -it wolfinch-redis redis-cli

# List all keys
KEYS *

# Get specific indicator
GET indicator:papertrader:BANKNIFTY-FUT:EMA:20

# Check memory usage
INFO memory

# Exit
EXIT
```

### **Check InfluxDB**

```bash
# Connect to InfluxDB CLI
docker exec -it wolfinch-influxdb influx

# List buckets
> bucket list

# Query candles
> from(bucket:"trading") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "candle")

# Exit
> exit
```

---

## 🔄 **Data Migration (SQLite → InfluxDB)**

If you have existing SQLite data:

```python
# migration_script.py
from db.candle_db import CandleDB  # Old SQLite
from db.candle_db_influx import CandleDBInflux  # New InfluxDB
from market import OHLC

# Initialize both databases
sqlite_db = CandleDB('papertrader', 'BANKNIFTY-FUT', OHLC)
influx_db = CandleDBInflux('papertrader', 'BANKNIFTY-FUT', OHLC)

# Get all candles from SQLite
candles = sqlite_db.db_get_all_candles()
print(f"Found {len(candles)} candles in SQLite")

# Save to InfluxDB
if candles:
    influx_db.db_save_candles(candles)
    print(f"Migrated {len(candles)} candles to InfluxDB")
```

Run migration:
```bash
python migration_script.py
```

---

## 🧹 **Maintenance**

### **Backup Data**

```bash
# Backup Redis
docker exec wolfinch-redis redis-cli SAVE
docker cp wolfinch-redis:/data/dump.rdb ./backup/redis-backup.rdb

# Backup InfluxDB
docker exec wolfinch-influxdb influx backup /tmp/backup
docker cp wolfinch-influxdb:/tmp/backup ./backup/influxdb-backup
```

### **Restore Data**

```bash
# Restore Redis
docker cp ./backup/redis-backup.rdb wolfinch-redis:/data/dump.rdb
docker-compose restart redis

# Restore InfluxDB
docker cp ./backup/influxdb-backup wolfinch-influxdb:/tmp/backup
docker exec wolfinch-influxdb influx restore /tmp/backup
```

### **Clear All Data**

```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data!)
docker volume rm wolfinch_redis-data
docker volume rm wolfinch_influxdb-data
docker volume rm wolfinch_grafana-data

# Restart fresh
docker-compose up -d
```

### **Update Images**

```bash
# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d --force-recreate
```

---

## 🐛 **Troubleshooting**

### **Services Won't Start**

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs influxdb

# Check if ports are already in use
sudo netstat -tlnp | grep 6379
sudo netstat -tlnp | grep 8086
```

### **InfluxDB Connection Failed**

```bash
# Check if InfluxDB is healthy
docker-compose ps influxdb

# Check health endpoint
curl http://localhost:8086/health

# View InfluxDB logs
docker-compose logs influxdb

# Restart InfluxDB
docker-compose restart influxdb
```

### **Redis Connection Failed**

```bash
# Test Redis
docker exec wolfinch-redis redis-cli ping
# Should return: PONG

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### **Disk Space Issues**

```bash
# Check Docker disk usage
docker system df

# Clean up unused data
docker system prune -a

# Check volume sizes
docker volume ls
du -sh /var/lib/docker/volumes/*
```

---

## 🚀 **Production Deployment**

### **Security Checklist**

- [ ] Change InfluxDB token
- [ ] Set Redis password
- [ ] Use environment variables for secrets
- [ ] Enable TLS/SSL
- [ ] Set up firewall rules
- [ ] Regular backups
- [ ] Monitor disk usage
- [ ] Set up log rotation

### **Performance Tuning**

```yaml
# docker-compose.yml
redis:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G

influxdb:
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

### **High Availability**

For production, consider:
- Redis Sentinel (automatic failover)
- Redis Cluster (horizontal scaling)
- InfluxDB Enterprise (clustering)
- Load balancer
- Multiple Wolfinch instances

---

## 📈 **Monitoring**

### **Resource Usage**

```bash
# Real-time stats
docker stats

# Specific service
docker stats wolfinch-redis wolfinch-influxdb
```

### **Logs**

```bash
# Follow all logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific time range
docker-compose logs --since 30m
```

---

## 🎯 **Next Steps**

1. ✅ Start Docker services
2. ✅ Verify connections
3. ✅ Run Wolfinch
4. ✅ Check data in InfluxDB UI
5. ✅ Set up Grafana dashboards
6. ✅ Monitor performance

---

**Your production-ready Docker environment is ready!** 🐳🚀
