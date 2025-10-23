# 🔄 RESTART WOLFINCH NOW

The bucket exists, but Wolfinch needs to be restarted to write data to it!

---

## ⚡ **Quick Restart**

### **Option 1: Use Restart Script**
```bash
./restart_wolfinch.sh
```

### **Option 2: Manual Restart**
```bash
# 1. Stop Wolfinch
# Go to the terminal where Wolfinch is running and press Ctrl+C

# 2. Start again
./start_wolfinch.sh
```

### **Option 3: Kill and Restart**
```bash
# Kill existing processes
pkill -f Wolfinch.py

# Wait 2 seconds
sleep 2

# Start fresh
./start_wolfinch.sh
```

---

## ✅ **What to Look For After Restart**

You should see these log messages:

```
[INFO:RedisCache] Redis connected: localhost:6379 db=0
[INFO:InfluxDB] InfluxDB connected: http://localhost:8086 org=wolfinch bucket=trading
[INFO:Wolfinch] Redis cache initialized
[INFO:Wolfinch] InfluxDB initialized
[INFO:Wolfinch] Trade logger initialized
[INFO:CANDLE-DB] Using InfluxDB for papertrader:BANKNIFTY-FUT
[INFO:CandleDB-Influx] InfluxDB candle database initialized: papertrader:BANKNIFTY-FUT
```

**Wait 30-60 seconds** for Wolfinch to:
1. Generate 5000 random candles
2. Calculate historic indicators
3. Write data to InfluxDB

---

## 🔍 **Verify Data After Restart**

### **1. Check InfluxDB Has Data (CLI)**
```bash
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "candle") |> count()' \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production
```

**Expected:** Should show ~5000 data points per field

### **2. Check InfluxDB UI**
1. Refresh the page: http://localhost:8086
2. Data Explorer
3. Select bucket: `trading`
4. Select measurement: `candle`
5. Select field: `close`
6. Click "Submit"

**You should see data!**

---

## 🐛 **If Still No Data**

Run the test script:
```bash
source venv/bin/activate
python test_influxdb_redis.py
```

**Expected output:**
```
✓ Redis connected
✓ InfluxDB connected
✓ CandleDBInflux initialized
✓ Candle saved successfully
✓ Retrieved 3 candles
✓ All systems operational!
```

---

## 📊 **Quick Check**

```bash
# One-liner to check everything
echo "=== Wolfinch Running? ===" && \
ps aux | grep "[W]olfinch.py" && \
echo -e "\n=== InfluxDB Data? ===" && \
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> count()' \
  --org wolfinch --token wolfinch-super-secret-token-change-in-production 2>/dev/null | head -20
```

---

**Just restart Wolfinch and wait 60 seconds - data will appear!** 🚀
