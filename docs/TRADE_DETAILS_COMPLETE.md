# ✅ Trade Details Logging - COMPLETE!

Every trade detail is now automatically logged to InfluxDB!

---

## 🎯 **What Gets Logged**

### **1. BUY Order Placed**
- Order ID, price, size
- Market price, volume
- Stop loss, take profit targets
- Timestamp

### **2. BUY Order Filled**
- Fill price, fill size
- Fees paid
- Market price at fill
- Position opened details
- Entry price
- Stop loss / take profit levels

### **3. SELL Order Placed**
- Order ID, price, size
- Market price, volume
- Stop loss, take profit
- Timestamp

### **4. SELL Order Filled**
- Fill price, fill size
- Fees paid
- Market price at fill
- **Position closed details:**
  - Entry price
  - Exit price
  - P&L (profit/loss in INR)
  - P&L % (percentage)
  - Trade duration (seconds)
  - Win/Loss flag

---

## 📊 **Data Saved to InfluxDB**

### **Measurement: `trade_event`**

**Event Types:**
- `order_placed` - When buy/sell order is created
- `order_filled` - When order executes
- `position_opened` - When buy fills (long position)
- `position_closed` - When sell fills (close position)

**Tags (indexed):**
- `event_type`, `exchange`, `product`, `order_id`, `position_id`
- `side` (BUY/SELL), `status` (placed/filled)

**Fields (values):**
- `price`, `size`, `fill_price`, `fill_size`, `fee`
- `market_price`, `market_volume`
- `stop_loss`, `take_profit`
- `entry_price`, `exit_price`
- `pnl`, `pnl_percent`, `duration_seconds`
- `win`, `loss` (1 or 0)

---

## 🚀 **How to Use**

**Just restart Wolfinch - logging is automatic!**

```bash
# Stop current Wolfinch (Ctrl+C in terminal)
# Then start:
./start_wolfinch.sh
```

**Look for these logs:**
```
[INFO:Wolfinch] Trade logger initialized
[INFO:TradeLogger] Logged order placed: BUY 10 BANKNIFTY-FUT @ 44500
[INFO:TradeLogger] Logged order filled: BUY 10 BANKNIFTY-FUT @ 44510
[INFO:TradeLogger] Logged position opened: 10 BANKNIFTY-FUT @ 44510
[INFO:TradeLogger] Logged order placed: SELL 10 BANKNIFTY-FUT @ 45100
[INFO:TradeLogger] Logged order filled: SELL 10 BANKNIFTY-FUT @ 45100
[INFO:TradeLogger] Logged position closed: BANKNIFTY-FUT P&L: 5900.00 (1.33%) - strategy
```

---

## 🔍 **Query Trade Details**

### **1. All Trades Today**
```flux
from(bucket: "trading")
  |> range(start: today())
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
```

### **2. Profitable Trades**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "pnl")
  |> filter(fn: (r) => r._value > 0)
```

### **3. Trade Details with P&L**
```flux
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

### **4. Average Trade Duration**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "duration_seconds")
  |> mean()
```

### **5. Total Fees Paid**
```flux
from(bucket: "trading")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "order_filled")
  |> filter(fn: (r) => r._field == "fee")
  |> sum()
```

### **6. Win Rate**
```flux
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "win")
  |> mean()
  |> map(fn: (r) => ({ r with _value: r._value * 100.0 }))
```

---

## 📈 **Grafana Dashboard**

Create panels for:

1. **Total Trades** (Stat)
2. **Win Rate** (Gauge) 
3. **Total P&L** (Stat)
4. **P&L Over Time** (Time Series)
5. **Trade Duration Distribution** (Histogram)
6. **Fees Paid** (Stat)
7. **Best Trade** (Stat - max pnl)
8. **Worst Trade** (Stat - min pnl)
9. **Recent Trades Table** (Table with all details)

---

## 📊 **Example Trade Flow in InfluxDB**

**Trade #1 - Profitable:**
```
Time: 12:00:00 | event: order_placed   | side: BUY  | price: 44500 | size: 10
Time: 12:00:01 | event: order_filled   | side: BUY  | fill_price: 44510 | fee: 22.25
Time: 12:00:01 | event: position_opened| entry: 44510 | stop_loss: 43600 | take_profit: 45400
Time: 12:15:30 | event: order_placed   | side: SELL | price: 45100 | size: 10
Time: 12:15:31 | event: order_filled   | side: SELL | fill_price: 45100 | fee: 22.55
Time: 12:15:31 | event: position_closed| exit: 45100 | pnl: 5855.20 | pnl%: 1.32 | duration: 930s | win: 1
```

**Trade #2 - Loss:**
```
Time: 13:00:00 | event: order_placed   | side: BUY  | price: 45200 | size: 10
Time: 13:00:01 | event: order_filled   | side: BUY  | fill_price: 45210 | fee: 22.60
Time: 13:00:01 | event: position_opened| entry: 45210 | stop_loss: 44300 | take_profit: 46100
Time: 13:05:20 | event: order_placed   | side: SELL | price: 44800 | size: 10
Time: 13:05:21 | event: order_filled   | side: SELL | fill_price: 44800 | fee: 22.40
Time: 13:05:21 | event: position_closed| exit: 44800 | pnl: -4145.00 | pnl%: -0.91 | duration: 320s | loss: 1
```

---

## ✅ **Verification**

After Wolfinch restarts and makes some trades:

```bash
# Check trade events
docker exec wolfinch-influxdb influx query \
  'from(bucket:"trading") 
   |> range(start: -1h) 
   |> filter(fn: (r) => r._measurement == "trade_event")
   |> group(columns: ["event_type"])
   |> count()' \
  --org wolfinch --token wolfinch-super-secret-token-change-in-production
```

**Expected output:**
```
event_type: order_placed    count: 4
event_type: order_filled    count: 4
event_type: position_opened count: 2
event_type: position_closed count: 2
```

---

## 🎯 **Summary**

✅ **BUY orders** - Logged when placed and filled  
✅ **SELL orders** - Logged when placed and filled  
✅ **Positions** - Opened and closed events  
✅ **P&L** - Calculated and logged  
✅ **Fees** - Tracked for every trade  
✅ **Duration** - Time held in position  
✅ **Market data** - Price and volume at trade time  
✅ **Strategy data** - Stop loss, take profit levels  
✅ **Win/Loss** - Flagged for easy filtering  

---

**Every trade detail is now saved to InfluxDB automatically!** 🎉📊📈

**Just restart Wolfinch and start trading!**
