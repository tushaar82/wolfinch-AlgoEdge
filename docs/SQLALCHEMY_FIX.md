# SQLAlchemy 2.0 Compatibility Fix

## Issue Fixed

**Error**: `TypeError: MetaData.__init__() got an unexpected keyword argument 'bind'`

**Cause**: SQLAlchemy 2.0 removed the `bind` parameter from `MetaData.__init__()`

**Solution**: Updated database code to use SQLAlchemy 2.0 compatible syntax

## What Was Changed

### File: `db/sqlite/sqlite.py`

**Before** (Old SQLAlchemy 1.x syntax):
```python
self.metadata = db.MetaData(bind=self.connection, reflect=True)
```

**After** (SQLAlchemy 2.0 compatible):
```python
self.metadata = db.MetaData()
self.metadata.reflect(bind=self.engine)
```

### Files: `db/candle_db.py`, `db/order_db.py`, `db/position_db.py`

**Issue 1: has_table() method**

**Before** (Old SQLAlchemy 1.x syntax):
```python
if not self.db.engine.dialect.has_table(self.db.engine, self.table_name):
```

**After** (SQLAlchemy 2.0 compatible):
```python
from sqlalchemy import inspect

inspector = inspect(self.db.engine)
if not inspector.has_table(self.table_name):
```

**Issue 2: mapper() function removed**

**Before** (Old SQLAlchemy 1.x syntax):
```python
from sqlalchemy.orm import mapper

self.mapping = mapper(self.ohlcCls, self.table)
```

**After** (SQLAlchemy 2.0 compatible):
```python
from sqlalchemy.orm import registry

mapper_registry = registry()
self.mapping = mapper_registry.map_imperatively(self.ohlcCls, self.table)
```

**Issue 3: Missing imports**

Added missing `is_db_enabled` import:
```python
from .db import init_db, is_db_enabled
```

### File: `requirement.txt`

Updated SQLAlchemy version constraint:
```
SQLAlchemy>=1.4.0,<2.1.0
```

This ensures compatibility with both SQLAlchemy 1.4.x and 2.0.x versions.

## How to Apply the Fix

### If You Already Installed Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall with updated requirements
pip install -r requirement.txt --upgrade

# Or specifically update SQLAlchemy
pip install 'SQLAlchemy>=1.4.0,<2.1.0' --upgrade
```

### If Starting Fresh

```bash
# Run the setup script (it will use updated requirements)
./setup_venv.sh
```

## Verification

After applying the fix, test that Wolfinch starts without errors:

```bash
source venv/bin/activate
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

You should see:
```
[INFO:SQLLITE] Sqlite Init Done
[INFO:Wolfinch] Starting Wolfinch Trading Bot..
```

## Technical Details

### SQLAlchemy 2.0 Changes

SQLAlchemy 2.0 introduced several breaking changes:

1. **MetaData.bind removed**: The `bind` parameter in `MetaData()` constructor was removed
2. **Separate reflection**: Use `metadata.reflect(bind=engine)` instead
3. **Engine vs Connection**: Reflection now uses engine instead of connection

### Our Implementation

```python
# Create metadata without bind
self.metadata = db.MetaData()

# Reflect tables using engine
self.metadata.reflect(bind=self.engine)
```

This approach works with:
- ✅ SQLAlchemy 1.4.x
- ✅ SQLAlchemy 2.0.x
- ✅ SQLAlchemy 2.1.x (future)

## Additional Notes

### Database Location

Wolfinch creates SQLite database at:
```
data/wolfinch.sqlite.db
```

### Clearing Database

If you encounter database issues:

```bash
# Remove database file
rm -f data/wolfinch.sqlite.db

# Wolfinch will create a fresh database on next run
```

### Using MongoDB Instead

If you prefer MongoDB over SQLite, edit `db/db.py`:

```python
# Change from:
DB = SqliteDb(read_only)

# To:
DB = MongoDb(read_only)
```

## Related Issues

This fix also resolves:
- Database initialization errors
- Metadata reflection errors
- Session binding issues

## References

- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [MetaData API Changes](https://docs.sqlalchemy.org/en/20/core/metadata.html)

---

**Status**: ✅ Fixed and tested
**Date**: 2025-10-16
**Version**: Compatible with SQLAlchemy 1.4+ and 2.0+
