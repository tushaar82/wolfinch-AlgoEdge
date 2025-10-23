# Troubleshooting Guide: No Data in InfluxDB/Grafana

Complete guide to fix common issues with InfluxDB, Redis, and Grafana integration.

---

## ✅ **Issue Fixed!**

### **Problem**
- No data in InfluxDB
- No dashboards in Grafana
- Redis not being used

### **Root Cause**
The main configuration file wasn't referencing `cache_db.yml`, so InfluxDB and Redis weren't being initialized.

### **Solution**
Added to `config/wolfinch_papertrader_nse_banknifty.yml`:
```yaml
# Cache and Database Configuration
cache_db:
   config: 'config/cache_db.yml'
```

---

## 🔍 **Verification Steps**

### **1. Check Services Are Running**

```bash
docker compose ps
```

**Expected output:**
```
NAME                  STATUS
wolfinch-redis        Up (healthy)
wolfinch-influxdb     Up (healthy)
wolfinch-grafana      Up
wolfinch-redis-commander  Up (healthy)
```

### **2. Test Redis Connection**

```bash
docker exec wolfinch-redis redis-cli ping
```

**Expected:** `PONG`

### **3. Test InfluxDB Connection**

```bash
curl http://localhost:8086/health
```

**Expected:** `{"status":"pass"}`

### **4. Run Test Script**

```bash
source venv/bin/activate
python test_influxdb_redis.py
```

**Expected:**
```
✓ Redis connected
✓ InfluxDB connected
✓ CandleDBInflux initialized
✓ All systems operational!
```

### **5. Start Wolfinch**

```bash
./start_wolfinch.sh
# OR
source venv/bin/activate
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

**Look for these log messages:**
```
[INFO:Wolfinch] Redis cache initialized
[INFO:Wolfinch] InfluxDB initialized
[INFO:MARKET] Using InfluxDB for papertrader:BANKNIFTY-FUT
[INFO:UI-DB] Using InfluxDB for candle data
```

### **6. Verify Data in InfluxDB**

```bash
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> count()' \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production
```

**Expected:** Should show count of data points

---

## 🐛 **Common Issues**

### **Issue 1: Services Not Starting**

**Symptoms:**
```bash
docker compose ps
# Shows "Exited" or "Restarting"
```

**Solution:**
```bash
# Check logs
docker compose logs redis
docker compose logs influxdb

# Restart services
docker compose restart

# If that doesn't work, recreate
docker compose down
docker compose up -d
```

---

### **Issue 2: InfluxDB Connection Refused**

**Symptoms:**
```
[ERROR] InfluxDB connection failed
```

**Solution:**
```bash
# 1. Check if InfluxDB is running
docker compose ps influxdb

# 2. Check health
curl http://localhost:8086/health

# 3. Check logs
docker compose logs influxdb

# 4. Restart InfluxDB
docker compose restart influxdb

# 5. Wait for it to be healthy
watch -n 1 'docker compose ps influxdb'
```

---

### **Issue 3: Redis Connection Failed**

**Symptoms:**
```
[ERROR] Redis connection failed
```

**Solution:**
```bash
# 1. Check if Redis is running
docker compose ps redis

# 2. Test connection
docker exec wolfinch-redis redis-cli ping

# 3. Check logs
docker compose logs redis

# 4. Restart Redis
docker compose restart redis
```

---

### **Issue 4: Wolfinch Not Using InfluxDB**

**Symptoms:**
```
[INFO:MARKET] Using SQLite for papertrader:BANKNIFTY-FUT
```

**Solution:**

**Check 1: Config file has cache_db reference**
```bash
grep -A 2 "cache_db:" config/wolfinch_papertrader_nse_banknifty.yml
```

Should show:
```yaml
cache_db:
   config: 'config/cache_db.yml'
```

**Check 2: cache_db.yml exists and is correct**
```bash
cat config/cache_db.yml | grep -A 5 "influxdb:"
```

Should show:
```yaml
influxdb:
  enabled: true
  url: 'http://localhost:8086'
  token: 'wolfinch-super-secret-token-change-in-production'
  org: 'wolfinch'
  bucket: 'trading'
```

**Check 3: Python packages installed**
```bash
source venv/bin/activate
pip list | grep -E "(redis|influxdb)"
```

Should show:
```
influxdb-client    1.38.0
redis              5.0.0
hiredis            2.2.0
```

If missing:
```bash
pip install redis hiredis influxdb-client
```

---

### **Issue 5: No Data in InfluxDB After Running Wolfinch**

**Symptoms:**
- Wolfinch runs without errors
- But InfluxDB query returns no data

**Solution:**

**Check 1: Wolfinch is actually generating candles**
```bash
# Look for log messages like:
# "Generated 5000 random candles for BANKNIFTY-FUT"
# "Imported Historic rates #num Candles (5000)"
```

**Check 2: Check if data is being written**
```bash
# In Wolfinch logs, look for:
grep "Wrote.*candles" wolfinch.log
```

**Check 3: Query InfluxDB directly**
```bash
docker exec -it wolfinch-influxdb influx

# Inside InfluxDB CLI:
> from(bucket:"trading") 
  |> range(start: -24h) 
  |> filter(fn: (r) => r._measurement == "candle")
  |> count()
```

**Check 4: Verify bucket exists**
```bash
docker exec wolfinch-influxdb influx bucket list \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production
```

---

### **Issue 6: Grafana Has No Dashboards**

**This is NORMAL!** Grafana starts empty. You need to create dashboards.

**Solution:**

**Step 1: Add InfluxDB Data Source**

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Configuration → Data Sources → Add data source
4. Select "InfluxDB"
5. Configure:
   - **Query Language:** Flux
   - **URL:** `http://influxdb:8086`
   - **Organization:** `wolfinch`
   - **Token:** `wolfinch-super-secret-token-change-in-production`
   - **Default Bucket:** `trading`
6. Click "Save & Test"

**Step 2: Create Dashboard**

1. Click "+" → Dashboard
2. Add Panel
3. Query:
```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "candle")
  |> filter(fn: (r) => r.product == "BANKNIFTY-FUT")
  |> filter(fn: (r) => r._field == "close")
```
4. Visualization: Time series
5. Title: "Bank Nifty Price"
6. Save Dashboard

---

### **Issue 7: Port Already in Use**

**Symptoms:**
```
Error: bind: address already in use
```

**Solution:**

**Find what's using the port:**
```bash
# For InfluxDB (8086)
sudo lsof -i :8086

# For Redis (6379)
sudo lsof -i :6379

# For Grafana (3000)
sudo lsof -i :3000
```

**Option 1: Stop the conflicting service**
```bash
sudo systemctl stop influxdb
sudo systemctl stop redis
```

**Option 2: Change ports in docker-compose.yml**
```yaml
influxdb:
  ports:
    - "8087:8086"  # Use 8087 instead of 8086
```

Then update `config/cache_db.yml`:
```yaml
influxdb:
  url: 'http://localhost:8087'
```

---

### **Issue 8: Permission Denied on Volumes**

**Symptoms:**
```
Error: permission denied
```

**Solution:**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ~/.docker

# Or recreate volumes
docker compose down -v
docker compose up -d
```

---

## 📊 **Quick Health Check**

Run this one-liner to check everything:

```bash
echo "=== Services ===" && \
docker compose ps && \
echo -e "\n=== Redis ===" && \
docker exec wolfinch-redis redis-cli ping && \
echo -e "\n=== InfluxDB ===" && \
curl -s http://localhost:8086/health | jq && \
echo -e "\n=== Redis Keys ===" && \
docker exec wolfinch-redis redis-cli KEYS "*" && \
echo -e "\n=== InfluxDB Data ===" && \
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> count()' \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production 2>/dev/null | head -20
```

---

## 🔄 **Complete Reset**

If nothing works, start fresh:

```bash
# 1. Stop Wolfinch
# Press Ctrl+C

# 2. Stop and remove all containers and volumes
docker compose down -v

# 3. Remove any SQLite databases (optional)
rm -f *.db

# 4. Start services fresh
docker compose up -d

# 5. Wait for services to be healthy
sleep 10
docker compose ps

# 6. Run test script
source venv/bin/activate
python test_influxdb_redis.py

# 7. Start Wolfinch
./start_wolfinch.sh
```

---

## 📞 **Getting Help**

If you're still having issues:

1. **Check logs:**
   ```bash
   docker compose logs > docker_logs.txt
   ```

2. **Run test script:**
   ```bash
   python test_influxdb_redis.py > test_results.txt
   ```

3. **Check Wolfinch logs:**
   ```bash
   # Look for ERROR or WARNING messages
   grep -E "(ERROR|WARNING)" wolfinch.log
   ```

4. **Verify configuration:**
   ```bash
   cat config/cache_db.yml
   cat config/wolfinch_papertrader_nse_banknifty.yml | grep -A 2 cache_db
   ```

---

## ✅ **Success Checklist**

- [ ] Docker services running (all healthy)
- [ ] Redis responds to PING
- [ ] InfluxDB health check passes
- [ ] Test script shows "All systems operational"
- [ ] Wolfinch logs show "Using InfluxDB"
- [ ] InfluxDB query returns data
- [ ] Grafana data source connected
- [ ] Grafana dashboard shows charts

---

**Once all checks pass, you're ready to trade!** 🚀📊
