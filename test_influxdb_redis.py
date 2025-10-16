#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify InfluxDB and Redis connectivity and data storage
"""

import sys
import time
from datetime import datetime

print("=" * 60)
print("Testing InfluxDB and Redis Integration")
print("=" * 60)
print()

# Test 1: Import modules
print("1. Testing imports...")
try:
    from db.influx_db import InfluxDB
    from db.redis_cache import RedisCache
    print("   ✓ Modules imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    print("   Run: pip install redis hiredis influxdb-client")
    sys.exit(1)

# Test 2: Connect to Redis
print("\n2. Testing Redis connection...")
redis = RedisCache(
    host='localhost',
    port=6379,
    db=0,
    enabled=True
)

if redis.is_enabled():
    print("   ✓ Redis connected")
    
    # Test write
    redis.set('test_key', 'test_value', ttl=60)
    value = redis.get('test_key')
    if value == 'test_value':
        print("   ✓ Redis write/read working")
    else:
        print("   ✗ Redis write/read failed")
    
    # Get stats
    stats = redis.get_stats()
    print(f"   ✓ Redis stats: {stats.get('used_memory_human', 'N/A')} used")
else:
    print("   ✗ Redis not available")
    print("   Check: docker compose ps redis")

# Test 3: Connect to InfluxDB
print("\n3. Testing InfluxDB connection...")
influx = InfluxDB(
    url='http://localhost:8086',
    token='wolfinch-super-secret-token-change-in-production',
    org='wolfinch',
    bucket='trading',
    enabled=True
)

if influx.is_enabled():
    print("   ✓ InfluxDB connected")
    
    # Test write candle
    timestamp = int(time.time())
    success = influx.write_candle(
        exchange='papertrader',
        product='TEST-PRODUCT',
        timestamp=timestamp,
        open_price=44500.0,
        high=44550.0,
        low=44480.0,
        close=44520.0,
        volume=1500.0
    )
    
    if success:
        print("   ✓ InfluxDB write working")
        
        # Test read
        time.sleep(1)  # Give InfluxDB time to index
        candles = influx.query_candles(
            exchange='papertrader',
            product='TEST-PRODUCT',
            start_time=timestamp - 60,
            limit=10
        )
        
        if candles:
            print(f"   ✓ InfluxDB read working ({len(candles)} candles)")
        else:
            print("   ⚠ InfluxDB read returned no data (might need more time)")
    else:
        print("   ✗ InfluxDB write failed")
else:
    print("   ✗ InfluxDB not available")
    print("   Check: docker compose ps influxdb")
    print("   Check: curl http://localhost:8086/health")

# Test 4: Test CandleDBInflux
print("\n4. Testing CandleDBInflux...")
try:
    from db.influx_db import init_influx_db
    from db.redis_cache import init_redis_cache
    from db.candle_db_influx import CandleDBInflux
    from market import OHLC
    
    # Initialize global instances
    init_redis_cache({
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'enabled': True
    })
    
    init_influx_db({
        'url': 'http://localhost:8086',
        'token': 'wolfinch-super-secret-token-change-in-production',
        'org': 'wolfinch',
        'bucket': 'trading',
        'enabled': True
    })
    
    candle_db = CandleDBInflux('papertrader', 'TEST-PRODUCT', OHLC)
    
    if candle_db.is_enabled():
        print("   ✓ CandleDBInflux initialized")
        
        # Create test candle
        test_candle = OHLC(
            time=int(time.time()),
            open=44500.0,
            high=44550.0,
            low=44480.0,
            close=44520.0,
            volume=1500.0
        )
        
        # Save candle
        success = candle_db.db_save_candle(test_candle)
        if success:
            print("   ✓ Candle saved successfully")
        else:
            print("   ✗ Candle save failed")
        
        # Query candles
        time.sleep(1)
        candles = candle_db.db_get_recent_candles(10)
        print(f"   ✓ Retrieved {len(candles)} candles")
    else:
        print("   ✗ CandleDBInflux not enabled")
except Exception as e:
    print(f"   ✗ CandleDBInflux test failed: {e}")

# Test 5: Check Redis cache
print("\n5. Testing Redis cache...")
if redis.is_enabled():
    # Check for cached data
    keys = redis.client.keys('*')
    print(f"   ✓ Redis has {len(keys)} keys")
    
    if keys:
        print("   Keys:")
        for key in keys[:5]:  # Show first 5
            print(f"     - {key.decode() if isinstance(key, bytes) else key}")
else:
    print("   ✗ Redis not available")

# Summary
print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
print(f"Redis:    {'✓ Working' if redis.is_enabled() else '✗ Not available'}")
print(f"InfluxDB: {'✓ Working' if influx.is_enabled() else '✗ Not available'}")
print()

if redis.is_enabled() and influx.is_enabled():
    print("✓ All systems operational!")
    print()
    print("Next steps:")
    print("1. Start Wolfinch: ./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml")
    print("2. Check InfluxDB UI: http://localhost:8086")
    print("3. Check Grafana: http://localhost:3000")
    print("4. Check Redis Commander: http://localhost:8081")
else:
    print("✗ Some services are not available")
    print()
    print("Troubleshooting:")
    print("1. Check services: docker compose ps")
    print("2. Check logs: docker compose logs")
    print("3. Restart services: docker compose restart")

print("=" * 60)
