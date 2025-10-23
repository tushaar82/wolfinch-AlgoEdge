#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Supertrend + ADX Strategy with Trailing SL
 Copyright: (c) 2024 Wolfinch Contributors

 Strategy Logic:
 - Supertrend for trend direction and entry/exit
 - ADX for trend strength confirmation
 - ATR-based trailing stop loss
 - Only trades in strong trending markets
'''

from .strategy import Strategy


class Supertrend_ADX(Strategy):
    """
    Supertrend + ADX Strategy

    Buy Signal:
    - Supertrend turns bullish (green)
    - ADX > threshold (strong trend)
    - Price above Supertrend line
    - +DI > -DI

    Sell Signal:
    - Supertrend turns bearish (red)
    - Price below Supertrend line
    """

    config = {
        'period': {
            'default': 100,
            'var': {'type': int, 'min': 50, 'max': 300}
        },
        'atr_period': {
            'default': 10,
            'var': {'type': int, 'min': 7, 'max': 20}
        },
        'atr_multiplier': {
            'default': 3.0,
            'var': {'type': float, 'min': 1.5, 'max': 5.0}
        },
        'adx_period': {
            'default': 14,
            'var': {'type': int, 'min': 10, 'max': 30}
        },
        'adx_threshold': {
            'default': 25,
            'var': {'type': int, 'min': 20, 'max': 40}
        },
        'trailing_atr_multiplier': {
            'default': 2.0,
            'var': {'type': float, 'min': 1.0, 'max': 4.0}
        }
    }

    def __init__(self, name, period=100, atr_period=10, atr_multiplier=3.0,
                 adx_period=14, adx_threshold=25, trailing_atr_multiplier=2.0,
                 *args, **kwargs):

        self.name = name
        self.period = period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.trailing_atr_multiplier = trailing_atr_multiplier

        # Register indicators
        self.set_indicator("ATR", self.atr_period)
        self.set_indicator("ADX", self.adx_period)

        # Supertrend state
        self.supertrend = None
        self.supertrend_direction = 0  # 1 = bullish, -1 = bearish
        self.basic_upper_band = None
        self.basic_lower_band = None
        self.final_upper_band = None
        self.final_lower_band = None

        # Trailing SL state
        self.entry_price = None
        self.trailing_sl = None

    def calculate_supertrend(self, candles):
        """Calculate Supertrend indicator"""
        if len(candles) < self.atr_period + 1:
            return None, 0

        cur_candle = candles[-1]
        prev_candle = candles[-2] if len(candles) > 1 else None

        # Get ATR
        atr = self.indicator(candles, 'ATR', self.atr_period)
        if atr is None:
            return None, 0

        # Calculate basic bands
        hl_avg = (cur_candle.high + cur_candle.low) / 2
        self.basic_upper_band = hl_avg + (self.atr_multiplier * atr)
        self.basic_lower_band = hl_avg - (self.atr_multiplier * atr)

        # Calculate final bands
        if self.final_upper_band is None:
            self.final_upper_band = self.basic_upper_band
            self.final_lower_band = self.basic_lower_band
        else:
            # Upper band
            if self.basic_upper_band < self.final_upper_band or \
               (prev_candle and prev_candle.close > self.final_upper_band):
                self.final_upper_band = self.basic_upper_band
            else:
                self.final_upper_band = self.final_upper_band

            # Lower band
            if self.basic_lower_band > self.final_lower_band or \
               (prev_candle and prev_candle.close < self.final_lower_band):
                self.final_lower_band = self.basic_lower_band
            else:
                self.final_lower_band = self.final_lower_band

        # Determine Supertrend direction
        prev_direction = self.supertrend_direction

        if cur_candle.close <= self.final_upper_band:
            self.supertrend = self.final_upper_band
            self.supertrend_direction = -1  # Bearish
        else:
            self.supertrend = self.final_lower_band
            self.supertrend_direction = 1  # Bullish

        return self.supertrend, self.supertrend_direction

    def generate_signal(self, candles):
        """
        Generate trading signal

        Returns:
            int: Signal strength (-3 to +3)
        """
        if len(candles) < self.period:
            return 0

        cur_candle = candles[-1]
        current_price = cur_candle.close

        # Calculate Supertrend
        supertrend_value, direction = self.calculate_supertrend(candles)
        if supertrend_value is None:
            return 0

        # Get ADX and DI values
        adx = self.indicator(candles, 'ADX', self.adx_period)
        if adx is None:
            return 0

        # Get previous direction
        prev_supertrend, prev_direction = self.calculate_supertrend(candles[:-1]) if len(candles) > 1 else (None, 0)

        # Update trailing SL
        atr = self.indicator(candles, 'ATR', self.atr_period)
        self._update_trailing_sl(current_price, atr)

        # Check trailing SL hit
        if self.trailing_sl and current_price <= self.trailing_sl:
            self._reset_trailing_sl()
            return -3

        signal = 0

        # === BUY SIGNAL ===
        # Supertrend turns bullish
        if direction == 1 and prev_direction != 1:
            # Strong trend confirmation
            if adx >= self.adx_threshold:
                signal = 3  # Strong buy
                self.entry_price = current_price
            else:
                signal = 2  # Buy (weak trend)
                self.entry_price = current_price

        # Continue bullish
        elif direction == 1 and current_price > supertrend_value:
            if adx >= self.adx_threshold * 1.2:
                signal = 1  # Weak buy (trending strongly)

        # === SELL SIGNAL ===
        # Supertrend turns bearish
        if direction == -1 and prev_direction != -1:
            if adx >= self.adx_threshold:
                signal = -3  # Strong sell
            else:
                signal = -2  # Sell
            self._reset_trailing_sl()

        # Continue bearish
        elif direction == -1 and current_price < supertrend_value:
            if adx >= self.adx_threshold * 1.2:
                signal = -1  # Weak sell

        return signal

    def _update_trailing_sl(self, current_price, atr):
        """Update ATR-based trailing stop loss"""
        if self.entry_price is None or atr is None:
            return

        # Calculate trailing SL using ATR
        sl_distance = atr * self.trailing_atr_multiplier
        new_sl = current_price - sl_distance

        # Update only if new SL is higher
        if self.trailing_sl is None or new_sl > self.trailing_sl:
            self.trailing_sl = new_sl

    def _reset_trailing_sl(self):
        """Reset trailing stop loss"""
        self.entry_price = None
        self.trailing_sl = None

    def get_trailing_sl(self):
        """Get current trailing stop loss price"""
        return self.trailing_sl

    def get_supertrend(self):
        """Get current Supertrend value and direction"""
        return self.supertrend, self.supertrend_direction


# EOF
