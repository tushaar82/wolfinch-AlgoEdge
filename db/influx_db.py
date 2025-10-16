#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: InfluxDB Time-Series Database Manager
#
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.
# 
#  Wolfinch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License, either version
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

from datetime import datetime
from typing import List, Dict, Optional, Any
from utils import getLogger

log = getLogger('InfluxDB')
log.setLevel(log.INFO)

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False
    log.warning("InfluxDB not available. Install with: pip install influxdb-client")


class InfluxDB:
    """
    InfluxDB Time-Series Database Manager for Wolfinch
    
    Optimized for storing:
    - OHLCV candle data
    - Indicator values over time
    - Trade execution data
    - Performance metrics
    """
    
    def __init__(self, url='http://localhost:8086', token=None, org='wolfinch', 
                 bucket='trading', enabled=True):
        """
        Initialize InfluxDB connection
        
        Args:
            url: InfluxDB server URL
            token: Authentication token
            org: Organization name
            bucket: Bucket (database) name
            enabled: Enable/disable InfluxDB
        """
        self.enabled = enabled and INFLUX_AVAILABLE
        self.client = None
        self.write_api = None
        self.query_api = None
        self.org = org
        self.bucket = bucket
        
        if not self.enabled:
            log.info("InfluxDB disabled")
            return
        
        try:
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                log.info(f"InfluxDB connected: {url} org={org} bucket={bucket}")
            else:
                log.error(f"InfluxDB health check failed: {health.message}")
                self.enabled = False
        except Exception as e:
            log.error(f"InfluxDB connection failed: {e}")
            self.enabled = False
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if InfluxDB is enabled and connected"""
        return self.enabled and self.client is not None
    
    # ============ Candle Data Operations ============
    
    def write_candle(self, exchange: str, product: str, timestamp: int, 
                    open_price: float, high: float, low: float, close: float, 
                    volume: float) -> bool:
        """
        Write a single candle to InfluxDB
        
        Args:
            exchange: Exchange name
            product: Product ID
            timestamp: Unix timestamp (seconds)
            open_price: Open price
            high: High price
            low: Low price
            close: Close price
            volume: Volume
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            point = Point("candle") \
                .tag("exchange", exchange) \
                .tag("product", product) \
                .field("open", float(open_price)) \
                .field("high", float(high)) \
                .field("low", float(low)) \
                .field("close", float(close)) \
                .field("volume", float(volume)) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            log.error(f"Error writing candle to InfluxDB: {e}")
            return False
    
    def write_candles_batch(self, exchange: str, product: str, candles: List[Dict]) -> bool:
        """
        Write multiple candles in batch
        
        Args:
            exchange: Exchange name
            product: Product ID
            candles: List of candle dicts with keys: timestamp, open, high, low, close, volume
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            points = []
            for candle in candles:
                point = Point("candle") \
                    .tag("exchange", exchange) \
                    .tag("product", product) \
                    .field("open", float(candle['open'])) \
                    .field("high", float(candle['high'])) \
                    .field("low", float(candle['low'])) \
                    .field("close", float(candle['close'])) \
                    .field("volume", float(candle['volume'])) \
                    .time(int(candle['timestamp']), WritePrecision.S)
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            log.info(f"Wrote {len(points)} candles to InfluxDB for {exchange}:{product}")
            return True
        except Exception as e:
            log.error(f"Error writing candles batch to InfluxDB: {e}")
            return False
    
    def query_candles(self, exchange: str, product: str, start_time: Optional[int] = None,
                     end_time: Optional[int] = None, limit: int = 1000) -> List[Dict]:
        """
        Query candles from InfluxDB
        
        Args:
            exchange: Exchange name
            product: Product ID
            start_time: Start timestamp (seconds), None = last 24 hours
            end_time: End timestamp (seconds), None = now
            limit: Maximum number of candles to return
        
        Returns:
            List of candle dicts
        """
        if not self.is_enabled():
            return []
        
        try:
            # Build time range
            if start_time:
                start_str = f"{start_time}"
            else:
                start_str = "-24h"
            
            if end_time:
                stop_str = f"|> range(stop: {end_time})"
            else:
                stop_str = ""
            
            # Flux query
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_str}) {stop_str}
                |> filter(fn: (r) => r["_measurement"] == "candle")
                |> filter(fn: (r) => r["exchange"] == "{exchange}")
                |> filter(fn: (r) => r["product"] == "{product}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: {limit})
                |> sort(columns: ["_time"])
            '''
            
            result = self.query_api.query(org=self.org, query=query)
            
            candles = []
            for table in result:
                for record in table.records:
                    candle = {
                        'timestamp': int(record.get_time().timestamp()),
                        'open': record.values.get('open', 0),
                        'high': record.values.get('high', 0),
                        'low': record.values.get('low', 0),
                        'close': record.values.get('close', 0),
                        'volume': record.values.get('volume', 0)
                    }
                    candles.append(candle)
            
            return candles
        except Exception as e:
            log.error(f"Error querying candles from InfluxDB: {e}")
            return []
    
    # ============ Indicator Data Operations ============
    
    def write_indicator(self, exchange: str, product: str, indicator_name: str,
                       timestamp: int, value: float, **tags) -> bool:
        """
        Write an indicator value
        
        Args:
            exchange: Exchange name
            product: Product ID
            indicator_name: Indicator name (e.g., 'EMA_20', 'RSI_14')
            timestamp: Unix timestamp (seconds)
            value: Indicator value
            **tags: Additional tags (e.g., period=20)
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            point = Point("indicator") \
                .tag("exchange", exchange) \
                .tag("product", product) \
                .tag("name", indicator_name)
            
            # Add additional tags
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, str(tag_value))
            
            point = point.field("value", float(value)) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            log.error(f"Error writing indicator to InfluxDB: {e}")
            return False
    
    # ============ Trade Data Operations ============
    
    def write_trade(self, exchange: str, product: str, timestamp: int,
                   side: str, price: float, size: float, order_id: str,
                   **fields) -> bool:
        """
        Write a trade execution
        
        Args:
            exchange: Exchange name
            product: Product ID
            timestamp: Unix timestamp (seconds)
            side: 'buy' or 'sell'
            price: Execution price
            size: Trade size
            order_id: Order ID
            **fields: Additional fields (e.g., fee, profit)
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            point = Point("trade") \
                .tag("exchange", exchange) \
                .tag("product", product) \
                .tag("side", side) \
                .tag("order_id", order_id) \
                .field("price", float(price)) \
                .field("size", float(size))
            
            # Add additional fields
            for field_key, field_value in fields.items():
                point = point.field(field_key, float(field_value))
            
            point = point.time(timestamp, WritePrecision.S)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            log.error(f"Error writing trade to InfluxDB: {e}")
            return False
    
    # ============ Performance Metrics ============
    
    def write_metric(self, metric_name: str, value: float, **tags) -> bool:
        """
        Write a performance metric
        
        Args:
            metric_name: Metric name (e.g., 'pnl', 'win_rate')
            value: Metric value
            **tags: Tags (e.g., exchange, product, strategy)
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            point = Point("metric") \
                .tag("name", metric_name)
            
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, str(tag_value))
            
            point = point.field("value", float(value)) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            log.error(f"Error writing metric to InfluxDB: {e}")
            return False
    
    # ============ Utility Methods ============
    
    def delete_data(self, start: str, stop: str, predicate: str) -> bool:
        """
        Delete data from InfluxDB
        
        Args:
            start: Start time (RFC3339 format or relative, e.g., '-1h')
            stop: Stop time (RFC3339 format or 'now')
            predicate: Delete predicate (e.g., '_measurement="candle"')
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            delete_api = self.client.delete_api()
            delete_api.delete(start, stop, predicate, bucket=self.bucket, org=self.org)
            log.info(f"Deleted data: {predicate} from {start} to {stop}")
            return True
        except Exception as e:
            log.error(f"Error deleting data from InfluxDB: {e}")
            return False
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            try:
                self.client.close()
                log.info("InfluxDB connection closed")
            except Exception as e:
                log.error(f"Error closing InfluxDB connection: {e}")


# Global InfluxDB instance
_influx_db = None

def init_influx_db(config: Dict) -> InfluxDB:
    """Initialize global InfluxDB instance"""
    global _influx_db
    _influx_db = InfluxDB(
        url=config.get('url', 'http://localhost:8086'),
        token=config.get('token'),
        org=config.get('org', 'wolfinch'),
        bucket=config.get('bucket', 'trading'),
        enabled=config.get('enabled', True)
    )
    return _influx_db

def get_influx_db() -> Optional[InfluxDB]:
    """Get global InfluxDB instance"""
    return _influx_db

# EOF
