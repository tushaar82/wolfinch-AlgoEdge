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
