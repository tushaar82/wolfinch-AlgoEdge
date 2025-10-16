#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic script to check why InfluxDB isn't being used
"""

import sys
import yaml

print("=" * 60)
print("Wolfinch InfluxDB Diagnostic")
print("=" * 60)
print()

# Test 1: Check if config file has cache_db reference
print("1. Checking main config file...")
try:
    with open('config/wolfinch_papertrader_nse_banknifty.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    if 'cache_db' in config:
        print(f"   ✓ cache_db found: {config['cache_db']}")
        cache_db_file = config['cache_db'].get('config', 'config/cache_db.yml')
        print(f"   ✓ cache_db file: {cache_db_file}")
    else:
        print("   ✗ cache_db NOT found in main config!")
        print("   This is the problem!")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error reading config: {e}")
    sys.exit(1)

# Test 2: Check if cache_db.yml exists and is valid
print("\n2. Checking cache_db.yml...")
try:
    with open(cache_db_file) as f:
        cache_config = yaml.load(f, Loader=yaml.FullLoader)
    
    if 'influxdb' in cache_config:
        influx_config = cache_config['influxdb']
        print(f"   ✓ InfluxDB config found")
        print(f"     - enabled: {influx_config.get('enabled', False)}")
        print(f"     - url: {influx_config.get('url', 'N/A')}")
        print(f"     - org: {influx_config.get('org', 'N/A')}")
        print(f"     - bucket: {influx_config.get('bucket', 'N/A')}")
        print(f"     - token: {'***' if influx_config.get('token') else 'NOT SET'}")
    else:
        print("   ✗ influxdb config NOT found!")
        sys.exit(1)
        
    if 'redis' in cache_config:
        redis_config = cache_config['redis']
        print(f"   ✓ Redis config found")
        print(f"     - enabled: {redis_config.get('enabled', False)}")
        print(f"     - host: {redis_config.get('host', 'N/A')}")
        print(f"     - port: {redis_config.get('port', 'N/A')}")
    else:
        print("   ✗ redis config NOT found!")
        
except Exception as e:
    print(f"   ✗ Error reading cache_db.yml: {e}")
    sys.exit(1)

# Test 3: Test InfluxDB connection
print("\n3. Testing InfluxDB connection...")
try:
    from db.influx_db import InfluxDB
    
    influx = InfluxDB(
        url=influx_config.get('url'),
        token=influx_config.get('token'),
        org=influx_config.get('org'),
        bucket=influx_config.get('bucket'),
        enabled=influx_config.get('enabled', True)
    )
    
    if influx.is_enabled():
        print("   ✓ InfluxDB connection successful!")
    else:
        print("   ✗ InfluxDB connection failed!")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error connecting to InfluxDB: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test Redis connection
print("\n4. Testing Redis connection...")
try:
    from db.redis_cache import RedisCache
    
    redis = RedisCache(
        host=redis_config.get('host'),
        port=redis_config.get('port'),
        db=redis_config.get('db', 0),
        enabled=redis_config.get('enabled', True)
    )
    
    if redis.is_enabled():
        print("   ✓ Redis connection successful!")
    else:
        print("   ✗ Redis connection failed!")
except Exception as e:
    print(f"   ✗ Error connecting to Redis: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test CandlesDb
print("\n5. Testing CandlesDb initialization...")
try:
    from db.candle_db import CandlesDb
    from market import OHLC
    
    # Initialize global instances first
    from db import init_influx_db, init_redis_cache
    init_redis_cache(redis_config)
    init_influx_db(influx_config)
    
    candle_db = CandlesDb(OHLC, 'papertrader', 'BANKNIFTY-FUT')
    
    if hasattr(candle_db, '_using_influx') and candle_db._using_influx:
        print("   ✓ CandlesDb is using InfluxDB!")
    else:
        print("   ✗ CandlesDb is using SQLite (not InfluxDB)")
        print("   This is the problem!")
        
except Exception as e:
    print(f"   ✗ Error testing CandlesDb: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Diagnostic Complete!")
print("=" * 60)
print()

if hasattr(candle_db, '_using_influx') and candle_db._using_influx:
    print("✓ Everything looks good!")
    print("✓ Wolfinch should use InfluxDB when restarted")
    print()
    print("Next steps:")
    print("1. Restart Wolfinch: ./quick_restart.sh")
    print("2. Wait 60 seconds")
    print("3. Check InfluxDB UI")
else:
    print("✗ Problem detected!")
    print("CandlesDb is not using InfluxDB")
    print()
    print("Possible causes:")
    print("1. InfluxDB not initialized before CandlesDb")
    print("2. InfluxDB connection failed")
    print("3. Configuration not loaded properly")
