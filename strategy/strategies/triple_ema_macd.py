#! /usr/bin/env python
'''
 Triple EMA Crossover + MACD Strategy
 Strong trend-following strategy with MACD confirmation
'''

from .strategy import Strategy


class Triple_EMA_MACD(Strategy):
    config = {
        'period': {'default': 100, 'var': {'type': int, 'min': 50, 'max': 300}},
        'ema_fast': {'default': 8, 'var': {'type': int, 'min': 5, 'max': 15}},
        'ema_medium': {'default': 13, 'var': {'type': int, 'min': 10, 'max': 25}},
        'ema_slow': {'default': 21, 'var': {'type': int, 'min': 15, 'max': 50}},
        'macd_fast': {'default': 12, 'var': {'type': int, 'min': 8, 'max': 15}},
        'macd_slow': {'default': 26, 'var': {'type': int, 'min': 20, 'max': 35}},
        'macd_signal': {'default': 9, 'var': {'type': int, 'min': 5, 'max': 15}},
        'trailing_sl_percent': {'default': 5, 'var': {'type': float, 'min': 2, 'max': 10}}
    }

    def __init__(self, name, period=100, ema_fast=8, ema_medium=13, ema_slow=21,
                 macd_fast=12, macd_slow=26, macd_signal=9, trailing_sl_percent=5, **kwargs):
        self.name = name
        self.period = period
        self.ema_fast = ema_fast
        self.ema_medium = ema_medium
        self.ema_slow = ema_slow
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.trailing_sl_percent = trailing_sl_percent

        self.set_indicator("EMA", [self.ema_fast, self.ema_medium, self.ema_slow])
        self.set_indicator("MACD", [self.macd_fast, self.macd_slow, self.macd_signal])

        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        current_price = cur_candle.close

        # Get EMAs
        ema_f = self.indicator(candles, 'EMA', self.ema_fast)
        ema_m = self.indicator(candles, 'EMA', self.ema_medium)
        ema_s = self.indicator(candles, 'EMA', self.ema_slow)
        ema_f_prev = self.indicator(candles, 'EMA', self.ema_fast, history=1)
        ema_m_prev = self.indicator(candles, 'EMA', self.ema_medium, history=1)

        # Get MACD
        macd = self.indicator(candles, 'MACD', [self.macd_fast, self.macd_slow, self.macd_signal])

        if None in [ema_f, ema_m, ema_s, macd]:
            return 0

        macd_line = macd['macd']
        signal_line = macd['signal']
        macd_hist = macd['histogram']

        # Update trailing SL
        self._update_trailing_sl(current_price)
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        # BUY SIGNAL
        triple_cross_up = (ema_f > ema_m > ema_s) and (ema_f_prev <= ema_m_prev)
        macd_bullish = macd_line > signal_line and macd_hist > 0

        if triple_cross_up and macd_bullish:
            self.entry_price = current_price
            self.highest_price = current_price
            return 3
        elif (ema_f > ema_m > ema_s) and macd_bullish:
            return 2

        # SELL SIGNAL
        triple_cross_down = (ema_f < ema_m < ema_s) and (ema_f_prev >= ema_m_prev)
        macd_bearish = macd_line < signal_line and macd_hist < 0

        if triple_cross_down and macd_bearish:
            self._reset_trailing_sl()
            return -3
        elif (ema_f < ema_m < ema_s) and macd_bearish:
            return -2

        return 0

    def _update_trailing_sl(self, current_price):
        if self.entry_price is None:
            return
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price
        self.trailing_sl = self.highest_price * (1 - self.trailing_sl_percent / 100)

    def _reset_trailing_sl(self):
        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def get_trailing_sl(self):
        return self.trailing_sl
