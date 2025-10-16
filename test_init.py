#!/usr/bin/env python
"""Test initialization sequence"""

import yaml

print("Testing initialization sequence...")
print()

# Step 1: Load config
print("1. Loading config...")
try:
    with open('config/wolfinch_papertrader_nse_banknifty.yml') as f:
        main_config = yaml.load(f, Loader=yaml.FullLoader)
    
    cache_db_ref = main_config.get('cache_db', {})
    cache_db_file = cache_db_ref.get('config', 'config/cache_db.yml')
    print(f"   ✓ cache_db_file: {cache_db_file}")
    
    with open(cache_db_file) as f:
        cache_db_config = yaml.load(f, Loader=yaml.FullLoader)
    
    redis_config = cache_db_config.get('redis', {})
    influx_config = cache_db_config.get('influxdb', {})
    
    print(f"   ✓ Redis enabled: {redis_config.get('enabled')}")
    print(f"   ✓ InfluxDB enabled: {influx_config.get('enabled')}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 2: Initialize Redis
print("\n2. Initializing Redis...")
try:
    from db import init_redis_cache
    redis_cache = init_redis_cache(redis_config)
    print(f"   ✓ Redis initialized: {redis_cache.is_enabled()}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Initialize InfluxDB
print("\n3. Initializing InfluxDB...")
try:
    from db import init_influx_db, get_influx_db
    influx_db = init_influx_db(influx_config)
    print(f"   ✓ InfluxDB initialized: {influx_db.is_enabled()}")
    
    # Verify global instance
    global_influx = get_influx_db()
    print(f"   ✓ Global InfluxDB available: {global_influx is not None}")
    print(f"   ✓ Global InfluxDB enabled: {global_influx.is_enabled() if global_influx else False}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Initialize Trade Logger
print("\n4. Initializing Trade Logger...")
try:
    from db import init_trade_logger, get_trade_logger
    trade_logger = init_trade_logger()
    print(f"   ✓ Trade logger initialized: {trade_logger is not None}")
    print(f"   ✓ Trade logger enabled: {trade_logger.is_enabled()}")
    
    # Verify global instance
    global_logger = get_trade_logger()
    print(f"   ✓ Global logger available: {global_logger is not None}")
    print(f"   ✓ Global logger enabled: {global_logger.is_enabled() if global_logger else False}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Test CandlesDb
print("\n5. Testing CandlesDb...")
try:
    from db import CandlesDb
    from market import OHLC
    
    candle_db = CandlesDb(OHLC, 'papertrader', 'BANKNIFTY-FUT')
    using_influx = hasattr(candle_db, '_using_influx') and candle_db._using_influx
    print(f"   ✓ CandlesDb using InfluxDB: {using_influx}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Initialization test complete!")
print("="*60)
