# Wolfinch AlgoEdge - Professional NSE FNO Trading System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)
![OpenAlgo](https://img.shields.io/badge/Broker-OpenAlgo-orange.svg)
![NSE](https://img.shields.io/badge/Market-NSE%20FNO-red.svg)

**Advanced algorithmic trading system for NSE F&O Options trading with OpenAlgo integration**

</div>

---

## 🚀 Features

### Core Capabilities
- ✅ **OpenAlgo Broker Integration** - Seamless connectivity using OpenAlgo SDK
- ✅ **NSE F&O Options Trading** - Full support for NIFTY, BANKNIFTY, FINNIFTY options
- ✅ **Lot Size Management** - Automatic calculation based on NSE specifications
- ✅ **7 Advanced Strategies** - Professional multi-timeframe algorithmic strategies
- ✅ **Trailing Stop Loss** - Built-in trailing SL for all strategies
- ✅ **Risk Management** - Daily loss limits with automatic order blocking
- ✅ **Live P&L Tracking** - Real-time profit/loss monitoring
- ✅ **Professional Dashboard** - Web-based UI for monitoring and control
- ✅ **Comprehensive Logging** - Every trade and action logged to database

---

## 🚦 Quick Start

```bash
# Start system
./start.sh

# Check health
./health.sh

# Access dashboard
# Open browser: http://localhost:8080

# Stop system
./stop.sh
```

---

## 📊 7 Trading Strategies

1. **EMA_RSI_MTF** - Multi-timeframe EMA + RSI with trailing SL
2. **Supertrend_ADX** - Supertrend + ADX with ATR-based SL
3. **VWAP_BB** - VWAP + Bollinger Bands mean reversion
4. **Triple_EMA_MACD** - Triple EMA crossover with MACD confirmation
5. **RSI_Divergence_Stoch** - Divergence detection with Stochastic timing
6. **Volume_Breakout_ATR** - Volume breakout with ATR stops
7. **MTF_Trend_Following** - Multi-timeframe comprehensive trend following

All strategies include built-in trailing stop loss mechanisms.

---

## 🎯 Risk Management

Configure in `config/wolfinch_openalgo_nifty.yml`:

```yaml
risk_management:
  enabled: true
  max_daily_loss: 5000           # ₹5000 daily loss limit
  max_daily_loss_percent: 5      # 5% of capital
  max_position_size: 10          # Max 10 lots per position
  max_open_positions: 3          # Max 3 concurrent positions
```

System automatically blocks trading when limits are breached.

---

## 📚 Documentation

See full documentation in this README or visit the [Wiki](wiki).

**Management Scripts:**
- `start.sh` - Start trading system
- `stop.sh` - Graceful shutdown
- `health.sh` - Health monitoring
- `clean.sh` - Cleanup logs and data

---

## ⚠️ Risk Disclaimer

Algorithmic trading involves substantial risk. This software is provided "as is" without warranty. Always test with paper trading first.

---

## 📄 License

GNU General Public License v3.0

---

**Happy Trading! 🚀**
