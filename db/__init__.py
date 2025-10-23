from .db_base import DbBase
from .order_db import OrderDb
from .db import init_db, clear_db, is_db_enabled
from .candle_db import CandlesDb
from .position_db import PositionDb

# InfluxDB and Redis support
try:
    from .influx_db import init_influx_db, get_influx_db
    from .redis_cache import init_redis_cache, get_redis_cache
    from .candle_db_influx import CandleDBInflux, create_candle_db
    from .trade_logger import TradeLogger, init_trade_logger, get_trade_logger
    from .indicator_logger import IndicatorLogger, init_indicator_logger, get_indicator_logger
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False

# PostgreSQL support
try:
    from .postgres_logger import PostgresLogger, init_postgres_logger, get_postgres_logger, POSTGRES_AVAILABLE
except ImportError:
    POSTGRES_AVAILABLE = False
