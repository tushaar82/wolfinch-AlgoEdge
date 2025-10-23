#
# Wolfinch Auto trading Bot
# Desc: Random Trading Strategy for Testing
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

import random
import time
from .strategy import Strategy
from strategy.strategy_logger import create_strategy_logger

class RANDOM_TRADER(Strategy):
    """
    Random Trading Strategy for Testing
    
    This strategy generates random buy/sell signals for testing the trading system.
    It's useful for:
    - Testing order execution
    - Testing UI updates
    - Testing position management
    - Testing stop-loss and take-profit
    """
    
    config = {
        'period': {'default': 20, 'var': {'type': int, 'min': 10, 'max': 100, 'step': 5}},
        'trade_probability': {'default': 10, 'var': {'type': int, 'min': 1, 'max': 100, 'step': 5}},
        'max_signal_strength': {'default': 3, 'var': {'type': int, 'min': 1, 'max': 3, 'step': 1}},
        'hold_candles': {'default': 5, 'var': {'type': int, 'min': 1, 'max': 20, 'step': 1}},
    }
    
    def __init__(self, name, period=20, trade_probability=10, max_signal_strength=3, hold_candles=5):
        """
        Initialize Random Trader Strategy
        
        Args:
            name: Strategy name
            period: Minimum candles before trading
            trade_probability: Probability (%) of generating a trade signal each candle
            max_signal_strength: Maximum signal strength (1-3)
            hold_candles: Number of candles to hold position before considering exit
        """
        self.name = name
        self.period = period
        self.trade_probability = trade_probability
        self.max_signal_strength = max_signal_strength
        self.hold_candles = hold_candles
        
        # Internal state
        self.position = None  # 'buy' or 'sell' or None
        self.position_candles = 0  # How long we've held the position
        self.last_signal = 0
        
        # Configure indicators (we'll use close price for reference)
        self.set_indicator("close")
        
        # Initialize indicator logger (will be set when strategy is attached to market)
        self.indicator_logger = None
    
    def generate_signal(self, candles):
        """
        Generate random trading signals
        
        Returns:
            signal: -3 to +3 (negative=sell, positive=buy, 0=hold)
        """
        len_candles = len(candles)
        
        # Wait for minimum period
        if len_candles < self.period:
            return 0
        
        # Get current price for logging (candles are dicts with 'ohlc' key)
        current_candle = candles[-1]['ohlc'] if len_candles > 0 else None
        current_price = current_candle.close if current_candle else 0
        current_volume = current_candle.volume if current_candle else 0
        
        # If we have a position, track how long we've held it
        if self.position:
            self.position_candles += 1
        
        # Exit logic: Random exit after holding for minimum candles
        if self.position and self.position_candles >= self.hold_candles:
            # 30% chance to exit each candle after minimum hold period
            if random.randint(1, 100) <= 30:
                if self.position == 'buy':
                    # Exit long position (sell)
                    signal = -random.randint(1, self.max_signal_strength)
                    self.position = None
                    self.position_candles = 0
                    self.last_signal = signal
                    return signal
                elif self.position == 'sell':
                    # Exit short position (buy to cover)
                    signal = random.randint(1, self.max_signal_strength)
                    self.position = None
                    self.position_candles = 0
                    self.last_signal = signal
                    return signal
        
        # Entry logic: Random entry if no position
        if not self.position:
            # Check if we should generate a trade signal
            if random.randint(1, 100) <= self.trade_probability:
                # Randomly decide buy or sell
                direction = random.choice(['buy', 'sell'])
                strength = random.randint(1, self.max_signal_strength)
                
                if direction == 'buy':
                    signal = strength
                    self.position = 'buy'
                    self.position_candles = 0
                else:
                    signal = -strength
                    self.position = 'sell'
                    self.position_candles = 0
                
                self.last_signal = signal
                return signal
        
        # Hold current position
        return 0


class AGGRESSIVE_RANDOM(Strategy):
    """
    Aggressive Random Trader - Trades more frequently
    """
    
    config = {
        'period': {'default': 10, 'var': {'type': int, 'min': 5, 'max': 50, 'step': 5}},
    }
    
    def __init__(self, name, period=10):
        self.name = name
        self.period = period
        self.position = None
        self.candles_in_position = 0
        
        self.set_indicator("close")
    
    def generate_signal(self, candles):
        """
        Generate aggressive random signals - trades every 3-5 candles
        """
        len_candles = len(candles)
        
        if len_candles < self.period:
            return 0
        
        if self.position:
            self.candles_in_position += 1
            
            # Exit after 3-5 candles
            if self.candles_in_position >= random.randint(3, 5):
                signal = -3 if self.position == 'buy' else 3
                self.position = None
                self.candles_in_position = 0
                return signal
        else:
            # Enter position with 50% probability
            if random.randint(1, 100) <= 50:
                self.position = random.choice(['buy', 'sell'])
                self.candles_in_position = 0
                return 3 if self.position == 'buy' else -3
        
        return 0


class SIMPLE_RANDOM(Strategy):
    """
    Simple Random Trader - Just alternates buy and sell
    """
    
    config = {
        'period': {'default': 20, 'var': {'type': int, 'min': 10, 'max': 100, 'step': 5}},
        'trade_every_n_candles': {'default': 10, 'var': {'type': int, 'min': 5, 'max': 50, 'step': 5}},
    }
    
    def __init__(self, name, period=20, trade_every_n_candles=10):
        self.name = name
        self.period = period
        self.trade_every_n_candles = trade_every_n_candles
        self.candle_count = 0
        self.last_action = None
        
        self.set_indicator("close")
    
    def generate_signal(self, candles):
        """
        Alternate between buy and sell every N candles
        """
        len_candles = len(candles)
        
        if len_candles < self.period:
            return 0
        
        self.candle_count += 1
        
        # Trade every N candles
        if self.candle_count >= self.trade_every_n_candles:
            self.candle_count = 0
            
            # Alternate between buy and sell
            if self.last_action == 'buy':
                self.last_action = 'sell'
                return -2  # Sell signal
            else:
                self.last_action = 'buy'
                return 2  # Buy signal
        
        return 0

# EOF
