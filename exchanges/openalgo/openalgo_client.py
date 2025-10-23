#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: OpenAlgo Exchange Implementation
 Copyright: (c) 2024 Wolfinch Contributors
 This file is part of Wolfinch.
'''

import json
import pprint
from decimal import Decimal
from datetime import datetime, timedelta
from time import sleep
import time
from dateutil.tz import tzlocal, tzutc

try:
    from openalgo import api as openalgo_api
except ImportError:
    print("OpenAlgo SDK not installed. Please run: pip install openalgo")
    raise

from utils import getLogger, readConf
from market import Market, OHLC, feed_enQ, get_market_by_product, Order
from exchanges import Exchange

log = getLogger('OpenAlgo')
log.setLevel(log.INFO)

# OpenAlgo CONFIG FILE
OPENALGO_CONF = 'config/openalgo.yml'

# NSE FNO Lot Sizes - Updated as of 2024
# These should be updated periodically from NSE
NSE_LOT_SIZES = {
    # Index Options
    'NIFTY': 50,
    'BANKNIFTY': 15,
    'FINNIFTY': 40,
    'MIDCPNIFTY': 75,

    # Stock Options (Top traded)
    'RELIANCE': 250,
    'TCS': 150,
    'HDFCBANK': 550,
    'INFY': 300,
    'ICICIBANK': 1375,
    'HINDUNILVR': 300,
    'ITC': 1600,
    'SBIN': 1500,
    'BHARTIARTL': 1600,
    'BAJFINANCE': 125,
    'ASIANPAINT': 300,
    'MARUTI': 100,
    'AXISBANK': 1200,
    'LT': 300,
    'SUNPHARMA': 700,
    'TITAN': 275,
    'ULTRACEMCO': 100,
    'NESTLEIND': 200,
    'TATAMOTORS': 1500,
    'WIPRO': 1200,
    'M&M': 300,
    'NTPC': 3375,
    'KOTAKBANK': 400,
    'POWERGRID': 2700,
    'TATASTEEL': 1500,
    'TECHM': 600,
    'ADANIPORTS': 500,
    'ONGC': 2475,
    'HINDALCO': 2850,
    'INDUSINDBK': 900,
    'JSWSTEEL': 1200,
    'BAJAJFINSV': 200,
    'DIVISLAB': 300,
    'DRREDDY': 125,
    'CIPLA': 700,
    'EICHERMOT': 175,
    'HEROMOTOCO': 100,
    'GRASIM': 300,
    'COALINDIA': 2100,
    'BRITANNIA': 200,
    'SHREECEM': 50,
    'UPL': 1200,
    'APOLLOHOSP': 150,
    'BAJAJ-AUTO': 150,
    'BPCL': 1500,
}


class OpenAlgo(Exchange):
    name = "openalgo"
    openalgo_conf = {}
    openalgo_products = []
    openalgo_accounts = {}
    client = None
    symbol_to_id = {}
    primary = False
    lot_sizes = {}

    def __init__(self, config, primary=False):
        log.info("Init OpenAlgo exchange")

        exch_cfg_file = config.get('config')
        if exch_cfg_file == None:
            exch_cfg_file = OPENALGO_CONF
        conf = readConf(exch_cfg_file)
        if (conf != None and len(conf)):
            self.openalgo_conf = conf['exchange']
        else:
            log.error("Failed to read OpenAlgo configuration")
            return None

        self.primary = True if primary else False

        # Get candle interval
        if config.get('candle_interval'):
            self.candle_interval = int(config['candle_interval'])

        # Get backfill config
        backfill = config.get('backfill')
        if backfill:
            if backfill.get('enabled'):
                self.openalgo_conf['backfill_enabled'] = backfill['enabled']
            if backfill.get('period'):
                self.openalgo_conf['backfill_period'] = int(backfill['period'])

        # Get OpenAlgo credentials
        api_key = self.openalgo_conf.get('apiKey')
        host_url = self.openalgo_conf.get('hostUrl', 'http://127.0.0.1:5000')

        if not api_key:
            log.critical("Invalid API Key in OpenAlgo Config!!")
            return None

        # Initialize OpenAlgo client
        try:
            self.client = openalgo_api.OpenAlgoClient(api_key=api_key, host_url=host_url)
            log.info(f"OpenAlgo client initialized with host: {host_url}")
        except Exception as e:
            log.critical(f"Unable to initialize OpenAlgo client: {e}")
            return None

        # Load lot sizes from config or use defaults
        custom_lot_sizes = self.openalgo_conf.get('lot_sizes', {})
        self.lot_sizes = {**NSE_LOT_SIZES, **custom_lot_sizes}

        log.info(f"Loaded {len(self.lot_sizes)} lot size configurations")

        # Get products from config
        if self.openalgo_conf.get('products'):
            for prod in self.openalgo_conf['products']:
                for symbol, details in prod.items():
                    product_info = {
                        'id': details.get('id', symbol),
                        'symbol': symbol,
                        'display_name': details.get('display_name', symbol),
                        'exchange': details.get('exchange', 'NSE'),
                        'segment': details.get('segment', 'FNO'),
                        'instrument_type': details.get('instrument_type', 'OPTIDX'),
                        'lot_size': self.lot_sizes.get(symbol.replace('NFO:', '').split('-')[0], 1),
                        'asset_type': details.get('asset_type', 'OPTIONS'),
                        'fund_type': details.get('fund_type', 'INR')
                    }
                    self.symbol_to_id[symbol] = product_info['id']
                    self.openalgo_products.append(product_info)
                    log.info(f"Loaded product: {symbol} with lot size: {product_info['lot_size']}")

        # Get account info
        try:
            account_info = self._get_account_info()
            if account_info:
                self.openalgo_accounts = account_info
                log.info("Account information retrieved successfully")
        except Exception as e:
            log.warning(f"Could not retrieve account info: {e}")

        log.info(f"OpenAlgo exchange initialized with {len(self.openalgo_products)} products")

    def _get_account_info(self):
        """Get account information from OpenAlgo"""
        try:
            # Using OpenAlgo SDK to get funds
            response = self.client.funds()
            if response and 'data' in response:
                return response['data']
            return {}
        except Exception as e:
            log.error(f"Error getting account info: {e}")
            return {}

    def get_lot_size(self, symbol):
        """Get lot size for a symbol"""
        # Extract base symbol from option symbol
        # Format: NIFTY-24JAN25-22000-CE -> NIFTY
        base_symbol = symbol.replace('NFO:', '').split('-')[0]
        lot_size = self.lot_sizes.get(base_symbol, 1)
        log.debug(f"Lot size for {symbol} (base: {base_symbol}): {lot_size}")
        return lot_size

    def calculate_quantity(self, symbol, lots=1):
        """Calculate quantity based on lots"""
        lot_size = self.get_lot_size(symbol)
        quantity = lots * lot_size
        log.debug(f"Calculated quantity for {symbol}: {lots} lots = {quantity} units")
        return quantity

    def buy(self, product, price=0, size=0, client_id=None):
        """
        Place a buy order
        For FNO: size parameter represents number of lots
        """
        try:
            symbol = product.get_name()
            lot_size = self.get_lot_size(symbol)

            # Convert lots to quantity
            if size > 0:
                quantity = int(size * lot_size)
            else:
                quantity = lot_size  # Default to 1 lot

            log.info(f"Placing BUY order: {symbol}, lots: {size}, quantity: {quantity}, price: {price}")

            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'exchange': product.get('exchange', 'NFO'),
                'action': 'BUY',
                'quantity': quantity,
                'price': price if price > 0 else 0,
                'product': product.get('product_type', 'MIS'),  # MIS or NRML
                'order_type': 'MARKET' if price == 0 else 'LIMIT',
                'price_type': 'MARKET' if price == 0 else 'LIMIT'
            }

            if client_id:
                order_params['client_id'] = client_id

            # Place order using OpenAlgo SDK
            response = self.client.placeorder(**order_params)

            if response and response.get('status') == 'success':
                order_id = response.get('orderid')
                log.info(f"Buy order placed successfully: {order_id}")
                return Order(
                    order_id=order_id,
                    symbol=symbol,
                    side='buy',
                    size=quantity,
                    price=price,
                    status='pending'
                )
            else:
                log.error(f"Buy order failed: {response}")
                return None

        except Exception as e:
            log.error(f"Error placing buy order: {e}")
            return None

    def sell(self, product, price=0, size=0, client_id=None):
        """
        Place a sell order
        For FNO: size parameter represents number of lots
        """
        try:
            symbol = product.get_name()
            lot_size = self.get_lot_size(symbol)

            # Convert lots to quantity
            if size > 0:
                quantity = int(size * lot_size)
            else:
                quantity = lot_size  # Default to 1 lot

            log.info(f"Placing SELL order: {symbol}, lots: {size}, quantity: {quantity}, price: {price}")

            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'exchange': product.get('exchange', 'NFO'),
                'action': 'SELL',
                'quantity': quantity,
                'price': price if price > 0 else 0,
                'product': product.get('product_type', 'MIS'),
                'order_type': 'MARKET' if price == 0 else 'LIMIT',
                'price_type': 'MARKET' if price == 0 else 'LIMIT'
            }

            if client_id:
                order_params['client_id'] = client_id

            # Place order using OpenAlgo SDK
            response = self.client.placeorder(**order_params)

            if response and response.get('status') == 'success':
                order_id = response.get('orderid')
                log.info(f"Sell order placed successfully: {order_id}")
                return Order(
                    order_id=order_id,
                    symbol=symbol,
                    side='sell',
                    size=quantity,
                    price=price,
                    status='pending'
                )
            else:
                log.error(f"Sell order failed: {response}")
                return None

        except Exception as e:
            log.error(f"Error placing sell order: {e}")
            return None

    def get_order(self, order_id):
        """Get order details"""
        try:
            response = self.client.orderbook()
            if response and 'data' in response:
                orders = response['data']
                for order in orders:
                    if str(order.get('orderid')) == str(order_id):
                        return order
            return None
        except Exception as e:
            log.error(f"Error getting order: {e}")
            return None

    def cancel_order(self, order_id):
        """Cancel an order"""
        try:
            log.info(f"Canceling order: {order_id}")
            response = self.client.cancelorder(orderid=order_id)

            if response and response.get('status') == 'success':
                log.info(f"Order canceled successfully: {order_id}")
                return True
            else:
                log.error(f"Cancel order failed: {response}")
                return False

        except Exception as e:
            log.error(f"Error canceling order: {e}")
            return False

    def get_products(self):
        """Get list of products"""
        return self.openalgo_products

    def get_accounts(self):
        """Get account information"""
        return self.openalgo_accounts

    def get_historic_rates(self, product, start=None, end=None, granularity=300):
        """
        Get historical candle data
        For OpenAlgo, this would typically use the historical data API
        """
        try:
            symbol = product if isinstance(product, str) else product.get_name()

            # Calculate date range
            if not end:
                end = datetime.now()
            if not start:
                start = end - timedelta(days=self.openalgo_conf.get('backfill_period', 30))

            log.info(f"Fetching historical data for {symbol} from {start} to {end}")

            # Convert granularity to interval format
            interval_map = {
                60: '1m',
                300: '5m',
                900: '15m',
                1800: '30m',
                3600: '1h',
                86400: '1d'
            }
            interval = interval_map.get(granularity, '5m')

            # Use OpenAlgo historical data API
            # Note: This is a placeholder - actual implementation depends on OpenAlgo's historical data endpoint
            candles = []

            # For now, return empty list - historical data fetching can be implemented
            # when OpenAlgo provides the historical data endpoint
            log.warning("Historical data fetching not yet implemented for OpenAlgo")

            return candles

        except Exception as e:
            log.error(f"Error getting historical rates: {e}")
            return []

    def get_product_order_book(self, product):
        """Get order book for a product"""
        try:
            response = self.client.orderbook()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            log.error(f"Error getting order book: {e}")
            return []

    def get_positions(self):
        """Get current positions"""
        try:
            response = self.client.positionbook()
            if response and 'data' in response:
                positions = response['data']
                log.debug(f"Retrieved {len(positions)} positions")
                return positions
            return []
        except Exception as e:
            log.error(f"Error getting positions: {e}")
            return []

    def get_holdings(self):
        """Get holdings"""
        try:
            response = self.client.holdingsbook()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            log.error(f"Error getting holdings: {e}")
            return []

    def close_position(self, symbol, quantity=None):
        """Close a position"""
        try:
            positions = self.get_positions()
            for pos in positions:
                if pos.get('symbol') == symbol:
                    qty = quantity if quantity else abs(pos.get('quantity', 0))
                    side = 'SELL' if pos.get('quantity', 0) > 0 else 'BUY'

                    order_params = {
                        'symbol': symbol,
                        'exchange': pos.get('exchange', 'NFO'),
                        'action': side,
                        'quantity': qty,
                        'product': pos.get('product', 'MIS'),
                        'order_type': 'MARKET',
                        'price_type': 'MARKET',
                        'price': 0
                    }

                    response = self.client.placeorder(**order_params)

                    if response and response.get('status') == 'success':
                        log.info(f"Position closed: {symbol}")
                        return True
                    else:
                        log.error(f"Failed to close position: {response}")
                        return False

            log.warning(f"No position found for {symbol}")
            return False

        except Exception as e:
            log.error(f"Error closing position: {e}")
            return False

    def close(self):
        """Close exchange connection"""
        log.info("Closing OpenAlgo exchange connection")
        # OpenAlgo SDK doesn't require explicit connection closing
        pass

    def __str__(self):
        return f"{{OpenAlgo Exchange: {len(self.openalgo_products)} products}}"

# EOF
