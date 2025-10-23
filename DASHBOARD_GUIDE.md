# Wolfinch AlgoEdge - Professional Dashboard Guide

## 🎨 Features Overview

The new dashboard provides a comprehensive, real-time trading interface with advanced features:

### ✅ Implemented Features

1. **User Authentication** 🔐
   - Secure login/logout system
   - Password hashing with bcrypt
   - Session management with Flask-Login
   - Default admin account (username: `admin`, password: `admin123`)

2. **Real-time Candlestick Charts** 📈
   - Powered by trading-vue-js library
   - Live candle updates via WebSocket
   - Support for multiple timeframes
   - Customizable indicators overlay
   - Dark theme optimized for trading

3. **Live P&L Tracking** 💰
   - Real-time profit/loss display in header
   - Separate realized and unrealized P&L
   - Color-coded (green=profit, red=loss)
   - Updates every 5 seconds + WebSocket push

4. **Position Monitoring** 📊
   - All open positions displayed
   - Entry price, current price, unrealized P&L
   - Trailing stop loss visualization
   - Real-time position updates via WebSocket

5. **Trade Entry/Exit Markers** 🎯
   - Buy signals marked with green ▲
   - Sell signals marked with red ▼
   - Displayed directly on candlestick chart
   - Historical trade visualization

6. **Order Management** 📋
   - Complete order history
   - Order status tracking
   - Side (buy/sell) identification
   - Execution price and quantity

7. **Strategy Monitoring** 🧠
   - Active strategies display
   - Strategy status indicators
   - Per-market strategy assignment
   - Start/stop controls (UI ready)

8. **Analytics Dashboard** 📉
   - Daily performance metrics
   - Trade statistics
   - Win rate calculations
   - Performance charts

9. **Risk Management Panel** 🛡️
   - Daily loss limit tracking
   - Position size limits display
   - Loss limit usage percentage
   - Trading status (active/blocked)
   - Real-time limit monitoring

10. **WebSocket Real-time Updates** ⚡
    - Live candle updates
    - Real-time position changes
    - Instant P&L updates
    - Trade execution notifications

---

## 🚀 Getting Started

### 1. Installation

```bash
# Install new dependencies
pip install flask-login flask-socketio python-socketio

# Or install all dependencies
pip install -r requirement.txt
```

### 2. Start the Enhanced Dashboard

The dashboard is automatically started when you run Wolfinch with the new UI enabled.

**Option 1: Using start script**
```bash
./start.sh
```

**Option 2: Manual start**
```bash
python Wolfinch.py --config config/wolfinch_openalgo_nifty.yml
```

### 3. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

You'll be redirected to the login page.

### 4. Login

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT**: Change the default password immediately after first login!

---

## 📱 Dashboard Sections

### 🏠 Dashboard (Overview)
- **Location**: Main landing page after login
- **Features**:
  - 4 stat cards (Realized P&L, Unrealized P&L, Open Positions, Trading Status)
  - Live candlestick chart with indicators
  - Recent trades table (last 10 trades)
  - Real-time updates via WebSocket

**What You See:**
- Current total P&L in large display at top
- Color-coded stats (green=profit, red=loss)
- Trading status indicator (green dot=active, red=blocked)

---

### 📈 Charts
- **Location**: Click "Charts" in sidebar
- **Features**:
  - Advanced trading-vue-js candlestick chart
  - Multiple indicator overlays (EMA, RSI, MACD, etc.)
  - Volume histogram below main chart
  - Trade entry/exit markers on chart
  - Zoom and pan capabilities
  - Trailing SL line visualization

**How to Use:**
1. Chart loads automatically with last 500 candles
2. Indicators are overlaid based on active strategy
3. Green triangles (▲) = Buy entries
4. Red triangles (▼) = Sell exits
5. Trailing SL shown as dynamic line

---

### 💼 Positions
- **Location**: Click "Positions" in sidebar
- **Features**:
  - All open positions listed
  - Entry price, current price, unrealized P&L
  - Lot size display
  - Entry time tracking
  - Color-coded borders (green=long, red=short)

**Position Card Shows:**
- Symbol name (e.g., NIFTY-24JAN25-22000-CE)
- Position type badge (LONG/SHORT)
- Number of lots
- Entry price
- Current market price
- Unrealized P&L (color-coded)
- Entry timestamp

**Real-time Updates:**
- Positions update every 10 seconds
- WebSocket pushes instant updates on changes
- P&L recalculates with every price tick

---

### 📋 Orders
- **Location**: Click "Orders" in sidebar
- **Features**:
  - Complete order history
  - Last 50 orders displayed
  - Order status tracking
  - Side (buy/sell) badges
  - Execution price and quantity

**Order Information:**
- Time of order
- Symbol
- Side (BUY/SELL badge)
- Quantity in units
- Limit/market price
- Status (pending/filled/cancelled)

---

### 🧠 Strategies
- **Location**: Click "Strategies" in sidebar
- **Features**:
  - All active strategies listed
  - Strategy name and market
  - Status indicator (active/inactive)
  - Start/Stop controls

**Strategy Card Shows:**
- Strategy name (e.g., EMA_RSI_MTF, Supertrend_ADX)
- Associated market
- Status indicator (green dot = active)
- Stop button to halt strategy

**Available Strategies:**
1. EMA_RSI_MTF - Multi-timeframe EMA + RSI
2. Supertrend_ADX - Supertrend with ADX confirmation
3. VWAP_BB - VWAP + Bollinger Bands
4. Triple_EMA_MACD - Triple EMA with MACD
5. RSI_Divergence_Stoch - RSI Divergence detection
6. Volume_Breakout_ATR - Volume breakout trading
7. MTF_Trend_Following - Multi-timeframe trending

---

### 📊 Analytics
- **Location**: Click "Analytics" in sidebar
- **Features**:
  - Daily performance metrics
  - Trade statistics
  - Win rate calculations
  - Profit factor
  - Average win/loss
  - Maximum drawdown

**Metrics Displayed:**
- Total trades today
- Winning trades
- Losing trades
- Win rate percentage
- Average profit per trade
- Average loss per trade
- Profit factor
- Sharpe ratio (if available)

---

### 🛡️ Risk Management
- **Location**: Click "Risk Management" in sidebar
- **Features**:
  - Daily loss limits display
  - Position size limits
  - Loss limit usage meter
  - Trading status indicator
  - Position slots usage

**Risk Panel Shows:**

**Left Card - Risk Limits:**
- Max Daily Loss (₹ amount)
- Max Daily Loss (% of capital)
- Max Position Size (lots)
- Max Open Positions (count)

**Right Card - Usage:**
- Loss limit used percentage (large display)
- Color-coded (green < 50%, yellow < 80%, red > 80%)
- Position slots used vs available

**Status Indicators:**
- Green dot = Trading active, within limits
- Red dot = Trading BLOCKED due to limit breach

---

## 🔧 Technical Details

### Architecture

```
Frontend (Browser)
    ↓
HTML/CSS/JavaScript
    ↓
Vue.js + trading-vue-js
    ↓
WebSocket (Socket.IO) ←→ Flask-SocketIO
    ↓
REST API Endpoints
    ↓
Flask API Server
    ↓
Risk Manager / Markets / Exchanges
    ↓
OpenAlgo Broker
```

### API Endpoints

**Authentication:**
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check auth status
- `POST /api/auth/register` - Register user (admin only)
- `POST /api/auth/change-password` - Change password

**Market Data:**
- `GET /api/markets` - Get all markets
- `GET /api/markets/<key>/candles` - Get candles for market
- `GET /api/markets/<key>/indicators` - Get indicator values

**Trading:**
- `GET /api/positions` - Get open positions
- `GET /api/orders` - Get order history
- `GET /api/trades` - Get trade history

**P&L & Risk:**
- `GET /api/pnl` - Get current P&L
- `GET /api/risk/status` - Get risk management status

**Strategies:**
- `GET /api/strategies` - Get active strategies

### WebSocket Events

**Client Subscribe:**
- `subscribe` - Subscribe to a channel (candles, positions, pnl, trades)
- `unsubscribe` - Unsubscribe from a channel

**Server Broadcasts:**
- `candle_update` - New candle data
- `position_update` - Position changed
- `pnl_update` - P&L changed
- `trade_update` - New trade executed

### Data Flow

1. **Login**: User logs in → Session created → Redirected to dashboard
2. **Initial Load**: Dashboard loads → Fetch all data via REST API
3. **Real-time**: WebSocket connects → Subscribe to channels → Receive live updates
4. **Chart Update**: New candle received → Update trading-vue-js chart → Redraw
5. **Trade Execution**: Order placed → Trade executed → WebSocket broadcast → Add marker to chart

---

## 🎨 Customization

### Change Theme Colors

Edit `ui/web_enhanced/index.html` CSS variables:

```css
:root {
    --primary-color: #667eea;    /* Purple */
    --secondary-color: #764ba2;   /* Darker purple */
    --success-color: #10b981;     /* Green */
    --danger-color: #ef4444;      /* Red */
    --dark-bg: #1a1d29;           /* Dark background */
    --card-bg: #242837;           /* Card background */
}
```

### Add Custom Indicators

Edit `ui/web_enhanced/js/dashboard.js`, in `addIndicators()` method:

```javascript
// Add RSI indicator
this.chartData.offchart.push({
    name: 'RSI',
    type: 'RSI',
    data: [],
    settings: {
        period: 14,
        color: '#f59e0b',
        overbought: 70,
        oversold: 30
    }
});
```

### Modify Dashboard Layout

Edit `ui/web_enhanced/index.html` to rearrange sections or add new components.

---

## 🔐 Security

### Change Default Password

After first login:

1. Click on your username in top-right
2. Select "Change Password"
3. Enter old password: `admin123`
4. Enter new strong password
5. Confirm new password
6. Click "Change"

### Create Additional Users

Only admin can create users:

1. Login as admin
2. Navigate to Settings (admin only)
3. Click "Add User"
4. Enter username, password, email
5. Click "Create"

### Session Security

- Sessions expire after 24 hours
- Cookies are HTTP-only
- Logout invalidates session immediately
- Passwords are hashed with bcrypt

---

## 🐛 Troubleshooting

### Dashboard Not Loading

**Check 1: Is the server running?**
```bash
./health.sh
```

**Check 2: Are dependencies installed?**
```bash
pip list | grep -E "(flask|socketio)"
```

**Check 3: Check browser console**
- Open browser developer tools (F12)
- Check Console tab for errors
- Check Network tab for failed requests

### WebSocket Not Connecting

**Check 1: Port is correct**
- Default port: 8080
- URL should be: `http://localhost:8080`

**Check 2: Firewall**
```bash
# Allow port 8080
sudo ufw allow 8080
```

**Check 3: Server logs**
```bash
tail -f logs/wolfinch_*.log | grep -i "websocket\|socketio"
```

### Login Not Working

**Check 1: Default credentials**
- Username: `admin`
- Password: `admin123`

**Check 2: User file exists**
```bash
ls -lah data/users.json
cat data/users.json
```

**Check 3: Reset users**
```bash
rm data/users.json
# Restart Wolfinch - default admin will be recreated
./stop.sh && ./start.sh
```

### Charts Not Displaying

**Check 1: JavaScript console errors**
- Open browser dev tools (F12)
- Check for trading-vue-js errors

**Check 2: Candle data available**
```bash
curl http://localhost:8080/api/markets
curl http://localhost:8080/api/markets/MARKET_KEY/candles
```

**Check 3: CDN access**
- Ensure trading-vue-js CDN is accessible
- Check internet connection

### Real-time Updates Not Working

**Check 1: WebSocket connection**
- Open browser dev tools → Network → WS tab
- Should see active WebSocket connection

**Check 2: Subscriptions**
- Check browser console
- Should see "Subscribed to..." messages

**Check 3: Server broadcasting**
```bash
tail -f logs/wolfinch_*.log | grep -i "broadcast"
```

---

## 📊 Dashboard Screenshots (Conceptual)

### Login Page
- Clean, modern design
- Purple gradient background
- Feature list on left
- Login form on right

### Dashboard Overview
- Dark theme
- 4 stat cards at top
- Large candlestick chart
- Recent trades table at bottom

### Positions View
- List of position cards
- Color-coded borders (green=long, red=short)
- Real-time P&L updates
- Entry/current price display

### Risk Management
- Risk limits table
- Large percentage display
- Color-coded status
- Position slots meter

---

## 🚀 Next Steps

1. **Login** and explore the dashboard
2. **Monitor** your trades in real-time
3. **Analyze** performance in Analytics section
4. **Manage** risk limits as needed
5. **Customize** theme and indicators to your preference

---

## 💡 Pro Tips

1. **Keep Dashboard Open**: Real-time updates only work when dashboard is open
2. **Multiple Monitors**: Use separate monitor for dashboard
3. **Browser Choice**: Chrome/Edge recommended for best performance
4. **Refresh Data**: Click section again to manually refresh
5. **Keyboard Shortcuts**: Ctrl+R to refresh page if needed

---

## 📚 Additional Resources

- **Trading Vue.js Docs**: https://github.com/tvjsx/trading-vue-js
- **Flask-SocketIO Docs**: https://flask-socketio.readthedocs.io/
- **Wolfinch Main README**: See README.md
- **Quick Start Guide**: See QUICK_START.md

---

## ✅ Feature Checklist

- [x] User authentication with login/logout
- [x] Real-time candlestick charts
- [x] Live P&L tracking
- [x] Position monitoring with trailing SL
- [x] Trade entry/exit markers on charts
- [x] Order management interface
- [x] Strategy monitoring panel
- [x] Analytics dashboard
- [x] Risk management panel
- [x] WebSocket real-time updates
- [x] REST API endpoints
- [x] Dark theme optimized for trading
- [x] Responsive design
- [x] Session management

---

**Happy Trading with the New Professional Dashboard! 🎉📈💰**
