# Redis + InfluxDB Quick Start (5 Minutes)

Get Redis and InfluxDB running with Wolfinch in 5 minutes using Docker.

---

## 🚀 **Fastest Setup (Docker)**

### **1. Start Redis & InfluxDB**

```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:latest

# Start InfluxDB
docker run -d --name influxdb \
  -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \
  -e DOCKER_INFLUXDB_INIT_ORG=wolfinch \
  -e DOCKER_INFLUXDB_INIT_BUCKET=trading \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
  influxdb:latest

# Verify
docker ps  # Should see both containers running
```

### **2. Install Python Packages**

```bash
cd ~/Projects/wolfinch
source venv/bin/activate
pip install redis hiredis influxdb-client
```

### **3. Configure Wolfinch**

Edit `config/cache_db.yml`:

```yaml
redis:
  enabled: true
  host: 'localhost'
  port: 6379

influxdb:
  enabled: true
  url: 'http://localhost:8086'
  token: 'my-super-secret-auth-token'  # ← Token from docker command
  org: 'wolfinch'
  bucket: 'trading'
```

### **4. Run Wolfinch**

```bash
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml

# Look for these lines:
# [INFO:RedisCache] Redis connected: localhost:6379 db=0
# [INFO:InfluxDB] InfluxDB connected: http://localhost:8086
```

### **5. Verify It's Working**

```bash
# Check Redis
redis-cli
> KEYS *
> GET indicator:papertrader:BANKNIFTY-FUT:EMA:20
> EXIT

# Check InfluxDB
# Open browser: http://localhost:8086
# Login: admin / adminpassword
# Data Explorer → Query Builder → Select "candle" measurement
```

---

## ✅ **Done!**

You now have:
- ✅ Redis caching (50-100x faster indicator lookups)
- ✅ InfluxDB time-series storage (optimized for candles)
- ✅ Production-ready architecture

---

## 🛑 **Stop Services**

```bash
# Stop containers
docker stop redis influxdb

# Remove containers
docker rm redis influxdb

# Remove data (optional)
docker volume prune
```

---

## 🔧 **Optional: Without Docker**

### **Ubuntu/Debian**

```bash
# Redis
sudo apt install redis-server
sudo systemctl start redis-server

# InfluxDB
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c
cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo apt update && sudo apt install influxdb2
sudo systemctl start influxdb

# Setup InfluxDB
influx setup --username admin --password adminpassword --org wolfinch --bucket trading --force
influx auth list  # Get your token
```

### **macOS**

```bash
# Redis
brew install redis
brew services start redis

# InfluxDB
brew install influxdb
brew services start influxdb

# Setup InfluxDB (open http://localhost:8086 in browser)
```

---

## 📊 **Performance Test**

```python
# Test Redis speed
import time
from db.redis_cache import get_redis_cache

redis = get_redis_cache()

# Write test
start = time.time()
for i in range(1000):
    redis.set(f"test:{i}", i)
print(f"Redis: 1000 writes in {time.time() - start:.3f}s")

# Read test
start = time.time()
for i in range(1000):
    redis.get(f"test:{i}")
print(f"Redis: 1000 reads in {time.time() - start:.3f}s")

# Expected: ~0.1-0.2 seconds for both (5000-10000 ops/sec)
```

---

## 🎯 **What's Next?**

1. **Monitor performance** - Check Redis hit rates
2. **Tune configuration** - Adjust TTL values
3. **Scale up** - Add more products/strategies
4. **Production deploy** - Use Redis Cluster + InfluxDB Cloud

See **REDIS_INFLUXDB_SETUP.md** for detailed documentation.

---

**Enjoy the speed boost!** ⚡🚀
