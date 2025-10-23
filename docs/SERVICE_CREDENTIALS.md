# Service URLs & Credentials

Quick reference for all Wolfinch services.

---

## 🌐 **Service URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **Wolfinch UI** | http://localhost:8089/wolfinch | Trading dashboard |
| **InfluxDB** | http://localhost:8086 | Time-series database |
| **Grafana** | http://localhost:3000 | Data visualization |
| **Redis Commander** | http://localhost:8081 | Redis browser |

---

## 🔑 **Credentials**

### **InfluxDB**
```
URL:      http://localhost:8086
Username: admin
Password: wolfinch2024
Org:      wolfinch
Bucket:   trading
Token:    wolfinch-super-secret-token-change-in-production
```

### **Grafana**
```
URL:      http://localhost:3000
Username: admin
Password: admin
```

### **Redis Commander**
```
URL:      http://localhost:8081
No authentication required (local development)
```

### **Wolfinch UI**
```
URL:      http://localhost:8089/wolfinch
No authentication (ui_codes file not present)
```

---

## 📊 **Quick Access Links**

### **InfluxDB Data Explorer**
```
http://localhost:8086/data-explorer
```
**What to do:**
1. Login with credentials above
2. Select bucket: `trading`
3. Select measurement: `candle`
4. Select field: `close`
5. Click "Submit" to see data

### **Grafana Dashboard Setup**
```
http://localhost:3000/datasources
```
**Add InfluxDB Data Source:**
1. Configuration → Data Sources → Add data source
2. Select "InfluxDB"
3. Settings:
   - Query Language: **Flux**
   - URL: **http://influxdb:8086**
   - Organization: **wolfinch**
   - Token: **wolfinch-super-secret-token-change-in-production**
   - Default Bucket: **trading**
4. Save & Test

### **Redis Commander**
```
http://localhost:8081
```
**Browse data:**
- View all keys
- Search for: `indicator:*` or `candles:*`
- Monitor memory usage

---

## 🔍 **Verify Data**

### **Check InfluxDB has data**
```bash
# Via CLI
docker exec -it wolfinch-influxdb influx

# Query candles
> from(bucket:"trading") 
  |> range(start: -1h) 
  |> filter(fn: (r) => r._measurement == "candle")
  |> limit(n: 10)
```

### **Check Redis has data**
```bash
# Via CLI
docker exec -it wolfinch-redis redis-cli

# List keys
> KEYS *

# Get indicator
> GET indicator:papertrader:BANKNIFTY-FUT:EMA:20
```

---

## 🎯 **First Time Setup**

### **1. Start Services**
```bash
./start_wolfinch.sh
```

### **2. Verify Services**
```bash
docker compose ps
```
All services should show "Up (healthy)"

### **3. Access UIs**
- Open http://localhost:8086 (InfluxDB)
- Open http://localhost:3000 (Grafana)
- Open http://localhost:8081 (Redis Commander)
- Open http://localhost:8089/wolfinch (Wolfinch)

### **4. Check Data in InfluxDB**
1. Login to InfluxDB
2. Go to Data Explorer
3. Query: `from(bucket:"trading") |> range(start: -1h)`
4. You should see candle data

---

## 📈 **Grafana Dashboard**

### **Create Trading Dashboard**

1. **Add InfluxDB Data Source** (see above)

2. **Create New Dashboard**
   - Click "+" → Dashboard
   - Add Panel

3. **Query Candle Data**
   ```flux
   from(bucket: "trading")
     |> range(start: -24h)
     |> filter(fn: (r) => r._measurement == "candle")
     |> filter(fn: (r) => r.product == "BANKNIFTY-FUT")
     |> filter(fn: (r) => r._field == "close")
   ```

4. **Visualization Options**
   - Graph type: Time series
   - Title: "Bank Nifty Close Price"
   - Y-axis: Price
   - X-axis: Time

5. **Save Dashboard**

---

## 🔐 **Security Notes**

⚠️ **For Production:**
1. Change InfluxDB token
2. Change Grafana password
3. Set Redis password
4. Enable Wolfinch UI authentication
5. Use HTTPS/TLS
6. Set up firewall rules

**Current setup is for LOCAL DEVELOPMENT ONLY!**

---

## 🐛 **Troubleshooting**

### **Can't access InfluxDB UI**
```bash
# Check if running
docker compose ps influxdb

# Check logs
docker compose logs influxdb

# Restart
docker compose restart influxdb
```

### **Can't access Grafana**
```bash
# Check if running
docker compose ps grafana

# Check logs
docker compose logs grafana

# Restart
docker compose restart grafana
```

### **No data in InfluxDB**
```bash
# Check if Wolfinch is writing data
docker compose logs | grep "Wrote.*candles"

# Check InfluxDB bucket
docker exec -it wolfinch-influxdb influx bucket list
```

---

## 📱 **Mobile Access**

To access from other devices on your network:

1. Find your IP address:
   ```bash
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```

2. Replace `localhost` with your IP:
   - InfluxDB: `http://192.168.1.X:8086`
   - Grafana: `http://192.168.1.X:3000`
   - Wolfinch: `http://192.168.1.X:8089/wolfinch`

---

**Save this file for quick reference!** 🔖
