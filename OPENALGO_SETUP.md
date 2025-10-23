# Wolfinch OpenAlgo Setup Guide

## Summary

I've configured Wolfinch to work with OpenAlgo for live/paper trading on NSE FNO (Futures & Options). The UI has been fixed and is ready to run on port **8089**.

## Issues Fixed

### 1. **UI Port Configuration**
- ✅ Fixed Redis port: `6379` → `6380` (to match Docker setup)
- ✅ Fixed InfluxDB port: `8086` → `8087` (to match Docker setup)
- ✅ Fixed UI port in OpenAlgo config: `8080` → `8089`

### 2. **Code Bugs Fixed**
- ✅ Fixed `random_trader.py` - Corrected candle data access (was trying to access `.close` on a dict instead of `['ohlc'].close`)
- ✅ Fixed OpenAlgo client initialization - Changed from `openalgo_api.OpenAlgoClient()` to `openalgo_api()` (correct API)

### 3. **Configuration Files Updated**
- ✅ `config/cache_db.yml` - Updated ports for Redis and InfluxDB
- ✅ `config/wolfinch_openalgo_nifty.yml` - Updated UI port to 8089
- ✅ `config/openalgo.yml` - Fixed API initialization

## Current Status

### ✅ Working
- Docker services (Redis, InfluxDB, Kafka, Grafana, etc.) - All running
- Wolfinch core initialization
- OpenAlgo client initialization
- UI server ready to start on port 8089

### ⚠️ Requires Action

#### 1. **Start OpenAlgo Server**
OpenAlgo server is not running on `http://127.0.0.1:5000`

**Error seen:**
```
connect_tcp.failed exception=ConnectError(ConnectionRefusedError(111, 'Connection refused'))
```

**To fix:**
- Install and start OpenAlgo server
- Or update `config/openalgo.yml` with the correct OpenAlgo server URL

#### 2. **Set OpenAlgo API Key**
Current placeholder: `test-api-key-replace-with-real-one`

**To fix:**
1. Get your API key from OpenAlgo dashboard (usually at `http://127.0.0.1:5000`)
2. Update `config/openalgo.yml`:
   ```yaml
   apiKey: 'your-actual-api-key-here'
   ```

#### 3. **Update Option Symbols (Optional)**
Current symbols are for January 2025 expiry which may be expired:
- `NFO:NIFTY-24JAN25-22000-CE`
- `NFO:NIFTY-24JAN25-22000-PE`
- `NFO:BANKNIFTY-24JAN25-48000-CE`

**To update:**
Edit `config/wolfinch_openalgo_nifty.yml` and `config/openalgo.yml` with current month options.

## How to Run Wolfinch with OpenAlgo

### Prerequisites
1. OpenAlgo server running on `http://127.0.0.1:5000`
2. Valid OpenAlgo API key configured
3. Docker services running (already done ✅)

### Start Wolfinch
```bash
cd /home/tushka/Projects/wolfinch-AlgoEdge
source venv/bin/activate
python Wolfinch.py --config config/wolfinch_openalgo_nifty.yml
```

### Access the UI
Once Wolfinch starts successfully:
- **URL:** `http://127.0.0.1:8089/wolfinch`
- **Alternative:** `http://192.168.31.66:8089/wolfinch`

## Configuration Files

### Main Config: `config/wolfinch_openalgo_nifty.yml`
- Exchange: OpenAlgo
- Products: NIFTY options
- Strategy: EMA_RSI_MTF (Multi-timeframe EMA + RSI)
- Candle Interval: 5 minutes (300 seconds)
- UI Port: 8089

### OpenAlgo Config: `config/openalgo.yml`
- API Key: **Needs to be set**
- Host URL: `http://127.0.0.1:5000`
- Products: NIFTY and BANKNIFTY options
- Lot Sizes: Configured for NSE FNO

### Database Config: `config/cache_db.yml`
- Redis: `localhost:6380`
- InfluxDB: `http://localhost:8087`
- Token: `wolfinch-super-secret-token-change-in-production`

## Testing Without OpenAlgo Server

If you want to test the UI without OpenAlgo server, you can use the paper trader:

```bash
python Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

Then access UI at: `http://127.0.0.1:8089/wolfinch`

## Next Steps

1. **Install/Start OpenAlgo Server**
   - Follow OpenAlgo installation guide
   - Ensure it's running on port 5000

2. **Get API Key**
   - Login to OpenAlgo dashboard
   - Generate API key
   - Update `config/openalgo.yml`

3. **Start Wolfinch**
   - Run the command above
   - Check logs for any errors
   - Access UI at port 8089

4. **Monitor**
   - Check Grafana: `http://localhost:3001` (admin/wolfinch2024)
   - Check InfluxDB: `http://localhost:8087`
   - Check Redis Commander: `http://localhost:8081`

## Troubleshooting

### UI Not Accessible
- Check if Wolfinch is running: `ps aux | grep Wolfinch`
- Check if port 8089 is listening: `lsof -i :8089`
- Check logs: `tail -f logs/wolfinch_openalgo.log`

### OpenAlgo Connection Failed
- Verify OpenAlgo server is running: `curl http://127.0.0.1:5000`
- Check OpenAlgo logs
- Verify API key is correct

### No Markets Configured
- Ensure product symbols in `wolfinch_openalgo_nifty.yml` match those in `openalgo.yml`
- Check that products are marked as `active: true`

## Files Modified

1. `config/cache_db.yml` - Updated Redis and InfluxDB ports
2. `config/wolfinch_openalgo_nifty.yml` - Updated UI port
3. `config/openalgo.yml` - Updated API key placeholder
4. `strategy/strategies/random_trader.py` - Fixed candle data access
5. `exchanges/openalgo/openalgo_client.py` - Fixed API initialization

---

**Status:** Ready to test with OpenAlgo server
**UI Port:** 8089
**Last Updated:** 2025-10-23 17:40
