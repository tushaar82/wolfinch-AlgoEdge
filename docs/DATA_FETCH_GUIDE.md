# InfluxDB Data Fetch Scripts - Usage Guide

Three powerful scripts to fetch, export, and analyze your trading data from InfluxDB.

---

## 📊 **1. View Data (fetch_influx_data.py)**

Display trading data in a beautiful terminal table format.

### **Usage:**

```bash
# View last 24 hours (default)
source venv/bin/activate
python fetch_influx_data.py

# View last 7 days
python fetch_influx_data.py 168  # 168 hours = 7 days

# View specific product
python fetch_influx_data.py 24 NIFTY-FUT
```

### **What it shows:**

- ✅ Trading statistics (total trades, P&L, win rate, fees)
- ✅ Recent candles (last 20)
- ✅ Recent trades (all in period)
- ✅ Closed positions with P&L

### **Example Output:**

```
============================================================
Wolfinch InfluxDB Data Viewer
============================================================

📊 Trading Statistics (Last 24h)
------------------------------------------------------------
Total Candles    5,000
Total Trades     10
Total P&L        ₹12,450.50
Win Rate         60.0%
Total Fees       ₹445.00

📈 Recent Candles - BANKNIFTY-FUT (Last 20)
------------------------------------------------------------
Time                 Open        High        Low         Close       Volume
2025-10-16 13:00:00  ₹44,500.00  ₹44,550.00  ₹44,480.00  ₹44,520.00  1,500

💰 Recent Trades
------------------------------------------------------------
Time                 Product          Side  Price       Size   Fee     Total
2025-10-16 12:30:00  BANKNIFTY-FUT    BUY   ₹44,510.00  10.00  ₹22.25  ₹445,122.25

📊 Closed Positions (P&L)
------------------------------------------------------------
Time                 Product          Entry       Exit        P&L         P&L %    Duration  Result
2025-10-16 12:45:00  BANKNIFTY-FUT    ₹44,510.00  ₹45,100.00  ₹5,855.20   1.32%    15m       WIN
```

---

## 💾 **2. Export to CSV (export_influx_data.py)**

Export all data to CSV files for Excel, Python pandas, or other analysis tools.

### **Usage:**

```bash
# Export last 7 days (default)
source venv/bin/activate
python export_influx_data.py

# Export last 30 days
python export_influx_data.py 30

# Export specific product
python export_influx_data.py 7 NIFTY-FUT

# Export to custom directory
python export_influx_data.py 7 BANKNIFTY-FUT my_exports
```

### **Output Files:**

Creates 3 CSV files in `exports/` directory:

1. **`candles_BANKNIFTY-FUT_7d.csv`**
   - Columns: timestamp, time, open, high, low, close, volume, exchange, product
   
2. **`trades_7d.csv`**
   - Columns: timestamp, time, exchange, product, order_id, side, fill_price, fill_size, fee, total_cost, market_price, slippage
   
3. **`positions_7d.csv`**
   - Columns: timestamp, time, exchange, product, position_id, entry_price, exit_price, size, pnl, pnl_percent, duration_seconds, duration_minutes, close_reason, win, loss

### **Example Output:**

```
======================================================================
Wolfinch InfluxDB Data Exporter
======================================================================

Configuration:
  - Days: 7
  - Product: BANKNIFTY-FUT
  - Output directory: exports

Connected to InfluxDB: http://localhost:8086
Bucket: trading

Exporting candles for BANKNIFTY-FUT (last 7 days)...
  ✓ Exported 5000 candles to exports/candles_BANKNIFTY-FUT_7d.csv
Exporting trades (last 7 days)...
  ✓ Exported 50 trades to exports/trades_7d.csv
Exporting positions (last 7 days)...
  ✓ Exported 25 positions to exports/positions_7d.csv

======================================================================
Export Summary:
  ✓ 5000 candles
  ✓ 50 trades
  ✓ 25 positions

Files saved to: exports/
======================================================================
```

### **Use CSV files with pandas:**

```python
import pandas as pd

# Load data
candles = pd.read_csv('exports/candles_BANKNIFTY-FUT_7d.csv')
trades = pd.read_csv('exports/trades_7d.csv')
positions = pd.read_csv('exports/positions_7d.csv')

# Analyze
print(f"Total P&L: {positions['pnl'].sum()}")
print(f"Win Rate: {positions['win'].mean() * 100}%")
print(f"Average trade duration: {positions['duration_minutes'].mean()} minutes")

# Plot
import matplotlib.pyplot as plt
candles['close'].plot()
plt.show()
```

---

## 📈 **3. Analyze Performance (analyze_trades.py)**

Get detailed trading performance analysis and insights.

### **Usage:**

```bash
# Analyze last 7 days (default)
source venv/bin/activate
python analyze_trades.py

# Analyze last 30 days
python analyze_trades.py 30
```

### **What it shows:**

- ✅ Total trades, wins, losses, win rate
- ✅ Total P&L, average P&L, best/worst trades
- ✅ Average trade duration
- ✅ Total fees and fee percentage
- ✅ Trades by product
- ✅ Risk metrics (std dev, risk-adjusted return)
- ✅ Last 5 trades

### **Example Output:**

```
======================================================================
Trading Performance Analysis (Last 7 days)
======================================================================

📊 Total Trades: 25
✅ Wins: 15
❌ Losses: 10
📈 Win Rate: 60.00%

💰 Total P&L: ₹45,230.50
📊 Average P&L per trade: ₹1,809.22
🎯 Best Trade: ₹8,500.00
⚠️  Worst Trade: ₹-3,200.00

⏱️  Average Trade Duration: 45.3 minutes (0.76 hours)
⏱️  Longest Trade: 180.0 minutes (3.00 hours)
⏱️  Shortest Trade: 5.0 minutes

💸 Total Fees Paid: ₹1,125.50
💸 Fees as % of P&L: 2.49%

📦 Trades by Product:
   - BANKNIFTY-FUT: 20 trades
   - NIFTY-FUT: 5 trades

📊 Risk Metrics:
   - P&L Std Dev: ₹2,450.30
   - Risk-Adjusted Return: 0.74

🕐 Last 5 Trades:
   ✅ 2025-10-16 13:15:30 | BANKNIFTY-FUT | ₹2,350.00
   ❌ 2025-10-16 12:45:20 | BANKNIFTY-FUT | ₹-1,200.00
   ✅ 2025-10-16 12:10:15 | NIFTY-FUT | ₹3,100.00
   ✅ 2025-10-16 11:30:45 | BANKNIFTY-FUT | ₹1,850.00
   ❌ 2025-10-16 10:55:30 | BANKNIFTY-FUT | ₹-800.00

======================================================================
```

---

## 🚀 **Quick Start**

### **1. Install dependencies (if needed):**

```bash
source venv/bin/activate
pip install influxdb-client pyyaml tabulate
```

### **2. View your data:**

```bash
python fetch_influx_data.py
```

### **3. Export to CSV:**

```bash
python export_influx_data.py
```

### **4. Analyze performance:**

```bash
python analyze_trades.py
```

---

## 📊 **Advanced Usage**

### **Combine with other tools:**

```bash
# Export and analyze with pandas
python export_influx_data.py 30
python -c "
import pandas as pd
df = pd.read_csv('exports/positions_30d.csv')
print('Win Rate:', df['win'].mean() * 100, '%')
print('Total P&L:', df['pnl'].sum())
print('Sharpe Ratio:', df['pnl'].mean() / df['pnl'].std())
"
```

### **Create custom queries:**

Edit the scripts to add your own queries! Example:

```python
# In fetch_influx_data.py, add:
def fetch_hourly_pnl(client, config, hours=24):
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "pnl")
      |> aggregateWindow(every: 1h, fn: sum)
    '''
    # ... process results
```

---

## 🎯 **Use Cases**

### **Daily Review:**
```bash
# Check today's performance
python analyze_trades.py 1
```

### **Weekly Report:**
```bash
# Export week's data for reporting
python export_influx_data.py 7
```

### **Monthly Analysis:**
```bash
# Detailed monthly analysis
python analyze_trades.py 30
python export_influx_data.py 30
```

### **Strategy Comparison:**
```bash
# Export data and analyze in Excel/Python
python export_influx_data.py 30
# Then use Excel pivot tables or pandas for strategy comparison
```

---

## 📁 **Output Files**

All exports go to `exports/` directory:

```
exports/
├── candles_BANKNIFTY-FUT_7d.csv
├── trades_7d.csv
└── positions_7d.csv
```

---

## 🐛 **Troubleshooting**

### **No data found:**

1. Check if Wolfinch is running and using InfluxDB:
   ```bash
   python diagnose.py
   ```

2. Check if data exists in InfluxDB:
   ```bash
   docker exec wolfinch-influxdb influx query \
     'from(bucket:"trading") |> range(start: -24h) |> count()' \
     --org wolfinch --token wolfinch-super-secret-token-change-in-production
   ```

### **Connection error:**

1. Check if InfluxDB is running:
   ```bash
   docker compose ps influxdb
   ```

2. Verify config:
   ```bash
   cat config/cache_db.yml
   ```

### **Import errors:**

```bash
source venv/bin/activate
pip install influxdb-client pyyaml tabulate
```

---

## 📚 **Summary**

| Script | Purpose | Output |
|--------|---------|--------|
| `fetch_influx_data.py` | View data in terminal | Beautiful tables |
| `export_influx_data.py` | Export to CSV | 3 CSV files |
| `analyze_trades.py` | Performance analysis | Detailed stats |

---

**All your trading data is now easily accessible!** 🎉📊📈
