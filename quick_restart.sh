#!/bin/bash
#
# Quick Restart Script - Kill and restart Wolfinch
#

echo "🔄 Quick Restart..."
echo ""

# Kill existing Wolfinch processes
echo "Stopping Wolfinch..."
pkill -f Wolfinch.py
sleep 2

# Check if stopped
if ps aux | grep -q "[W]olfinch.py"; then
    echo "Force killing..."
    pkill -9 -f Wolfinch.py
    sleep 1
fi

echo "✓ Stopped"
echo ""

# Start Wolfinch
echo "🚀 Starting Wolfinch..."
echo ""

source venv/bin/activate
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
