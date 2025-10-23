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

## Port Mappings

- Redis: localhost:6380
- InfluxDB: localhost:8087
- PostgreSQL: localhost:5432
- Kafka: localhost:9094
- Zookeeper: localhost:2182
- Grafana: localhost:3001
- Prometheus: localhost:9090
- Alertmanager: localhost:9093
- Redis Commander: localhost:8081
- Kafka UI: localhost:8090

## Documentation

- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)
- [Monitoring Guide](docs/MONITORING_GUIDE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Docker Setup](docs/DOCKER_SETUP.md)

## Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/ -m "not integration"

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Backup

```bash
./scripts/backup_databases.sh
```

## Health Check

```bash
./scripts/health_check.sh
```

## Configuration

### Exchange Configuration

Edit `config/binance.yml` or `config/openalgo.yml` to configure exchange settings.

### Strategy Configuration

Edit `config/wolfinch_<strategy>.yml` to configure trading strategies.

### Database Configuration

All database credentials are in `.env` file. Default credentials:
- PostgreSQL: wolfinch/wolfinch2024
- InfluxDB: admin/wolfinch2024
- Grafana: admin/wolfinch2024

## Development

### Project Structure

```
wolfinch-AlgoEdge/
├── config/              # Configuration files
├── db/                  # Database modules
├── decision/            # Decision making modules
├── docs/                # Documentation
├── exchanges/           # Exchange implementations
├── indicators/          # Technical indicators
├── infra/               # Infrastructure (Kafka, metrics)
├── market/              # Market and order management
├── risk/                # Risk management
├── sims/                # Simulation and backtesting
├── stats/               # Statistics and analytics
├── strategy/            # Trading strategies
├── tests/               # Test suite
├── ui/                  # Web UI
└── utils/               # Utility functions
```

### Adding a New Exchange

1. Create exchange client in `exchanges/<exchange_name>/`
2. Implement methods from `exchanges/exchange_base.py`
3. Add configuration in `config/<exchange_name>.yml`
4. Register in exchange factory

### Adding a New Strategy

1. Create strategy in `strategy/strategies/<strategy_name>.py`
2. Inherit from base strategy class
3. Implement `generate_signal()` method
4. Add configuration in `config/`

## Monitoring & Observability

### Prometheus Metrics

The platform exports comprehensive metrics:
- Trading metrics (orders, positions, P&L)
- Performance metrics (win rate, Sharpe ratio, drawdown)
- System metrics (API calls, database writes, errors)
- Market data metrics (prices, volumes, indicators)

Access metrics at: http://localhost:8000/metrics

### Grafana Dashboards

Pre-configured dashboards for:
- Trading activity and performance
- System health and infrastructure
- Market data and indicators

### Kafka Event Streaming

All trading events are published to Kafka topics:
- `wolfinch.orders.*` - Order events
- `wolfinch.trades.*` - Trade events
- `wolfinch.positions.*` - Position events
- `wolfinch.market.*` - Market data
- `wolfinch.strategy.*` - Strategy signals

### Database Logging

- **InfluxDB**: Time-series data (candles, indicators, metrics)
- **PostgreSQL**: Audit logs (trades, system events, performance)
- **Redis**: Hot data cache (recent candles, indicators)

## Production Deployment

See [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for detailed production deployment guide.

Key considerations:
- Change all default passwords
- Enable SSL/TLS for all services
- Configure backup schedules
- Set up monitoring alerts
- Implement rate limiting
- Use secrets management

## Troubleshooting

### Services not starting

```bash
# Check Docker logs
docker-compose logs <service-name>

# Restart services
docker-compose restart
```

### Database connection issues

```bash
# Check database health
./scripts/health_check.sh

# Verify credentials in .env file
```

### Kafka connection issues

```bash
# Check Kafka UI
http://localhost:8090

# Verify Kafka is running
docker-compose ps kafka
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

GPL-3.0 - See LICENSE file

## Support

For issues and questions, please open a GitHub issue.

## Acknowledgments

- Built on the Wolfinch trading framework
- Uses Binance and OpenAlgo APIs
- Powered by InfluxDB, PostgreSQL, Kafka, Prometheus, and Grafana
