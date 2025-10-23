#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Enhanced API Server with Authentication and WebSocket
 Copyright: (c) 2024 Wolfinch Contributors
'''

import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, render_template_string, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps

from utils import getLogger
from .auth import get_user_manager, User
from risk import get_risk_manager

log = getLogger('APIServer')
log.setLevel(log.INFO)

# Flask app
app = Flask(__name__, static_folder='web_enhanced', static_url_path='/static')
app.config['SECRET_KEY'] = 'wolfinch-secret-key-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# User manager
user_manager = get_user_manager()

# Global state - will be populated by main bot
g_markets = {}
g_exchanges = {}
g_strategies = {}


@login_manager.user_loader
def load_user(username):
    """Load user for Flask-Login"""
    user = user_manager.get_user(username)
    return user


def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.username != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== Authentication Routes ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = user_manager.authenticate(username, password)
    if user:
        login_user(user, remember=True)
        session.permanent = True
        log.info(f"User logged in: {username}")
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint"""
    username = current_user.username
    logout_user()
    log.info(f"User logged out: {username}")
    return jsonify({'success': True})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    return jsonify({'authenticated': False})


@app.route('/api/auth/register', methods=['POST'])
@admin_required
def register():
    """Register new user (admin only)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    success, message = user_manager.create_user(username, password, email)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'error': message}), 400


@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    success, message = user_manager.change_password(
        current_user.username, old_password, new_password
    )
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'error': message}), 400


# ==================== Market Data Routes ====================

@app.route('/api/markets', methods=['GET'])
@login_required
def get_markets():
    """Get all available markets"""
    markets = []
    for market_key, market in g_markets.items():
        markets.append({
            'key': market_key,
            'exchange': market.exchange.name if hasattr(market, 'exchange') else 'unknown',
            'product': market.product.get_name() if hasattr(market, 'product') else market_key,
            'status': 'active' if hasattr(market, 'running') and market.running else 'inactive'
        })
    return jsonify({'markets': markets})


@app.route('/api/markets/<market_key>/candles', methods=['GET'])
@login_required
def get_market_candles(market_key):
    """Get candle data for a market"""
    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 1000)  # Max 1000 candles

    market = g_markets.get(market_key)
    if not market:
        return jsonify({'error': 'Market not found'}), 404

    try:
        candles = []
        candle_list = market.candles[-limit:] if hasattr(market, 'candles') else []

        for candle in candle_list:
            candles.append({
                'time': int(candle.time.timestamp() * 1000) if hasattr(candle, 'time') else 0,
                'open': float(candle.open),
                'high': float(candle.high),
                'low': float(candle.low),
                'close': float(candle.close),
                'volume': float(candle.volume) if hasattr(candle, 'volume') else 0
            })

        return jsonify({'candles': candles})
    except Exception as e:
        log.error(f"Error getting candles: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets/<market_key>/indicators', methods=['GET'])
@login_required
def get_market_indicators(market_key):
    """Get indicator values for a market"""
    market = g_markets.get(market_key)
    if not market:
        return jsonify({'error': 'Market not found'}), 404

    try:
        indicators = {}
        if hasattr(market, 'strategy') and market.strategy:
            strategy = market.strategy
            # Get indicator list from strategy
            if hasattr(strategy, 'get_indicators'):
                indicator_list = strategy.get_indicators()
                for name, periods in indicator_list.items():
                    indicators[name] = periods

        return jsonify({'indicators': indicators})
    except Exception as e:
        log.error(f"Error getting indicators: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Position & Order Routes ====================

@app.route('/api/positions', methods=['GET'])
@login_required
def get_positions():
    """Get all open positions"""
    try:
        risk_manager = get_risk_manager()
        positions = risk_manager.get_all_positions()

        position_list = []
        for symbol, pos in positions.items():
            position_list.append({
                'symbol': symbol,
                'lots': pos.get('lots', 0),
                'entry_price': float(pos.get('entry_price', 0)),
                'current_price': float(pos.get('current_price', 0)),
                'unrealized_pnl': float(pos.get('unrealized_pnl', 0)),
                'entry_time': pos.get('entry_time', '')
            })

        return jsonify({'positions': position_list})
    except Exception as e:
        log.error(f"Error getting positions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    """Get order history"""
    try:
        # Get orders from markets
        orders = []
        for market_key, market in g_markets.items():
            if hasattr(market, 'orders'):
                for order in market.orders[-100:]:  # Last 100 orders
                    orders.append({
                        'id': order.id if hasattr(order, 'id') else '',
                        'symbol': market.product.get_name() if hasattr(market, 'product') else '',
                        'side': order.side if hasattr(order, 'side') else '',
                        'quantity': float(order.size) if hasattr(order, 'size') else 0,
                        'price': float(order.price) if hasattr(order, 'price') else 0,
                        'status': order.status if hasattr(order, 'status') else '',
                        'time': order.time.isoformat() if hasattr(order, 'time') else ''
                    })

        orders.sort(key=lambda x: x['time'], reverse=True)
        return jsonify({'orders': orders})
    except Exception as e:
        log.error(f"Error getting orders: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades', methods=['GET'])
@login_required
def get_trades():
    """Get trade history"""
    try:
        risk_manager = get_risk_manager()
        trades = risk_manager.get_daily_trades()

        return jsonify({'trades': trades})
    except Exception as e:
        log.error(f"Error getting trades: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== P&L & Risk Routes ====================

@app.route('/api/pnl', methods=['GET'])
@login_required
def get_pnl():
    """Get current P&L"""
    try:
        risk_manager = get_risk_manager()
        pnl = risk_manager.get_daily_pnl()

        return jsonify({
            'realized': float(pnl['realized']),
            'unrealized': float(pnl['unrealized']),
            'total': float(pnl['total'])
        })
    except Exception as e:
        log.error(f"Error getting P&L: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/status', methods=['GET'])
@login_required
def get_risk_status():
    """Get risk management status"""
    try:
        risk_manager = get_risk_manager()
        stats = risk_manager.get_stats()

        return jsonify(stats)
    except Exception as e:
        log.error(f"Error getting risk status: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Strategy Routes ====================

@app.route('/api/strategies', methods=['GET'])
@login_required
def get_strategies():
    """Get all strategies"""
    strategies = []
    for market_key, market in g_markets.items():
        if hasattr(market, 'strategy') and market.strategy:
            strategy = market.strategy
            strategies.append({
                'market': market_key,
                'name': strategy.name if hasattr(strategy, 'name') else 'Unknown',
                'status': 'active'
            })

    return jsonify({'strategies': strategies})


# ==================== WebSocket Events ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    log.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Wolfinch'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    log.info(f"Client disconnected: {request.sid}")


@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to real-time updates"""
    room = data.get('channel', 'general')
    join_room(room)
    log.info(f"Client {request.sid} subscribed to {room}")
    emit('subscribed', {'channel': room})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from updates"""
    room = data.get('channel', 'general')
    leave_room(room)
    log.info(f"Client {request.sid} unsubscribed from {room}")
    emit('unsubscribed', {'channel': room})


# ==================== Broadcasting Functions ====================

def broadcast_candle_update(market_key, candle):
    """Broadcast candle update to subscribed clients"""
    try:
        data = {
            'market': market_key,
            'time': int(candle.time.timestamp() * 1000),
            'open': float(candle.open),
            'high': float(candle.high),
            'low': float(candle.low),
            'close': float(candle.close),
            'volume': float(candle.volume) if hasattr(candle, 'volume') else 0
        }
        socketio.emit('candle_update', data, room='candles')
    except Exception as e:
        log.error(f"Error broadcasting candle: {e}")


def broadcast_position_update(symbol, position):
    """Broadcast position update"""
    try:
        data = {
            'symbol': symbol,
            'lots': position.get('lots', 0),
            'entry_price': float(position.get('entry_price', 0)),
            'current_price': float(position.get('current_price', 0)),
            'unrealized_pnl': float(position.get('unrealized_pnl', 0)),
            'trailing_sl': float(position.get('trailing_sl', 0)) if position.get('trailing_sl') else None
        }
        socketio.emit('position_update', data, room='positions')
    except Exception as e:
        log.error(f"Error broadcasting position: {e}")


def broadcast_pnl_update(pnl):
    """Broadcast P&L update"""
    try:
        data = {
            'realized': float(pnl['realized']),
            'unrealized': float(pnl['unrealized']),
            'total': float(pnl['total']),
            'timestamp': datetime.now().isoformat()
        }
        socketio.emit('pnl_update', data, room='pnl')
    except Exception as e:
        log.error(f"Error broadcasting P&L: {e}")


def broadcast_trade_update(trade):
    """Broadcast trade execution"""
    try:
        socketio.emit('trade_update', trade, room='trades')
    except Exception as e:
        log.error(f"Error broadcasting trade: {e}")


# ==================== Static File Routes ====================

@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('web_enhanced', 'index.html')


@app.route('/login')
def login_page():
    """Serve login page"""
    return send_from_directory('web_enhanced', 'login.html')


# ==================== Server Initialization ====================

def init_api_server(markets=None, exchanges=None):
    """Initialize API server with market data"""
    global g_markets, g_exchanges
    if markets:
        g_markets = markets
    if exchanges:
        g_exchanges = exchanges
    log.info("API server initialized")


def run_api_server(host='0.0.0.0', port=8080):
    """Run the API server"""
    log.info(f"Starting enhanced API server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False)


# EOF
