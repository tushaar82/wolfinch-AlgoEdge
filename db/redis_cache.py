#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: Redis Cache Manager for high-performance data caching
#
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.
# 
#  Wolfinch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  Wolfinch is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with Wolfinch.  If not, see <https://www.gnu.org/licenses/>.

import json
import pickle
from typing import Any, Optional, List, Dict
from utils import getLogger

log = getLogger('RedisCache')
log.setLevel(log.INFO)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    log.warning("Redis not available. Install with: pip install redis hiredis")


class RedisCache:
    """
    Redis Cache Manager for Wolfinch
    
    Provides high-performance caching for:
    - Market indicators (EMA, RSI, etc.)
    - Recent candle data
    - Position states
    - Strategy states
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, enabled=True):
        """
        Initialize Redis connection
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number (0-15)
            password: Redis password (optional)
            enabled: Enable/disable Redis caching
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.client = None
        
        if not self.enabled:
            log.info("Redis caching disabled")
            return
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # We'll handle encoding
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.client.ping()
            log.info(f"Redis connected: {host}:{port} db={db}")
        except Exception as e:
            log.error(f"Redis connection failed: {e}")
            self.enabled = False
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if Redis is enabled and connected"""
        return self.enabled and self.client is not None
    
    # ============ Generic Cache Operations ============
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds (None = no expiry)
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            pickled_value = pickle.dumps(value)
            if ttl:
                self.client.setex(key, ttl, pickled_value)
            else:
                self.client.set(key, pickled_value)
            return True
        except Exception as e:
            log.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
        
        Returns:
            Cached value or default
        """
        if not self.is_enabled():
            return default
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            return pickle.loads(value)
        except Exception as e:
            log.error(f"Redis GET error for key '{key}': {e}")
            return default
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self.is_enabled():
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            log.error(f"Redis DELETE error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_enabled():
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            log.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiry time for a key"""
        if not self.is_enabled():
            return False
        
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            log.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
    
    # ============ List Operations ============
    
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list"""
        if not self.is_enabled():
            return 0
        
        try:
            pickled_values = [pickle.dumps(v) for v in values]
            return self.client.lpush(key, *pickled_values)
        except Exception as e:
            log.error(f"Redis LPUSH error for key '{key}': {e}")
            return 0
    
    def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of a list"""
        if not self.is_enabled():
            return 0
        
        try:
            pickled_values = [pickle.dumps(v) for v in values]
            return self.client.rpush(key, *pickled_values)
        except Exception as e:
            log.error(f"Redis RPUSH error for key '{key}': {e}")
            return 0
    
    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get a range of elements from a list"""
        if not self.is_enabled():
            return []
        
        try:
            values = self.client.lrange(key, start, end)
            return [pickle.loads(v) for v in values]
        except Exception as e:
            log.error(f"Redis LRANGE error for key '{key}': {e}")
            return []
    
    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim a list to the specified range"""
        if not self.is_enabled():
            return False
        
        try:
            return self.client.ltrim(key, start, end)
        except Exception as e:
            log.error(f"Redis LTRIM error for key '{key}': {e}")
            return False
    
    # ============ Hash Operations ============
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """Set a field in a hash"""
        if not self.is_enabled():
            return 0
        
        try:
            pickled_value = pickle.dumps(value)
            return self.client.hset(name, key, pickled_value)
        except Exception as e:
            log.error(f"Redis HSET error for hash '{name}' key '{key}': {e}")
            return 0
    
    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """Get a field from a hash"""
        if not self.is_enabled():
            return default
        
        try:
            value = self.client.hget(name, key)
            if value is None:
                return default
            return pickle.loads(value)
        except Exception as e:
            log.error(f"Redis HGET error for hash '{name}' key '{key}': {e}")
            return default
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all fields from a hash"""
        if not self.is_enabled():
            return {}
        
        try:
            hash_data = self.client.hgetall(name)
            return {k.decode(): pickle.loads(v) for k, v in hash_data.items()}
        except Exception as e:
            log.error(f"Redis HGETALL error for hash '{name}': {e}")
            return {}
    
    # ============ Wolfinch-Specific Methods ============
    
    def cache_indicator(self, exchange: str, product: str, indicator: str, 
                       period: int, value: Any, ttl: int = 300) -> bool:
        """
        Cache an indicator value
        
        Args:
            exchange: Exchange name
            product: Product ID
            indicator: Indicator name (e.g., 'EMA', 'RSI')
            period: Indicator period
            value: Indicator value
            ttl: Time to live in seconds (default: 5 minutes)
        """
        key = f"indicator:{exchange}:{product}:{indicator}:{period}"
        return self.set(key, value, ttl)
    
    def get_indicator(self, exchange: str, product: str, indicator: str, 
                     period: int, default: Any = None) -> Any:
        """Get a cached indicator value"""
        key = f"indicator:{exchange}:{product}:{indicator}:{period}"
        return self.get(key, default)
    
    def cache_candles(self, exchange: str, product: str, candles: List[Any], 
                     max_candles: int = 1000) -> bool:
        """
        Cache recent candles (FIFO list)
        
        Args:
            exchange: Exchange name
            product: Product ID
            candles: List of candle objects
            max_candles: Maximum candles to keep
        """
        key = f"candles:{exchange}:{product}"
        try:
            # Add new candles to the right
            self.rpush(key, *candles)
            # Trim to keep only recent candles
            self.ltrim(key, -max_candles, -1)
            return True
        except Exception as e:
            log.error(f"Error caching candles: {e}")
            return False
    
    def get_candles(self, exchange: str, product: str, count: int = 100) -> List[Any]:
        """Get recent candles from cache"""
        key = f"candles:{exchange}:{product}"
        return self.lrange(key, -count, -1)
    
    def cache_position(self, exchange: str, product: str, position: Dict) -> bool:
        """Cache current position state"""
        key = f"position:{exchange}:{product}"
        return self.set(key, position, ttl=3600)  # 1 hour TTL
    
    def get_position(self, exchange: str, product: str) -> Optional[Dict]:
        """Get cached position state"""
        key = f"position:{exchange}:{product}"
        return self.get(key)
    
    def cache_strategy_state(self, exchange: str, product: str, strategy: str, 
                            state: Dict) -> bool:
        """Cache strategy state"""
        key = f"strategy:{exchange}:{product}:{strategy}"
        return self.set(key, state, ttl=3600)  # 1 hour TTL
    
    def get_strategy_state(self, exchange: str, product: str, strategy: str) -> Optional[Dict]:
        """Get cached strategy state"""
        key = f"strategy:{exchange}:{product}:{strategy}"
        return self.get(key)
    
    def flush_all(self) -> bool:
        """Flush all cached data (use with caution!)"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.flushdb()
            log.warning("Redis cache flushed!")
            return True
        except Exception as e:
            log.error(f"Redis FLUSHDB error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self.is_enabled():
            return {"enabled": False}
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            log.error(f"Error getting Redis stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                log.info("Redis connection closed")
            except Exception as e:
                log.error(f"Error closing Redis connection: {e}")


# Global Redis cache instance
_redis_cache = None

def init_redis_cache(config: Dict) -> RedisCache:
    """Initialize global Redis cache"""
    global _redis_cache
    _redis_cache = RedisCache(
        host=config.get('host', 'localhost'),
        port=config.get('port', 6379),
        db=config.get('db', 0),
        password=config.get('password'),
        enabled=config.get('enabled', True)
    )
    return _redis_cache

def get_redis_cache() -> Optional[RedisCache]:
    """Get global Redis cache instance"""
    return _redis_cache

# EOF
