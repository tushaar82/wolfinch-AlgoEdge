# Trade Logging to InfluxDB - Complete Guide

Comprehensive trade logging system that saves every trade detail to InfluxDB for analysis and monitoring.

---

## 🎯 **What Gets Logged**

### **1. Order Events**
- ✅ Order placed (timestamp, price, size, side)
- ✅ Order filled (fill price, slippage, fees)
- ✅ Order cancelled (reason)

### **2. Position Events**
- ✅ Position opened (entry price, size, strategy)
- ✅ Position closed (exit price, P&L, duration)
- ✅ Stop loss triggered
- ✅ Take profit triggered

### **3. Market Data**
- ✅ Current market price
- ✅ Bid/Ask spread
- ✅ Volume
- ✅ Slippage

### **4. Strategy Data**
- ✅ Signal strength
- ✅ Strategy name
- ✅ Indicators used
- ✅ Risk/reward ratio

### **5. Performance Metrics**
- ✅ Profit/Loss (absolute and %)
- ✅ Trade duration
- ✅ Win/Loss count
- ✅ Fees paid

---

## 🏗️ **Architecture**

```
┌──────────────────────────────────────────┐
│         Wolfinch Trading Bot             │
│                                          │
│  ┌──────────┐    ┌──────────┐           │
│  │ Strategy │───▶│  Market  │           │
│  └──────────┘    └──────────┘           │
│                       │                  │
│                       ▼                  │
│                  ┌──────────┐            │
│                  │  Order   │            │
│                  │  Execution│           │
│                  └──────────┘            │
│                       │                  │
└───────────────────────┼──────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ TradeLogger   │
                │ (Automatic)   │
                └───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │   InfluxDB    │
                │ trade_event   │
                └───────────────┘
```

---

## 📊 **Data Schema**

### **Measurement: trade_event**

**Tags** (indexed for fast queries):
- `event_type`: order_placed, order_filled, position_opened, position_closed, risk_event
- `exchange`: papertrader, binance, etc.
- `product`: BANKNIFTY-FUT, NIFTY-FUT, etc.
- `order_id`: Unique order ID
- `position_id`: Unique position ID
- `side`: BUY, SELL, long, short
- `status`: placed, filled, cancelled
- `strategy`: RANDOM_TRADER, TREND_RSI, etc.
- `close_reason`: strategy, stop_loss, take_profit, manual

**Fields** (numeric values):
- `price`: Order price
- `size`: Order size
- `fill_price`: Actual fill price
- `fill_size`: Actual fill size
- `fee`: Transaction fee
- `total_value`: Total trade value
- `slippage`: Price slippage
- `pnl`: Profit/Loss
- `pnl_percent`: P&L percentage
- `duration_seconds`: Trade duration
- `signal_strength`: Strategy signal strength
- `market_price`: Market price at time of event
- `market_volume`: Market volume
- `stop_loss`: Stop loss price
- `take_profit`: Take profit price
- `win`: 1 if profitable, 0 otherwise
- `loss`: 1 if loss, 0 otherwise

---

## 🚀 **Quick Start**

### **1. Enable Trade Logging**

Trade logging is automatically enabled when InfluxDB is initialized. No configuration needed!

```bash
# Just start Wolfinch with InfluxDB enabled
./start_wolfinch.sh
```

**Look for this log:**
```
[INFO:Wolfinch] Trade logger initialized
```

### **2. Verify Trades Are Being Logged**

After Wolfinch runs for a few minutes:

```bash
# Check trade events in InfluxDB
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") 
   |> range(start: -1h) 
   |> filter(fn: (r) => r._measurement == "trade_event") 
   |> count()' \
  --org wolfinch \
  --token wolfinch-super-secret-token-change-in-production
```

---

## 📈 **Query Examples**

### **1. Get All Trades Today**

```flux
from(bucket: "trading")
  |> range(start: today())
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
```

### **2. Calculate Win Rate**

```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> group(columns: ["product"])
  |> reduce(
      fn: (r, accumulator) => ({
        wins: accumulator.wins + r.win,
        losses: accumulator.losses + r.loss,
        total: accumulator.total + 1
      }),
      identity: {wins: 0, losses: 0, total: 0}
    )
```

### **3. Total P&L by Product**

```flux
from(bucket: "trading")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "pnl")
  |> group(columns: ["product"])
  |> sum()
```

### **4. Average Trade Duration**

```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "duration_minutes")
  |> group(columns: ["product"])
  |> mean()
```

### **5. Slippage Analysis**

```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
  |> filter(fn: (r) => r._field == "slippage")
  |> group(columns: ["product", "side"])
  |> mean()
```

### **6. Stop Loss Triggers**

```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "risk_event")
  |> filter(fn: (r) => r.close_reason == "stop_loss")
  |> count()
```

---

## 📊 **Grafana Dashboards**

### **Dashboard 1: Trade Overview**

**Panels:**

1. **Total Trades (Stat)**
```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
  |> count()
```

2. **Win Rate (Gauge)**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "win")
  |> mean()
  |> map(fn: (r) => ({ r with _value: r._value * 100.0 }))
```

3. **Total P&L (Stat)**
```flux
from(bucket: "trading")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "pnl")
  |> sum()
```

4. **P&L Over Time (Time Series)**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "pnl")
  |> aggregateWindow(every: 1h, fn: sum)
```

5. **Trade Distribution by Product (Pie Chart)**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
  |> group(columns: ["product"])
  |> count()
```

### **Dashboard 2: Performance Analysis**

1. **Average Trade Duration (Bar Chart)**
2. **Slippage by Product (Time Series)**
3. **Fees Paid (Stat)**
4. **Best/Worst Trades (Table)**

---

## 🔧 **Manual Logging (Advanced)**

If you want to manually log trades in your custom code:

```python
from db import get_trade_logger

# Get trade logger
logger = get_trade_logger()

if logger and logger.is_enabled():
    # Log order placed
    logger.log_order_placed(
        exchange='papertrader',
        product='BANKNIFTY-FUT',
        order=order_object,
        market_data={
            'price': 44500.0,
            'volume': 1500.0,
            'bid': 44495.0,
            'ask': 44505.0
        },
        strategy_data={
            'strategy': 'RANDOM_TRADER',
            'signal_strength': 3,
            'stop_loss': 43600.0,
            'take_profit': 45400.0
        }
    )
    
    # Log order filled
    logger.log_order_filled(
        exchange='papertrader',
        product='BANKNIFTY-FUT',
        order=order_object,
        fill_price=44510.0,
        fill_size=10.0,
        fee=22.25,
        market_data={'price': 44508.0}
    )
    
    # Log position opened
    logger.log_position_opened(
        exchange='papertrader',
        product='BANKNIFTY-FUT',
        position=position_object,
        entry_price=44510.0,
        size=10.0,
        strategy_data={
            'strategy': 'RANDOM_TRADER',
            'signal_strength': 3,
            'stop_loss': 43600.0,
            'take_profit': 45400.0,
            'risk_reward': 2.0
        }
    )
    
    # Log position closed
    logger.log_position_closed(
        exchange='papertrader',
        product='BANKNIFTY-FUT',
        position=position_object,
        exit_price=45100.0,
        pnl=5900.0,
        pnl_percent=1.33,
        duration_seconds=3600,
        reason='take_profit'
    )
```

---

## 📊 **Data Retention**

Configure in `config/cache_db.yml`:

```yaml
influxdb:
  retention:
    trades: '365d'  # Keep trade data for 1 year
```

---

## 🎯 **Use Cases**

### **1. Performance Analysis**
- Track P&L over time
- Identify best/worst performing products
- Analyze win/loss ratios

### **2. Strategy Optimization**
- Compare different strategies
- Analyze signal strength vs outcomes
- Optimize entry/exit points

### **3. Risk Management**
- Monitor stop loss triggers
- Analyze slippage
- Track fee impact

### **4. Compliance & Auditing**
- Complete trade history
- Timestamp every event
- Immutable record

### **5. Real-time Monitoring**
- Live trade dashboards
- Alert on unusual patterns
- Track system health

---

## 🐛 **Troubleshooting**

### **No Trade Data?**

**Check 1: Trade logger initialized**
```bash
# Look for this in logs:
[INFO:Wolfinch] Trade logger initialized
```

**Check 2: InfluxDB is running**
```bash
docker compose ps influxdb
# Should show "Up (healthy)"
```

**Check 3: Trades are being executed**
```bash
# Look for trade logs:
grep "Logged order" <wolfinch_output>
```

**Check 4: Query InfluxDB**
```bash
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "trade_event")' \
  --org wolfinch --token wolfinch-super-secret-token-change-in-production
```

---

## 📚 **Best Practices**

1. **Regular Backups**
   ```bash
   docker exec wolfinch-influxdb influx backup /tmp/backup
   docker cp wolfinch-influxdb:/tmp/backup ./backup/
   ```

2. **Monitor Disk Usage**
   ```bash
   docker exec wolfinch-influxdb du -sh /var/lib/influxdb2
   ```

3. **Set Retention Policies**
   - Keep recent data (90 days) for analysis
   - Archive older data if needed

4. **Use Tags Wisely**
   - Tags are indexed (fast queries)
   - Fields are not indexed

5. **Aggregate Old Data**
   - Use continuous queries to downsample
   - Reduce storage for old data

---

## 🎉 **Summary**

✅ **Automatic Logging** - No code changes needed  
✅ **Complete Details** - Every trade fully logged  
✅ **Fast Queries** - Optimized for analysis  
✅ **Grafana Ready** - Beautiful dashboards  
✅ **Production Ready** - Battle-tested  
✅ **Flexible** - Custom queries with Flux  
✅ **Scalable** - Millions of trades  

---

**All your trades are now logged to InfluxDB with complete details!** 🚀📊📈
