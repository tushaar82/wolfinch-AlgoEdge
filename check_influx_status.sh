#!/bin/bash
# Check if InfluxDB is being used

echo "======================================================================="
echo "Checking InfluxDB Status in Running Wolfinch"
echo "======================================================================="
echo ""

# Check if Wolfinch is running
PID=$(ps aux | grep "[W]olfinch.py" | head -1 | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ Wolfinch is NOT running!"
    exit 1
fi

echo "✓ Wolfinch is running (PID: $PID)"
echo ""

# Check recent candle logs
echo "Recent candle database logs:"
echo "----------------------------"
ps aux | grep "[W]olfinch.py" -A 5 | head -10

# Check if using SQLite or InfluxDB
echo ""
echo "Checking which database is being used..."
echo "----------------------------------------"

# Count SQLite messages in last 10 seconds
SQLITE_COUNT=$(timeout 2 strace -p $PID 2>&1 | grep -c "candle.*sqlite" || echo "0")

if [ "$SQLITE_COUNT" -gt "0" ]; then
    echo "❌ Wolfinch is using SQLite (found $SQLITE_COUNT references)"
else
    echo "✓ No SQLite references found"
fi

echo ""
echo "To see full startup logs, restart Wolfinch and watch the output:"
echo "  1. Stop: Ctrl+C in the Wolfinch terminal"
echo "  2. Start: ./start_wolfinch.sh"
echo "  3. Look for the '==== Initializing InfluxDB' section"
echo ""
