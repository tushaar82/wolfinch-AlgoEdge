# Multi-Stock, Multi-Strategy Trading Guide

Complete guide for running multiple strategies on multiple stocks simultaneously using Wolfinch PaperTrader.

## 🎯 Overview

Wolfinch PaperTrader now supports:
- ✅ **Multiple stocks** - Trade Bank Nifty, Nifty, Reliance, TCS, Infosys, etc. simultaneously
- ✅ **Multiple strategies** - Different strategy for each stock
- ✅ **Independent parameters** - Each stock has its own risk management
- ✅ **Shared capital** - All products share the same trading capital pool
- ✅ **CSV-based data** - Just add CSV files to `raw_data/` directory

## 📁 File Structure

```
raw_data/
├── BANK_minute.csv       # Bank Nifty data
├── NIFTY_minute.csv      # Nifty 50 data
├── RELIANCE_minute.csv   # Reliance Industries
├── TCS_minute.csv        # TCS
├── INFY_minute.csv       # Infosys
├── HDFC_minute.csv       # HDFC Bank
├── ICICI_minute.csv      # ICICI Bank
└── ... (add more as needed)
```

## 🚀 Quick Start

### Step 1: Add Your CSV Files

Place all your stock CSV files in the `raw_data/` directory:

```bash
# Your CSV files should be in this format:
# timestamp,open,high,low,close,volume
```

### Step 2: Configure Products

Edit `config/papertrader.yml` to list all your stocks:

```yaml
products:
  - 'BANKNIFTY':
      id: 'BANKNIFTY-FUT'
      asset_type: 'BANKNIFTY'
      fund_type: 'INR'
      csv_file: 'BANK_minute.csv'
  
  - 'RELIANCE':
      id: 'RELIANCE-FUT'
      asset_type: 'RELIANCE'
      fund_type: 'INR'
      csv_file: 'RELIANCE_minute.csv'
  
  # Add more...
```

### Step 3: Configure Strategies

Edit `config/wolfinch_papertrader_nse_banknifty.yml` to assign strategies:

```yaml
products:
  # Bank Nifty with EMA_RSI
  - 'BANKNIFTY-FUT':
      active: true
      fund_max_liquidity: 400000
      decision:
        model: simple
        config:
          strategy: EMA_RSI
          params: {...}
  
  # Nifty with TRABOS
  - 'NIFTY-FUT':
      active: true
      fund_max_liquidity: 300000
      decision:
        model: simple
        config:
          strategy: TRABOS
          params: {...}
```

### Step 4: Run Wolfinch

```bash
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

## 📊 Configuration Examples

### Example 1: Same Strategy, Different Parameters

Trade 3 stocks with EMA_RSI but different parameters:

```yaml
products:
  # Aggressive for Bank Nifty
  - 'BANKNIFTY-FUT':
      active: true
      decision:
        config:
          strategy: EMA_RSI
          params: {'period': 60, 'ema_s': 3, 'ema_m': 8, 'ema_l': 13, 'ema_ll': 34, 'rsi': 14}
  
  # Conservative for Nifty
  - 'NIFTY-FUT':
      active: true
      decision:
        config:
          strategy: EMA_RSI
          params: {'period': 100, 'ema_s': 8, 'ema_m': 21, 'ema_l': 34, 'ema_ll': 89, 'rsi': 21}
  
  # Balanced for Reliance
  - 'RELIANCE-FUT':
      active: true
      decision:
        config:
          strategy: EMA_RSI
          params: {'period': 80, 'ema_s': 5, 'ema_m': 13, 'ema_l': 21, 'ema_ll': 50, 'rsi': 14}
```

### Example 2: Different Strategies per Stock

```yaml
products:
  # Bank Nifty - EMA_RSI (momentum)
  - 'BANKNIFTY-FUT':
      decision:
        config:
          strategy: EMA_RSI
          params: {'period': 80, 'ema_s': 5, 'ema_m': 13, 'ema_l': 21, 'ema_ll': 50, 'rsi': 14}
  
  # Nifty - TRABOS (multi-indicator)
  - 'NIFTY-FUT':
      decision:
        config:
          strategy: TRABOS
          params: {'period': 100, 'ema': 20, 'atr': 40, 'mfi': 60}
  
  # Reliance - TREND_RSI (trend following)
  - 'RELIANCE-FUT':
      decision:
        config:
          strategy: TREND_RSI
          params: {'period': 100, 'rsi': 14, 'rsi_low': 30, 'rsi_high': 70}
  
  # TCS - EMA_DEV (deviation based)
  - 'TCS-FUT':
      decision:
        config:
          strategy: EMA_DEV
          params: {'period': 120, 'ema_buy_s': 90, 'ema_buy_l': 70}
```

### Example 3: Capital Allocation

Allocate different amounts to each stock:

```yaml
# Total capital: 10 Lakhs
products:
  # 40% to Bank Nifty (high liquidity)
  - 'BANKNIFTY-FUT':
      fund_max_liquidity: 400000  # 4 Lakhs
      fund_max_per_buy_value: 50000
  
  # 30% to Nifty
  - 'NIFTY-FUT':
      fund_max_liquidity: 300000  # 3 Lakhs
      fund_max_per_buy_value: 40000
  
  # 20% to Reliance
  - 'RELIANCE-FUT':
      fund_max_liquidity: 200000  # 2 Lakhs
      fund_max_per_buy_value: 30000
  
  # 10% to TCS
  - 'TCS-FUT':
      fund_max_liquidity: 100000  # 1 Lakh
      fund_max_per_buy_value: 20000
```

## 🎛️ Available Strategies

### 1. EMA_RSI
**Best for**: Trending markets, intraday trading
```yaml
strategy: EMA_RSI
params:
  period: 80          # Lookback period
  ema_s: 5           # Fast EMA
  ema_m: 13          # Medium EMA
  ema_l: 21          # Slow EMA
  ema_ll: 50         # Very slow EMA
  rsi: 14            # RSI period
  rsi_bullish_mark: 50
```

### 2. TRABOS
**Best for**: Volatile markets, multi-indicator confirmation
```yaml
strategy: TRABOS
params:
  period: 100
  ema: 20
  atr: 40
  mfi: 60
  mfi_dir_len: 2
  obv_dir_len: 2
  stop_x: 5
  profit_x: 4
  vosc_short: 50
  vosc_long: 100
  timeout_buy: 0
  timeout_sell: 20
```

### 3. TREND_RSI
**Best for**: Trend following with RSI confirmation
```yaml
strategy: TREND_RSI
params:
  period: 100
  rsi: 14
  rsi_low: 30
  rsi_high: 70
```

### 4. EMA_DEV
**Best for**: Mean reversion, deviation-based trading
```yaml
strategy: EMA_DEV
params:
  period: 195
  ema_buy_s: 90
  ema_buy_l: 70
  ema_sell_s: 85
  ema_sell_l: 70
  rsi: 76
  treshold_pct_buy_s: 1.69
  treshold_pct_buy_l: 1.31
  treshold_pct_sell_s: 0.61
  treshold_pct_sell_l: 1.0
```

### 5. TREND_BOLLINGER
**Best for**: Volatility-based trading
```yaml
strategy: TREND_BOLLINGER
params:
  period: 100
  bb_period: 20
  bb_std: 2
```

### 6. TRIX_RSI
**Best for**: Momentum trading
```yaml
strategy: TRIX_RSI
params:
  period: 100
  trix: 15
  rsi: 14
```

## 💡 Best Practices

### Capital Management

```yaml
# Rule of thumb: Don't allocate more than 90% of total capital
# Keep 10% as buffer

# Total: 10 Lakhs
initial_fund: 1000000

# Allocate 9 Lakhs across products
products:
  - 'STOCK1': fund_max_liquidity: 300000  # 30%
  - 'STOCK2': fund_max_liquidity: 300000  # 30%
  - 'STOCK3': fund_max_liquidity: 300000  # 30%
  # 1 Lakh remains as buffer
```

### Risk Management per Stock

```yaml
# Conservative
stop_loss:
  rate: 1.5  # 1.5% stop loss
take_profit:
  rate: 2.5  # 2.5% take profit

# Moderate
stop_loss:
  rate: 2    # 2% stop loss
take_profit:
  rate: 3    # 3% take profit

# Aggressive
stop_loss:
  rate: 3    # 3% stop loss
take_profit:
  rate: 5    # 5% take profit
```

### Enable/Disable Stocks

```yaml
# Enable only the stocks you want to trade
products:
  - 'BANKNIFTY-FUT':
      active: true   # Trading enabled
  
  - 'NIFTY-FUT':
      active: true   # Trading enabled
  
  - 'TCS-FUT':
      active: false  # Disabled - will not trade
  
  - 'INFY-FUT':
      active: false  # Disabled - will not trade
```

## 📈 Monitoring Multiple Stocks

### UI Access

Open `http://localhost:8080` to see:
- All active products
- Individual P&L for each stock
- Strategy signals for each stock
- Overall portfolio performance

### Console Logs

Watch the console for:
```
[BANKNIFTY-FUT] BUY signal: 2
[NIFTY-FUT] SELL signal: -1
[RELIANCE-FUT] HOLD signal: 0
```

## 🔧 Adding New Stocks

### Step 1: Add CSV File

```bash
# Add your CSV to raw_data/
cp ~/Downloads/HDFC_minute.csv raw_data/
```

### Step 2: Register in papertrader.yml

```yaml
products:
  - 'HDFC':
      id: 'HDFC-FUT'
      asset_type: 'HDFC'
      fund_type: 'INR'
      csv_file: 'HDFC_minute.csv'
```

### Step 3: Configure Strategy

```yaml
products:
  - 'HDFC-FUT':
      active: true
      fund_max_liquidity: 200000
      fund_max_per_buy_value: 30000
      asset_max_per_trade_size: 50
      asset_min_per_trade_size: 1
      stop_loss:
        enabled: true
        kind: strategy
        rate: 2
      take_profit:
        enabled: true
        kind: strategy
        rate: 3
      decision:
        model: simple
        config:
          strategy: EMA_RSI
          params: {'period': 80, 'ema_s': 5, 'ema_m': 13, 'ema_l': 21, 'ema_ll': 50, 'rsi': 14, 'rsi_bullish_mark': 50}
```

### Step 4: Restart Wolfinch

```bash
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

## 📊 Example Portfolios

### Portfolio 1: Index Heavy

```yaml
# 70% indices, 30% stocks
products:
  - 'BANKNIFTY-FUT': fund_max_liquidity: 400000  # 40%
  - 'NIFTY-FUT': fund_max_liquidity: 300000      # 30%
  - 'RELIANCE-FUT': fund_max_liquidity: 200000   # 20%
  - 'TCS-FUT': fund_max_liquidity: 100000        # 10%
```

### Portfolio 2: Diversified

```yaml
# Equal allocation
products:
  - 'BANKNIFTY-FUT': fund_max_liquidity: 225000  # 22.5%
  - 'NIFTY-FUT': fund_max_liquidity: 225000      # 22.5%
  - 'RELIANCE-FUT': fund_max_liquidity: 225000   # 22.5%
  - 'TCS-FUT': fund_max_liquidity: 225000        # 22.5%
```

### Portfolio 3: Sector Focused

```yaml
# Banking sector
products:
  - 'BANKNIFTY-FUT': fund_max_liquidity: 300000  # 30%
  - 'HDFC-FUT': fund_max_liquidity: 200000       # 20%
  - 'ICICI-FUT': fund_max_liquidity: 200000      # 20%
  - 'AXIS-FUT': fund_max_liquidity: 200000       # 20%
  - 'SBI-FUT': fund_max_liquidity: 100000        # 10%
```

## 🎯 Strategy Combinations

### Combination 1: Momentum + Mean Reversion

```yaml
# Use momentum for indices, mean reversion for stocks
products:
  - 'BANKNIFTY-FUT':
      strategy: EMA_RSI  # Momentum
  - 'NIFTY-FUT':
      strategy: TRABOS   # Momentum
  - 'RELIANCE-FUT':
      strategy: EMA_DEV  # Mean reversion
  - 'TCS-FUT':
      strategy: EMA_DEV  # Mean reversion
```

### Combination 2: All Trend Following

```yaml
# Consistent trend-following across all
products:
  - 'BANKNIFTY-FUT':
      strategy: TREND_RSI
  - 'NIFTY-FUT':
      strategy: TREND_RSI
  - 'RELIANCE-FUT':
      strategy: TREND_RSI
```

## 🚨 Important Notes

1. **Shared Capital**: All products share the same capital pool (initial_fund)
2. **CSV Sync**: Ensure all CSV files have similar timestamp ranges
3. **Active Flag**: Use `active: false` to disable trading without removing config
4. **Performance**: More products = more processing, monitor system resources
5. **Backtesting**: Test each strategy individually before combining

## 📝 Troubleshooting

### Issue: "CSV file not found"
```bash
# Check if file exists
ls -la raw_data/BANK_minute.csv

# Verify filename in config matches exactly
```

### Issue: "No trades on some stocks"
- Check if `active: true` is set
- Verify CSV has enough data
- Check strategy parameters aren't too restrictive

### Issue: "Running out of capital"
- Reduce `fund_max_liquidity` for each product
- Ensure total allocation < initial_fund

## 🎓 Next Steps

1. Start with 2-3 stocks
2. Test each strategy individually
3. Gradually add more stocks
4. Monitor performance and adjust
5. Optimize parameters using genetic optimizer

Happy multi-stock trading! 🚀
