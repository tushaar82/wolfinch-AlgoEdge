# Wolfinch AlgoEdge - Docker Services

All Docker services are now running successfully! 🎉

## Service URLs and Ports

### Core Services

| Service | URL | Port (Host:Container) | Description |
|---------|-----|----------------------|-------------|
| **Redis** | `redis://localhost:6380` | `6380:6379` | Caching and real-time data |
| **InfluxDB** | http://localhost:8087 | `8087:8086` | Time-series database |
| **PostgreSQL** | `postgresql://localhost:5432` | `5432:5432` | Relational database |
| **Kafka** | `localhost:9094` | `9094:9092` | Event streaming |
| **Zookeeper** | `localhost:2182` | `2182:2181` | Kafka coordination |

### Monitoring & Management UIs

| Service | URL | Port | Credentials |
|---------|-----|------|-------------|
| **Grafana** | http://localhost:3001 | `3001:3000` | admin / wolfinch2024 |
| **Prometheus** | http://localhost:9090 | `9090:9090` | No auth |
| **Alertmanager** | http://localhost:9093 | `9093:9093` | No auth |
| **Redis Commander** | http://localhost:8081 | `8081:8081` | No auth |
| **Kafka UI** | http://localhost:8090 | `8090:8080` | No auth |

## Database Credentials

### InfluxDB
- **URL**: http://localhost:8087
- **Organization**: wolfinch
- **Bucket**: trading
- **Username**: admin
- **Password**: wolfinch2024
- **Token**: `wolfinch-super-secret-token-change-in-production`

### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Database**: wolfinch
- **Username**: wolfinch
- **Password**: wolfinch2024
- **Connection String**: `postgresql://wolfinch:wolfinch2024@localhost:5432/wolfinch`

### Redis
- **Host**: localhost
- **Port**: 6380
- **No password configured** (for development)

## Port Changes (Due to Conflicts with Velox Project)

The following ports were changed to avoid conflicts with the running Velox services:

| Service | Original Port | New Port | Reason |
|---------|--------------|----------|--------|
| Redis | 6379 | **6380** | Conflict with velox-redis |
| InfluxDB | 8086 | **8087** | Conflict with velox-influxdb |
| Zookeeper | 2181 | **2182** | Conflict with velox-zookeeper |
| Kafka | 9092 | **9094** | Conflict with velox-kafka |
| Kafka (Host) | 9093 | **9095** | Conflict with velox-kafka |
| Grafana | 3000 | **3001** | Conflict with velox-grafana |

## Docker Commands

### Start all services
```bash
docker compose up -d
```

### Stop all services
```bash
docker compose down
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f redis
docker compose logs -f kafka
docker compose logs -f influxdb
```

### Check service status
```bash
docker compose ps
```

### Restart a service
```bash
docker compose restart <service-name>
```

### Remove all volumes (CAUTION: This will delete all data!)
```bash
docker compose down -v
```

## Configuration Files

All configuration files are located in the `config/` directory:

- `config/redis.conf` - Redis configuration
- `config/prometheus.yml` - Prometheus scrape configuration
- `config/alertmanager.yml` - Alert routing and notification configuration
- `config/postgres/init.sql` - PostgreSQL initialization script
- `config/grafana/provisioning/datasources/` - Grafana datasource provisioning
- `config/grafana/provisioning/dashboards/` - Grafana dashboard provisioning

## Health Checks

All services have health checks configured. You can verify their status with:

```bash
docker compose ps
```

Services should show `(healthy)` status after a few seconds of startup.

## Next Steps

1. **Configure Grafana Dashboards**: Access Grafana at http://localhost:3001 and create dashboards
2. **Set up Kafka Topics**: Use Kafka UI at http://localhost:8090 to create topics
3. **Test Database Connections**: Verify connectivity to InfluxDB and PostgreSQL
4. **Configure Alerts**: Set up alert rules in Prometheus and notification channels in Alertmanager

## Troubleshooting

### Port Already in Use
If you see "port already allocated" errors, check for conflicting services:
```bash
sudo lsof -i :<port>
```

### Container Won't Start
Check logs for the specific container:
```bash
docker compose logs <service-name>
```

### Permission Issues
Ensure config files have correct permissions:
```bash
chmod 644 config/*.yml config/*.conf
```

## Security Notes

⚠️ **IMPORTANT**: The current configuration uses default passwords and tokens for development purposes only.

**Before deploying to production:**
1. Change all default passwords
2. Update the InfluxDB token
3. Configure TLS/SSL for all services
4. Set up proper authentication for Redis
5. Configure firewall rules
6. Enable Redis password authentication
7. Set up proper network isolation

## Network

All services are connected via the `wolfinch-network` bridge network with subnet `172.25.0.0/16`.

Services can communicate with each other using their container names (e.g., `redis`, `kafka`, `influxdb`).
