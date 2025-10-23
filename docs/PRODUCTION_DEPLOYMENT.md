# Production Deployment Guide

## Quick Start

### 1. Setup Environment
```bash
git clone <repo>
cd wolfinch-AlgoEdge
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start Services
```bash
docker-compose up -d
./scripts/health_check.sh
```

### 3. Start Wolfinch
```bash
source venv/bin/activate
pip install -r requirement.txt
./start_wolfinch.sh --config config/your_config.yml
```

## Security Checklist
- [ ] Change all default passwords in .env
- [ ] Configure firewall (allow only necessary ports)
- [ ] Enable SSL/TLS for external access
- [ ] Setup automated backups: `crontab -e` → `0 2 * * * /path/to/scripts/backup_databases.sh`
- [ ] Configure alert emails in alertmanager.yml

## Monitoring
- Grafana: http://localhost:3001 (admin/wolfinch2024)
- Prometheus: http://localhost:9090
- Metrics: http://localhost:8000/metrics

## Troubleshooting
```bash
# Check health
./scripts/health_check.sh

# View logs
docker-compose logs <service>
tail -f logs/wolfinch_*.log

# Restart
docker-compose restart
```
