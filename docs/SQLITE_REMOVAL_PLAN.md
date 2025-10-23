# SQLite Complete Removal Plan

Complete migration from SQLite to InfluxDB for all data storage.

---

## 📊 **Current SQLite Usage**

### **1. Candle Data** ✅ DONE
- **Status:** Already migrated to InfluxDB
- **File:** `db/candle_db.py`
- **Solution:** Automatic InfluxDB/SQLite fallback implemented

### **2. Order Data** ⚠️ IN PROGRESS
- **Status:** Currently uses SQLite
- **File:** `db/order_db.py`
- **Purpose:** Store order history for state restoration
- **Solution:** Use InfluxDB trade_event data

### **3. Position Data** ⚠️ IN PROGRESS
- **Status:** Currently uses SQLite
- **File:** `db/position_db.py`
- **Purpose:** Store position history for state restoration
- **Solution:** Use InfluxDB trade_event data

### **4. Base DB** ⚠️ NEEDS UPDATE
- **Status:** SQLite engine
- **File:** `db/db.py`
- **Purpose:** SQLAlchemy database initialization
- **Solution:** Make optional, only for fallback

---

## 🎯 **Migration Strategy**

### **Phase 1: Candle Data** ✅ COMPLETE
- ✅ Created `CandleDBInflux` class
- ✅ Modified `CandlesDb` to auto-select InfluxDB
- ✅ SQLite used only as fallback

### **Phase 2: Trade Logging** ✅ COMPLETE
- ✅ Created `TradeLogger` class
- ✅ Integrated into market execution
- ✅ All trades logged to InfluxDB

### **Phase 3: Order/Position State** 🔄 CURRENT
- ⚠️ Orders and positions still use SQLite
- ⚠️ Need to migrate to InfluxDB
- ⚠️ Or disable if not needed

### **Phase 4: Complete SQLite Removal** 📋 PLANNED
- Remove SQLite dependencies
- Remove `db/db.py` SQLAlchemy code
- Remove `.db` files from gitignore
- Update documentation

---

## 🔧 **Implementation Options**

### **Option 1: Migrate Orders/Positions to InfluxDB** (Recommended)

**Pros:**
- Complete InfluxDB migration
- No SQLite dependency
- Better performance
- Unified data storage

**Cons:**
- More work required
- Need to implement state restoration from InfluxDB

**Implementation:**
1. Create `OrderDBInflux` class
2. Create `PositionDBInflux` class
3. Store orders/positions in InfluxDB
4. Restore state from InfluxDB on restart

### **Option 2: Disable Order/Position Persistence** (Simplest)

**Pros:**
- Immediate SQLite removal
- Simpler codebase
- Less storage needed

**Cons:**
- No state restoration after restart
- Lose order/position history (but we have trade_event logs!)

**Implementation:**
1. Modify `OrderDb` to use in-memory dict only
2. Modify `PositionDb` to use in-memory dict only
3. Remove SQLite initialization
4. Remove `.db` files

### **Option 3: Keep SQLite for Orders/Positions Only** (Current)

**Pros:**
- No changes needed
- State restoration works
- Minimal risk

**Cons:**
- Still depends on SQLite
- Dual database system
- More complexity

---

## 💡 **Recommendation: Option 2 (Disable Persistence)**

**Why?**

1. **Trade data is already in InfluxDB** - We log all trades with complete details
2. **Orders/positions are ephemeral** - They're only needed during runtime
3. **State restoration is rarely needed** - Most trading bots restart fresh
4. **Simpler is better** - Less code, less complexity
5. **InfluxDB has everything** - Can rebuild state from trade_event if needed

**What we lose:**
- Ability to restore exact order/position state after crash
- Order/position history in SQLite (but we have it in InfluxDB!)

**What we gain:**
- ✅ Zero SQLite dependency
- ✅ Simpler codebase
- ✅ Faster startup
- ✅ Less disk usage
- ✅ Unified InfluxDB storage

---

## 🚀 **Implementation Steps (Option 2)**

### **Step 1: Disable SQLite in OrderDb**

```python
# db/order_db.py
class OrderDb(object):
    def __init__(self, orderCls, exchange_name, product_id, read_only=False):
        self.OrderCls = orderCls
        self.db_enable = False  # Always False
        self.ORDER_DB = {}  # In-memory only
        log.info(f"OrderDb initialized (in-memory only, no persistence)")
    
    # Remove all SQLite methods
    # Keep only in-memory dict operations
```

### **Step 2: Disable SQLite in PositionDb**

```python
# db/position_db.py
class PositionDb(object):
    def __init__(self, positionCls, exchange_name, product_id, read_only=False):
        self.PositionCls = positionCls
        self.db_enable = False  # Always False
        self.POSITION_DB = {}  # In-memory only
        log.info(f"PositionDb initialized (in-memory only, no persistence)")
    
    # Remove all SQLite methods
    # Keep only in-memory dict operations
```

### **Step 3: Remove SQLite Dependencies**

```python
# db/__init__.py
from .db_base import DbBase
# Remove: from .db import init_db, clear_db, is_db_enabled
from .candle_db import CandlesDb
from .order_db import OrderDb
from .position_db import PositionDb
```

### **Step 4: Update requirements.txt**

```txt
# Remove SQLAlchemy (if only used for SQLite)
# Keep only:
influxdb-client>=1.38.0
redis>=5.0.0
hiredis>=2.2.0
```

### **Step 5: Clean up files**

```bash
# Remove SQLite database files
rm -f *.db

# Update .gitignore
# Remove: *.db
```

---

## 📊 **Data Availability After Migration**

### **What's in InfluxDB:**

✅ **Candles** - All OHLCV data  
✅ **Orders** - All order_placed, order_filled events  
✅ **Positions** - All position_opened, position_closed events  
✅ **Trades** - Complete trade history with P&L  
✅ **Performance** - All metrics and statistics  

### **What's NOT needed:**

❌ **Order state** - Ephemeral, only needed during runtime  
❌ **Position state** - Ephemeral, only needed during runtime  
❌ **SQLite files** - Replaced by InfluxDB  

---

## ⚠️ **Considerations**

### **State Restoration**

**Before (with SQLite):**
- Wolfinch crashes → Restart → Restore orders/positions from SQLite
- Can continue exactly where it left off

**After (without SQLite):**
- Wolfinch crashes → Restart → Start fresh
- Can query InfluxDB to see what happened
- Can rebuild state from trade_event if needed

**Impact:**
- Minimal - Most trading strategies start fresh anyway
- Can implement InfluxDB-based restoration if needed later

### **Backtesting**

**No impact** - Backtesting uses in-memory data anyway

### **Live Trading**

**Minimal impact** - Orders/positions are managed by exchange
- Wolfinch just tracks them locally
- Can query exchange API to get current state

---

## ✅ **Benefits of Complete SQLite Removal**

1. **Simpler Architecture**
   - One database (InfluxDB)
   - No dual-database complexity
   - Easier to maintain

2. **Better Performance**
   - No SQLite file I/O
   - Faster startup
   - Less disk usage

3. **Unified Data**
   - All data in InfluxDB
   - Single source of truth
   - Easier queries

4. **Modern Stack**
   - Time-series optimized
   - Better for trading data
   - Grafana integration

5. **Scalability**
   - InfluxDB handles millions of points
   - SQLite limited to single file
   - Better for production

---

## 📋 **Migration Checklist**

- [ ] Backup existing SQLite databases
- [ ] Verify all trade data is in InfluxDB
- [ ] Disable SQLite in OrderDb
- [ ] Disable SQLite in PositionDb
- [ ] Remove SQLite initialization
- [ ] Update requirements.txt
- [ ] Remove .db files
- [ ] Update documentation
- [ ] Test Wolfinch startup
- [ ] Test trading execution
- [ ] Verify data in InfluxDB

---

## 🎯 **Recommendation**

**Proceed with Option 2: Disable Order/Position Persistence**

**Rationale:**
- ✅ All important data is already in InfluxDB (trades, P&L, candles)
- ✅ Orders/positions are ephemeral runtime state
- ✅ Simpler codebase, easier to maintain
- ✅ Better performance
- ✅ Can always add InfluxDB-based restoration later if needed

**Next Steps:**
1. Backup current .db files (just in case)
2. Modify OrderDb and PositionDb to disable SQLite
3. Remove SQLite dependencies
4. Test thoroughly
5. Remove .db files

---

**Ready to proceed with complete SQLite removal?** 🚀
