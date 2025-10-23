# Database Schema Documentation

## PostgreSQL Schema

### audit.trade_logs
Stores all trading activity for audit compliance.

```sql
CREATE TABLE audit.trade_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- BUY, SELL
    order_type VARCHAR(20),        -- MARKET, LIMIT
    quantity DECIMAL(20, 8),
    price DECIMAL(20, 8),
    status VARCHAR(20),            -- filled, pending, cancelled
    order_id VARCHAR(100),
    strategy VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### audit.system_events
Logs system events and errors.

```sql
CREATE TABLE audit.system_events (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
    component VARCHAR(100),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### analytics.performance_metrics
Stores performance metrics for analysis.

```sql
CREATE TABLE analytics.performance_metrics (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    pnl DECIMAL(20, 8),
    return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    win_rate DECIMAL(10, 4),
    total_trades INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## InfluxDB Schema

### Measurements

**candle** - OHLCV data
- Tags: exchange, symbol
- Fields: open, high, low, close, volume
- Timestamp: candle close time

**trade_event** - Trading events
- Tags: event_type, exchange, product, order_id, side, status
- Fields: price, size, fee, pnl, duration
- Timestamp: event time

**indicator** - Technical indicators
- Tags: exchange, symbol, indicator_name
- Fields: value
- Timestamp: calculation time

**metric** - System metrics
- Tags: component, metric_type
- Fields: value
- Timestamp: metric time

## Redis Schema

### Key Patterns

**Candles:** `candle:{exchange}:{symbol}:{interval}`
- Type: List
- TTL: 1 hour
- Value: JSON array of recent candles

**Indicators:** `indicator:{exchange}:{symbol}:{name}`
- Type: Hash
- TTL: 5 minutes
- Fields: value, timestamp

**Market Data:** `market:{exchange}:{symbol}`
- Type: Hash
- TTL: 1 minute
- Fields: price, volume, bid, ask

## Kafka Topics

### Topic Structure

**wolfinch.orders.submitted**
```json
{
  "event_type": "ORDER_SUBMITTED",
  "timestamp": "2024-10-23T18:00:00Z",
  "data": {
    "order_id": "12345",
    "symbol": "BTC-USD",
    "side": "buy",
    "quantity": 0.1,
    "price": 50000,
    "order_type": "MARKET"
  }
}
```

**wolfinch.orders.executed**
```json
{
  "event_type": "ORDER_EXECUTED",
  "timestamp": "2024-10-23T18:00:01Z",
  "data": {
    "order_id": "12345",
    "symbol": "BTC-USD",
    "executed_price": 50000,
    "executed_quantity": 0.1
  }
}
```

**wolfinch.trades.completed**
```json
{
  "event_type": "TRADE_COMPLETED",
  "timestamp": "2024-10-23T18:05:00Z",
  "data": {
    "trade_id": "67890",
    "symbol": "BTC-USD",
    "entry_price": 50000,
    "exit_price": 51000,
    "pnl": 100,
    "strategy": "momentum"
  }
}
```

## Query Examples

### PostgreSQL

```sql
-- Daily P&L by strategy
SELECT 
    DATE(timestamp) as date,
    strategy,
    SUM(CASE WHEN action='SELL' THEN 
        (price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp)) * quantity 
    END) as daily_pnl
FROM audit.trade_logs
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp), strategy;

-- Win rate calculation
SELECT 
    strategy,
    COUNT(*) FILTER (WHERE metadata->>'pnl' > '0') * 100.0 / COUNT(*) as win_rate
FROM audit.trade_logs
WHERE action = 'SELL'
GROUP BY strategy;
```

### InfluxDB (Flux)

```flux
// Average candle volume
from(bucket: "trading")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "candle")
  |> filter(fn: (r) => r._field == "volume")
  |> mean()

// Trade P&L over time
from(bucket: "trading")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "trade_event")
  |> filter(fn: (r) => r.event_type == "position_closed")
  |> filter(fn: (r) => r._field == "pnl")
  |> aggregateWindow(every: 1h, fn: sum)
```

## Data Retention

- **PostgreSQL**: Unlimited (manual cleanup recommended)
- **InfluxDB**: 30 days (configurable in docker-compose.yml)
- **Redis**: 1 hour - 5 minutes (per key type)
- **Kafka**: 7 days (configurable)

## Backup Strategy

All databases backed up via `scripts/backup_databases.sh`:
- PostgreSQL: SQL dump
- InfluxDB: Native backup
- Redis: RDB snapshot
- Kafka: Not backed up (event streaming only)
