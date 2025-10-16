#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: Trade Logger - Save all trades to InfluxDB with minute details
#
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.
# 
#  Wolfinch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  Wolfinch is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with Wolfinch.  If not, see <https://www.gnu.org/licenses/>.

import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils import getLogger

log = getLogger('TradeLogger')
log.setLevel(log.INFO)


class TradeLogger:
    """
    Comprehensive trade logger for InfluxDB
    
    Logs every trade with complete details:
    - Order information (ID, type, side, status)
    - Execution details (price, size, fees)
    - Market conditions (current price, volume)
    - Strategy information (signal strength, indicators)
    - Performance metrics (P&L, ROI, duration)
    - Risk metrics (stop loss, take profit)
    """
    
    def __init__(self):
        """Initialize trade logger"""
        self.influx = None
        self.redis = None
        self.enabled = False
        
        try:
            from .influx_db import get_influx_db
            from .redis_cache import get_redis_cache
            
            self.influx = get_influx_db()
            self.redis = get_redis_cache()
            
            if self.influx and self.influx.is_enabled():
                self.enabled = True
                log.info("Trade logger initialized with InfluxDB")
            else:
                log.warning("InfluxDB not available - trade logging disabled")
        except Exception as e:
            log.error(f"Failed to initialize trade logger: {e}")
    
    def is_enabled(self) -> bool:
        """Check if trade logging is enabled"""
        return self.enabled
    
    def log_order_placed(self, exchange: str, product: str, order: Any, 
                        market_data: Optional[Dict] = None, 
                        strategy_data: Optional[Dict] = None) -> bool:
        """
        Log when an order is placed
        
        Args:
            exchange: Exchange name
            product: Product ID
            order: Order object
            market_data: Current market conditions
            strategy_data: Strategy signals and indicators
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            # Build trade data
            trade_data = {
                'exchange': exchange,
                'product': product,
                'order_id': str(order.id) if hasattr(order, 'id') else 'unknown',
                'side': str(order.side) if hasattr(order, 'side') else 'unknown',
                'order_type': str(order.type) if hasattr(order, 'type') else 'market',
                'status': 'placed',
                'price': float(order.price) if hasattr(order, 'price') else 0.0,
                'size': float(order.size) if hasattr(order, 'size') else 0.0,
                'timestamp': timestamp
            }
            
            # Add market data if available
            if market_data:
                trade_data.update({
                    'market_price': float(market_data.get('price', 0)),
                    'market_volume': float(market_data.get('volume', 0)),
                    'market_bid': float(market_data.get('bid', 0)),
                    'market_ask': float(market_data.get('ask', 0)),
                })
            
            # Add strategy data if available
            if strategy_data:
                trade_data.update({
                    'signal_strength': float(strategy_data.get('signal_strength', 0)),
                    'strategy_name': str(strategy_data.get('strategy', 'unknown')),
                    'stop_loss': float(strategy_data.get('stop_loss', 0)),
                    'take_profit': float(strategy_data.get('take_profit', 0)),
                })
            
            # Write to InfluxDB
            self._write_trade_event('order_placed', trade_data)
            
            log.info(f"Logged order placed: {order.side} {order.size} {product} @ {order.price}")
            return True
            
        except Exception as e:
            log.error(f"Error logging order placed: {e}")
            return False
    
    def log_order_filled(self, exchange: str, product: str, order: Any,
                        fill_price: float, fill_size: float, fee: float = 0.0,
                        market_data: Optional[Dict] = None) -> bool:
        """
        Log when an order is filled
        
        Args:
            exchange: Exchange name
            product: Product ID
            order: Order object
            fill_price: Actual fill price
            fill_size: Actual fill size
            fee: Transaction fee
            market_data: Market conditions at fill time
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'order_id': str(order.id) if hasattr(order, 'id') else 'unknown',
                'side': str(order.side) if hasattr(order, 'side') else 'unknown',
                'status': 'filled',
                'fill_price': float(fill_price),
                'fill_size': float(fill_size),
                'fee': float(fee),
                'total_value': float(fill_price * fill_size),
                'total_cost': float(fill_price * fill_size + fee),
                'timestamp': timestamp
            }
            
            # Add market data
            if market_data:
                trade_data.update({
                    'market_price': float(market_data.get('price', 0)),
                    'slippage': float(fill_price - market_data.get('price', fill_price)),
                })
            
            # Write to InfluxDB
            self._write_trade_event('order_filled', trade_data)
            
            log.info(f"Logged order filled: {order.side} {fill_size} {product} @ {fill_price}")
            return True
            
        except Exception as e:
            log.error(f"Error logging order filled: {e}")
            return False
    
    def log_order_cancelled(self, exchange: str, product: str, order: Any,
                           reason: str = 'user_cancelled') -> bool:
        """Log when an order is cancelled"""
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'order_id': str(order.id) if hasattr(order, 'id') else 'unknown',
                'side': str(order.side) if hasattr(order, 'side') else 'unknown',
                'status': 'cancelled',
                'reason': reason,
                'timestamp': timestamp
            }
            
            self._write_trade_event('order_cancelled', trade_data)
            
            log.info(f"Logged order cancelled: {order.id} - {reason}")
            return True
            
        except Exception as e:
            log.error(f"Error logging order cancelled: {e}")
            return False
    
    def log_position_opened(self, exchange: str, product: str, position: Any,
                           entry_price: float, size: float, 
                           strategy_data: Optional[Dict] = None) -> bool:
        """
        Log when a position is opened
        
        Args:
            exchange: Exchange name
            product: Product ID
            position: Position object
            entry_price: Entry price
            size: Position size
            strategy_data: Strategy information
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'position_id': str(position.id) if hasattr(position, 'id') else 'unknown',
                'side': 'long' if size > 0 else 'short',
                'entry_price': float(entry_price),
                'size': abs(float(size)),
                'position_value': float(entry_price * abs(size)),
                'timestamp': timestamp
            }
            
            # Add strategy data
            if strategy_data:
                trade_data.update({
                    'strategy_name': str(strategy_data.get('strategy', 'unknown')),
                    'signal_strength': float(strategy_data.get('signal_strength', 0)),
                    'stop_loss_price': float(strategy_data.get('stop_loss', 0)),
                    'take_profit_price': float(strategy_data.get('take_profit', 0)),
                    'risk_reward_ratio': float(strategy_data.get('risk_reward', 0)),
                })
            
            self._write_trade_event('position_opened', trade_data)
            
            log.info(f"Logged position opened: {size} {product} @ {entry_price}")
            return True
            
        except Exception as e:
            log.error(f"Error logging position opened: {e}")
            return False
    
    def log_position_closed(self, exchange: str, product: str, position: Any,
                           exit_price: float, pnl: float, pnl_percent: float,
                           duration_seconds: int, reason: str = 'strategy') -> bool:
        """
        Log when a position is closed
        
        Args:
            exchange: Exchange name
            product: Product ID
            position: Position object
            exit_price: Exit price
            pnl: Profit/Loss in currency
            pnl_percent: Profit/Loss percentage
            duration_seconds: How long position was held
            reason: Reason for closing (strategy, stop_loss, take_profit, etc.)
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'position_id': str(position.id) if hasattr(position, 'id') else 'unknown',
                'exit_price': float(exit_price),
                'pnl': float(pnl),
                'pnl_percent': float(pnl_percent),
                'duration_seconds': int(duration_seconds),
                'duration_minutes': int(duration_seconds / 60),
                'duration_hours': float(duration_seconds / 3600),
                'close_reason': reason,
                'win': 1 if pnl > 0 else 0,
                'loss': 1 if pnl < 0 else 0,
                'timestamp': timestamp
            }
            
            # Add entry data if available
            if hasattr(position, 'entry_price'):
                trade_data['entry_price'] = float(position.entry_price)
                trade_data['price_change'] = float(exit_price - position.entry_price)
                trade_data['price_change_percent'] = float((exit_price - position.entry_price) / position.entry_price * 100)
            
            if hasattr(position, 'size'):
                trade_data['size'] = abs(float(position.size))
            
            self._write_trade_event('position_closed', trade_data)
            
            log.info(f"Logged position closed: {product} P&L: {pnl:.2f} ({pnl_percent:.2f}%) - {reason}")
            return True
            
        except Exception as e:
            log.error(f"Error logging position closed: {e}")
            return False
    
    def log_stop_loss_hit(self, exchange: str, product: str, position: Any,
                         stop_price: float, current_price: float, loss: float) -> bool:
        """Log when stop loss is triggered"""
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'position_id': str(position.id) if hasattr(position, 'id') else 'unknown',
                'event_type': 'stop_loss',
                'stop_price': float(stop_price),
                'trigger_price': float(current_price),
                'loss': float(loss),
                'timestamp': timestamp
            }
            
            self._write_trade_event('risk_event', trade_data)
            
            log.warning(f"Logged stop loss hit: {product} @ {current_price} (loss: {loss})")
            return True
            
        except Exception as e:
            log.error(f"Error logging stop loss: {e}")
            return False
    
    def log_take_profit_hit(self, exchange: str, product: str, position: Any,
                           target_price: float, current_price: float, profit: float) -> bool:
        """Log when take profit is triggered"""
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            trade_data = {
                'exchange': exchange,
                'product': product,
                'position_id': str(position.id) if hasattr(position, 'id') else 'unknown',
                'event_type': 'take_profit',
                'target_price': float(target_price),
                'trigger_price': float(current_price),
                'profit': float(profit),
                'timestamp': timestamp
            }
            
            self._write_trade_event('risk_event', trade_data)
            
            log.info(f"Logged take profit hit: {product} @ {current_price} (profit: {profit})")
            return True
            
        except Exception as e:
            log.error(f"Error logging take profit: {e}")
            return False
    
    def log_performance_snapshot(self, exchange: str, product: str, 
                                performance_data: Dict) -> bool:
        """
        Log periodic performance snapshot
        
        Args:
            exchange: Exchange name
            product: Product ID
            performance_data: Dict with performance metrics
        """
        if not self.enabled:
            return False
        
        try:
            timestamp = int(time.time())
            
            metric_data = {
                'exchange': exchange,
                'product': product,
                'timestamp': timestamp
            }
            metric_data.update(performance_data)
            
            self._write_trade_event('performance_snapshot', metric_data)
            
            return True
            
        except Exception as e:
            log.error(f"Error logging performance snapshot: {e}")
            return False
    
    def _write_trade_event(self, event_type: str, data: Dict) -> bool:
        """
        Write trade event to InfluxDB
        
        Args:
            event_type: Type of event (order_placed, order_filled, etc.)
            data: Event data
        """
        if not self.influx:
            return False
        
        try:
            from influxdb_client import Point, WritePrecision
            
            # Create point
            point = Point("trade_event") \
                .tag("event_type", event_type) \
                .tag("exchange", data.get('exchange', 'unknown')) \
                .tag("product", data.get('product', 'unknown'))
            
            # Add tags
            if 'order_id' in data:
                point = point.tag("order_id", str(data['order_id']))
            if 'position_id' in data:
                point = point.tag("position_id", str(data['position_id']))
            if 'side' in data:
                point = point.tag("side", str(data['side']))
            if 'status' in data:
                point = point.tag("status", str(data['status']))
            if 'strategy_name' in data:
                point = point.tag("strategy", str(data['strategy_name']))
            if 'close_reason' in data:
                point = point.tag("close_reason", str(data['close_reason']))
            
            # Add fields (numeric values)
            for key, value in data.items():
                if key not in ['exchange', 'product', 'order_id', 'position_id', 
                              'side', 'status', 'strategy_name', 'close_reason', 'timestamp']:
                    if isinstance(value, (int, float)):
                        point = point.field(key, float(value))
                    elif isinstance(value, str):
                        point = point.field(key + "_str", value)
            
            # Set timestamp
            point = point.time(data.get('timestamp', int(time.time())), WritePrecision.S)
            
            # Write to InfluxDB
            self.influx.write_api.write(bucket=self.influx.bucket, org=self.influx.org, record=point)
            
            return True
            
        except Exception as e:
            log.error(f"Error writing trade event to InfluxDB: {e}")
            return False


# Global trade logger instance
_trade_logger = None

def init_trade_logger() -> TradeLogger:
    """Initialize global trade logger"""
    global _trade_logger
    _trade_logger = TradeLogger()
    return _trade_logger

def get_trade_logger() -> Optional[TradeLogger]:
    """
    Get global trade logger instance
    Returns None if not initialized - call init_trade_logger() first!
    """
    global _trade_logger
    return _trade_logger

# EOF
