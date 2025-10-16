#
# wolfinch Auto trading Bot
# Desc: order_db impl - In-Memory Only (No SQLite)
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

log = getLogger ('ORDER-DB')
log.setLevel (log.INFO)

# Order db is an in-memory dictionary, keyed with order.id (UUID)
# All order data is logged to InfluxDB via TradeLogger
# No SQLite persistence - orders are ephemeral runtime state

class OrderDb(object):
    """
    In-memory order database
    Orders are logged to InfluxDB via TradeLogger for persistence
    """
    def __init__ (self, orderCls, exchange_name, product_id, read_only=False):
        self.OrderCls = orderCls
        self.db_enable = False  # Always False - no SQLite
        self.ORDER_DB = {}  # In-memory dictionary
        self.exchange_name = exchange_name
        self.product_id = product_id
        
        log.info(f"OrderDb initialized for {exchange_name}:{product_id} (in-memory only, no SQLite)")
        log.info("Order events are logged to InfluxDB via TradeLogger")
    
    # In-memory operations only (no SQLite)
                        
    def db_add_or_update_order (self, order):     
        """Add or update order in memory"""
        log.debug(f"Adding order {order.id} to in-memory cache")
        self.ORDER_DB[order.id] = order
        
    def db_del_order (self, order):       
        """Delete order from memory"""
        log.debug(f"Deleting order {order.id} from in-memory cache")
        if order.id in self.ORDER_DB:
            del self.ORDER_DB[order.id]
        
    def db_get_order (self, order_id):
        """Get order from memory"""
        log.debug(f"Getting order {order_id} from in-memory cache")
        return self.ORDER_DB.get(order_id)
        
    def get_all_orders (self):
        """Get all orders from memory"""
        return self.ORDER_DB.values()
            
    def clear_order_db(self):
        """Clear all orders from memory"""
        log.info("Clearing in-memory order database")
        self.ORDER_DB = {}

# EOF
