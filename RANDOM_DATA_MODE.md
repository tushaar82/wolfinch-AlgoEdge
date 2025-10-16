# Random Data Generation Mode

PaperTrader now generates random OHLC data automatically - no CSV files needed!

## 🎲 **What Changed**

### Before (CSV Mode)
- Required CSV files in `raw_data/`
- Slow to load large files (975K rows)
- File format issues
- Manual data preparation

### After (Random Mode) ✨
- **Instant startup** - generates data in memory
- **No files needed** - works out of the box
- **Realistic price movements** - proper OHLC candles
- **Configurable** - adjust number of candles

---

## 🚀 **Benefits**

✅ **Fast** - Generates 5000 candles instantly  
✅ **Easy** - No CSV file management  
✅ **Realistic** - Proper volatility and price movements  
✅ **Flexible** - Adjust candle count in config  
✅ **Perfect for testing** - Random trader + random data = complete test environment  

---

## ⚙️ **Configuration**

### Number of Candles

Edit `config/papertrader.yml`:

```yaml
exchange:
  random_candles: 5000  # Adjust this number
```

**Recommendations:**
- **Quick testing**: 1000 candles (~16 minutes of data)
- **Normal testing**: 5000 candles (~83 hours / 3.5 days)
- **Extended testing**: 10000 candles (~7 days)
- **Long-term**: 50000 candles (~35 days)

### Starting Prices

Automatically set based on product name:
- **BANKNIFTY**: 44,500
- **NIFTY**: 19,500
- **RELIANCE**: 2,500
- **TCS**: 3,500
- **INFY**: 1,500
- **Others**: 1,000

---

## 📊 **Generated Data Characteristics**

### Price Movement
- **Volatility**: 0.1% to 1.5% per candle
- **Direction**: Random (50/50 up/down)
- **Realistic OHLC**: Proper high/low ranges

### Volume
- **Range**: 1,000 to 5,000 per candle
- **Random**: Varies naturally

### Timestamps
- **Interval**: 1 minute
- **Start**: Current time minus (num_candles * 60 seconds)
- **End**: Current time

---

## 🎯 **Perfect for Testing**

### Random Trader + Random Data = Complete Test

```yaml
# In config/wolfinch_papertrader_nse_banknifty.yml
strategy: RANDOM_TRADER
params: {'period': 20, 'trade_probability': 20}

# In config/papertrader.yml
random_candles: 5000
```

This gives you:
- ✅ Instant data generation
- ✅ Random trading signals
- ✅ Complete order flow
- ✅ Position management
- ✅ P&L tracking
- ✅ UI updates

---

## 🔄 **Switching Back to CSV Mode**

If you want to use real CSV data later, just uncomment the CSV loading code in `papertrader.py`:

```python
# In __init__ method, replace:
self.csv_data[product['id']] = self._generate_random_ohlc_data(...)

# With:
csv_file_path = os.path.join(self.raw_data_dir, product['csv_file'])
if os.path.exists(csv_file_path):
    self.csv_data[product['id']] = self._load_csv_data(csv_file_path)
else:
    # Fallback to random data
    self.csv_data[product['id']] = self._generate_random_ohlc_data(...)
```

---

## 📈 **Example Output**

```
[INFO:PaperTrader] Generating 5000 random candles for BANKNIFTY starting at 44500.0
[INFO:PaperTrader] Generated 5000 candles for BANKNIFTY, price range: 44500.00 to 45234.56
[INFO:PaperTrader] Generating 5000 random candles for RELIANCE starting at 2500.0
[INFO:PaperTrader] Generated 5000 candles for RELIANCE, price range: 2500.00 to 2567.89
```

---

## 🎛️ **Customization**

### Change Volatility

Edit `_generate_random_ohlc_data()` in `papertrader.py`:

```python
# More volatile (for testing stop-loss/take-profit)
volatility = random.uniform(0.005, 0.030)  # 0.5% to 3%

# Less volatile (for trend strategies)
volatility = random.uniform(0.0005, 0.005)  # 0.05% to 0.5%
```

### Add Trend

```python
# Add upward trend
trend = 0.0005  # 0.05% upward bias
price_change = current_price * (volatility * direction + trend)

# Add downward trend
trend = -0.0005  # 0.05% downward bias
```

### Custom Starting Price

```python
# In config, add to product definition:
products:
  - 'CUSTOM':
      id: 'CUSTOM-FUT'
      start_price: 10000.0  # Custom starting price
```

---

## 💡 **Use Cases**

### 1. Strategy Development
- Test new strategies instantly
- No need to find/prepare data
- Iterate quickly

### 2. System Testing
- Test order execution
- Test position management
- Test UI updates
- Test database operations

### 3. Demo/Presentation
- Show system capabilities
- No data preparation needed
- Consistent behavior

### 4. Learning
- Learn Wolfinch without data setup
- Understand trading flow
- Experiment with parameters

---

## 🎉 **Quick Start**

```bash
# 1. Just run - no data prep needed!
source venv/bin/activate
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml

# 2. Open UI
# Browser: http://localhost:8089/wolfinch

# 3. Watch trades happen automatically!
```

---

## 📝 **Notes**

- Random data is generated fresh each time you start
- Data is stored in memory, not saved to disk
- Each product gets its own independent random walk
- Timestamps are realistic (1-minute intervals)
- OHLC relationships are maintained (high ≥ open/close, low ≤ open/close)

---

**Perfect for testing! No CSV files, no data preparation, just run and trade!** 🚀🎲
