# Random Trading Strategy - Testing Guide

Quick guide for testing Wolfinch with random trading strategies.

## 🎲 Available Random Strategies

### 1. RANDOM_TRADER (Default)
**Best for**: General testing with realistic behavior

**Behavior**:
- Generates random buy/sell signals with configurable probability
- Holds positions for a minimum number of candles
- Exits randomly after minimum hold period
- Variable signal strength (1-3)

**Parameters**:
```yaml
strategy: RANDOM_TRADER
params:
  period: 20                    # Min candles before trading
  trade_probability: 20         # 20% chance to trade each candle
  max_signal_strength: 3        # Signal strength 1-3
  hold_candles: 5               # Min candles to hold position
```

**Trading Frequency**: ~20% of candles (configurable)

---

### 2. AGGRESSIVE_RANDOM
**Best for**: Testing high-frequency trading

**Behavior**:
- Trades very frequently (every 3-5 candles)
- Quick entries and exits
- Always uses maximum signal strength (3)
- Good for stress testing

**Parameters**:
```yaml
strategy: AGGRESSIVE_RANDOM
params:
  period: 10                    # Min candles before trading
```

**Trading Frequency**: Every 3-5 candles

---

### 3. SIMPLE_RANDOM
**Best for**: Predictable testing pattern

**Behavior**:
- Alternates between buy and sell
- Trades every N candles (configurable)
- Predictable pattern for debugging
- Medium signal strength (2)

**Parameters**:
```yaml
strategy: SIMPLE_RANDOM
params:
  period: 20                    # Min candles before trading
  trade_every_n_candles: 10     # Trade every 10 candles
```

**Trading Frequency**: Every N candles (exact)

---

## 🚀 Quick Start

### 1. Already Configured!

The config is already set up with RANDOM_TRADER on Bank Nifty:

```yaml
# In config/wolfinch_papertrader_nse_banknifty.yml
- 'BANKNIFTY-FUT':
    strategy: RANDOM_TRADER
    params: {'period': 20, 'trade_probability': 20, 'max_signal_strength': 3, 'hold_candles': 5}
```

### 2. Run Wolfinch

```bash
source venv/bin/activate
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

### 3. Watch the Action

Open UI at: `http://localhost:8089/wolfinch`

You should see:
- Random buy/sell orders being placed
- Positions opening and closing
- Stop-loss and take-profit triggers
- P&L updates

---

## 🎛️ Adjusting Trading Frequency

### More Trades (Aggressive)

```yaml
# Option 1: Increase probability
strategy: RANDOM_TRADER
params: {'period': 10, 'trade_probability': 50, 'max_signal_strength': 3, 'hold_candles': 3}

# Option 2: Use aggressive strategy
strategy: AGGRESSIVE_RANDOM
params: {'period': 5}
```

### Fewer Trades (Conservative)

```yaml
strategy: RANDOM_TRADER
params: {'period': 50, 'trade_probability': 5, 'max_signal_strength': 2, 'hold_candles': 10}
```

### Predictable Pattern

```yaml
strategy: SIMPLE_RANDOM
params: {'period': 20, 'trade_every_n_candles': 15}
# Will trade exactly every 15 candles
```

---

## 📊 What to Test

### ✅ Order Execution
- [ ] Buy orders execute correctly
- [ ] Sell orders execute correctly
- [ ] Order fills are instant (paper trading)
- [ ] Fees are calculated

### ✅ Position Management
- [ ] Positions open correctly
- [ ] Positions close correctly
- [ ] Multiple positions handled
- [ ] Position tracking in UI

### ✅ Risk Management
- [ ] Stop-loss triggers work
- [ ] Take-profit triggers work
- [ ] Position sizing correct
- [ ] Capital management works

### ✅ UI Updates
- [ ] Charts update in real-time
- [ ] Order history displays
- [ ] Position list updates
- [ ] P&L calculations correct

### ✅ Performance
- [ ] System handles multiple products
- [ ] No memory leaks
- [ ] CSV data processes correctly
- [ ] Database updates work

---

## 🔧 Switching Strategies

### In Config File

Edit `config/wolfinch_papertrader_nse_banknifty.yml`:

```yaml
# Comment out current strategy
# strategy: RANDOM_TRADER
# params: {...}

# Uncomment desired strategy
strategy: AGGRESSIVE_RANDOM
params: {'period': 10}
```

### Multiple Products, Different Strategies

```yaml
products:
  # Bank Nifty - Random trader
  - 'BANKNIFTY-FUT':
      strategy: RANDOM_TRADER
      params: {'trade_probability': 20}
  
  # Nifty - Aggressive random
  - 'NIFTY-FUT':
      active: true
      strategy: AGGRESSIVE_RANDOM
      params: {'period': 10}
  
  # Reliance - Simple alternating
  - 'RELIANCE-FUT':
      active: true
      strategy: SIMPLE_RANDOM
      params: {'trade_every_n_candles': 10}
```

---

## 📈 Expected Behavior

### RANDOM_TRADER (20% probability)
```
Candle 1-19: No trades (warming up)
Candle 20: 20% chance to trade
Candle 21: 20% chance to trade
...
If position opened at candle 25:
Candle 25-29: Hold (min 5 candles)
Candle 30+: 30% chance to exit each candle
```

### AGGRESSIVE_RANDOM
```
Candle 1-9: No trades (warming up)
Candle 10: 50% chance to enter
If entered:
  Hold for 3-5 candles
  Exit
  Immediately 50% chance to re-enter
```

### SIMPLE_RANDOM (every 10 candles)
```
Candle 1-19: No trades (warming up)
Candle 20: BUY (signal +2)
Candle 30: SELL (signal -2)
Candle 40: BUY (signal +2)
Candle 50: SELL (signal -2)
...
```

---

## 🐛 Troubleshooting

### No Trades Happening

**Check**:
1. Enough candles processed? (need > period)
2. CSV data loading correctly?
3. Strategy active in config?
4. Sufficient capital available?

**Solution**:
```bash
# Check logs for:
# "RANDOM_TRADER: BUY signal: X"
# "RANDOM_TRADER: SELL signal: X"
```

### Too Many Trades

**Solution**: Reduce probability or increase hold time
```yaml
params: {'trade_probability': 5, 'hold_candles': 20}
```

### Too Few Trades

**Solution**: Increase probability or use aggressive strategy
```yaml
strategy: AGGRESSIVE_RANDOM
params: {'period': 5}
```

---

## 💡 Tips

1. **Start with RANDOM_TRADER** - Good balance for testing
2. **Use AGGRESSIVE_RANDOM** - For stress testing
3. **Use SIMPLE_RANDOM** - For debugging specific issues
4. **Monitor console logs** - See trade signals in real-time
5. **Check UI frequently** - Verify updates are working
6. **Test with small capital** - Start with lower amounts
7. **One product first** - Test single product before multiple

---

## 🎯 Back to Real Strategies

When done testing, switch back to real strategies:

```yaml
# EMA_RSI
strategy: EMA_RSI
params: {'period': 80, 'ema_s': 5, 'ema_m': 13, 'ema_l': 21, 'ema_ll': 50, 'rsi': 14, 'rsi_bullish_mark': 50}

# TRABOS
strategy: TRABOS
params: {'period': 100, 'ema': 20, 'atr': 40, 'mfi': 60}

# TREND_RSI
strategy: TREND_RSI
params: {'period': 100, 'rsi_periods': 14, 'oversold_rsi': 30, 'overbought_rsi': 70}
```

---

## 📝 Example Console Output

```
[INFO:RANDOM_TRADER] Generating BUY signal: strength 2
[INFO:MARKET] BUY: 1 sig: 2
[INFO:ORDER-BOOK] Opening position: BUY @ 44500.00
[INFO:RANDOM_TRADER] Holding position for 5 candles
[INFO:RANDOM_TRADER] Generating SELL signal: strength -3
[INFO:MARKET] SELL: 1 sig: -3
[INFO:ORDER-BOOK] Closing position: SELL @ 44650.00 | Profit: +150.00
```

Happy testing! 🎲🚀
