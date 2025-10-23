#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wolfinch Auto trading Bot
# Desc: PostgreSQL Audit Logger - Save all trades and events to PostgreSQL
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

import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal
from utils import getLogger

log = getLogger('PostgresLogger')
log.setLevel(log.INFO)

# Check if psycopg2 is available
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import Json, RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    log.warning("psycopg2 not installed - PostgreSQL logging disabled")
    POSTGRES_AVAILABLE = False


class PostgresLogger:
    """
    Comprehensive PostgreSQL audit logger
    
    Logs all trading activities to PostgreSQL for:
    - Audit compliance
    - Long-term storage
    - Relational queries
    - Performance analytics
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL logger
        
        Args:
            config: Database configuration dict with keys:
                - host: Database host
                - port: Database port
                - database: Database name
                - user: Database user
                - password: Database password
        """
        self.config = config
        self.connection_pool = None
        self.enabled = False
        self.batch_buffer = []
        self.batch_size = 100
        self.last_flush_time = time.time()
        self.flush_interval = 10  # seconds
        
        if not POSTGRES_AVAILABLE:
            log.warning("PostgreSQL logger disabled - psycopg2 not available")
            return
        
        try:
            # Create connection pool
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=config.get('host', 'localhost'),
                port=config.get('port', 5432),
                database=config.get('database', 'wolfinch'),
                user=config.get('user', 'wolfinch'),
                password=config.get('password', 'wolfinch2024')
            )
            
            if self.connection_pool:
                self.enabled = True
                log.info(f"PostgreSQL logger initialized: {config.get('host')}:{config.get('port')}/{config.get('database')}")
                
                # Test connection
                conn = self._get_connection()
                if conn:
                    self._release_connection(conn)
                    log.info("PostgreSQL connection test successful")
            else:
                log.error("Failed to create PostgreSQL connection pool")
                
        except Exception as e:
            log.error(f"Failed to initialize PostgreSQL logger: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if PostgreSQL logging is enabled"""
        return self.enabled and POSTGRES_AVAILABLE
    
    def _get_connection(self):
        """Get connection from pool"""
        try:
            if self.connection_pool:
                return self.connection_pool.getconn()
        except Exception as e:
            log.error(f"Error getting connection from pool: {e}")
        return None
    
    def _release_connection(self, conn):
        """Release connection back to pool"""
        try:
            if self.connection_pool and conn:
                self.connection_pool.putconn(conn)
        except Exception as e:
            log.error(f"Error releasing connection: {e}")
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """
        Execute a query with automatic connection management
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results if fetch=True, else None
        """
        if not self.is_enabled():
            return None
        
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor if fetch else None)
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                conn.commit()
                return results
            else:
                conn.commit()
                return True
                
        except Exception as e:
            log.error(f"Error executing query: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._release_connection(conn)
    
    def log_trade(self, exchange: str, symbol: str, action: str, order_type: str,
                  quantity: float, price: float, status: str, order_id: str,
                  strategy: str = None, metadata: Dict = None) -> bool:
        """
        Log a trade to audit.trade_logs
        
        Args:
            exchange: Exchange name
            symbol: Trading symbol
            action: BUY or SELL
            order_type: MARKET, LIMIT, etc.
            quantity: Order quantity
            price: Order price
            status: Order status
            order_id: Order ID
            strategy: Strategy name
            metadata: Additional metadata as dict
        """
        if not self.is_enabled():
            return False
        
        try:
            query = """
                INSERT INTO audit.trade_logs 
                (timestamp, exchange, symbol, action, order_type, quantity, price, status, order_id, strategy, metadata)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                exchange,
                symbol,
                action,
                order_type,
                Decimal(str(quantity)),
                Decimal(str(price)),
                status,
                order_id,
                strategy,
                Json(metadata) if metadata else None
            )
            
            result = self._execute_query(query, params)
            
            if result:
                log.debug(f"Logged trade: {action} {quantity} {symbol} @ {price}")
                return True
            
            return False
            
        except Exception as e:
            log.error(f"Error logging trade: {e}")
            return False
    
    def log_system_event(self, event_type: str, severity: str, component: str,
                        message: str, metadata: Dict = None) -> bool:
        """
        Log a system event to audit.system_events
        
        Args:
            event_type: Type of event (e.g., 'order_placed', 'error', 'startup')
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            component: Component name (e.g., 'market', 'exchange', 'strategy')
            message: Event message
            metadata: Additional metadata as dict
        """
        if not self.is_enabled():
            return False
        
        try:
            query = """
                INSERT INTO audit.system_events 
                (timestamp, event_type, severity, component, message, metadata)
                VALUES (NOW(), %s, %s, %s, %s, %s)
            """
            
            params = (
                event_type,
                severity,
                component,
                message,
                Json(metadata) if metadata else None
            )
            
            result = self._execute_query(query, params)
            
            if result:
                log.debug(f"Logged system event: {event_type} - {severity}")
                return True
            
            return False
            
        except Exception as e:
            log.error(f"Error logging system event: {e}")
            return False
    
    def log_performance_metrics(self, strategy: str, symbol: str, pnl: float,
                               return_pct: float, sharpe_ratio: float = None,
                               max_drawdown: float = None, win_rate: float = None,
                               total_trades: int = None, metadata: Dict = None) -> bool:
        """
        Log performance metrics to analytics.performance_metrics
        
        Args:
            strategy: Strategy name
            symbol: Trading symbol
            pnl: Profit/Loss
            return_pct: Return percentage
            sharpe_ratio: Sharpe ratio
            max_drawdown: Maximum drawdown
            win_rate: Win rate percentage
            total_trades: Total number of trades
            metadata: Additional metadata as dict
        """
        if not self.is_enabled():
            return False
        
        try:
            query = """
                INSERT INTO analytics.performance_metrics 
                (timestamp, strategy, symbol, pnl, return_pct, sharpe_ratio, max_drawdown, win_rate, total_trades, metadata)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                strategy,
                symbol,
                Decimal(str(pnl)),
                Decimal(str(return_pct)),
                Decimal(str(sharpe_ratio)) if sharpe_ratio is not None else None,
                Decimal(str(max_drawdown)) if max_drawdown is not None else None,
                Decimal(str(win_rate)) if win_rate is not None else None,
                total_trades,
                Json(metadata) if metadata else None
            )
            
            result = self._execute_query(query, params)
            
            if result:
                log.debug(f"Logged performance metrics: {strategy} - {symbol}")
                return True
            
            return False
            
        except Exception as e:
            log.error(f"Error logging performance metrics: {e}")
            return False
    
    def log_order_lifecycle(self, order_id: str, status: str, timestamp: datetime = None,
                           metadata: Dict = None) -> bool:
        """
        Log order lifecycle event
        
        Args:
            order_id: Order ID
            status: Order status
            timestamp: Event timestamp
            metadata: Additional metadata
        """
        return self.log_system_event(
            event_type='order_lifecycle',
            severity='INFO',
            component='order_book',
            message=f"Order {order_id} status: {status}",
            metadata={'order_id': order_id, 'status': status, **(metadata or {})}
        )
    
    def log_position_change(self, symbol: str, action: str, quantity: float,
                           price: float, pnl: float = None, metadata: Dict = None) -> bool:
        """
        Log position change event
        
        Args:
            symbol: Trading symbol
            action: OPEN or CLOSE
            quantity: Position quantity
            price: Position price
            pnl: Profit/Loss (for close)
            metadata: Additional metadata
        """
        return self.log_system_event(
            event_type='position_change',
            severity='INFO',
            component='position_manager',
            message=f"Position {action}: {quantity} {symbol} @ {price}",
            metadata={
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'pnl': pnl,
                **(metadata or {})
            }
        )
    
    def get_trades(self, start_time: datetime = None, end_time: datetime = None,
                   symbol: str = None, strategy: str = None, limit: int = 1000) -> List[Dict]:
        """
        Query trades from audit.trade_logs
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            symbol: Filter by symbol
            strategy: Filter by strategy
            limit: Maximum number of results
            
        Returns:
            List of trade records as dicts
        """
        if not self.is_enabled():
            return []
        
        try:
            conditions = []
            params = []
            
            if start_time:
                conditions.append("timestamp >= %s")
                params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= %s")
                params.append(end_time)
            
            if symbol:
                conditions.append("symbol = %s")
                params.append(symbol)
            
            if strategy:
                conditions.append("strategy = %s")
                params.append(strategy)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT * FROM audit.trade_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            params.append(limit)
            
            results = self._execute_query(query, tuple(params), fetch=True)
            return results if results else []
            
        except Exception as e:
            log.error(f"Error querying trades: {e}")
            return []
    
    def get_performance_summary(self, strategy: str, start_time: datetime = None,
                               end_time: datetime = None) -> Dict:
        """
        Get performance summary for a strategy
        
        Args:
            strategy: Strategy name
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Performance summary dict
        """
        if not self.is_enabled():
            return {}
        
        try:
            conditions = ["strategy = %s"]
            params = [strategy]
            
            if start_time:
                conditions.append("timestamp >= %s")
                params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= %s")
                params.append(end_time)
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT 
                    strategy,
                    COUNT(*) as total_records,
                    SUM(pnl) as total_pnl,
                    AVG(return_pct) as avg_return,
                    AVG(sharpe_ratio) as avg_sharpe,
                    MAX(max_drawdown) as max_drawdown,
                    AVG(win_rate) as avg_win_rate,
                    SUM(total_trades) as total_trades
                FROM analytics.performance_metrics
                WHERE {where_clause}
                GROUP BY strategy
            """
            
            results = self._execute_query(query, tuple(params), fetch=True)
            
            if results and len(results) > 0:
                return dict(results[0])
            
            return {}
            
        except Exception as e:
            log.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_system_events(self, severity: str = None, start_time: datetime = None,
                         end_time: datetime = None, limit: int = 1000) -> List[Dict]:
        """
        Query system events from audit.system_events
        
        Args:
            severity: Filter by severity
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum number of results
            
        Returns:
            List of event records as dicts
        """
        if not self.is_enabled():
            return []
        
        try:
            conditions = []
            params = []
            
            if severity:
                conditions.append("severity = %s")
                params.append(severity)
            
            if start_time:
                conditions.append("timestamp >= %s")
                params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= %s")
                params.append(end_time)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT * FROM audit.system_events
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            params.append(limit)
            
            results = self._execute_query(query, tuple(params), fetch=True)
            return results if results else []
            
        except Exception as e:
            log.error(f"Error querying system events: {e}")
            return []
    
    def flush_batch(self) -> bool:
        """Flush any buffered writes (for future batch implementation)"""
        # Placeholder for batch write implementation
        return True
    
    def close(self):
        """Close all connections and cleanup"""
        try:
            if self.connection_pool:
                self.connection_pool.closeall()
                log.info("PostgreSQL connection pool closed")
        except Exception as e:
            log.error(f"Error closing PostgreSQL connection pool: {e}")


# Global PostgreSQL logger instance
_postgres_logger = None


def init_postgres_logger(config: Dict[str, Any] = None) -> Optional[PostgresLogger]:
    """
    Initialize global PostgreSQL logger
    
    Args:
        config: Database configuration dict
        
    Returns:
        PostgresLogger instance or None if initialization failed
    """
    global _postgres_logger
    
    if not POSTGRES_AVAILABLE:
        log.warning("PostgreSQL logger not available - psycopg2 not installed")
        return None
    
    if config is None:
        # Default configuration
        config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'wolfinch',
            'user': 'wolfinch',
            'password': 'wolfinch2024'
        }
    
    try:
        _postgres_logger = PostgresLogger(config)
        if _postgres_logger.is_enabled():
            log.info("Global PostgreSQL logger initialized successfully")
            return _postgres_logger
        else:
            log.warning("PostgreSQL logger initialized but not enabled")
            return None
    except Exception as e:
        log.error(f"Failed to initialize global PostgreSQL logger: {e}")
        return None


def get_postgres_logger() -> Optional[PostgresLogger]:
    """
    Get global PostgreSQL logger instance
    
    Returns:
        PostgresLogger instance or None if not initialized
    """
    global _postgres_logger
    return _postgres_logger


# EOF
