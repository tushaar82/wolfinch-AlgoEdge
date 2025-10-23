#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Risk Management System
 Copyright: (c) 2024 Wolfinch Contributors

 Features:
 - Daily loss limit tracking
 - Position size management
 - Max open positions control
 - Order blocking when limits breached
 - Comprehensive logging
'''

import json
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from utils import getLogger

log = getLogger('RiskManager')
log.setLevel(log.INFO)


class RiskManager:
    """
    Centralized Risk Management System
    Enforces trading limits and protects capital
    """

    def __init__(self, config=None):
        """
        Initialize Risk Manager

        Args:
            config: Risk management configuration dict
        """
        self.config = config or {}

        # Daily loss limits
        self.max_daily_loss = self.config.get('max_daily_loss', 0)  # Absolute INR amount
        self.max_daily_loss_percent = self.config.get('max_daily_loss_percent', 0)  # Percentage

        # Position limits
        self.max_position_size = self.config.get('max_position_size', 0)  # Max lots per position
        self.max_open_positions = self.config.get('max_open_positions', 0)  # Max concurrent positions

        # State tracking
        self.daily_pnl = 0
        self.current_date = date.today()
        self.open_positions = {}
        self.daily_trades = []
        self.blocked = False
        self.block_reason = None

        # Starting capital (for percentage calculations)
        self.starting_capital = self.config.get('starting_capital', 100000)

        # Persistence
        self.state_file = Path('data/risk_state.json')
        self._load_state()

        log.info(f"Risk Manager initialized - Daily Loss Limit: ₹{self.max_daily_loss}, "
                 f"Max Positions: {self.max_open_positions}")

    def _load_state(self):
        """Load persisted state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Check if it's a new day - reset daily counters
                saved_date = datetime.strptime(state.get('date'), '%Y-%m-%d').date()
                if saved_date != self.current_date:
                    log.info("New trading day - resetting daily counters")
                    self._reset_daily_counters()
                else:
                    # Restore state
                    self.daily_pnl = state.get('daily_pnl', 0)
                    self.open_positions = state.get('open_positions', {})
                    self.daily_trades = state.get('daily_trades', [])
                    self.blocked = state.get('blocked', False)
                    self.block_reason = state.get('block_reason', None)

                    log.info(f"Loaded state - Daily P&L: ₹{self.daily_pnl:.2f}, "
                             f"Open Positions: {len(self.open_positions)}, Blocked: {self.blocked}")
        except Exception as e:
            log.error(f"Error loading risk state: {e}")
            self._reset_daily_counters()

    def _save_state(self):
        """Persist state to file"""
        try:
            # Ensure data directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {
                'date': self.current_date.strftime('%Y-%m-%d'),
                'daily_pnl': float(self.daily_pnl),
                'open_positions': self.open_positions,
                'daily_trades': self.daily_trades,
                'blocked': self.blocked,
                'block_reason': self.block_reason,
                'timestamp': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            log.error(f"Error saving risk state: {e}")

    def _reset_daily_counters(self):
        """Reset counters for new trading day"""
        log.info("Resetting daily counters for new trading day")
        self.daily_pnl = 0
        self.daily_trades = []
        self.blocked = False
        self.block_reason = None
        self.current_date = date.today()
        self._save_state()

    def can_place_order(self, symbol, side, lots, price):
        """
        Check if order can be placed based on risk limits

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            lots: Number of lots
            price: Order price

        Returns:
            tuple: (allowed: bool, reason: str)
        """
        # Check if new day - reset counters
        if date.today() != self.current_date:
            self._reset_daily_counters()

        # Check if already blocked
        if self.blocked:
            return False, f"Trading blocked: {self.block_reason}"

        # Check daily loss limit
        if self.max_daily_loss > 0 and abs(self.daily_pnl) >= self.max_daily_loss:
            self.blocked = True
            self.block_reason = f"Daily loss limit reached: ₹{abs(self.daily_pnl):.2f}"
            self._save_state()
            log.critical(self.block_reason)
            return False, self.block_reason

        # Check daily loss percentage limit
        if self.max_daily_loss_percent > 0:
            loss_percent = (abs(self.daily_pnl) / self.starting_capital) * 100
            if loss_percent >= self.max_daily_loss_percent:
                self.blocked = True
                self.block_reason = f"Daily loss % limit reached: {loss_percent:.2f}%"
                self._save_state()
                log.critical(self.block_reason)
                return False, self.block_reason

        # Check max position size
        if self.max_position_size > 0 and lots > self.max_position_size:
            reason = f"Position size {lots} exceeds max {self.max_position_size} lots"
            log.warning(reason)
            return False, reason

        # Check max open positions (for new positions)
        if side == 'buy' and self.max_open_positions > 0:
            if symbol not in self.open_positions:
                # New position
                if len(self.open_positions) >= self.max_open_positions:
                    reason = f"Max open positions {self.max_open_positions} reached"
                    log.warning(reason)
                    return False, reason

        # All checks passed
        return True, "OK"

    def record_trade(self, symbol, side, lots, price, pnl=0, trade_id=None):
        """
        Record a trade execution

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            lots: Number of lots
            price: Execution price
            pnl: Realized P&L (for exit trades)
            trade_id: Unique trade identifier
        """
        trade = {
            'trade_id': trade_id or f"{symbol}_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'lots': lots,
            'price': float(price),
            'pnl': float(pnl)
        }

        self.daily_trades.append(trade)

        # Update P&L
        if pnl != 0:
            self.daily_pnl += pnl
            log.info(f"Trade P&L: ₹{pnl:.2f}, Daily P&L: ₹{self.daily_pnl:.2f}")

        # Update positions
        if side == 'buy':
            if symbol not in self.open_positions:
                self.open_positions[symbol] = {
                    'lots': lots,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat(),
                    'current_price': price,
                    'unrealized_pnl': 0
                }
                log.info(f"New position opened: {symbol} @ ₹{price}, Lots: {lots}")
            else:
                # Add to existing position (averaging)
                pos = self.open_positions[symbol]
                total_lots = pos['lots'] + lots
                avg_price = ((pos['lots'] * pos['entry_price']) + (lots * price)) / total_lots
                pos['lots'] = total_lots
                pos['entry_price'] = avg_price
                log.info(f"Position increased: {symbol} @ ₹{avg_price:.2f}, Lots: {total_lots}")

        elif side == 'sell':
            if symbol in self.open_positions:
                pos = self.open_positions[symbol]
                pos['lots'] -= lots

                # Position fully closed
                if pos['lots'] <= 0:
                    log.info(f"Position closed: {symbol}, Realized P&L: ₹{pnl:.2f}")
                    del self.open_positions[symbol]
                else:
                    log.info(f"Position reduced: {symbol}, Remaining lots: {pos['lots']}")

        self._save_state()

    def update_position_price(self, symbol, current_price):
        """
        Update current price for open position and calculate unrealized P&L

        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        if symbol in self.open_positions:
            pos = self.open_positions[symbol]
            pos['current_price'] = current_price

            # Calculate unrealized P&L
            price_diff = current_price - pos['entry_price']
            pos['unrealized_pnl'] = price_diff * pos['lots']

            log.debug(f"Position update: {symbol} @ ₹{current_price:.2f}, "
                     f"Unrealized P&L: ₹{pos['unrealized_pnl']:.2f}")

            self._save_state()

    def get_position(self, symbol):
        """Get position details for a symbol"""
        return self.open_positions.get(symbol, None)

    def get_all_positions(self):
        """Get all open positions"""
        return self.open_positions

    def get_daily_pnl(self):
        """Get current daily P&L (realized + unrealized)"""
        realized_pnl = self.daily_pnl

        # Add unrealized P&L from open positions
        unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.open_positions.values())

        return {
            'realized': realized_pnl,
            'unrealized': unrealized_pnl,
            'total': realized_pnl + unrealized_pnl
        }

    def get_daily_trades(self):
        """Get all trades for current day"""
        return self.daily_trades

    def get_stats(self):
        """Get comprehensive risk statistics"""
        pnl = self.get_daily_pnl()

        return {
            'date': self.current_date.strftime('%Y-%m-%d'),
            'daily_pnl': pnl,
            'open_positions': len(self.open_positions),
            'daily_trades': len(self.daily_trades),
            'blocked': self.blocked,
            'block_reason': self.block_reason,
            'limits': {
                'max_daily_loss': self.max_daily_loss,
                'max_daily_loss_percent': self.max_daily_loss_percent,
                'max_position_size': self.max_position_size,
                'max_open_positions': self.max_open_positions
            },
            'utilization': {
                'loss_limit_used_pct': (abs(pnl['total']) / self.max_daily_loss * 100)
                                       if self.max_daily_loss > 0 else 0,
                'position_slots_used': len(self.open_positions),
                'position_slots_available': self.max_open_positions - len(self.open_positions)
            }
        }

    def reset_block(self):
        """
        Manually reset trading block
        Use with caution - typically only for new trading day
        """
        log.warning("Manually resetting trading block")
        self.blocked = False
        self.block_reason = None
        self._save_state()

    def close_all_positions(self):
        """
        Emergency: Close all positions
        Returns list of positions that need to be closed
        """
        log.critical("EMERGENCY: Close all positions requested")
        positions_to_close = list(self.open_positions.keys())
        return positions_to_close

    def __str__(self):
        stats = self.get_stats()
        pnl = stats['daily_pnl']
        return (f"RiskManager(P&L: ₹{pnl['total']:.2f}, "
                f"Positions: {stats['open_positions']}/{self.max_open_positions}, "
                f"Blocked: {self.blocked})")


# Global risk manager instance
_global_risk_manager = None


def get_risk_manager(config=None):
    """Get global risk manager instance"""
    global _global_risk_manager
    if _global_risk_manager is None:
        _global_risk_manager = RiskManager(config)
    return _global_risk_manager


def init_risk_manager(config):
    """Initialize global risk manager with config"""
    global _global_risk_manager
    _global_risk_manager = RiskManager(config)
    return _global_risk_manager


# EOF
