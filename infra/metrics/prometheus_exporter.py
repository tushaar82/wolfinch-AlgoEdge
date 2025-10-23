#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: Prometheus Metrics Exporter
#
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.

import os
from utils import getLogger

log = getLogger('PrometheusExporter')
log.setLevel(log.INFO)

# Check if prometheus_client is available
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info, start_http_server, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    log.warning("prometheus_client not installed - Prometheus metrics disabled")
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    """
    Comprehensive Prometheus metrics exporter for trading application
    
    Exports metrics for:
    - Trading activity (orders, positions, trades)
    - Performance (P&L, win rate, Sharpe ratio)
    - System health (API calls, database writes, errors)
    - Market data (prices, volumes, indicators)
    """
    
    def __init__(self, port=8000):
        """
        Initialize Prometheus exporter
        
        Args:
            port: HTTP server port for /metrics endpoint
        """
        self.port = port
        self.enabled = False
        self.server_started = False
        
        if not PROMETHEUS_AVAILABLE:
            log.warning("Prometheus exporter disabled - prometheus_client not available")
            return
        
        try:
            self._init_metrics()
            self.enabled = True
            log.info("Prometheus exporter initialized")
        except Exception as e:
            log.error(f"Failed to initialize Prometheus exporter: {e}")
    
    def _init_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # ========== Trading Metrics ==========
        self.orders_total = Counter(
            'wolfinch_orders_total',
            'Total orders placed',
            ['exchange', 'symbol', 'side', 'order_type', 'status']
        )
        
        self.orders_filled_total = Counter(
            'wolfinch_orders_filled_total',
            'Total orders filled',
            ['exchange', 'symbol', 'side']
        )
        
        self.orders_rejected_total = Counter(
            'wolfinch_orders_rejected_total',
            'Total orders rejected',
            ['exchange', 'symbol', 'reason']
        )
        
        self.positions_open = Gauge(
            'wolfinch_positions_open',
            'Current open positions',
            ['exchange', 'symbol', 'strategy']
        )
        
        self.positions_closed_total = Counter(
            'wolfinch_positions_closed_total',
            'Total positions closed',
            ['exchange', 'symbol', 'strategy', 'outcome']
        )
        
        self.trade_pnl = Histogram(
            'wolfinch_trade_pnl',
            'P&L distribution',
            ['exchange', 'symbol', 'strategy'],
            buckets=[-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000]
        )
        
        self.trade_duration_seconds = Histogram(
            'wolfinch_trade_duration_seconds',
            'Trade duration distribution',
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400]
        )
        
        # ========== Performance Metrics ==========
        self.account_balance = Gauge(
            'wolfinch_account_balance',
            'Current account balance',
            ['exchange', 'currency']
        )
        
        self.unrealized_pnl = Gauge(
            'wolfinch_unrealized_pnl',
            'Unrealized P&L',
            ['exchange', 'symbol']
        )
        
        self.realized_pnl = Gauge(
            'wolfinch_realized_pnl',
            'Realized P&L',
            ['exchange', 'symbol', 'strategy']
        )
        
        self.win_rate = Gauge(
            'wolfinch_win_rate',
            'Win rate percentage',
            ['strategy']
        )
        
        self.sharpe_ratio = Gauge(
            'wolfinch_sharpe_ratio',
            'Sharpe ratio',
            ['strategy']
        )
        
        self.max_drawdown = Gauge(
            'wolfinch_max_drawdown',
            'Maximum drawdown',
            ['strategy']
        )
        
        # ========== System Metrics ==========
        self.api_requests_total = Counter(
            'wolfinch_api_requests_total',
            'Total API requests',
            ['exchange', 'endpoint', 'status']
        )
        
        self.api_request_duration_seconds = Histogram(
            'wolfinch_api_request_duration_seconds',
            'API request latency',
            ['exchange', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.api_errors_total = Counter(
            'wolfinch_api_errors_total',
            'API errors',
            ['exchange', 'error_type']
        )
        
        self.kafka_messages_sent_total = Counter(
            'wolfinch_kafka_messages_sent_total',
            'Kafka messages sent',
            ['topic']
        )
        
        self.kafka_errors_total = Counter(
            'wolfinch_kafka_errors_total',
            'Kafka errors'
        )
        
        self.influxdb_writes_total = Counter(
            'wolfinch_influxdb_writes_total',
            'InfluxDB writes'
        )
        
        self.influxdb_errors_total = Counter(
            'wolfinch_influxdb_errors_total',
            'InfluxDB errors'
        )
        
        self.postgres_writes_total = Counter(
            'wolfinch_postgres_writes_total',
            'PostgreSQL writes'
        )
        
        self.postgres_errors_total = Counter(
            'wolfinch_postgres_errors_total',
            'PostgreSQL errors'
        )
        
        # ========== Market Data Metrics ==========
        self.market_price = Gauge(
            'wolfinch_market_price',
            'Current market price',
            ['exchange', 'symbol']
        )
        
        self.market_volume = Gauge(
            'wolfinch_market_volume',
            'Current volume',
            ['exchange', 'symbol']
        )
        
        self.candles_processed_total = Counter(
            'wolfinch_candles_processed_total',
            'Candles processed',
            ['exchange', 'symbol']
        )
        
        self.indicators_calculated_total = Counter(
            'wolfinch_indicators_calculated_total',
            'Indicators calculated',
            ['indicator_name']
        )
        
        log.info("All Prometheus metrics initialized")
    
    def is_enabled(self):
        """Check if Prometheus exporter is enabled"""
        return self.enabled and PROMETHEUS_AVAILABLE
    
    def start_server(self):
        """Start HTTP server for /metrics endpoint"""
        if not self.is_enabled():
            log.warning("Prometheus exporter not enabled, server not started")
            return False
        
        if self.server_started:
            log.warning("Prometheus server already started")
            return True
        
        try:
            start_http_server(self.port)
            self.server_started = True
            log.info(f"Prometheus metrics server started on port {self.port}")
            log.info(f"Metrics available at http://localhost:{self.port}/metrics")
            return True
        except Exception as e:
            log.error(f"Failed to start Prometheus server: {e}")
            return False
    
    # ========== Recording Methods ==========
    
    def record_order(self, exchange, symbol, side, order_type, status):
        """Record order event"""
        if not self.is_enabled():
            return
        
        try:
            self.orders_total.labels(
                exchange=exchange,
                symbol=symbol,
                side=side,
                order_type=order_type,
                status=status
            ).inc()
            
            if status == 'filled':
                self.orders_filled_total.labels(
                    exchange=exchange,
                    symbol=symbol,
                    side=side
                ).inc()
            elif status == 'rejected':
                self.orders_rejected_total.labels(
                    exchange=exchange,
                    symbol=symbol,
                    reason='unknown'
                ).inc()
        except Exception as e:
            log.error(f"Error recording order metric: {e}")
    
    def record_trade(self, exchange, symbol, pnl, duration, strategy='default'):
        """Record trade completion"""
        if not self.is_enabled():
            return
        
        try:
            self.trade_pnl.labels(
                exchange=exchange,
                symbol=symbol,
                strategy=strategy
            ).observe(pnl)
            
            self.trade_duration_seconds.observe(duration)
            
            outcome = 'win' if pnl > 0 else 'loss'
            self.positions_closed_total.labels(
                exchange=exchange,
                symbol=symbol,
                strategy=strategy,
                outcome=outcome
            ).inc()
        except Exception as e:
            log.error(f"Error recording trade metric: {e}")
    
    def update_position_count(self, exchange, symbol, strategy, count):
        """Update position gauge"""
        if not self.is_enabled():
            return
        
        try:
            self.positions_open.labels(
                exchange=exchange,
                symbol=symbol,
                strategy=strategy
            ).set(count)
        except Exception as e:
            log.error(f"Error updating position count: {e}")
    
    def record_api_call(self, exchange, endpoint, duration, status):
        """Record API call"""
        if not self.is_enabled():
            return
        
        try:
            self.api_requests_total.labels(
                exchange=exchange,
                endpoint=endpoint,
                status=status
            ).inc()
            
            self.api_request_duration_seconds.labels(
                exchange=exchange,
                endpoint=endpoint
            ).observe(duration)
            
            if status != 'success':
                self.api_errors_total.labels(
                    exchange=exchange,
                    error_type=status
                ).inc()
        except Exception as e:
            log.error(f"Error recording API call metric: {e}")
    
    def update_account_balance(self, exchange, currency, balance):
        """Update account balance"""
        if not self.is_enabled():
            return
        
        try:
            self.account_balance.labels(
                exchange=exchange,
                currency=currency
            ).set(balance)
        except Exception as e:
            log.error(f"Error updating account balance: {e}")
    
    def update_unrealized_pnl(self, exchange, symbol, pnl):
        """Update unrealized P&L"""
        if not self.is_enabled():
            return
        
        try:
            self.unrealized_pnl.labels(
                exchange=exchange,
                symbol=symbol
            ).set(pnl)
        except Exception as e:
            log.error(f"Error updating unrealized P&L: {e}")
    
    def update_realized_pnl(self, exchange, symbol, strategy, pnl):
        """Update realized P&L"""
        if not self.is_enabled():
            return
        
        try:
            self.realized_pnl.labels(
                exchange=exchange,
                symbol=symbol,
                strategy=strategy
            ).set(pnl)
        except Exception as e:
            log.error(f"Error updating realized P&L: {e}")
    
    def update_win_rate(self, strategy, win_rate):
        """Update win rate"""
        if not self.is_enabled():
            return
        
        try:
            self.win_rate.labels(strategy=strategy).set(win_rate)
        except Exception as e:
            log.error(f"Error updating win rate: {e}")
    
    def update_sharpe_ratio(self, strategy, sharpe):
        """Update Sharpe ratio"""
        if not self.is_enabled():
            return
        
        try:
            self.sharpe_ratio.labels(strategy=strategy).set(sharpe)
        except Exception as e:
            log.error(f"Error updating Sharpe ratio: {e}")
    
    def update_max_drawdown(self, strategy, drawdown):
        """Update max drawdown"""
        if not self.is_enabled():
            return
        
        try:
            self.max_drawdown.labels(strategy=strategy).set(drawdown)
        except Exception as e:
            log.error(f"Error updating max drawdown: {e}")
    
    def update_market_price(self, exchange, symbol, price):
        """Update market price"""
        if not self.is_enabled():
            return
        
        try:
            self.market_price.labels(
                exchange=exchange,
                symbol=symbol
            ).set(price)
        except Exception as e:
            log.error(f"Error updating market price: {e}")
    
    def update_market_volume(self, exchange, symbol, volume):
        """Update market volume"""
        if not self.is_enabled():
            return
        
        try:
            self.market_volume.labels(
                exchange=exchange,
                symbol=symbol
            ).set(volume)
        except Exception as e:
            log.error(f"Error updating market volume: {e}")
    
    def record_candle_processed(self, exchange, symbol):
        """Record candle processed"""
        if not self.is_enabled():
            return
        
        try:
            self.candles_processed_total.labels(
                exchange=exchange,
                symbol=symbol
            ).inc()
        except Exception as e:
            log.error(f"Error recording candle processed: {e}")
    
    def record_indicator_calculated(self, indicator_name):
        """Record indicator calculation"""
        if not self.is_enabled():
            return
        
        try:
            self.indicators_calculated_total.labels(
                indicator_name=indicator_name
            ).inc()
        except Exception as e:
            log.error(f"Error recording indicator calculated: {e}")
    
    def record_kafka_message(self, topic):
        """Record Kafka message sent"""
        if not self.is_enabled():
            return
        
        try:
            self.kafka_messages_sent_total.labels(topic=topic).inc()
        except Exception as e:
            log.error(f"Error recording Kafka message: {e}")
    
    def record_kafka_error(self):
        """Record Kafka error"""
        if not self.is_enabled():
            return
        
        try:
            self.kafka_errors_total.inc()
        except Exception as e:
            log.error(f"Error recording Kafka error: {e}")
    
    def record_influxdb_write(self):
        """Record InfluxDB write"""
        if not self.is_enabled():
            return
        
        try:
            self.influxdb_writes_total.inc()
        except Exception as e:
            log.error(f"Error recording InfluxDB write: {e}")
    
    def record_influxdb_error(self):
        """Record InfluxDB error"""
        if not self.is_enabled():
            return
        
        try:
            self.influxdb_errors_total.inc()
        except Exception as e:
            log.error(f"Error recording InfluxDB error: {e}")
    
    def record_postgres_write(self):
        """Record PostgreSQL write"""
        if not self.is_enabled():
            return
        
        try:
            self.postgres_writes_total.inc()
        except Exception as e:
            log.error(f"Error recording PostgreSQL write: {e}")
    
    def record_postgres_error(self):
        """Record PostgreSQL error"""
        if not self.is_enabled():
            return
        
        try:
            self.postgres_errors_total.inc()
        except Exception as e:
            log.error(f"Error recording PostgreSQL error: {e}")
    
    def record_error(self, component, error_type):
        """Record generic error"""
        if not self.is_enabled():
            return
        
        try:
            # Log to API errors as a catch-all
            self.api_errors_total.labels(
                exchange=component,
                error_type=error_type
            ).inc()
        except Exception as e:
            log.error(f"Error recording error metric: {e}")


# Global Prometheus exporter instance
_prometheus_exporter = None


def init_prometheus_exporter(port=None):
    """
    Initialize global Prometheus exporter
    
    Args:
        port: HTTP server port (default from env or 8000)
        
    Returns:
        PrometheusExporter instance or None
    """
    global _prometheus_exporter
    
    if not PROMETHEUS_AVAILABLE:
        log.warning("Prometheus exporter not available - prometheus_client not installed")
        return None
    
    # Get port from environment or use default
    if port is None:
        port = int(os.environ.get('PROMETHEUS_PORT', 8000))
    
    # Check if enabled
    enabled = os.environ.get('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    if not enabled:
        log.info("Prometheus exporter disabled by configuration")
        return None
    
    try:
        _prometheus_exporter = PrometheusExporter(port=port)
        if _prometheus_exporter.is_enabled():
            log.info("Global Prometheus exporter initialized successfully")
            return _prometheus_exporter
        else:
            log.warning("Prometheus exporter initialized but not enabled")
            return None
    except Exception as e:
        log.error(f"Failed to initialize global Prometheus exporter: {e}")
        return None


def get_prometheus_exporter():
    """
    Get global Prometheus exporter instance
    
    Returns:
        PrometheusExporter instance or None if not initialized
    """
    global _prometheus_exporter
    return _prometheus_exporter


# EOF
