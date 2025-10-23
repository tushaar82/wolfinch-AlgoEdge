#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: VWAP + Bollinger Bands Strategy with Trailing SL
 Copyright: (c) 2024 Wolfinch Contributors

 Strategy Logic:
 - VWAP for institutional levels
 - Bollinger Bands for volatility and entry/exit
 - Mean reversion + trend following hybrid
'''

from .strategy import Strategy


class VWAP_BB(Strategy):
    """
    VWAP + Bollinger Bands Strategy

    Buy Signal:
    - Price bounces off lower Bollinger Band
    - Price above VWAP (or crossing above)
    - Volume increasing

    Sell Signal:
    - Price reaches upper Bollinger Band
    - Price below VWAP
    """

    config = {
        'period': {
            'default': 100,
            'var': {'type': int, 'min': 50, 'max': 300}
        },
        'bb_period': {
            'default': 20,
            'var': {'type': int, 'min': 10, 'max': 50}
        },
        'bb_std': {
            'default': 2.0,
            'var': {'type': float, 'min': 1.5, 'max': 3.0}
        },
        'trailing_sl_percent': {
            'default': 4,
            'var': {'type': float, 'min': 2, 'max': 8}
        }
    }

    def __init__(self, name, period=100, bb_period=20, bb_std=2.0,
                 trailing_sl_percent=4, *args, **kwargs):

        self.name = name
        self.period = period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.trailing_sl_percent = trailing_sl_percent

        # Register indicators
        self.set_indicator("BB", self.bb_period)
        self.set_indicator("VWAP", 0)
        self.set_indicator("SMA", 20)

        # Trailing SL state
        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        """Generate trading signal"""
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        prev_candle = candles[-2] if len(candles) > 1 else None

        # Get indicators
        bb = self.indicator(candles, 'BB', self.bb_period)
        vwap = self.indicator(candles, 'VWAP', 0)
        volume_avg = self.indicator(candles, 'SMA', 20)

        if None in [bb, vwap]:
            return 0

        current_price = cur_candle.close
        bb_upper = bb['upper']
        bb_middle = bb['middle']
        bb_lower = bb['lower']

        # Update trailing SL
        self._update_trailing_sl(current_price)

        # Check trailing SL hit
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        signal = 0

        # === BUY SIGNAL ===
        # Price bouncing from lower BB
        near_lower_bb = current_price <= bb_lower * 1.02
        bouncing_up = prev_candle and prev_candle.close < bb_lower and current_price >= bb_lower

        # VWAP confirmation
        above_vwap = current_price > vwap
        crossing_vwap = prev_candle and prev_candle.close <= vwap and current_price > vwap

        # Volume confirmation
        volume_high = cur_candle.volume > volume_avg * 1.3 if volume_avg else False

        if bouncing_up and (above_vwap or crossing_vwap) and volume_high:
            signal = 3  # Strong buy
            self.entry_price = current_price
            self.highest_price = current_price
        elif near_lower_bb and above_vwap:
            signal = 2  # Buy
            self.entry_price = current_price
            self.highest_price = current_price
        elif crossing_vwap and current_price > bb_middle:
            signal = 1  # Weak buy

        # === SELL SIGNAL ===
        # Price at upper BB
        near_upper_bb = current_price >= bb_upper * 0.98
        touching_upper = current_price >= bb_upper

        # VWAP confirmation
        below_vwap = current_price < vwap
        crossing_vwap_down = prev_candle and prev_candle.close >= vwap and current_price < vwap

        if touching_upper and (below_vwap or crossing_vwap_down):
            signal = -3  # Strong sell
            self._reset_trailing_sl()
        elif near_upper_bb:
            signal = -2  # Sell
            self._reset_trailing_sl()
        elif crossing_vwap_down:
            signal = -1  # Weak sell

        return signal

    def _update_trailing_sl(self, current_price):
        """Update trailing stop loss"""
        if self.entry_price is None:
            return

        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price

        sl_distance = self.highest_price * (self.trailing_sl_percent / 100)
        self.trailing_sl = self.highest_price - sl_distance

    def _reset_trailing_sl(self):
        """Reset trailing stop loss"""
        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def get_trailing_sl(self):
        """Get current trailing stop loss price"""
        return self.trailing_sl


# EOF
