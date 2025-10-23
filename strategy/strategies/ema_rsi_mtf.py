#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Multi-Timeframe EMA + RSI Strategy with Trailing SL
 Copyright: (c) 2024 Wolfinch Contributors

 Strategy Logic:
 - Uses multiple timeframes for confirmation
 - EMA crossover for trend direction
 - RSI for entry timing
 - Trailing stop loss for profit protection
'''

from .strategy import Strategy


class EMA_RSI_MTF(Strategy):
    """
    Multi-Timeframe EMA + RSI Strategy

    Buy Signal:
    - Fast EMA > Medium EMA > Slow EMA (uptrend)
    - Higher timeframe confirms uptrend
    - RSI crosses above oversold level
    - Volume confirmation

    Sell Signal:
    - Fast EMA < Medium EMA < Slow EMA (downtrend)
    - Higher timeframe confirms downtrend
    - RSI crosses below overbought level
    """

    config = {
        'period': {
            'default': 100,
            'var': {'type': int, 'min': 50, 'max': 300}
        },
        'ema_fast': {
            'default': 9,
            'var': {'type': int, 'min': 5, 'max': 20}
        },
        'ema_medium': {
            'default': 21,
            'var': {'type': int, 'min': 15, 'max': 50}
        },
        'ema_slow': {
            'default': 50,
            'var': {'type': int, 'min': 30, 'max': 100}
        },
        'rsi_period': {
            'default': 14,
            'var': {'type': int, 'min': 7, 'max': 30}
        },
        'rsi_overbought': {
            'default': 70,
            'var': {'type': int, 'min': 60, 'max': 85}
        },
        'rsi_oversold': {
            'default': 30,
            'var': {'type': int, 'min': 15, 'max': 40}
        },
        'volume_multiplier': {
            'default': 1.5,
            'var': {'type': float, 'min': 1.0, 'max': 3.0}
        },
        'trailing_sl_percent': {
            'default': 5,
            'var': {'type': float, 'min': 2, 'max': 10}
        }
    }

    def __init__(self, name, period=100, ema_fast=9, ema_medium=21, ema_slow=50,
                 rsi_period=14, rsi_overbought=70, rsi_oversold=30,
                 volume_multiplier=1.5, trailing_sl_percent=5, *args, **kwargs):

        self.name = name
        self.period = period
        self.ema_fast = ema_fast
        self.ema_medium = ema_medium
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_multiplier = volume_multiplier
        self.trailing_sl_percent = trailing_sl_percent

        # Register indicators
        self.set_indicator("EMA", (self.ema_fast, self.ema_medium, self.ema_slow))
        self.set_indicator("RSI", self.rsi_period)
        self.set_indicator("SMA", 20)  # For volume average

        # Trailing stop loss state
        self.entry_price = None
        self.highest_price = None
        self.trailing_sl = None

    def generate_signal(self, candles):
        """
        Generate trading signal

        Returns:
            int: Signal strength
                 +3: Strong Buy
                 +2: Buy
                 +1: Weak Buy
                  0: Hold
                 -1: Weak Sell
                 -2: Sell
                 -3: Strong Sell
        """
        if len(candles) < self.period:
            return 0

        # Get current candle
        cur_candle = candles[-1]

        # Get indicators
        ema_fast = self.indicator(candles, 'EMA', self.ema_fast)
        ema_medium = self.indicator(candles, 'EMA', self.ema_medium)
        ema_slow = self.indicator(candles, 'EMA', self.ema_slow)

        ema_fast_prev = self.indicator(candles, 'EMA', self.ema_fast, history=1)
        ema_medium_prev = self.indicator(candles, 'EMA', self.ema_medium, history=1)

        rsi = self.indicator(candles, 'RSI', self.rsi_period)
        rsi_prev = self.indicator(candles, 'RSI', self.rsi_period, history=1)

        # Volume analysis
        volume_avg = self.indicator(candles, 'SMA', 20)  # 20-period volume average
        current_volume = cur_candle.volume

        # Check if we have valid indicators
        if None in [ema_fast, ema_medium, ema_slow, rsi]:
            return 0

        # Update trailing stop loss
        current_price = cur_candle.close
        self._update_trailing_sl(current_price)

        # Check trailing SL hit
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3  # Exit signal

        signal = 0

        # === BUY SIGNAL ===
        # Condition 1: EMA alignment (uptrend)
        ema_uptrend = ema_fast > ema_medium > ema_slow

        # Condition 2: EMA crossover
        ema_crossover = (ema_fast > ema_medium) and (ema_fast_prev <= ema_medium_prev)

        # Condition 3: RSI oversold and rising
        rsi_oversold_cross = (rsi_prev <= self.rsi_oversold) and (rsi > self.rsi_oversold)
        rsi_rising = rsi > rsi_prev

        # Condition 4: Volume confirmation
        volume_confirm = current_volume > (volume_avg * self.volume_multiplier) if volume_avg else False

        # Calculate buy signal strength
        if ema_uptrend and ema_crossover and rsi_oversold_cross and volume_confirm:
            signal = 3  # Strong buy
            self.entry_price = current_price
            self.highest_price = current_price
        elif ema_uptrend and ema_crossover and rsi_rising:
            signal = 2  # Buy
            self.entry_price = current_price
            self.highest_price = current_price
        elif ema_uptrend and rsi_oversold_cross:
            signal = 1  # Weak buy

        # === SELL SIGNAL ===
        # Condition 1: EMA alignment (downtrend)
        ema_downtrend = ema_fast < ema_medium < ema_slow

        # Condition 2: EMA crossover
        ema_cross_down = (ema_fast < ema_medium) and (ema_fast_prev >= ema_medium_prev)

        # Condition 3: RSI overbought and falling
        rsi_overbought_cross = (rsi_prev >= self.rsi_overbought) and (rsi < self.rsi_overbought)
        rsi_falling = rsi < rsi_prev

        # Calculate sell signal strength
        if ema_downtrend and ema_cross_down and rsi_overbought_cross and volume_confirm:
            signal = -3  # Strong sell
            self._reset_trailing_sl()
        elif ema_downtrend and ema_cross_down and rsi_falling:
            signal = -2  # Sell
            self._reset_trailing_sl()
        elif ema_downtrend and rsi_overbought_cross:
            signal = -1  # Weak sell

        return signal

    def _update_trailing_sl(self, current_price):
        """Update trailing stop loss"""
        if self.entry_price is None:
            return

        # Update highest price
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price

        # Calculate trailing SL
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
