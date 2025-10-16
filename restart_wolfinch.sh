#!/bin/bash
#
# Restart Wolfinch Script
#

echo "🔄 Restarting Wolfinch..."

# Find and kill existing Wolfinch processes
PIDS=$(ps aux | grep "[W]olfinch.py" | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "Stopping existing Wolfinch processes: $PIDS"
    kill $PIDS
    sleep 2
    
    # Force kill if still running
    PIDS=$(ps aux | grep "[W]olfinch.py" | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo "Force stopping: $PIDS"
        kill -9 $PIDS
    fi
fi

echo "✓ Stopped old processes"
echo ""

# Start Wolfinch
echo "🚀 Starting Wolfinch..."
./start_wolfinch.sh
