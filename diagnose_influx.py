#!/usr/bin/env python
"""Diagnose why InfluxDB isn't being used - Mimics Wolfinch startup exactly"""

import sys

print("\n" + "="*70)
print("InfluxDB Initialization Diagnostic - Mimics Wolfinch Startup")
print("="*70 + "\n")

# Step 1: Check INFLUX_AVAILABLE
print("Step 1: Check if InfluxDB modules are available")
try:
    from db import init_influx_db, init_redis_cache, init_trade_logger, INFLUX_AVAILABLE
    print(f"   ✓ INFLUX_AVAILABLE = {INFLUX_AVAILABLE}")
    if not INFLUX_AVAILABLE:
        print("   ✗ InfluxDB modules not available!")
        print("   This is why Wolfinch is using SQLite")
        sys.exit(1)
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Step 2: Load config (mimics Wolfinch exactly)
print("Step 2: Load configuration (mimics Wolfinch)")
try:
    from utils import readConf, get_config, load_config
    
    # Load main config first (this is what Wolfinch does)
    print("   Loading main config...")
    if not load_config('config/wolfinch_papertrader_nse_banknifty.yml'):
        print("   ✗ Failed to load main config")
        sys.exit(1)
    print("   ✓ Main config loaded")
    
    # Get config (this is what Wolfinch_init does)
    main_config = get_config()
    print(f"   ✓ get_config() returned: {type(main_config)}")
    print(f"   ✓ Config has cache_db: {'cache_db' in main_config if main_config else False}")
    
    # Get cache_db file path
    if main_config and 'cache_db' in main_config:
        cache_db_ref = main_config.get('cache_db', {})
        cache_db_file = cache_db_ref.get('config', 'config/cache_db.yml')
        print(f"   ✓ cache_db from main config: {cache_db_file}")
    else:
        cache_db_file = 'config/cache_db.yml'
        print(f"   ⚠ cache_db not in main config, using default: {cache_db_file}")
    
    # Load cache_db config
    print(f"   Loading {cache_db_file}...")
    cache_db_config = readConf(cache_db_file)
    if not cache_db_config:
        print(f"   ✗ Failed to load {cache_db_file}")
        sys.exit(1)
    print(f"   ✓ cache_db config loaded")
    print(f"   ✓ Keys: {list(cache_db_config.keys())}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Step 3: Initialize Redis (mimics Wolfinch_init)
print("Step 3: Initialize Redis")
try:
    redis_config = cache_db_config.get('redis', {})
    print(f"   Redis enabled: {redis_config.get('enabled', False)}")
    if redis_config.get('enabled', False):
        redis_cache = init_redis_cache(redis_config)
        print(f"   ✓ Redis initialized")
        print(f"   ✓ Redis enabled: {redis_cache.is_enabled()}")
    else:
        print("   ⚠ Redis disabled in config")
except Exception as e:
    print(f"   ✗ Redis initialization failed: {e}")
    import traceback
    traceback.print_exc()
print()

# Step 4: Initialize InfluxDB (mimics Wolfinch_init)
print("Step 4: Initialize InfluxDB")
try:
    influx_config = cache_db_config.get('influxdb', {})
    print(f"   InfluxDB config: {influx_config}")
    print(f"   InfluxDB enabled: {influx_config.get('enabled', False)}")
    
    if influx_config.get('enabled', False):
        print("   Calling init_influx_db()...")
        influx_db = init_influx_db(influx_config)
        print(f"   ✓ InfluxDB initialized")
        print(f"   ✓ InfluxDB enabled: {influx_db.is_enabled()}")
        
        # Check global instance
        from db import get_influx_db
        global_db = get_influx_db()
        print(f"   ✓ Global InfluxDB exists: {global_db is not None}")
        if global_db:
            print(f"   ✓ Global InfluxDB enabled: {global_db.is_enabled()}")
    else:
        print("   ✗ InfluxDB disabled in config!")
        print("   This is why Wolfinch is using SQLite!")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ InfluxDB initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Step 5: Initialize TradeLogger (mimics Wolfinch_init)
print("Step 5: Initialize TradeLogger")
try:
    print("   Calling init_trade_logger()...")
    trade_logger = init_trade_logger()
    print(f"   ✓ TradeLogger initialized: {trade_logger is not None}")
    if trade_logger:
        print(f"   ✓ TradeLogger enabled: {trade_logger.is_enabled()}")
    
    # Check global instance
    from db import get_trade_logger
    global_logger = get_trade_logger()
    print(f"   ✓ Global TradeLogger exists: {global_logger is not None}")
    if global_logger:
        print(f"   ✓ Global TradeLogger enabled: {global_logger.is_enabled()}")
except Exception as e:
    print(f"   ✗ TradeLogger initialization failed: {e}")
    import traceback
    traceback.print_exc()
print()

# Step 6: Test CandlesDb (this is what market.py does)
print("Step 6: Test CandlesDb (mimics market.py)")
try:
    from db import CandlesDb
    from market import OHLC
    
    print("   Creating CandlesDb...")
    candle_db = CandlesDb(OHLC, 'papertrader', 'BANKNIFTY-FUT')
    print(f"   ✓ CandlesDb created")
    
    # Check if using InfluxDB
    using_influx = hasattr(candle_db, '_using_influx') and candle_db._using_influx
    print(f"   Using InfluxDB: {using_influx}")
    
    if not using_influx:
        print("   ✗ CandlesDb is using SQLite instead of InfluxDB!")
        print("   ✗ This is the problem!")
    else:
        print("   ✓ CandlesDb is correctly using InfluxDB!")
        
except Exception as e:
    print(f"   ✗ CandlesDb test failed: {e}")
    import traceback
    traceback.print_exc()
print()

print("="*70)
print("Diagnostic complete!")
print("="*70 + "\n")

print("Summary:")
print("--------")
if INFLUX_AVAILABLE:
    print("✓ InfluxDB modules are available")
else:
    print("✗ InfluxDB modules NOT available")

try:
    from db import get_influx_db
    db = get_influx_db()
    if db and db.is_enabled():
        print("✓ InfluxDB is initialized and enabled")
    else:
        print("✗ InfluxDB is NOT initialized or disabled")
except:
    print("✗ Cannot get InfluxDB instance")

try:
    from db import get_trade_logger
    logger = get_trade_logger()
    if logger and logger.is_enabled():
        print("✓ TradeLogger is initialized and enabled")
    else:
        print("✗ TradeLogger is NOT initialized or disabled")
except:
    print("✗ Cannot get TradeLogger instance")

print()
