I have created the following plan after thorough exploration and analysis of the codebase. Follow the below plan verbatim. Trust the files and references. Do not re-verify what's written in the plan. Explore only when absolutely necessary. First implement all the proposed file changes and then I'll review all the changes together at the end.

### Observations

## Current State Analysis

The Wolfinch AlgoEdge trading platform has a solid foundation with:

1. **Infrastructure**: Docker Compose with all required services (Kafka, InfluxDB, PostgreSQL, Prometheus, Grafana, Redis, Zookeeper, Alertmanager)
2. **Partial Integrations**: 
   - InfluxDB client with comprehensive methods for candles, indicators, trades, metrics
   - Kafka producer with event streaming topics
   - PostgreSQL schema with audit tables (trade_logs, system_events, performance_metrics)
   - Redis cache for hot data
   - Trade logger and indicator logger for InfluxDB
3. **Exchange Implementations**:
   - **Binance**: Only basic market data ingestion; trading methods (buy, sell, cancel_order, get_order) are placeholders marked "Not-Implemented"
   - **OpenAlgo**: More complete with buy/sell/cancel, positions, holdings, close_position
   - **PaperTrader**: Fully functional simulation exchange
4. **Missing Components**:
   - No Prometheus metrics exporters
   - No PostgreSQL audit logging integration
   - No Kafka event publishing in trading flow
   - No Grafana dashboards
   - Limited testing infrastructure
   - Binance client missing 50+ API methods

## Key Findings

- Main entry point: `Wolfinch.py` initializes all systems and runs main trading loop
- Trading flow: Strategy → Market → OrderBook → Exchange → Logging
- Database strategy: In-memory for runtime state, InfluxDB for time-series, PostgreSQL for audit (not yet integrated)
- Configuration: YAML-based with separate configs for exchanges, cache_db, prometheus, grafana
- No PostgreSQL integration code exists yet (psycopg2 in requirements but unused)

### Approach

## Implementation Strategy

**Phase 1: Complete Binance Integration** - Implement all missing Binance API methods following OpenAlgo pattern

**Phase 2: Deep Database Integration** - Add PostgreSQL audit logging, enhance Kafka event streaming, ensure all activities are logged

**Phase 3: Prometheus & Monitoring** - Add metrics exporters, create custom application metrics, configure scraping

**Phase 4: Grafana Dashboards** - Create comprehensive dashboards for trading, system health, and performance

**Phase 5: Testing & Production Readiness** - Add integration tests, health checks, cleanup unnecessary files, documentation

**Phase 6: Deployment Optimization** - Ensure production-grade reliability, backup strategies, monitoring alerts

### Reasoning

I explored the codebase systematically:
1. Listed directory structure to understand organization
2. Read docker-compose.yml to see configured services
3. Examined database implementations (influx_db.py, trade_logger.py, postgres init.sql, kafka_producer.py)
4. Analyzed exchange implementations (binanceClient.py, openalgo_client.py, exchange_base.py)
5. Studied main application flow (Wolfinch.py, exchanges_ops.py, market.py, order_book.py)
6. Searched for existing integrations (Prometheus metrics, PostgreSQL usage, Kafka consumers)
7. Identified gaps through grep searches (TODO/FIXME, Not-Implemented methods)
8. Used web search agent to get comprehensive Binance API method list
9. Reviewed configuration files and requirements to understand dependencies

## Mermaid Diagram

sequenceDiagram
    participant Strategy
    participant Market
    participant Exchange
    participant TradeLogger
    participant PostgresLogger
    participant KafkaProducer
    participant PrometheusExporter
    participant InfluxDB
    participant PostgreSQL
    participant Kafka
    
    Strategy->>Market: Generate Signal
    Market->>Exchange: Place Order (buy/sell)
    Exchange->>Exchange: Execute Order via API
    Exchange-->>Market: Order Confirmation
    
    par Log to All Systems
        Market->>TradeLogger: log_order_placed()
        TradeLogger->>InfluxDB: Write trade_event
        
        Market->>PostgresLogger: log_trade()
        PostgresLogger->>PostgreSQL: INSERT INTO audit.trade_logs
        
        Market->>KafkaProducer: publish_order_executed()
        KafkaProducer->>Kafka: Send to wolfinch.orders.executed
        
        Market->>PrometheusExporter: record_order()
        PrometheusExporter->>PrometheusExporter: Increment orders_total counter
    end
    
    Market->>Market: Update Position
    
    par Log Position Change
        Market->>TradeLogger: log_position_opened()
        TradeLogger->>InfluxDB: Write position data
        
        Market->>PostgresLogger: log_position_change()
        PostgresLogger->>PostgreSQL: INSERT INTO analytics
        
        Market->>KafkaProducer: publish_position_updated()
        KafkaProducer->>Kafka: Send to wolfinch.positions.updated
        
        Market->>PrometheusExporter: update_position_count()
        PrometheusExporter->>PrometheusExporter: Update positions_open gauge
    end
    
    Note over InfluxDB,Kafka: All activities logged for analysis
    Note over PrometheusExporter: Metrics scraped by Prometheus
    Note over Kafka: Events consumed by analytics pipeline

## Proposed File Changes

### exchanges/binanceClient/binanceClient.py(MODIFY)

References: 

- exchanges/openalgo/openalgo_client.py(MODIFY)
- exchanges/exchange_base.py
- market/order.py
- db/trade_logger.py

**Implement Complete Binance API Integration**

Refer to the comprehensive Binance API list from the agent report and implement all missing methods:

1. **Trading Methods** (currently placeholders):
   - `buy(trade_req)` - Place buy orders (LIMIT, MARKET, STOP_LOSS, TAKE_PROFIT, LIMIT_MAKER)
   - `sell(trade_req)` - Place sell orders with all order types
   - `get_order(prod_id, order_id)` - Query order status
   - `cancel_order(prod_id, order_id)` - Cancel specific order
   - `cancel_all_orders(prod_id)` - Cancel all open orders for symbol
   - `modify_order(order_id, new_price, new_quantity)` - Modify existing order

2. **Account Methods** (new):
   - `get_account_info()` - Get account balances and permissions
   - `get_balance(asset)` - Get balance for specific asset
   - `get_positions()` - Get current positions (for futures)
   - `get_open_orders(prod_id=None)` - Get all open orders
   - `get_order_history(prod_id, limit=500)` - Get order history
   - `get_trade_history(prod_id, limit=500)` - Get trade history

3. **Market Data Methods** (enhance existing):
   - `get_ticker(prod_id)` - Get 24h ticker statistics
   - `get_order_book_depth(prod_id, limit=100)` - Get order book with depth
   - `get_recent_trades(prod_id, limit=500)` - Get recent trades
   - `get_aggregate_trades(prod_id, start_time, end_time)` - Get aggregate trades

4. **WebSocket Methods** (enhance existing):
   - Implement user data stream for real-time order/position updates
   - Add reconnection logic with exponential backoff
   - Implement proper error handling and heartbeat

5. **Futures-Specific Methods** (if needed):
   - `set_leverage(symbol, leverage)` - Set leverage for symbol
   - `change_margin_type(symbol, margin_type)` - Change margin type (ISOLATED/CROSS)
   - `get_position_risk(symbol)` - Get position risk info
   - `get_funding_rate(symbol)` - Get funding rate

6. **Integration Points**:
   - Use `self.auth_client` (already initialized) for authenticated requests
   - Follow the pattern from `openalgo_client.py` for order creation and response handling
   - Return `Order` objects from `market.order` module
   - Handle API rate limits with retry logic
   - Log all API calls and responses
   - Integrate with TradeLogger for all order/trade events
   - Publish Kafka events for all trading activities
   - Write audit logs to PostgreSQL for compliance

7. **Error Handling**:
   - Catch `BinanceAPIException` and `BinanceRequestException`
   - Implement retry logic with exponential backoff
   - Log all errors with full context
   - Return None or raise appropriate exceptions

8. **Configuration**:
   - Support both testnet and production endpoints
   - Add API key rotation support
   - Configure request timeouts and retry limits

Refer to `exchanges/openalgo/openalgo_client.py` as the implementation template, and the Binance Python SDK documentation for exact API signatures.

### exchanges/openalgo/openalgo_client.py(MODIFY)

References: 

- exchanges/binanceClient/binanceClient.py(MODIFY)
- db/trade_logger.py
- infra/kafka/kafka_producer.py(MODIFY)

**Enhance OpenAlgo Client for Feature Parity**

1. **Add Missing Methods** to match Binance implementation:
   - `modify_order(order_id, new_price, new_quantity)` - Modify existing order
   - `cancel_all_orders(symbol)` - Cancel all open orders for symbol
   - `get_order_history(symbol, limit=500)` - Get order history
   - `get_trade_history(symbol, limit=500)` - Get trade history
   - `get_account_balance()` - Get detailed account balance
   - `get_margin_info(symbol)` - Get margin information

2. **Enhance Existing Methods**:
   - Add comprehensive error handling with retry logic
   - Improve logging for all API calls
   - Add request/response validation
   - Implement rate limiting awareness

3. **Integration Enhancements**:
   - Integrate with TradeLogger for all operations
   - Publish Kafka events for all trading activities
   - Write audit logs to PostgreSQL
   - Cache frequently accessed data in Redis

4. **WebSocket Support** (if OpenAlgo SDK supports):
   - Implement real-time order updates
   - Add position update streams
   - Implement reconnection logic

Refer to the enhanced `exchanges/binanceClient/binanceClient.py` for implementation patterns.

### db/postgres_logger.py(NEW)

References: 

- db/trade_logger.py
- config/postgres/init.sql
- db/influx_db.py

**Create PostgreSQL Audit Logger**

Create a comprehensive PostgreSQL logger similar to `db/trade_logger.py` but for relational audit storage:

1. **Class Structure**:
   - `PostgresLogger` class with connection management
   - Use `psycopg2` for database connectivity
   - Connection pooling for performance
   - Automatic reconnection on failure

2. **Core Methods**:
   - `log_trade(exchange, symbol, action, order_type, quantity, price, status, order_id, strategy, metadata)` - Insert into `audit.trade_logs`
   - `log_system_event(event_type, severity, component, message, metadata)` - Insert into `audit.system_events`
   - `log_performance_metrics(strategy, symbol, pnl, return_pct, sharpe_ratio, max_drawdown, win_rate, total_trades, metadata)` - Insert into `analytics.performance_metrics`
   - `log_order_lifecycle(order_id, status, timestamp, metadata)` - Track complete order lifecycle
   - `log_position_change(symbol, action, quantity, price, pnl, metadata)` - Track position changes

3. **Batch Operations**:
   - Implement batch insert for high-frequency logging
   - Buffer writes and flush periodically (every 10 seconds or 100 records)
   - Ensure data integrity with transactions

4. **Query Methods**:
   - `get_trades(start_time, end_time, symbol=None, strategy=None)` - Query trades
   - `get_performance_summary(strategy, start_time, end_time)` - Get performance metrics
   - `get_system_events(severity, start_time, end_time)` - Query system events

5. **Configuration**:
   - Read connection details from environment variables or config file
   - Support connection string format: `postgresql://user:password@host:port/database`
   - Default to docker-compose values: `postgresql://wolfinch:wolfinch2024@localhost:5432/wolfinch`

6. **Error Handling**:
   - Graceful degradation if PostgreSQL is unavailable
   - Log errors but don't crash the application
   - Implement retry logic with exponential backoff

7. **Global Instance**:
   - Singleton pattern with `init_postgres_logger()` and `get_postgres_logger()`
   - Initialize in `Wolfinch.py` during startup

Refer to `db/trade_logger.py` for structure and `config/postgres/init.sql` for schema.

### db/__init__.py(MODIFY)

References: 

- db/postgres_logger.py(NEW)

**Add PostgreSQL Logger to DB Module Exports**

Add import and export for the new PostgreSQL logger:

1. Add import statement:
   ```python
   from .postgres_logger import PostgresLogger, init_postgres_logger, get_postgres_logger
   ```

2. Add to module exports so it can be imported as `from db import get_postgres_logger`

3. Add `POSTGRES_AVAILABLE` flag similar to `INFLUX_AVAILABLE` to handle cases where psycopg2 is not installed

4. Wrap import in try-except block to handle missing dependencies gracefully

### infra/kafka/kafka_producer.py(MODIFY)

References: 

- db/trade_logger.py
- db/indicator_logger.py

**Enhance Kafka Producer with Additional Event Types**

1. **Add New Event Publishing Methods**:
   - `publish_order_modified(order, old_price, new_price, old_quantity, new_quantity)` - Order modification events
   - `publish_account_update(account_info)` - Account balance/margin updates
   - `publish_market_data_update(symbol, price, volume, bid, ask)` - Market data snapshots
   - `publish_indicator_calculated(symbol, indicator_name, value, timestamp)` - Indicator calculations
   - `publish_strategy_signal(strategy, symbol, signal_type, strength, metadata)` - Strategy signals
   - `publish_performance_snapshot(strategy, metrics)` - Performance metrics
   - `publish_error_event(component, error_type, message, stack_trace)` - Error tracking

2. **Add New Topics** to `TOPICS` dictionary:
   - `'ORDERS_MODIFIED': 'wolfinch.orders.modified'`
   - `'ACCOUNT_UPDATED': 'wolfinch.account.updated'`
   - `'MARKET_DATA_UPDATED': 'wolfinch.market.updated'`
   - `'INDICATORS_CALCULATED': 'wolfinch.indicators.calculated'`
   - `'STRATEGY_SIGNALS': 'wolfinch.strategy.signals'`
   - `'PERFORMANCE_SNAPSHOTS': 'wolfinch.performance.snapshots'`
   - `'ERROR_EVENTS': 'wolfinch.errors'`

3. **Enhance Configuration**:
   - Add topic configuration (partitions, replication factor)
   - Add compression settings (already has gzip)
   - Add batch size tuning
   - Add retry configuration

4. **Add Batch Publishing**:
   - `publish_batch(events)` - Publish multiple events efficiently
   - Buffer events and flush periodically

5. **Add Health Check**:
   - `is_healthy()` - Check Kafka connection status
   - `get_metrics()` - Get producer metrics (messages sent, errors, latency)

6. **Error Handling**:
   - Add circuit breaker pattern for Kafka failures
   - Implement fallback to local file logging if Kafka is down
   - Add dead letter queue for failed messages

Refer to existing methods for implementation patterns.

### infra/metrics/prometheus_exporter.py(NEW)

References: 

- requirement.txt(MODIFY)
- config/prometheus.yml(MODIFY)

**Create Prometheus Metrics Exporter**

Create a comprehensive Prometheus metrics exporter for the trading application:

1. **Import Required Libraries**:
   - `from prometheus_client import Counter, Gauge, Histogram, Summary, Info, start_http_server, generate_latest`
   - `from prometheus_client import CollectorRegistry, REGISTRY`

2. **Define Metrics**:

   **Trading Metrics**:
   - `orders_total` (Counter) - Total orders placed, labels: [exchange, symbol, side, order_type, status]
   - `orders_filled_total` (Counter) - Total orders filled, labels: [exchange, symbol, side]
   - `orders_rejected_total` (Counter) - Total orders rejected, labels: [exchange, symbol, reason]
   - `positions_open` (Gauge) - Current open positions, labels: [exchange, symbol, strategy]
   - `positions_closed_total` (Counter) - Total positions closed, labels: [exchange, symbol, strategy, outcome]
   - `trade_pnl` (Histogram) - P&L distribution, labels: [exchange, symbol, strategy]
   - `trade_duration_seconds` (Histogram) - Trade duration distribution

   **Performance Metrics**:
   - `account_balance` (Gauge) - Current account balance, labels: [exchange, currency]
   - `unrealized_pnl` (Gauge) - Unrealized P&L, labels: [exchange, symbol]
   - `realized_pnl` (Gauge) - Realized P&L, labels: [exchange, symbol, strategy]
   - `win_rate` (Gauge) - Win rate percentage, labels: [strategy]
   - `sharpe_ratio` (Gauge) - Sharpe ratio, labels: [strategy]
   - `max_drawdown` (Gauge) - Maximum drawdown, labels: [strategy]

   **System Metrics**:
   - `api_requests_total` (Counter) - Total API requests, labels: [exchange, endpoint, status]
   - `api_request_duration_seconds` (Histogram) - API request latency
   - `api_errors_total` (Counter) - API errors, labels: [exchange, error_type]
   - `kafka_messages_sent_total` (Counter) - Kafka messages sent, labels: [topic]
   - `kafka_errors_total` (Counter) - Kafka errors
   - `influxdb_writes_total` (Counter) - InfluxDB writes
   - `influxdb_errors_total` (Counter) - InfluxDB errors
   - `postgres_writes_total` (Counter) - PostgreSQL writes
   - `postgres_errors_total` (Counter) - PostgreSQL errors

   **Market Data Metrics**:
   - `market_price` (Gauge) - Current market price, labels: [exchange, symbol]
   - `market_volume` (Gauge) - Current volume, labels: [exchange, symbol]
   - `candles_processed_total` (Counter) - Candles processed, labels: [exchange, symbol]
   - `indicators_calculated_total` (Counter) - Indicators calculated, labels: [indicator_name]

3. **Exporter Class**:
   - `PrometheusExporter` class with methods to update metrics
   - `start_server(port=8000)` - Start HTTP server for /metrics endpoint
   - `record_order(exchange, symbol, side, order_type, status)` - Record order event
   - `record_trade(exchange, symbol, pnl, duration)` - Record trade completion
   - `update_position_count(exchange, symbol, strategy, count)` - Update position gauge
   - `record_api_call(exchange, endpoint, duration, status)` - Record API call
   - `update_account_balance(exchange, currency, balance)` - Update balance
   - `record_error(component, error_type)` - Record error

4. **Integration Points**:
   - Initialize in `Wolfinch.py` during startup
   - Call from exchange clients after each API call
   - Call from market.py after each trade signal
   - Call from order_book.py after position changes
   - Call from database modules after writes

5. **Configuration**:
   - Read port from environment variable `PROMETHEUS_PORT` (default: 8000)
   - Support disabling metrics with `PROMETHEUS_ENABLED` flag

6. **Global Instance**:
   - Singleton pattern with `init_prometheus_exporter()` and `get_prometheus_exporter()`

Refer to prometheus_client documentation and `requirement.txt` which already includes prometheus-client.

### infra/metrics/__init__.py(NEW)

References: 

- infra/metrics/prometheus_exporter.py(NEW)

**Create Metrics Module Init File**

Create module initialization file for metrics:

1. Import and export PrometheusExporter:
   ```python
   from .prometheus_exporter import PrometheusExporter, init_prometheus_exporter, get_prometheus_exporter
   ```

2. Add module docstring explaining the metrics infrastructure

3. Export all public APIs

### Wolfinch.py(MODIFY)

References: 

- db/postgres_logger.py(NEW)
- infra/kafka/kafka_producer.py(MODIFY)
- infra/metrics/prometheus_exporter.py(NEW)

**Integrate All Monitoring and Logging Systems**

Enhance the main application to initialize and use all monitoring systems:

1. **In `Wolfinch_init()` function** (after InfluxDB/Redis initialization around line 174):
   - Initialize PostgreSQL logger:
     ```python
     from db import init_postgres_logger, POSTGRES_AVAILABLE
     if POSTGRES_AVAILABLE:
         postgres_config = {
             'host': 'localhost',
             'port': 5432,
             'database': 'wolfinch',
             'user': 'wolfinch',
             'password': 'wolfinch2024'
         }
         init_postgres_logger(postgres_config)
     ```
   
   - Initialize Kafka producer:
     ```python
     from infra.kafka.kafka_producer import get_kafka_producer
     kafka_producer = get_kafka_producer()
     ```
   
   - Initialize Prometheus exporter:
     ```python
     from infra.metrics import init_prometheus_exporter
     prometheus_exporter = init_prometheus_exporter(port=8000)
     prometheus_exporter.start_server()
     ```

2. **In `process_market()` function** (around line 243):
   - Add Prometheus metrics recording:
     ```python
     from infra.metrics import get_prometheus_exporter
     exporter = get_prometheus_exporter()
     if exporter:
         exporter.update_position_count(market.exchange_name, market.product_id, 
                                       market.strategy_name, len(market.order_book.open_positions))
     ```

3. **In `Wolfinch_end()` function** (around line 199):
   - Close PostgreSQL logger
   - Flush Kafka producer
   - Stop Prometheus exporter

4. **Add Health Check Endpoint**:
   - Create `/health` endpoint that checks:
     - InfluxDB connectivity
     - PostgreSQL connectivity
     - Kafka connectivity
     - Redis connectivity
     - Exchange connectivity

5. **Add Graceful Shutdown**:
   - Ensure all buffers are flushed
   - Close all database connections
   - Stop all background threads

Refer to existing initialization patterns in the file.

### market/market.py(MODIFY)

References: 

- db/trade_logger.py
- db/postgres_logger.py(NEW)
- infra/kafka/kafka_producer.py(MODIFY)
- infra/metrics/prometheus_exporter.py(NEW)

**Integrate Comprehensive Logging in Market Module**

Add logging to all critical trading operations:

1. **In Order Handling Methods** (lines 597-824):
   - In `buy_order_filled()` method:
     - Add PostgreSQL audit log: `get_postgres_logger().log_trade(...)`
     - Add Kafka event: `get_kafka_producer().publish_order_executed(...)`
     - Add Prometheus metric: `get_prometheus_exporter().record_order(...)`
   
   - In `sell_order_filled()` method:
     - Same logging as buy_order_filled
   
   - In `buy_order_cancelled()` and `sell_order_cancelled()` methods:
     - Log cancellation to all systems

2. **In Position Management** (when positions are opened/closed):
   - Log position opened to PostgreSQL, Kafka, Prometheus
   - Log position closed with P&L to all systems
   - Calculate and log performance metrics

3. **In `consume_trade_signal()` method** (around line 1335):
   - Log strategy signals to Kafka
   - Record signal strength in Prometheus

4. **In `update_market_states()` method** (around line 1241):
   - Periodically publish market state to Kafka
   - Update market price gauge in Prometheus

5. **In `add_new_candle()` method** (around line 1273):
   - Log candle to InfluxDB (already done)
   - Increment candle counter in Prometheus

6. **Error Handling**:
   - Wrap all logging calls in try-except
   - Log errors but don't crash trading
   - Use `log.error()` for logging failures

7. **Import Statements** (add at top of file):
   ```python
   from db import get_postgres_logger, get_trade_logger
   from infra.kafka.kafka_producer import get_kafka_producer
   from infra.metrics import get_prometheus_exporter
   ```

Refer to `db/trade_logger.py` for logging patterns and ensure all critical events are captured.

### config/prometheus.yml(MODIFY)

References: 

- docker-compose.yml(MODIFY)

**Enhance Prometheus Configuration**

1. **Update Wolfinch App Scrape Config** (around line 57):
   - Change target to actual metrics endpoint: `['localhost:8000']`
   - Add scrape interval: `scrape_interval: 15s`
   - Add scrape timeout: `scrape_timeout: 10s`

2. **Add Service Exporters**:
   - Add Redis exporter:
     ```yaml
     - job_name: 'redis-exporter'
       static_configs:
         - targets: ['redis-exporter:9121']
           labels:
             service: 'redis'
     ```
   
   - Add PostgreSQL exporter:
     ```yaml
     - job_name: 'postgres-exporter'
       static_configs:
         - targets: ['postgres-exporter:9187']
           labels:
             service: 'postgres'
     ```
   
   - Add Kafka JMX exporter:
     ```yaml
     - job_name: 'kafka-jmx'
       static_configs:
         - targets: ['kafka-jmx-exporter:9308']
           labels:
             service: 'kafka'
     ```

3. **Add Alert Rules** (create new section):
   ```yaml
   rule_files:
     - '/etc/prometheus/alerts/*.yml'
   ```

4. **Update Existing Scrape Configs**:
   - Remove placeholder targets that don't have exporters
   - Keep only services that will actually expose metrics

Refer to Prometheus documentation for scrape configuration best practices.

### docker-compose.yml(MODIFY)

References: 

- config/prometheus.yml(MODIFY)

**Add Prometheus Exporters to Docker Compose**

1. **Add Redis Exporter Service**:
   ```yaml
   redis-exporter:
     image: oliver006/redis_exporter:latest
     container_name: wolfinch-redis-exporter
     ports:
       - "9121:9121"
     environment:
       - REDIS_ADDR=redis:6379
     depends_on:
       - redis
     networks:
       - wolfinch-network
   ```

2. **Add PostgreSQL Exporter Service**:
   ```yaml
   postgres-exporter:
     image: prometheuscommunity/postgres-exporter:latest
     container_name: wolfinch-postgres-exporter
     ports:
       - "9187:9187"
     environment:
       - DATA_SOURCE_NAME=postgresql://wolfinch:wolfinch2024@postgres:5432/wolfinch?sslmode=disable
     depends_on:
       - postgres
     networks:
       - wolfinch-network
   ```

3. **Add Kafka JMX Exporter** (modify Kafka service):
   - Add JMX exporter as sidecar or add JMX port to Kafka service
   - Add environment variables for JMX:
     ```yaml
     KAFKA_JMX_OPTS: "-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.rmi.server.hostname=kafka -Dcom.sun.management.jmxremote.rmi.port=9999"
     JMX_PORT: 9999
     ```

4. **Update Prometheus Service**:
   - Add volume mount for alert rules:
     ```yaml
     - ./config/prometheus/alerts:/etc/prometheus/alerts
     ```

5. **Update Grafana Service**:
   - Add volume mount for custom dashboards:
     ```yaml
     - ./config/grafana/dashboards:/var/lib/grafana/dashboards
     ```

6. **Add Health Check Scripts**:
   - Ensure all services have proper health checks
   - Add restart policies for production

Refer to official Docker images documentation for each exporter.

### config/prometheus/alerts/trading_alerts.yml(NEW)

References: 

- config/alertmanager.yml
- config/prometheus.yml(MODIFY)

**Create Prometheus Alert Rules for Trading**

Create comprehensive alert rules for the trading system:

1. **Trading Alerts**:
   - High order rejection rate (>10% in 5 minutes)
   - No orders placed in last 30 minutes (system might be stuck)
   - Unusual P&L swing (>5% in 5 minutes)
   - Position count exceeds limit
   - Stop loss triggered multiple times

2. **System Alerts**:
   - API error rate high (>5% in 5 minutes)
   - InfluxDB write failures
   - PostgreSQL write failures
   - Kafka producer errors
   - Redis connection lost

3. **Performance Alerts**:
   - Account balance dropped below threshold
   - Max drawdown exceeded
   - Win rate dropped below threshold
   - API latency high (>1s p95)

4. **Alert Format**:
   ```yaml
   groups:
     - name: trading_alerts
       interval: 30s
       rules:
         - alert: HighOrderRejectionRate
           expr: rate(orders_rejected_total[5m]) > 0.1
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "High order rejection rate"
             description: "Order rejection rate is {{ $value }} per second"
   ```

Refer to Prometheus alerting documentation and `config/alertmanager.yml` for alert routing.

### config/grafana/dashboards/trading_dashboard.json(NEW)

References: 

- config/grafana/provisioning/datasources/datasources.yml

**Create Comprehensive Trading Dashboard**

Create a Grafana dashboard JSON file with the following panels:

1. **Overview Row**:
   - Current account balance (Gauge)
   - Total P&L today (Stat)
   - Open positions count (Stat)
   - Win rate (Gauge)
   - Orders placed today (Stat)

2. **Trading Activity Row**:
   - Orders per minute (Time series graph)
   - Order status distribution (Pie chart)
   - Orders by exchange and symbol (Bar chart)
   - Order fill rate (Time series)

3. **Performance Row**:
   - Cumulative P&L (Time series)
   - P&L distribution (Histogram)
   - Win/Loss ratio (Pie chart)
   - Sharpe ratio over time (Time series)
   - Max drawdown (Time series)

4. **Positions Row**:
   - Open positions by symbol (Table)
   - Position duration distribution (Histogram)
   - Unrealized P&L by position (Bar chart)
   - Position size distribution (Histogram)

5. **Market Data Row**:
   - Price charts for active symbols (Time series)
   - Volume by symbol (Bar chart)
   - Spread analysis (Time series)

6. **System Health Row**:
   - API latency (Time series)
   - API error rate (Time series)
   - Database write rates (Time series)
   - Kafka message rate (Time series)

7. **Data Sources**:
   - Use Prometheus for metrics
   - Use InfluxDB for time-series data (candles, indicators)

8. **Variables**:
   - Exchange selector
   - Symbol selector
   - Strategy selector
   - Time range selector

9. **Refresh**:
   - Auto-refresh every 30 seconds
   - Live mode for real-time monitoring

Refer to Grafana dashboard JSON schema and use InfluxDB Flux queries for time-series data.

### config/grafana/dashboards/system_dashboard.json(NEW)

References: 

- config/grafana/provisioning/datasources/datasources.yml

**Create System Health Dashboard**

Create a Grafana dashboard for system monitoring:

1. **Infrastructure Row**:
   - Redis memory usage (Gauge)
   - Redis hit rate (Gauge)
   - PostgreSQL connections (Gauge)
   - PostgreSQL query rate (Time series)
   - InfluxDB write rate (Time series)
   - Kafka lag (Time series)

2. **Application Row**:
   - Wolfinch process CPU usage (Time series)
   - Wolfinch process memory usage (Time series)
   - Active markets count (Stat)
   - Candles processed per minute (Time series)
   - Indicators calculated per minute (Time series)

3. **API Row**:
   - API requests by exchange (Time series)
   - API latency percentiles (Time series)
   - API error rate by exchange (Time series)
   - API rate limit usage (Gauge)

4. **Database Row**:
   - InfluxDB write latency (Time series)
   - PostgreSQL write latency (Time series)
   - Redis operation latency (Time series)
   - Database error rates (Time series)

5. **Alerts Row**:
   - Active alerts (Table)
   - Alert history (Time series)
   - Alert severity distribution (Pie chart)

6. **Logs Row**:
   - Recent error logs (Table)
   - Log rate by severity (Time series)

Use Prometheus as primary data source.

### config/grafana/provisioning/dashboards/dashboards.yml(MODIFY)

References: 

- docker-compose.yml(MODIFY)
- config/grafana/dashboards/trading_dashboard.json(NEW)

**Configure Dashboard Provisioning**

Update the dashboard provisioning configuration to auto-load dashboards:

1. Add dashboard provider configuration:
   ```yaml
   apiVersion: 1
   
   providers:
     - name: 'Wolfinch Dashboards'
       orgId: 1
       folder: 'Wolfinch'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       allowUiUpdates: true
       options:
         path: /var/lib/grafana/dashboards
   ```

2. Ensure the path matches the volume mount in docker-compose.yml

3. Set appropriate permissions for dashboard updates

Refer to Grafana provisioning documentation.

### tests/integration/test_binance_integration.py(NEW)

References: 

- exchanges/binanceClient/binanceClient.py(MODIFY)
- test_influxdb_redis.py

**Create Binance Integration Tests**

Create comprehensive integration tests for Binance client:

1. **Test Setup**:
   - Use pytest framework
   - Mock Binance API responses
   - Use testnet credentials for live tests
   - Setup/teardown fixtures

2. **Test Cases**:
   - `test_binance_connection()` - Test basic connectivity
   - `test_get_account_info()` - Test account info retrieval
   - `test_place_buy_order()` - Test buy order placement
   - `test_place_sell_order()` - Test sell order placement
   - `test_cancel_order()` - Test order cancellation
   - `test_get_order_status()` - Test order status query
   - `test_get_positions()` - Test position retrieval
   - `test_get_order_book()` - Test order book retrieval
   - `test_get_historic_rates()` - Test historical data
   - `test_websocket_connection()` - Test WebSocket connectivity
   - `test_error_handling()` - Test error scenarios
   - `test_rate_limiting()` - Test rate limit handling

3. **Integration Tests**:
   - `test_full_trade_lifecycle()` - Test complete buy-sell cycle
   - `test_logging_integration()` - Verify all logs are written
   - `test_kafka_events()` - Verify Kafka events are published
   - `test_prometheus_metrics()` - Verify metrics are recorded

4. **Mock Data**:
   - Create mock responses for all API endpoints
   - Use realistic data from Binance API documentation

5. **Assertions**:
   - Verify return values
   - Check database writes
   - Validate Kafka messages
   - Confirm Prometheus metrics

Refer to pytest documentation and existing test files.

### tests/integration/test_database_integration.py(NEW)

References: 

- db/influx_db.py
- db/postgres_logger.py(NEW)
- db/redis_cache.py
- infra/kafka/kafka_producer.py(MODIFY)

**Create Database Integration Tests**

Create tests for all database integrations:

1. **InfluxDB Tests**:
   - `test_influxdb_connection()` - Test connectivity
   - `test_write_candle()` - Test candle writes
   - `test_write_trade()` - Test trade writes
   - `test_query_candles()` - Test candle queries
   - `test_batch_writes()` - Test batch operations

2. **PostgreSQL Tests**:
   - `test_postgres_connection()` - Test connectivity
   - `test_log_trade()` - Test trade audit logging
   - `test_log_system_event()` - Test system event logging
   - `test_log_performance_metrics()` - Test metrics logging
   - `test_query_trades()` - Test trade queries
   - `test_batch_inserts()` - Test batch operations

3. **Redis Tests**:
   - `test_redis_connection()` - Test connectivity
   - `test_cache_indicator()` - Test indicator caching
   - `test_cache_candles()` - Test candle caching
   - `test_cache_expiry()` - Test TTL functionality

4. **Kafka Tests**:
   - `test_kafka_connection()` - Test connectivity
   - `test_publish_order_event()` - Test order event publishing
   - `test_publish_trade_event()` - Test trade event publishing
   - `test_batch_publishing()` - Test batch operations

5. **Integration Tests**:
   - `test_full_logging_pipeline()` - Test data flows through all systems
   - `test_data_consistency()` - Verify data consistency across databases
   - `test_failover_scenarios()` - Test graceful degradation

6. **Setup**:
   - Use Docker Compose to spin up test databases
   - Use pytest fixtures for setup/teardown
   - Clean up test data after each test

Refer to existing test files and database modules.

### tests/integration/test_end_to_end.py(NEW)

References: 

- Wolfinch.py(MODIFY)
- docker-compose.yml(MODIFY)

**Create End-to-End Integration Tests**

Create comprehensive end-to-end tests:

1. **Full Trading Cycle Test**:
   - Start Wolfinch with test configuration
   - Generate market data
   - Trigger strategy signal
   - Place order
   - Verify order execution
   - Close position
   - Verify all logging (InfluxDB, PostgreSQL, Kafka)
   - Verify Prometheus metrics
   - Verify Grafana can query data

2. **Multi-Exchange Test**:
   - Test trading on multiple exchanges simultaneously
   - Verify data isolation
   - Verify correct routing

3. **Failure Recovery Test**:
   - Simulate database failures
   - Verify graceful degradation
   - Verify recovery after reconnection

4. **Performance Test**:
   - High-frequency order placement
   - Measure latency
   - Verify no data loss
   - Check memory usage

5. **Setup**:
   - Use Docker Compose for full stack
   - Use pytest-docker plugin
   - Implement proper cleanup

Refer to pytest documentation for end-to-end testing patterns.

### tests/__init__.py(NEW)

**Create Tests Module Init File**

Create empty __init__.py to make tests a Python package.

### tests/integration/__init__.py(NEW)

**Create Integration Tests Module Init File**

Create empty __init__.py to make integration tests a Python package.

### pytest.ini(NEW)

**Create Pytest Configuration**

Create pytest configuration file:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html
    --cov-report=term-missing
markers =
    integration: Integration tests (deselect with '-m "not integration"')
    slow: Slow tests (deselect with '-m "not slow"')
    unit: Unit tests
```

This configures pytest for the project with coverage reporting.

### requirement.txt(MODIFY)

**Update Requirements with Testing Dependencies**

Add testing and additional dependencies:

1. **Testing Libraries**:
   - `pytest>=7.4.0`
   - `pytest-cov>=4.1.0`
   - `pytest-mock>=3.11.1`
   - `pytest-asyncio>=0.21.1`
   - `pytest-docker>=2.0.0`

2. **Additional Dependencies**:
   - `python-binance>=1.0.17` (official Binance Python SDK)
   - `websocket-client>=1.6.0` (already present, ensure version)

3. **Ensure Existing Dependencies**:
   - Verify all existing dependencies are present
   - Update versions if needed for security

Keep existing dependencies intact.

### docs/PRODUCTION_DEPLOYMENT.md(NEW)

References: 

- docker-compose.yml(MODIFY)
- docs/DOCKER_SETUP.md

**Create Production Deployment Guide**

Create comprehensive production deployment documentation:

1. **Prerequisites**:
   - System requirements (CPU, RAM, disk)
   - Docker and Docker Compose versions
   - Network requirements
   - Security considerations

2. **Configuration**:
   - Environment variables
   - API keys and secrets management
   - Database credentials
   - SSL/TLS certificates
   - Firewall rules

3. **Deployment Steps**:
   - Clone repository
   - Configure environment
   - Start services with docker-compose
   - Verify health checks
   - Initialize databases
   - Start Wolfinch application

4. **Monitoring Setup**:
   - Access Grafana dashboards
   - Configure Alertmanager notifications
   - Set up log aggregation
   - Configure backup schedules

5. **Security Hardening**:
   - Change default passwords
   - Enable authentication
   - Configure network isolation
   - Set up SSL/TLS
   - Implement rate limiting

6. **Backup and Recovery**:
   - Database backup procedures
   - Configuration backup
   - Disaster recovery plan
   - Restore procedures

7. **Maintenance**:
   - Update procedures
   - Log rotation
   - Database maintenance
   - Performance tuning

8. **Troubleshooting**:
   - Common issues and solutions
   - Log locations
   - Debug mode
   - Support contacts

Refer to existing documentation in `docs/` directory.

### docs/MONITORING_GUIDE.md(NEW)

References: 

- config/prometheus.yml(MODIFY)
- config/grafana/dashboards/trading_dashboard.json(NEW)
- config/prometheus/alerts/trading_alerts.yml(NEW)

**Create Monitoring and Observability Guide**

Create comprehensive monitoring documentation:

1. **Overview**:
   - Monitoring architecture
   - Data flow diagram
   - Key metrics to watch

2. **Prometheus Metrics**:
   - List all available metrics
   - Metric naming conventions
   - Label descriptions
   - Query examples

3. **Grafana Dashboards**:
   - Dashboard descriptions
   - Panel explanations
   - How to customize
   - Creating new dashboards

4. **Alerting**:
   - Alert rules explanation
   - Alert severity levels
   - Notification channels
   - Alert response procedures

5. **Logging**:
   - Log levels and locations
   - InfluxDB data retention
   - PostgreSQL audit queries
   - Kafka topic structure

6. **Performance Monitoring**:
   - Key performance indicators
   - Latency monitoring
   - Resource utilization
   - Bottleneck identification

7. **Troubleshooting**:
   - Using metrics for debugging
   - Common patterns
   - Performance issues
   - Data inconsistencies

Refer to created dashboards and alert rules.

### docs/DATABASE_SCHEMA.md(NEW)

References: 

- config/postgres/init.sql
- db/influx_db.py
- db/redis_cache.py
- infra/kafka/kafka_producer.py(MODIFY)

**Create Database Schema Documentation**

Document all database schemas and data models:

1. **InfluxDB Schema**:
   - Measurements: candle, indicator, trade, metric, trade_event
   - Tags and fields for each measurement
   - Retention policies
   - Query examples

2. **PostgreSQL Schema**:
   - Tables: audit.trade_logs, audit.system_events, analytics.performance_metrics
   - Column descriptions
   - Indexes
   - Foreign keys
   - Query examples

3. **Redis Schema**:
   - Key patterns
   - Data structures
   - TTL policies
   - Usage examples

4. **Kafka Topics**:
   - Topic names and purposes
   - Message schemas
   - Partitioning strategy
   - Retention policies

5. **Data Flow**:
   - How data moves between systems
   - Data consistency guarantees
   - Backup and recovery

6. **Query Examples**:
   - Common queries for each database
   - Performance optimization tips
   - Aggregation examples

Refer to database initialization scripts and logger implementations.

### scripts/cleanup_unnecessary_files.sh(NEW)

**Create Cleanup Script for Unnecessary Files**

Create a script to remove unnecessary files:

```bash
#!/bin/bash
# Cleanup unnecessary files for production deployment

echo "Cleaning up unnecessary files..."

# Remove duplicate/old shell scripts
rm -f quick_restart.sh
rm -f restart_wolfinch.sh
rm -f clean.sh

# Remove old documentation duplicates
rm -f OPENALGO_SETUP.md
rm -f OPENALGO_SUCCESS.md
rm -f FINAL_SUMMARY.md
rm -f INTEGRATION_ANALYSIS.md
rm -f DOCKER_SERVICES.md

# Remove test/diagnostic scripts (keep in dev, remove in prod)
rm -f test_init.py
rm -f test_influxdb_redis.py
rm -f diagnose_influx.py
rm -f fetch_influx_data.py
rm -f export_influx_data.py
rm -f analyze_trades.py

# Remove old update files
rm -f update.ms

# Clean up __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Clean up .pyc files
find . -type f -name "*.pyc" -delete

# Clean up .DS_Store files (macOS)
find . -type f -name ".DS_Store" -delete

echo "Cleanup complete!"
echo "Kept essential files:"
echo "  - start.sh (main startup script)"
echo "  - stop.sh (shutdown script)"
echo "  - health.sh (health check script)"
echo "  - setup_venv.sh (environment setup)"
echo "  - start_wolfinch.sh (Wolfinch startup)"
```

Make the script executable: `chmod +x scripts/cleanup_unnecessary_files.sh`

### scripts/health_check.sh(NEW)

References: 

- health.sh

**Create Comprehensive Health Check Script**

Create a script to check health of all services:

```bash
#!/bin/bash
# Comprehensive health check for all Wolfinch services

echo "=== Wolfinch Health Check ==="
echo ""

# Check Docker services
echo "Checking Docker services..."
docker-compose ps

# Check Redis
echo ""
echo "Checking Redis..."
redis-cli -h localhost -p 6380 ping || echo "❌ Redis not responding"

# Check InfluxDB
echo ""
echo "Checking InfluxDB..."
curl -s http://localhost:8087/health || echo "❌ InfluxDB not responding"

# Check PostgreSQL
echo ""
echo "Checking PostgreSQL..."
psql -h localhost -p 5432 -U wolfinch -d wolfinch -c "SELECT 1;" || echo "❌ PostgreSQL not responding"

# Check Kafka
echo ""
echo "Checking Kafka..."
docker exec wolfinch-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 || echo "❌ Kafka not responding"

# Check Prometheus
echo ""
echo "Checking Prometheus..."
curl -s http://localhost:9090/-/healthy || echo "❌ Prometheus not responding"

# Check Grafana
echo ""
echo "Checking Grafana..."
curl -s http://localhost:3001/api/health || echo "❌ Grafana not responding"

# Check Wolfinch metrics endpoint
echo ""
echo "Checking Wolfinch metrics..."
curl -s http://localhost:8000/metrics | head -n 5 || echo "❌ Wolfinch metrics not available"

echo ""
echo "=== Health Check Complete ==="
```

Make executable: `chmod +x scripts/health_check.sh`

### scripts/backup_databases.sh(NEW)

**Create Database Backup Script**

Create a script to backup all databases:

```bash
#!/bin/bash
# Backup all Wolfinch databases

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backups in $BACKUP_DIR"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec wolfinch-postgres pg_dump -U wolfinch wolfinch > "$BACKUP_DIR/postgres_backup.sql"

# Backup InfluxDB
echo "Backing up InfluxDB..."
docker exec wolfinch-influxdb influx backup /tmp/influxdb_backup
docker cp wolfinch-influxdb:/tmp/influxdb_backup "$BACKUP_DIR/influxdb_backup"

# Backup Redis (RDB snapshot)
echo "Backing up Redis..."
docker exec wolfinch-redis redis-cli -p 6379 SAVE
docker cp wolfinch-redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"

# Backup configuration files
echo "Backing up configuration..."
cp -r config "$BACKUP_DIR/config"

# Create backup manifest
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest.txt" << EOF
Backup created: $(date)
PostgreSQL: postgres_backup.sql
InfluxDB: influxdb_backup/
Redis: redis_dump.rdb
Config: config/
EOF

echo "Backup complete: $BACKUP_DIR"

# Compress backup
echo "Compressing backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "Compressed backup: $BACKUP_DIR.tar.gz"
```

Make executable: `chmod +x scripts/backup_databases.sh`

### .env.example(NEW)

**Create Environment Variables Template**

Create a template for environment variables:

```bash
# Wolfinch Environment Configuration
# Copy this file to .env and update with your values

# Application
WOLFINCH_ENV=production
LOG_LEVEL=INFO

# Binance API
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BINANCE_TESTNET=false

# OpenAlgo API
OPENALGO_API_KEY=your_openalgo_api_key_here
OPENALGO_HOST=http://127.0.0.1:5000

# InfluxDB
INFLUXDB_URL=http://localhost:8087
INFLUXDB_TOKEN=wolfinch-super-secret-token-change-in-production
INFLUXDB_ORG=wolfinch
INFLUXDB_BUCKET=trading

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=wolfinch
POSTGRES_USER=wolfinch
POSTGRES_PASSWORD=wolfinch2024

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_PASSWORD=

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9095
KAFKA_ENABLED=true

# Prometheus
PROMETHEUS_PORT=8000
PROMETHEUS_ENABLED=true

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=wolfinch2024

# Alertmanager
ALERT_EMAIL=alerts@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=change_this_to_a_random_secret_key
JWT_SECRET=change_this_to_a_random_jwt_secret
```

Add .env to .gitignore to prevent committing secrets.

### .gitignore(MODIFY)

**Create .gitignore File**

Create comprehensive .gitignore:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Backups
backups/
*.tar.gz
*.zip

# Docker
.docker/

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Data files
data/*.json
data/*.csv
!data/README.md

# Temporary files
*.tmp
*.temp

# API Keys and Secrets
config/*_secret.yml
config/*_private.yml
*.pem
*.key
```

### README.md(NEW)

References: 

- docs/PRODUCTION_DEPLOYMENT.md(NEW)
- docs/MONITORING_GUIDE.md(NEW)

**Create Comprehensive README**

Create a production-ready README:

```markdown
# Wolfinch AlgoEdge - Production Trading Platform

A comprehensive algorithmic trading platform with deep integration of Kafka, InfluxDB, PostgreSQL, Grafana, and Prometheus.

## Features

- **Multi-Exchange Support**: Binance, OpenAlgo, Paper Trading
- **Real-time Monitoring**: Prometheus metrics + Grafana dashboards
- **Comprehensive Logging**: InfluxDB (time-series) + PostgreSQL (audit) + Kafka (events)
- **High Performance**: Redis caching for hot data
- **Production Ready**: Health checks, alerting, backup strategies
- **Extensible**: Plugin architecture for strategies and indicators

## Architecture

```
┌─────────────┐
│  Wolfinch   │
│   Engine    │
└──────┬──────┘
       │
       ├──────► Exchanges (Binance, OpenAlgo)
       ├──────► InfluxDB (Time-series data)
       ├──────► PostgreSQL (Audit logs)
       ├──────► Kafka (Event streaming)
       ├──────► Redis (Caching)
       └──────► Prometheus (Metrics)
                    │
                    ▼
               Grafana (Dashboards)
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.8+
- 4GB RAM minimum

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd wolfinch-AlgoEdge
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Setup Python environment:
   ```bash
   ./setup_venv.sh
   source venv/bin/activate
   pip install -r requirement.txt
   ```

5. Start Wolfinch:
   ```bash
   ./start_wolfinch.sh --config config/your_config.yml
   ```

## Monitoring

- **Grafana**: http://localhost:3001 (admin/wolfinch2024)
- **Prometheus**: http://localhost:9090
- **Kafka UI**: http://localhost:8090
- **InfluxDB**: http://localhost:8087
- **Redis Commander**: http://localhost:8081

## Documentation

- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)
- [Monitoring Guide](docs/MONITORING_GUIDE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [API Documentation](docs/API.md)

## Testing

```bash
pytest tests/
```

## Backup

```bash
./scripts/backup_databases.sh
```

## Health Check

```bash
./scripts/health_check.sh
```

## License

GPL-3.0 - See LICENSE file

## Support

For issues and questions, please open a GitHub issue.
```