#
# wolfinch Auto trading Bot
# Desc: Position impl - In-Memory Only (No SQLite)
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

log = getLogger ('POSITION-DB')
log.setLevel (log.INFO)

# Position db is an in-memory dictionary
# All position data is logged to InfluxDB via TradeLogger
# No SQLite persistence - positions are ephemeral runtime state

class PositionDb(object):
    """
    In-memory position database
    Positions are logged to InfluxDB via TradeLogger for persistence
    """
    def __init__ (self, positionCls, exchange_name, product_id, read_only=False):
        self.db_enable = False  # Always False - no SQLite
        self.PositionCls = positionCls
        self.exchange_name = exchange_name
        self.product_id = product_id
        
        log.info(f"PositionDb initialized for {exchange_name}:{product_id} (in-memory only, no SQLite)")
        log.info("Position events are logged to InfluxDB via TradeLogger")
    
    # In-memory operations only (no SQLite)
    
    def db_save_position (self, position):
        """Save position - no-op (logged to InfluxDB via TradeLogger)"""
        log.debug(f"Position {position.id} logged to InfluxDB via TradeLogger")
        
    def db_save_positions (self, positions):
        """Save positions - no-op (logged to InfluxDB via TradeLogger)"""
        log.debug(f"Positions logged to InfluxDB via TradeLogger")
        
    def db_delete_position(self, position):
        """Delete position - no-op"""
        log.debug(f"Position {position.id} deleted (in-memory only)")
        
    def db_get_all_positions (self, order_db):
        """Get all positions - returns empty (no persistence)"""
        log.debug("No position persistence - returning empty list")
        return []
            
    def clear_position_db(self):
        """Clear positions - no-op"""
        log.debug("No position persistence to clear")
   
# EOF
