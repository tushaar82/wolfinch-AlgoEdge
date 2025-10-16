#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Strategy Logger Helper
Provides easy integration of indicator logging for strategies
"""

from typing import Dict, Any, Optional
from utils import getLogger

log = getLogger('StrategyLogger')
log.setLevel(log.DEBUG)


class StrategyLogger:
    """
    Helper class for strategies to log indicators and signals to InfluxDB
    """
    
    def __init__(self, strategy_name: str, exchange: str, product: str):
        """
        Initialize strategy logger
        
        Args:
            strategy_name: Name of the strategy
            exchange: Exchange name
            product: Product ID
        """
        self.strategy_name = strategy_name
        self.exchange = exchange
        self.product = product
        self.indicator_logger = None
        
        # Try to get indicator logger
        try:
            from db import get_indicator_logger
            self.indicator_logger = get_indicator_logger()
            if self.indicator_logger and self.indicator_logger.is_enabled():
                log.info(f"Strategy logger enabled for {strategy_name}")
            else:
                log.debug(f"Indicator logging not available for {strategy_name}")
        except Exception as e:
            log.debug(f"Could not initialize indicator logger: {e}")
    
    def log_indicators(self, timestamp: int, indicators: Dict[str, Any],
                      signal: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log indicator values
        
        Args:
            timestamp: Unix timestamp
            indicators: Dictionary of indicator values (e.g., {'rsi': 65.5, 'ema_20': 44500})
            signal: Optional signal info (e.g., {'buy': True, 'strength': 0.8})
        
        Returns:
            True if logged successfully
        
        Example:
            logger.log_indicators(
                timestamp=int(time.time()),
                indicators={
                    'rsi': 65.5,
                    'macd': 120.5,
                    'macd_signal': 115.2,
                    'ema_20': 44500,
                    'sma_50': 44300
                },
                signal={
                    'buy': True,
                    'strength': 0.8
                }
            )
        """
        if not self.indicator_logger:
            return False
        
        return self.indicator_logger.log_indicators(
            exchange=self.exchange,
            product=self.product,
            strategy_name=self.strategy_name,
            timestamp=timestamp,
            indicators=indicators,
            signal=signal
        )
    
    def log_signal(self, timestamp: int, signal_type: str, signal_strength: float,
                  indicators: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log strategy signal
        
        Args:
            timestamp: Unix timestamp
            signal_type: 'buy', 'sell', 'hold', 'neutral'
            signal_strength: Signal strength (0.0 to 1.0)
            indicators: Current indicator values
            metadata: Additional metadata (price, volume, etc.)
        
        Returns:
            True if logged successfully
        
        Example:
            logger.log_signal(
                timestamp=int(time.time()),
                signal_type='buy',
                signal_strength=0.85,
                indicators={'rsi': 65.5, 'macd': 120.5},
                metadata={'price': 44500, 'volume': 1500}
            )
        """
        if not self.indicator_logger:
            return False
        
        return self.indicator_logger.log_strategy_signal(
            exchange=self.exchange,
            product=self.product,
            strategy_name=self.strategy_name,
            timestamp=timestamp,
            signal_type=signal_type,
            signal_strength=signal_strength,
            indicators=indicators,
            metadata=metadata
        )
    
    def log_performance(self, timestamp: int, metrics: Dict[str, Any]) -> bool:
        """
        Log strategy performance metrics
        
        Args:
            timestamp: Unix timestamp
            metrics: Performance metrics
        
        Returns:
            True if logged successfully
        
        Example:
            logger.log_performance(
                timestamp=int(time.time()),
                metrics={
                    'total_trades': 10,
                    'win_rate': 0.6,
                    'total_pnl': 5000,
                    'avg_trade_duration': 3600
                }
            )
        """
        if not self.indicator_logger:
            return False
        
        return self.indicator_logger.log_strategy_performance(
            exchange=self.exchange,
            product=self.product,
            strategy_name=self.strategy_name,
            timestamp=timestamp,
            metrics=metrics
        )


def create_strategy_logger(strategy_name: str, exchange: str, product: str) -> StrategyLogger:
    """
    Factory function to create a strategy logger
    
    Args:
        strategy_name: Name of the strategy
        exchange: Exchange name
        product: Product ID
    
    Returns:
        StrategyLogger instance
    
    Example:
        # In your strategy __init__:
        self.logger = create_strategy_logger('TREND_RSI', 'papertrader', 'BANKNIFTY-FUT')
        
        # In your strategy generate method:
        self.logger.log_indicators(
            timestamp=int(time.time()),
            indicators={'rsi': rsi_value, 'ema': ema_value}
        )
    """
    return StrategyLogger(strategy_name, exchange, product)

# EOF
