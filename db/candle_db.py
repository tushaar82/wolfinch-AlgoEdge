#
# wolfinch Auto trading Bot
# Desc: Candle Database - InfluxDB Primary, SQLite Fallback
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



from utils import getLogger
from .db import init_db
from sqlalchemy import *
from sqlalchemy.orm import registry
from sqlalchemy import inspect

log = getLogger ('CANDLE-DB')
log.setLevel (log.DEBUG)

# SQLAlchemy 2.0: Create a registry for classical mapping
mapper_registry = registry()

class CandlesDb(object):
    """
    Candle Database with InfluxDB as primary storage
    Automatically uses InfluxDB if available, falls back to SQLite
    """
    def __init__ (self, ohlcCls, exchange_name, product_id, read_only=False):
        # Try to use InfluxDB first
        try:
            from .candle_db_influx import CandleDBInflux
            from .influx_db import get_influx_db
            
            influx = get_influx_db()
            if influx and influx.is_enabled():
                # Use InfluxDB
                log.info(f"Using InfluxDB for {exchange_name}:{product_id}")
                self._impl = CandleDBInflux(exchange_name, product_id, ohlcCls)
                self._using_influx = True
                return
        except Exception as e:
            log.debug(f"InfluxDB not available: {e}")
        
        # Fallback to SQLite
        log.info(f"Using SQLite for {exchange_name}:{product_id}")
        self._using_influx = False
        self._init_sqlite(ohlcCls, exchange_name, product_id, read_only)
    
    def _init_sqlite(self, ohlcCls, exchange_name, product_id, read_only=False):
        self.OHLCCls = ohlcCls
        self.db = init_db(read_only)
        log.info ("init candlesdb: %s %s"%(exchange_name, product_id))
        
        self.table_name = "candle_%s_%s"%(exchange_name, product_id)
        # SQLAlchemy 2.0 compatible: use inspect() instead of dialect.has_table()
        inspector = inspect(self.db.engine)
        if not inspector.has_table(self.table_name):  # If table don't exist, Create.
            # Create a table with the appropriate Columns
            log.info ("creating table: %s"%(self.table_name))            
            self.table = Table(self.table_name, self.db.metadata,
#                 Column('Id', Integer, primary_key=True),
#                 Column('time', Integer, nullable=False),
                Column('time', Integer, primary_key=True, nullable=False),                
                Column('open', Numeric, default=0),
                Column('high', Numeric, default=0),
                Column('low', Numeric, default=0),
                Column('close', Numeric, default=0),
                Column('volume', Numeric, default=0))
            # Implement the creation
            self.db.metadata.create_all(self.db.engine, checkfirst=True)   
        else:
            log.info ("table %s exists already"%self.table_name)
            self.table = self.db.metadata.tables[self.table_name]
        try:
            # HACK ALERT: to support multi-table with same class on sqlalchemy mapping
            class T (ohlcCls):
                def __init__ (self, c):
                    self.time = c.time
                    self.open = c.open
                    self.high = c.high
                    self.low = c.low
                    self.close = c.close
                    self.volume = c.volume
            self.ohlcCls = T
            # SQLAlchemy 2.0: Use registry.map_imperatively instead of mapper
            self.mapping = mapper_registry.map_imperatively(self.ohlcCls, self.table)
        except Exception as e:
            log.debug ("mapping failed with except: %s \n trying once again with non_primary mapping"%(e))
#             self.mapping = mapper(ohlcCls, self.table, non_primary=True)            
            raise e
                    
    def __str__ (self):
        return "{time: %s, open: %g, high: %g, low: %g, close: %g, volume: %g}"%(
            str(self.time), self.open, self.high, self.low, self.close, self.volume)

    # Public API - delegates to InfluxDB or SQLite
    def db_save_candle (self, candle):
        if self._using_influx:
            return self._impl.db_save_candle(candle)
        else:
            return self._db_save_candle_sqlite(candle)
    
    def db_save_candles (self, candles):
        if self._using_influx:
            return self._impl.db_save_candles(candles)
        else:
            return self._db_save_candles_sqlite(candles)
    
    def db_get_candles_after_time(self, after):
        if self._using_influx:
            return self._impl.db_get_candles_after_time(after)
        else:
            return self._db_get_candles_after_time_sqlite(after)
    
    def db_get_all_candles (self):
        if self._using_influx:
            return self._impl.db_get_all_candles()
        else:
            return self._db_get_all_candles_sqlite()
    
    def db_get_recent_candles(self, count=100):
        """Get recent candles (InfluxDB optimized)"""
        if self._using_influx:
            return self._impl.db_get_recent_candles(count)
        else:
            # SQLite fallback - get all and slice
            all_candles = self._db_get_all_candles_sqlite()
            return all_candles[-count:] if len(all_candles) > count else all_candles

    # SQLite implementation methods
    def _db_save_candle_sqlite (self, candle):
        log.debug ("Adding candle to SQLite db")
        c = self.ohlcCls(candle)
        self.db.session.merge (c)
        self.db.session.commit()
        
    def _db_save_candles_sqlite (self, candles):
        log.debug ("Adding candle list to SQLite db")
        for cdl in candles:
            c = self.ohlcCls(cdl)
            self.db.session.merge (c)
        self.db.session.commit()
        
    def _db_get_candles_after_time_sqlite(self, after):
        log.debug ("retrieving candles after time: %d from SQLite db"%(after))
        try:
            res_list = []            
            ResultSet = self.db.session.query(self.mapping).filter(self.ohlcCls.time >= after).order_by(self.ohlcCls.time).all()
            log.info ("Retrieved %d candles for table: %s"%(len(ResultSet), self.table_name))
            
            if (len(ResultSet)):
                res_list = [self.OHLCCls(c.time, c.open, c.high, c.low, c.close, c.volume) for c in ResultSet]
            #clear cache now
            self.db.session.expire_all()
            return res_list
        except Exception as e:
            print(str(e))
            return []          
        
        
    def _db_get_all_candles_sqlite (self):
        log.debug ("retrieving candles from SQLite db")
        try:
            res_list = []
            ResultSet = self.db.session.query(self.mapping).order_by(self.ohlcCls.time).all()
            log.info ("Retrieved %d candles for table: %s"%(len(ResultSet), self.table_name))
            
            if (len(ResultSet)):
                res_list = [self.OHLCCls(c.time, c.open, c.high, c.low, c.close, c.volume) for c in ResultSet]
            #clear cache now
            self.db.session.expire_all()
            return res_list
        except Exception as e:
            print(str(e))
            return []             
# EOF
