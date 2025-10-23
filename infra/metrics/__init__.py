"""
Wolfinch Metrics Infrastructure

This module provides Prometheus metrics exporting for comprehensive
monitoring and observability of the trading system.

Usage:
    from infra.metrics import init_prometheus_exporter, get_prometheus_exporter
    
    # Initialize during startup
    exporter = init_prometheus_exporter(port=8000)
    exporter.start_server()
    
    # Use throughout application
    exporter = get_prometheus_exporter()
    if exporter:
        exporter.record_order('binance', 'BTC-USD', 'buy', 'market', 'filled')
"""

from .prometheus_exporter import (
    PrometheusExporter,
    init_prometheus_exporter,
    get_prometheus_exporter,
    PROMETHEUS_AVAILABLE
)

__all__ = [
    'PrometheusExporter',
    'init_prometheus_exporter',
    'get_prometheus_exporter',
    'PROMETHEUS_AVAILABLE'
]
