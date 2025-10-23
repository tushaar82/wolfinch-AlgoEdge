# Quick Start Guide

## 🚀 **Get Data Flowing to InfluxDB**

### **Step 1: Restart Wolfinch**

The configuration has been fixed. Now restart Wolfinch:

```bash
# Stop current Wolfinch (Press Ctrl+C in the terminal where it's running)
# Then run:
./start_wolfinch.sh
```

**Or use the restart script:**
```bash
./restart_wolfinch.sh
```

### **Step 2: Verify InfluxDB/Redis Initialization**

Look for these log messages when Wolfinch starts:

```
✅ GOOD - You should see:
[INFO:RedisCache] Redis connected: localhost:6379 db=0
[INFO:InfluxDB] InfluxDB connected: http://localhost:8086 org=wolfinch bucket=trading
[INFO:Wolfinch] Redis cache initialized
[INFO:Wolfinch] InfluxDB initialized
[INFO:MARKET] Using InfluxDB for papertrader:BANKNIFTY-FUT

❌ BAD - If you see:
[WARNING] InfluxDB/Redis initialization skipped
[INFO:MARKET] Using SQLite for papertrader:BANKNIFTY-FUT
```

### **Step 3: Wait for Data (30 seconds)**

Wolfinch needs to:
1. Generate random candles (5000 candles)
2. Process historic indicators
3. Start live trading
4. Write candles to InfluxDB

This takes about 30-60 seconds.

### **Step 4: Check InfluxDB Has Data**

```bash
# Run this command
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "candle") |> count()' \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production
```

**Expected output:**
```
Table: keys: [_start, _stop, _field, _measurement, exchange, product]
...
close    candle    papertrader    BANKNIFTY-FUT    ...    5000
high     candle    papertrader    BANKNIFTY-FUT    ...    5000
low      candle    papertrader    BANKNIFTY-FUT    ...    5000
open     candle    papertrader    BANKNIFTY-FUT    ...    5000
volume   candle    papertrader    BANKNIFTY-FUT    ...    5000
```

### **Step 5: Refresh InfluxDB UI**

1. Go to http://localhost:8086
2. Data Explorer
3. Click the **refresh icon** or press F5
4. You should now see data!

---

## 🎨 **Create Grafana Dashboard**

### **1. Add InfluxDB Data Source**

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Configuration → Data Sources → Add data source
4. Select "InfluxDB"
5. Configure:
   - Query Language: **Flux**
   - URL: **`http://influxdb:8086`** ⚠️ Use `influxdb`, NOT `localhost`
   - Organization: **`wolfinch`**
   - Token: **`wolfinch-super-secret-token-change-in-production`**
   - Default Bucket: **`trading`**
6. Click "Save & Test" → Should show ✅ green checkmark

### **2. Create Dashboard**

1. Click "+" → Dashboard
2. Add Panel
3. In the query editor, paste:

```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "candle")
  |> filter(fn: (r) => r.product == "BANKNIFTY-FUT")
  |> filter(fn: (r) => r._field == "close")
```

4. Settings:
   - Visualization: **Time series**
   - Title: **"Bank Nifty Close Price"**
   - Y-axis label: **"Price (INR)"**

5. Click "Apply"
6. Click "Save dashboard" (disk icon)
7. Name: "Wolfinch Trading Dashboard"

### **3. Add More Panels**

**Volume Panel:**
```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "candle")
  |> filter(fn: (r) => r.product == "BANKNIFTY-FUT")
  |> filter(fn: (r) => r._field == "volume")
```

**OHLC Candlestick (All Fields):**
```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "candle")
  |> filter(fn: (r) => r.product == "BANKNIFTY-FUT")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

Visualization: **Candlestick**

---

## 🔍 **Troubleshooting**

### **No data after restart?**

```bash
# 1. Check Wolfinch is running
ps aux | grep Wolfinch.py

# 2. Check logs for errors
# Look at the terminal where Wolfinch is running

# 3. Verify services are up
docker compose ps

# 4. Run test script
source venv/bin/activate
python test_influxdb_redis.py
```

### **Still using SQLite?**

Check the logs. If you see:
```
[INFO:MARKET] Using SQLite for papertrader:BANKNIFTY-FUT
```

Then InfluxDB wasn't initialized. Check:

```bash
# 1. Verify config file exists
cat config/cache_db.yml

# 2. Verify main config references it
grep cache_db config/wolfinch_papertrader_nse_banknifty.yml

# 3. Check Python packages
source venv/bin/activate
pip list | grep -E "(redis|influxdb)"
```

### **InfluxDB UI shows "No keys found"?**

This means:
1. Wolfinch hasn't started yet, OR
2. Wolfinch is using SQLite instead of InfluxDB, OR
3. Data hasn't been written yet (wait 60 seconds)

**Solution:**
```bash
# Restart Wolfinch
./restart_wolfinch.sh

# Wait 60 seconds

# Check data
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> count()' \
  --org wolfinch --token wolfinch-super-secret-token-change-in-production
```

---

## ✅ **Success Checklist**

- [ ] Wolfinch restarted
- [ ] Logs show "Redis cache initialized"
- [ ] Logs show "InfluxDB initialized"  
- [ ] Logs show "Using InfluxDB for papertrader:BANKNIFTY-FUT"
- [ ] InfluxDB query returns data
- [ ] InfluxDB UI shows candle data
- [ ] Grafana data source connected
- [ ] Grafana dashboard created

---

## 📊 **Service URLs**

| Service | URL | Credentials |
|---------|-----|-------------|
| Wolfinch UI | http://localhost:8089/wolfinch | None |
| InfluxDB | http://localhost:8086 | admin / wolfinch2024 |
| Grafana | http://localhost:3000 | admin / admin |
| Redis Commander | http://localhost:8081 | None |

---

**Once you see data in InfluxDB, you're all set!** 🎉
