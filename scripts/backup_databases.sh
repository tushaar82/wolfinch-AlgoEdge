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
docker exec wolfinch-influxdb influx backup /tmp/influxdb_backup 2>/dev/null
docker cp wolfinch-influxdb:/tmp/influxdb_backup "$BACKUP_DIR/influxdb_backup" 2>/dev/null

# Backup Redis (RDB snapshot)
echo "Backing up Redis..."
docker exec wolfinch-redis redis-cli -p 6379 SAVE 2>/dev/null
docker cp wolfinch-redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb" 2>/dev/null

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
