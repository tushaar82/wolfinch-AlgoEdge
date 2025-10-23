-- Wolfinch AlgoEdge PostgreSQL Initialization Script
-- This script sets up the database schema for audit logs, backups, and analytics

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS backups;

-- Audit log table
CREATE TABLE IF NOT EXISTS audit.trade_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    order_type VARCHAR(20),
    quantity DECIMAL(20, 8),
    price DECIMAL(20, 8),
    status VARCHAR(20),
    order_id VARCHAR(100),
    strategy VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    pnl DECIMAL(20, 8),
    return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    win_rate DECIMAL(10, 4),
    total_trades INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System events table
CREATE TABLE IF NOT EXISTS audit.system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    component VARCHAR(100),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trade_logs_timestamp ON audit.trade_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trade_logs_symbol ON audit.trade_logs(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_logs_strategy ON audit.trade_logs(strategy);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON analytics.performance_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_strategy ON analytics.performance_metrics(strategy);
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON audit.system_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_events_type ON audit.system_events(event_type);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA audit TO wolfinch;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO wolfinch;
GRANT ALL PRIVILEGES ON SCHEMA backups TO wolfinch;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO wolfinch;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO wolfinch;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA backups TO wolfinch;
