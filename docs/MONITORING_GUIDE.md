# Monitoring and Observability Guide

## Overview

Wolfinch AlgoEdge provides comprehensive monitoring through:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **InfluxDB** - Time-series data
- **PostgreSQL** - Audit logs
- **Kafka** - Event streaming

## Prometheus Metrics

### Access
- Metrics endpoint: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090

### Key Metrics

**Trading:**
- `wolfinch_orders_total` - Total orders by status
- `wolfinch_positions_open` - Current open positions
- `wolfinch_trade_pnl` - P&L distribution
- `wolfinch_win_rate` - Win rate percentage

**System:**
- `wolfinch_api_requests_total` - API requests
- `wolfinch_api_request_duration_seconds` - API latency
- `wolfinch_influxdb_writes_total` - InfluxDB writes
- `wolfinch_postgres_writes_total` - PostgreSQL writes

**Market:**
- `wolfinch_market_price` - Current price
- `wolfinch_candles_processed_total` - Candles processed

## Grafana Dashboards

### Access
URL: http://localhost:3001
Credentials: admin/wolfinch2024

### Available Dashboards

**Trading Dashboard:**
- Account balance and P&L
- Open positions
- Order activity
- Performance metrics

**System Dashboard:**
- Service health status
- API latency and errors
- Database performance
- Kafka message rates

## Alerts

### Configuration
Alert rules: `config/prometheus/alerts/trading_alerts.yml`

### Key Alerts
- High order rejection rate
- No orders placed (system stuck)
- Low account balance
- High API error rate
- Database connection failures

### Alert Channels
Configure in `config/alertmanager.yml`:
- Email notifications
- Slack webhooks
- PagerDuty integration

## Database Queries

### PostgreSQL Audit Logs
```sql
-- Recent trades
SELECT * FROM audit.trade_logs 
ORDER BY timestamp DESC LIMIT 10;

-- Performance by strategy
SELECT strategy, COUNT(*), AVG(pnl) 
FROM audit.trade_logs 
WHERE action='SELL' 
GROUP BY strategy;

-- System events
SELECT * FROM audit.system_events 
WHERE severity='ERROR' 
ORDER BY timestamp DESC;
```

### InfluxDB Queries
```flux
// Recent candles
from(bucket: "trading")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "candle")

// Trade events
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "trade_event")
```

## Kafka Topics

### Access
Kafka UI: http://localhost:8090

### Topics
- `wolfinch.orders.executed` - Order executions
- `wolfinch.trades.completed` - Trade completions
- `wolfinch.positions.updated` - Position updates
- `wolfinch.strategy.signals` - Strategy signals

## Best Practices

1. **Regular Monitoring**
   - Check dashboards daily
   - Review alerts weekly
   - Analyze performance monthly

2. **Alert Tuning**
   - Adjust thresholds based on trading patterns
   - Reduce false positives
   - Ensure critical alerts are actionable

3. **Data Retention**
   - InfluxDB: 30 days (configurable)
   - PostgreSQL: Unlimited (manual cleanup)
   - Prometheus: 30 days (configurable)

4. **Performance Optimization**
   - Monitor query performance
   - Archive old data
   - Optimize dashboard queries
