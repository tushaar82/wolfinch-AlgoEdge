#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: NSE-specific Validators and Market Features
 Copyright: (c) 2024 Wolfinch Contributors
'''

from datetime import datetime, time as dt_time, date
from typing import Tuple

from utils import getLogger

log = getLogger('NSEValidator')
log.setLevel(log.INFO)


# NSE Market Timings
NSE_TIMINGS = {
    'pre_open_start': dt_time(9, 0, 0),
    'pre_open_end': dt_time(9, 15, 0),
    'regular_start': dt_time(9, 15, 0),
    'regular_end': dt_time(15, 30, 0),
    'post_close_start': dt_time(15, 40, 0),
    'post_close_end': dt_time(16, 0, 0)
}

# NSE Holidays 2025 (Update annually)
NSE_HOLIDAYS_2025 = [
    date(2025, 1, 26),  # Republic Day
    date(2025, 3, 14),  # Holi
    date(2025, 3, 31),  # Id-Ul-Fitr
    date(2025, 4, 10),  # Mahavir Jayanti
    date(2025, 4, 14),  # Dr. Ambedkar Jayanti
    date(2025, 4, 18),  # Good Friday
    date(2025, 5, 1),   # Maharashtra Day
    date(2025, 8, 15),  # Independence Day
    date(2025, 8, 27),  # Ganesh Chaturthi
    date(2025, 10, 2),  # Gandhi Jayanti
    date(2025, 10, 22), # Dussehra
    date(2025, 10, 23), # Dussehra (Muhurat Trading)
    date(2025, 11, 12), # Diwali (Laxmi Pujan)
    date(2025, 11, 13), # Diwali (Balipratipada)
    date(2025, 11, 24), # Gurunanak Jayanti
    date(2025, 12, 25), # Christmas
]


class NSEValidator:
    """
    NSE-specific validation and market features
    """

    @staticmethod
    def is_market_open(current_time=None) -> Tuple[bool, str]:
        """
        Check if NSE market is currently open

        Returns:
            Tuple[bool, str]: (is_open, reason)
        """
        if current_time is None:
            current_time = datetime.now()

        current_date = current_time.date()
        current_time_only = current_time.time()

        # Check if holiday
        if current_date in NSE_HOLIDAYS_2025:
            return False, "NSE Holiday"

        # Check if weekend
        if current_time.weekday() >= 5:  # Saturday=5, Sunday=6
            return False, "Weekend"

        # Check if during regular trading hours
        if NSE_TIMINGS['regular_start'] <= current_time_only <= NSE_TIMINGS['regular_end']:
            return True, "Regular Market Hours"

        # Check if pre-open session
        if NSE_TIMINGS['pre_open_start'] <= current_time_only < NSE_TIMINGS['pre_open_end']:
            return False, "Pre-Open Session (no orders)"

        # Check if after market hours
        if current_time_only < NSE_TIMINGS['regular_start']:
            return False, f"Market opens at {NSE_TIMINGS['regular_start']}"

        if current_time_only > NSE_TIMINGS['regular_end']:
            return False, "Market closed"

        return False, "Outside trading hours"

    @staticmethod
    def is_expiry_day(current_date=None, symbol='NIFTY') -> bool:
        """
        Check if today is expiry day

        Weekly expiry: Thursday
        Monthly expiry: Last Thursday of month
        """
        if current_date is None:
            current_date = datetime.now().date()

        # Check if Thursday (weekly expiry)
        if current_date.weekday() == 3:  # Thursday
            return True

        return False

    @staticmethod
    def get_next_expiry(symbol='NIFTY', current_date=None) -> date:
        """Get next expiry date for symbol"""
        if current_date is None:
            current_date = datetime.now().date()

        # Find next Thursday
        days_ahead = 3 - current_date.weekday()  # Thursday is 3
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        next_expiry = current_date + timedelta(days=days_ahead)
        return next_expiry

    @staticmethod
    def validate_lot_size(symbol, quantity, lot_size) -> Tuple[bool, str]:
        """
        Validate that quantity is a multiple of lot size

        Args:
            symbol: Trading symbol
            quantity: Order quantity
            lot_size: Lot size for symbol

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if quantity % lot_size != 0:
            return False, f"Quantity {quantity} not a multiple of lot size {lot_size}"

        if quantity <= 0:
            return False, f"Quantity must be positive"

        return True, "OK"

    @staticmethod
    def validate_price_circuit(current_price, order_price, circuit_percent=5.0) -> Tuple[bool, str]:
        """
        Validate order price is within circuit limits

        Args:
            current_price: Current LTP
            order_price: Proposed order price
            circuit_percent: Circuit limit percentage

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if order_price <= 0:
            return False, "Price must be positive"

        lower_limit = current_price * (1 - circuit_percent / 100)
        upper_limit = current_price * (1 + circuit_percent / 100)

        if order_price < lower_limit:
            return False, f"Price {order_price} below lower circuit {lower_limit:.2f}"

        if order_price > upper_limit:
            return False, f"Price {order_price} above upper circuit {upper_limit:.2f}"

        return True, "OK"

    @staticmethod
    def validate_freeze_quantity(symbol, quantity) -> Tuple[bool, str]:
        """
        Validate against NSE freeze quantity limits

        Freeze limits (approximate):
        - Index options: 36000 for NIFTY, 12000 for BANKNIFTY
        - Stock options: Varies by stock
        """
        freeze_limits = {
            'NIFTY': 36000,
            'BANKNIFTY': 12000,
            'FINNIFTY': 28000,
        }

        base_symbol = symbol.split('-')[0] if '-' in symbol else symbol
        freeze_limit = freeze_limits.get(base_symbol, 10000)

        if quantity > freeze_limit:
            return False, f"Quantity {quantity} exceeds freeze limit {freeze_limit}"

        return True, "OK"

    @staticmethod
    def should_square_off(current_time=None, symbol='NIFTY') -> Tuple[bool, str]:
        """
        Check if positions should be squared off

        Square off conditions:
        - 15 minutes before market close on expiry day
        - 30 minutes before market close on regular days
        """
        if current_time is None:
            current_time = datetime.now()

        is_expiry = NSEValidator.is_expiry_day(current_time.date(), symbol)

        market_close = datetime.combine(current_time.date(), NSE_TIMINGS['regular_end'])

        if is_expiry:
            # Square off 15 minutes before close on expiry
            square_off_time = market_close - timedelta(minutes=15)
            if current_time >= square_off_time:
                return True, "Expiry day - auto square off"
        else:
            # Square off 30 minutes before close on regular days
            square_off_time = market_close - timedelta(minutes=30)
            if current_time >= square_off_time:
                return True, "Near market close - recommended square off"

        return False, "No square off needed"


# Export validator instance
nse_validator = NSEValidator()


# EOF
