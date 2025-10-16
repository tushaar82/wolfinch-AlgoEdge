#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: Indicator Logger - Save all indicator values to InfluxDB
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

import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils import getLogger

log = getLogger('IndicatorLogger')
log.setLevel(log.INFO)


class IndicatorLogger:
    """
    Comprehensive indicator logger for InfluxDB
    
    Logs all indicator values with strategy information:
    - Technical indicators (RSI, MACD, EMA, SMA, etc.)
    - Strategy signals (buy/sell strength)
    - Market conditions
    - Custom indicators
    """

    def __init__(self):
        """Initialize indicator logger"""
        self.influx = None
        self.enabled = False

        try:
            from .influx_db import get_influx_db

            self.influx = get_influx_db()

            if self.influx and self.influx.is_enabled():
                self.enabled = True
                log.info("Indicator logger initialized with InfluxDB")
            else:
                log.warning("InfluxDB not available - indicator logging disabled")
        except Exception as e:
            log.error(f"Failed to initialize indicator logger: {e}")

    def is_enabled(self) -> bool:
        """Check if indicator logging is enabled"""
        return self.enabled

    def log_indicators(self, exchange: str, product: str, strategy_name: str,
                      timestamp: int, indicators: Dict[str, Any],
                      signal: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log indicator values to InfluxDB
        
        Args:
            exchange: Exchange name (e.g., 'papertrader', 'binance')
            product: Product ID (e.g., 'BANKNIFTY-FUT')
            strategy_name: Strategy name (e.g., 'RANDOM_TRADER', 'TREND_RSI')
            timestamp: Unix timestamp
            indicators: Dictionary of indicator values
            signal: Optional signal information (buy/sell strength, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Build measurement data
            tags = {
                'exchange': exchange,
                'product': product,
                'strategy': strategy_name
            }

            fields = {}
            
            # Add all indicator values
            for key, value in indicators.items():
                if value is not None:
                    try:
                        # Convert to float if possible
                        if isinstance(value, (int, float)):
                            fields[key] = float(value)
                        elif isinstance(value, bool):
                            fields[key] = 1.0 if value else 0.0
                        elif isinstance(value, str):
                            # Store strings as tags instead
                            tags[f'ind_{key}'] = value
                    except (ValueError, TypeError):
                        log.debug(f"Skipping non-numeric indicator: {key}={value}")

            # Add signal information if provided
            if signal:
                for key, value in signal.items():
                    if value is not None and isinstance(value, (int, float, bool)):
                        try:
                            if isinstance(value, bool):
                                fields[f'signal_{key}'] = 1.0 if value else 0.0
                            else:
                                fields[f'signal_{key}'] = float(value)
                        except (ValueError, TypeError):
                            pass

            # Only write if we have fields
            if not fields:
                log.debug("No numeric indicators to log")
                return False

            # Write to InfluxDB
            self.influx.write_point(
                measurement='indicator',
                tags=tags,
                fields=fields,
                timestamp=timestamp
            )

            log.debug(f"Logged {len(fields)} indicators for {strategy_name} on {product}")
            return True

        except Exception as e:
            log.error(f"Error logging indicators: {e}")
            return False

    def log_strategy_signal(self, exchange: str, product: str, strategy_name: str,
                           timestamp: int, signal_type: str, signal_strength: float,
                           indicators: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log strategy signal with indicator context
        
        Args:
            exchange: Exchange name
            product: Product ID
            strategy_name: Strategy name
            timestamp: Unix timestamp
            signal_type: 'buy', 'sell', 'hold', 'neutral'
            signal_strength: Signal strength (0.0 to 1.0)
            indicators: Current indicator values
            metadata: Additional metadata (price, volume, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            tags = {
                'exchange': exchange,
                'product': product,
                'strategy': strategy_name,
                'signal_type': signal_type
            }

            fields = {
                'signal_strength': float(signal_strength)
            }

            # Add indicator values
            if indicators:
                for key, value in indicators.items():
                    if value is not None and isinstance(value, (int, float)):
                        try:
                            fields[f'ind_{key}'] = float(value)
                        except (ValueError, TypeError):
                            pass

            # Add metadata
            if metadata:
                for key, value in metadata.items():
                    if value is not None and isinstance(value, (int, float)):
                        try:
                            fields[key] = float(value)
                        except (ValueError, TypeError):
                            pass

            # Write to InfluxDB
            self.influx.write_point(
                measurement='strategy_signal',
                tags=tags,
                fields=fields,
                timestamp=timestamp
            )

            log.debug(f"Logged {signal_type} signal for {strategy_name}: strength={signal_strength}")
            return True

        except Exception as e:
            log.error(f"Error logging strategy signal: {e}")
            return False

    def log_strategy_performance(self, exchange: str, product: str, strategy_name: str,
                                timestamp: int, metrics: Dict[str, Any]) -> bool:
        """
        Log strategy performance metrics
        
        Args:
            exchange: Exchange name
            product: Product ID
            strategy_name: Strategy name
            timestamp: Unix timestamp
            metrics: Performance metrics (win_rate, total_trades, pnl, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            tags = {
                'exchange': exchange,
                'product': product,
                'strategy': strategy_name
            }

            fields = {}
            
            # Add all numeric metrics
            for key, value in metrics.items():
                if value is not None and isinstance(value, (int, float)):
                    try:
                        fields[key] = float(value)
                    except (ValueError, TypeError):
                        pass

            if not fields:
                return False

            # Write to InfluxDB
            self.influx.write_point(
                measurement='strategy_performance',
                tags=tags,
                fields=fields,
                timestamp=timestamp
            )

            log.debug(f"Logged performance metrics for {strategy_name}")
            return True

        except Exception as e:
            log.error(f"Error logging strategy performance: {e}")
            return False


# Global indicator logger instance
_indicator_logger = None

def init_indicator_logger() -> IndicatorLogger:
    """Initialize global indicator logger"""
    global _indicator_logger
    _indicator_logger = IndicatorLogger()
    return _indicator_logger

def get_indicator_logger() -> Optional[IndicatorLogger]:
    """
    Get global indicator logger instance
    Returns None if not initialized - call init_indicator_logger() first!
    """
    global _indicator_logger
    return _indicator_logger

# EOF
