#! /usr/bin/env python
'''
 Volume Breakout + ATR Strategy
 Captures breakout moves with volume confirmation and ATR-based stops
'''

from .strategy import Strategy


class Volume_Breakout_ATR(Strategy):
    config = {
        'period': {'default': 100, 'var': {'type': int, 'min': 50, 'max': 300}},
        'breakout_period': {'default': 20, 'var': {'type': int, 'min': 10, 'max': 50}},
        'volume_multiplier': {'default': 2.0, 'var': {'type': float, 'min': 1.5, 'max': 4.0}},
        'atr_period': {'default': 14, 'var': {'type': int, 'min': 10, 'max': 20}},
        'atr_sl_multiplier': {'default': 2.5, 'var': {'type': float, 'min': 1.5, 'max': 4.0}}
    }

    def __init__(self, name, period=100, breakout_period=20, volume_multiplier=2.0,
                 atr_period=14, atr_sl_multiplier=2.5, **kwargs):
        self.name = name
        self.period = period
        self.breakout_period = breakout_period
        self.volume_multiplier = volume_multiplier
        self.atr_period = atr_period
        self.atr_sl_multiplier = atr_sl_multiplier

        self.set_indicator("SMA", 20)
        self.set_indicator("ATR", self.atr_period)

        self.entry_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        current_price = cur_candle.close

        # Calculate recent high/low
        recent_candles = candles[-self.breakout_period:]
        recent_high = max(c.high for c in recent_candles[:-1])
        recent_low = min(c.low for c in recent_candles[:-1])

        # Get volume average
        volume_avg = self.indicator(candles, 'SMA', 20)
        current_volume = cur_candle.volume

        # Get ATR
        atr = self.indicator(candles, 'ATR', self.atr_period)

        if None in [volume_avg, atr]:
            return 0

        # Update trailing SL
        self._update_trailing_sl(current_price, atr)
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        # BUY SIGNAL - Breakout above recent high with volume
        volume_surge = current_volume > volume_avg * self.volume_multiplier
        price_breakout = current_price > recent_high

        if price_breakout and volume_surge:
            self.entry_price = current_price
            return 3
        elif price_breakout:
            return 2

        # SELL SIGNAL - Breakdown below recent low with volume
        price_breakdown = current_price < recent_low

        if price_breakdown and volume_surge:
            self._reset_trailing_sl()
            return -3
        elif price_breakdown:
            return -2

        return 0

    def _update_trailing_sl(self, current_price, atr):
        if self.entry_price is None or atr is None:
            return
        sl_distance = atr * self.atr_sl_multiplier
        new_sl = current_price - sl_distance
        if self.trailing_sl is None or new_sl > self.trailing_sl:
            self.trailing_sl = new_sl

    def _reset_trailing_sl(self):
        self.entry_price = None
        self.trailing_sl = None

    def get_trailing_sl(self):
        return self.trailing_sl
