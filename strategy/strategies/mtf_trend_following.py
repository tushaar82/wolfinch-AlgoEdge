#! /usr/bin/env python
'''
 Multi-Timeframe Trend Following Strategy
 Aligns multiple timeframes for high-probability trend trades
'''

from .strategy import Strategy


class MTF_Trend_Following(Strategy):
    config = {
        'period': {'default': 100, 'var': {'type': int, 'min': 50, 'max': 300}},
        'ema_short': {'default': 21, 'var': {'type': int, 'min': 10, 'max': 30}},
        'ema_long': {'default': 50, 'var': {'type': int, 'min': 30, 'max': 100}},
        'ema_trend': {'default': 200, 'var': {'type': int, 'min': 100, 'max': 300}},
        'rsi_period': {'default': 14, 'var': {'type': int, 'min': 10, 'max': 21}},
        'atr_period': {'default': 14, 'var': {'type': int, 'min': 10, 'max': 20}},
        'trailing_atr_mult': {'default': 2.0, 'var': {'type': float, 'min': 1.0, 'max': 4.0}}
    }

    def __init__(self, name, period=100, ema_short=21, ema_long=50, ema_trend=200,
                 rsi_period=14, atr_period=14, trailing_atr_mult=2.0, **kwargs):
        self.name = name
        self.period = period
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.ema_trend = ema_trend
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.trailing_atr_mult = trailing_atr_mult

        self.set_indicator("EMA", [self.ema_short, self.ema_long, self.ema_trend])
        self.set_indicator("RSI", self.rsi_period)
        self.set_indicator("ATR", self.atr_period)

        self.entry_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        current_price = cur_candle.close

        # Get EMAs
        ema_s = self.indicator(candles, 'EMA', self.ema_short)
        ema_l = self.indicator(candles, 'EMA', self.ema_long)
        ema_t = self.indicator(candles, 'EMA', self.ema_trend)
        ema_s_prev = self.indicator(candles, 'EMA', self.ema_short, history=1)
        ema_l_prev = self.indicator(candles, 'EMA', self.ema_long, history=1)

        # Get RSI and ATR
        rsi = self.indicator(candles, 'RSI', self.rsi_period)
        atr = self.indicator(candles, 'ATR', self.atr_period)

        if None in [ema_s, ema_l, ema_t, rsi, atr]:
            return 0

        # Update trailing SL
        self._update_trailing_sl(current_price, atr)
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        # Determine overall trend
        uptrend = current_price > ema_t and ema_s > ema_l
        downtrend = current_price < ema_t and ema_s < ema_l

        # BUY SIGNAL
        ema_cross_up = (ema_s > ema_l) and (ema_s_prev <= ema_l_prev)
        rsi_healthy = 30 < rsi < 70

        if uptrend and ema_cross_up and rsi_healthy:
            self.entry_price = current_price
            return 3
        elif uptrend and ema_cross_up:
            self.entry_price = current_price
            return 2
        elif uptrend and current_price > ema_s:
            return 1

        # SELL SIGNAL
        ema_cross_down = (ema_s < ema_l) and (ema_s_prev >= ema_l_prev)

        if downtrend and ema_cross_down:
            self._reset_trailing_sl()
            return -3
        elif ema_cross_down:
            self._reset_trailing_sl()
            return -2
        elif downtrend and current_price < ema_s:
            return -1

        return 0

    def _update_trailing_sl(self, current_price, atr):
        if self.entry_price is None or atr is None:
            return
        sl_distance = atr * self.trailing_atr_mult
        new_sl = current_price - sl_distance
        if self.trailing_sl is None or new_sl > self.trailing_sl:
            self.trailing_sl = new_sl

    def _reset_trailing_sl(self):
        self.entry_price = None
        self.trailing_sl = None

    def get_trailing_sl(self):
        return self.trailing_sl
