// Wolfinch AlgoEdge - Dashboard JavaScript
// Real-time trading dashboard with WebSocket updates

let socket = null;
let chartData = [];
let tradeMarkers = [];
let currentMarket = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initWebSocket();
    loadInitialData();
    startDataRefresh();
});

// Check authentication
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();

        if (!data.authenticated) {
            window.location.href = '/login';
            return;
        }

        document.getElementById('username').textContent = data.user.username;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
    }
}

// Logout
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// Initialize WebSocket
function initWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('WebSocket connected');
        // Subscribe to channels
        socket.emit('subscribe', { channel: 'candles' });
        socket.emit('subscribe', { channel: 'positions' });
        socket.emit('subscribe', { channel: 'pnl' });
        socket.emit('subscribe', { channel: 'trades' });
    });

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });

    // Real-time candle updates
    socket.on('candle_update', (data) => {
        updateChart(data);
    });

    // Real-time position updates
    socket.on('position_update', (data) => {
        updatePositionDisplay(data);
    });

    // Real-time P&L updates
    socket.on('pnl_update', (data) => {
        updatePnLDisplay(data);
    });

    // Real-time trade updates
    socket.on('trade_update', (data) => {
        addTradeToTable(data);
        addTradeMarker(data);
    });
}

// Load initial data
async function loadInitialData() {
    await loadMarkets();
    await loadPnL();
    await loadPositions();
    await loadTrades();
    await loadOrders();
    await loadStrategies();
    await loadRiskStatus();
}

// Load markets
async function loadMarkets() {
    try {
        const response = await fetch('/api/markets');
        const data = await response.json();

        if (data.markets && data.markets.length > 0) {
            currentMarket = data.markets[0].key;
            await loadCandles(currentMarket);
        }
    } catch (error) {
        console.error('Error loading markets:', error);
    }
}

// Load candles and initialize chart
async function loadCandles(marketKey) {
    try {
        const response = await fetch(`/api/markets/${marketKey}/candles?limit=500`);
        const data = await response.json();

        if (data.candles) {
            chartData = data.candles;
            initChart();
        }
    } catch (error) {
        console.error('Error loading candles:', error);
    }
}

// Initialize Trading Vue.js chart
function initChart() {
    if (chartData.length === 0) return;

    // Prepare data for trading-vue-js
    const ohlcv = chartData.map(candle => [
        candle.time,
        candle.open,
        candle.high,
        candle.low,
        candle.close,
        candle.volume
    ]);

    // Create Vue instance with trading chart
    new Vue({
        el: '#trading-chart',
        template: `
            <trading-vue
                :data="chartData"
                :width="width"
                :height="height"
                :color-back="colorBack"
                :color-grid="colorGrid"
                :color-text="colorText"
            ></trading-vue>
        `,
        data: {
            chartData: {
                chart: {
                    type: 'Candles',
                    data: ohlcv
                },
                onchart: [],
                offchart: []
            },
            width: window.innerWidth - 350,
            height: 550,
            colorBack: '#242837',
            colorGrid: '#363b52',
            colorText: '#e5e7eb'
        },
        mounted() {
            // Add indicators
            this.addIndicators();
            // Add trade markers
            this.addTradeMarkers();
        },
        methods: {
            addIndicators() {
                // Add EMA indicators
                this.chartData.onchart.push({
                    name: 'EMA',
                    type: 'EMA',
                    data: [],
                    settings: {
                        period: 21,
                        color: '#667eea'
                    }
                });

                // Add volume
                this.chartData.offchart.push({
                    name: 'Volume',
                    type: 'Volume',
                    data: ohlcv.map(c => [c[0], c[5]]),
                    settings: {
                        colorUp: '#10b981',
                        colorDown: '#ef4444'
                    }
                });
            },
            addTradeMarkers() {
                // Add entry/exit markers
                tradeMarkers.forEach(marker => {
                    this.chartData.onchart.push({
                        type: 'Trades',
                        data: [[marker.time, marker.price]],
                        settings: {
                            color: marker.side === 'buy' ? '#10b981' : '#ef4444',
                            icon: marker.side === 'buy' ? '▲' : '▼'
                        }
                    });
                });
            }
        }
    });
}

// Update chart with new candle
function updateChart(candleData) {
    if (!chartData) return;

    // Check if last candle should be updated or new candle added
    const lastCandle = chartData[chartData.length - 1];
    if (lastCandle && lastCandle.time === candleData.time) {
        // Update existing candle
        chartData[chartData.length - 1] = candleData;
    } else {
        // Add new candle
        chartData.push(candleData);
        if (chartData.length > 500) {
            chartData.shift(); // Keep only last 500 candles
        }
    }

    // Re-render chart (trading-vue-js will handle this)
}

// Load and display P&L
async function loadPnL() {
    try {
        const response = await fetch('/api/pnl');
        const data = await response.json();
        updatePnLDisplay(data);
    } catch (error) {
        console.error('Error loading P&L:', error);
    }
}

// Update P&L display
function updatePnLDisplay(data) {
    const total = data.total || 0;
    const realized = data.realized || 0;
    const unrealized = data.unrealized || 0;

    // Update header P&L
    const pnlElement = document.getElementById('total-pnl');
    pnlElement.textContent = formatCurrency(total);
    pnlElement.className = 'pnl-display ' + (total >= 0 ? 'pnl-positive' : 'pnl-negative');

    // Update stats
    document.getElementById('stat-realized').textContent = formatCurrency(realized);
    document.getElementById('stat-realized').className = 'stat-value ' + (realized >= 0 ? 'text-success' : 'text-danger');

    document.getElementById('stat-unrealized').textContent = formatCurrency(unrealized);
    document.getElementById('stat-unrealized').className = 'stat-value ' + (unrealized >= 0 ? 'text-success' : 'text-danger');
}

// Load and display positions
async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const data = await response.json();

        if (data.positions) {
            displayPositions(data.positions);
            document.getElementById('stat-positions').textContent = data.positions.length;
        }
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

// Display positions
function displayPositions(positions) {
    const container = document.getElementById('positions-container');

    if (positions.length === 0) {
        container.innerHTML = '<div class="text-center text-muted p-5">No open positions</div>';
        return;
    }

    let html = '';
    positions.forEach(pos => {
        const pnlClass = pos.unrealized_pnl >= 0 ? 'text-success' : 'text-danger';
        html += `
            <div class="position-card ${pos.lots > 0 ? 'long' : 'short'}">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <h5>${pos.symbol}</h5>
                        <span class="badge ${pos.lots > 0 ? 'badge-buy' : 'badge-sell'}">
                            ${pos.lots > 0 ? 'LONG' : 'SHORT'} ${Math.abs(pos.lots)} lots
                        </span>
                    </div>
                    <div class="col-md-2">
                        <small class="text-muted">Entry</small>
                        <div>${formatCurrency(pos.entry_price)}</div>
                    </div>
                    <div class="col-md-2">
                        <small class="text-muted">Current</small>
                        <div>${formatCurrency(pos.current_price)}</div>
                    </div>
                    <div class="col-md-2">
                        <small class="text-muted">Unrealized P&L</small>
                        <div class="${pnlClass}"><strong>${formatCurrency(pos.unrealized_pnl)}</strong></div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Entry Time</small>
                        <div>${new Date(pos.entry_time).toLocaleString()}</div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Update individual position
function updatePositionDisplay(data) {
    // This will be called on WebSocket updates
    loadPositions(); // Reload all positions for simplicity
}

// Load and display trades
async function loadTrades() {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();

        if (data.trades) {
            displayTrades(data.trades);
        }
    } catch (error) {
        console.error('Error loading trades:', error);
    }
}

// Display trades in table
function displayTrades(trades) {
    const tbody = document.getElementById('trades-table');

    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No trades yet</td></tr>';
        return;
    }

    let html = '';
    trades.slice(-10).reverse().forEach(trade => {
        const pnlClass = trade.pnl >= 0 ? 'text-success' : 'text-danger';
        html += `
            <tr>
                <td>${new Date(trade.timestamp).toLocaleTimeString()}</td>
                <td>${trade.symbol}</td>
                <td><span class="badge ${trade.side === 'buy' ? 'badge-buy' : 'badge-sell'}">${trade.side.toUpperCase()}</span></td>
                <td>${trade.lots}</td>
                <td>${formatCurrency(trade.price)}</td>
                <td class="${pnlClass}">${formatCurrency(trade.pnl)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// Add trade to table (real-time)
function addTradeToTable(trade) {
    loadTrades(); // Reload trades for simplicity
}

// Add trade marker to chart
function addTradeMarker(trade) {
    tradeMarkers.push({
        time: trade.timestamp,
        price: trade.price,
        side: trade.side
    });

    // Update chart with new marker
    if (chartData.length > 0) {
        initChart(); // Re-initialize chart with new markers
    }
}

// Load and display orders
async function loadOrders() {
    try {
        const response = await fetch('/api/orders');
        const data = await response.json();

        if (data.orders) {
            displayOrders(data.orders);
        }
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

// Display orders
function displayOrders(orders) {
    const tbody = document.getElementById('orders-table');

    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No orders yet</td></tr>';
        return;
    }

    let html = '';
    orders.slice(0, 50).forEach(order => {
        html += `
            <tr>
                <td>${new Date(order.time).toLocaleTimeString()}</td>
                <td>${order.symbol}</td>
                <td><span class="badge ${order.side === 'buy' ? 'badge-buy' : 'badge-sell'}">${order.side.toUpperCase()}</span></td>
                <td>${order.quantity}</td>
                <td>${formatCurrency(order.price)}</td>
                <td><span class="badge bg-secondary">${order.status}</span></td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// Load and display strategies
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies');
        const data = await response.json();

        if (data.strategies) {
            displayStrategies(data.strategies);
        }
    } catch (error) {
        console.error('Error loading strategies:', error);
    }
}

// Display strategies
function displayStrategies(strategies) {
    const container = document.getElementById('strategies-container');

    if (strategies.length === 0) {
        container.innerHTML = '<div class="text-center text-muted p-5">No active strategies</div>';
        return;
    }

    let html = '';
    strategies.forEach(strategy => {
        html += `
            <div class="stat-card">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <h5>${strategy.name}</h5>
                        <p class="text-muted mb-0">Market: ${strategy.market}</p>
                    </div>
                    <div class="col-md-3">
                        <span class="status-indicator status-active"></span> Active
                    </div>
                    <div class="col-md-3 text-end">
                        <button class="btn btn-sm btn-outline-danger">Stop</button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Load risk status
async function loadRiskStatus() {
    try {
        const response = await fetch('/api/risk/status');
        const data = await response.json();

        displayRiskStatus(data);
    } catch (error) {
        console.error('Error loading risk status:', error);
    }
}

// Display risk status
function displayRiskStatus(data) {
    // Update trading status
    const statusElement = document.getElementById('stat-status');
    if (data.blocked) {
        statusElement.innerHTML = '<span class="status-indicator status-blocked"></span> Blocked';
        statusElement.parentElement.className = 'stat-value text-danger';
    } else {
        statusElement.innerHTML = '<span class="status-indicator status-active"></span> Active';
        statusElement.parentElement.className = 'stat-value text-success';
    }

    // Update risk limits section
    const limitsHtml = `
        <table class="table">
            <tr>
                <td>Max Daily Loss</td>
                <td class="text-end"><strong>₹${data.limits?.max_daily_loss || 0}</strong></td>
            </tr>
            <tr>
                <td>Max Daily Loss %</td>
                <td class="text-end"><strong>${data.limits?.max_daily_loss_percent || 0}%</strong></td>
            </tr>
            <tr>
                <td>Max Position Size</td>
                <td class="text-end"><strong>${data.limits?.max_position_size || 0} lots</strong></td>
            </tr>
            <tr>
                <td>Max Open Positions</td>
                <td class="text-end"><strong>${data.limits?.max_open_positions || 0}</strong></td>
            </tr>
        </table>
    `;
    document.getElementById('risk-limits').innerHTML = limitsHtml;

    // Update usage section
    const usageHtml = `
        <div class="text-center">
            <div style="font-size: 48px; font-weight: bold;" class="${data.utilization?.loss_limit_used_pct > 80 ? 'text-danger' : 'text-success'}">
                ${data.utilization?.loss_limit_used_pct?.toFixed(1) || 0}%
            </div>
            <p class="text-muted">Loss Limit Used</p>
            <hr>
            <p><strong>${data.utilization?.position_slots_used || 0}</strong> / <strong>${data.limits?.max_open_positions || 0}</strong> Position Slots</p>
        </div>
    `;
    document.getElementById('risk-usage').innerHTML = usageHtml;
}

// Section navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    document.getElementById(`section-${sectionName}`).style.display = 'block';

    // Update active nav
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');

    // Load section-specific data
    switch(sectionName) {
        case 'positions':
            loadPositions();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'strategies':
            loadStrategies();
            break;
        case 'risk':
            loadRiskStatus();
            break;
    }
}

// Start periodic data refresh
function startDataRefresh() {
    // Refresh P&L every 5 seconds
    setInterval(loadPnL, 5000);

    // Refresh positions every 10 seconds
    setInterval(loadPositions, 10000);

    // Refresh risk status every 15 seconds
    setInterval(loadRiskStatus, 15000);
}

// Utility: Format currency
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Utility: Format time
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}
