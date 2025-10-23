#! /usr/bin/env python
'''
 RSI Divergence + Stochastic Strategy
 Detects divergences and uses Stochastic for timing
'''

from .strategy import Strategy


class RSI_Divergence_Stoch(Strategy):
    config = {
        'period': {'default': 100, 'var': {'type': int, 'min': 50, 'max': 300}},
        'rsi_period': {'default': 14, 'var': {'type': int, 'min': 10, 'max': 21}},
        'stoch_k': {'default': 14, 'var': {'type': int, 'min': 10, 'max': 20}},
        'stoch_d': {'default': 3, 'var': {'type': int, 'min': 2, 'max': 5}},
        'stoch_oversold': {'default': 20, 'var': {'type': int, 'min': 10, 'max': 30}},
        'stoch_overbought': {'default': 80, 'var': {'type': int, 'min': 70, 'max': 90}},
        'trailing_sl_percent': {'default': 4, 'var': {'type': float, 'min': 2, 'max': 8}}
    }

    def __init__(self, name, period=100, rsi_period=14, stoch_k=14, stoch_d=3,
                 stoch_oversold=20, stoch_overbought=80, trailing_sl_percent=4, **kwargs):
        self.name = name
        self.period = period
        self.rsi_period = rsi_period
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.stoch_oversold = stoch_oversold
        self.stoch_overbought = stoch_overbought
        self.trailing_sl_percent = trailing_sl_percent

        self.set_indicator("RSI", self.rsi_period)
        self.set_indicator("STOCH", [self.stoch_k, self.stoch_d])

        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        current_price = cur_candle.close

        # Get indicators
        rsi = self.indicator(candles, 'RSI', self.rsi_period)
        rsi_prev = self.indicator(candles, 'RSI', self.rsi_period, history=1)
        stoch = self.indicator(candles, 'STOCH', [self.stoch_k, self.stoch_d])

        if None in [rsi, stoch]:
            return 0

        stoch_k = stoch.get('k', 50)
        stoch_d = stoch.get('d', 50)

        # Update trailing SL
        self._update_trailing_sl(current_price)
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        # Detect bullish divergence (simplified)
        # Price makes lower low but RSI makes higher low
        bullish_divergence = self._detect_bullish_divergence(candles)

        # Detect bearish divergence
        # Price makes higher high but RSI makes lower high
        bearish_divergence = self._detect_bearish_divergence(candles)

        # BUY SIGNAL
        stoch_oversold_cross = stoch_k < self.stoch_oversold and stoch_k > stoch_d
        rsi_oversold = rsi < 30

        if bullish_divergence and stoch_oversold_cross:
            self.entry_price = current_price
            self.highest_price = current_price
            return 3
        elif rsi_oversold and stoch_oversold_cross:
            return 2

        # SELL SIGNAL
        stoch_overbought_cross = stoch_k > self.stoch_overbought and stoch_k < stoch_d
        rsi_overbought = rsi > 70

        if bearish_divergence and stoch_overbought_cross:
            self._reset_trailing_sl()
            return -3
        elif rsi_overbought and stoch_overbought_cross:
            return -2

        return 0

    def _detect_bullish_divergence(self, candles):
        """Simplified bullish divergence detection"""
        if len(candles) < 20:
            return False

        # Compare recent lows
        prices = [c.close for c in candles[-20:]]
        rsis = [self.indicator(candles[:i+1], 'RSI', self.rsi_period) or 50
                for i in range(len(candles)-20, len(candles))]

        if len(prices) < 10 or len(rsis) < 10:
            return False

        # Simple check: if price trending down but RSI trending up
        price_trend = prices[-1] < prices[0]
        rsi_trend = rsis[-1] > rsis[0]

        return price_trend and rsi_trend

    def _detect_bearish_divergence(self, candles):
        """Simplified bearish divergence detection"""
        if len(candles) < 20:
            return False

        prices = [c.close for c in candles[-20:]]
        rsis = [self.indicator(candles[:i+1], 'RSI', self.rsi_period) or 50
                for i in range(len(candles)-20, len(candles))]

        if len(prices) < 10 or len(rsis) < 10:
            return False

        # Simple check: if price trending up but RSI trending down
        price_trend = prices[-1] > prices[0]
        rsi_trend = rsis[-1] < rsis[0]

        return price_trend and rsi_trend

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
