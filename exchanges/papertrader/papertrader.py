#! /usr/bin/env python
# '''
#  Wolfinch Auto trading Bot
#  Desc: Paper Trader exchange - Reads data from CSV files
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
# '''

import json
import csv
import os
import threading
import time
import random
from datetime import datetime, timedelta
from dateutil.tz import tzlocal, tzutc

from utils import getLogger, readConf
from market import Market, OHLC, feed_enQ, get_market_by_product, Order
from exchanges import Exchange

log = getLogger('PaperTrader')
log.setLevel(log.DEBUG)

# PaperTrader CONFIG FILE
PAPERTRADER_CONF = 'config/papertrader.yml'

class PaperTrader(Exchange):
    name = "papertrader"
    papertrader_conf = {}
    papertrader_products = []
    papertrader_accounts = {}
    primary = False
    csv_data = {}
    feed_thread = None
    stop_feed = False
    
    def __init__(self, config, primary=False):
        log.info("Init PaperTrader exchange")
        
        exch_cfg_file = config['config']
        
        conf = readConf(exch_cfg_file)
        if (conf != None and len(conf)):
            self.papertrader_conf = conf['exchange']
        else:
            log.critical("Unable to read papertrader config")
            return None
        
        self.primary = True if primary else False
        
        # get config
        if config.get('candle_interval'):
            self.candle_interval = int(config['candle_interval'])
        else:
            self.candle_interval = 300  # default 5 minutes
        
        # get raw_data directory
        self.raw_data_dir = self.papertrader_conf.get('raw_data_dir', 'raw_data')
        
        # Setup products from config
        products_config = self.papertrader_conf.get('products', [])
        for prod_cfg in products_config:
            for symbol, details in prod_cfg.items():
                product = {
                    'id': details['id'],
                    'symbol': symbol,
                    'display_name': symbol,
                    'asset_type': details.get('asset_type', 'BTC'),
                    'fund_type': details.get('fund_type', 'USD'),
                    'csv_file': details.get('csv_file')
                }
                self.papertrader_products.append(product)
                
                # Generate random data instead of loading CSV
                # This is much faster and easier for testing!
                num_candles = self.papertrader_conf.get('random_candles', 5000)
                self.csv_data[product['id']] = self._generate_random_ohlc_data(
                    product_name=symbol,
                    num_candles=num_candles
                )
                log.info(f"Generated {len(self.csv_data[product['id']])} random candles for {symbol}")
                
                # Optional: Still support CSV if file exists and random_data is disabled
                # csv_file_path = os.path.join(self.raw_data_dir, product['csv_file'])
                # if os.path.exists(csv_file_path):
                #     self.csv_data[product['id']] = self._load_csv_data(csv_file_path)
                #     log.info(f"Loaded {len(self.csv_data[product['id']])} rows from {csv_file_path}")
                # else:
                #     log.error(f"CSV file not found: {csv_file_path}")
        
        # Setup accounts with initial balances
        for prod in self.papertrader_products:
            # Fund account (USD, USDT, etc.)
            if prod['fund_type'] not in self.papertrader_accounts:
                self.papertrader_accounts[prod['fund_type']] = {
                    'asset': prod['fund_type'],
                    'free': str(self.papertrader_conf.get('initial_fund', 10000.0)),
                    'locked': '0.0'
                }
            
            # Asset account (BTC, ETH, etc.)
            if prod['asset_type'] not in self.papertrader_accounts:
                self.papertrader_accounts[prod['asset_type']] = {
                    'asset': prod['asset_type'],
                    'free': str(self.papertrader_conf.get('initial_asset', 0.0)),
                    'locked': '0.0'
                }
        
        log.info("**PaperTrader init success**\n Products: %s\n Accounts: %s" % (
            self.papertrader_products, self.papertrader_accounts))
    
    def _generate_random_ohlc_data(self, product_name, num_candles=5000, start_price=None):
        """
        Generate random OHLC data for testing
        
        Args:
            product_name: Name of the product (for price range)
            num_candles: Number of candles to generate
            start_price: Starting price (auto-determined if None)
        """
        # Determine starting price based on product
        if start_price is None:
            if 'BANK' in product_name.upper():
                start_price = 44500.0  # Bank Nifty
            elif 'NIFTY' in product_name.upper():
                start_price = 19500.0  # Nifty 50
            elif 'RELIANCE' in product_name.upper():
                start_price = 2500.0   # Reliance
            elif 'TCS' in product_name.upper():
                start_price = 3500.0   # TCS
            elif 'INFY' in product_name.upper():
                start_price = 1500.0   # Infosys
            else:
                start_price = 1000.0   # Default
        
        data = []
        current_price = start_price
        # Start from current time minus num_candles minutes
        start_time = int(time.time()) - (num_candles * 60)
        
        log.info(f"Generating {num_candles} random candles for {product_name} starting at {start_price}")
        
        for i in range(num_candles):
            timestamp = start_time + (i * 60)  # 1 minute intervals
            
            # Generate realistic price movement
            volatility = random.uniform(0.001, 0.015)  # 0.1% to 1.5%
            direction = random.choice([-1, 1])
            
            open_price = current_price
            price_change = current_price * volatility * direction
            close_price = current_price + price_change
            
            # Generate high and low
            high_offset = random.uniform(0.0005, volatility * 1.5)
            low_offset = random.uniform(0.0005, volatility * 1.2)
            
            high_price = max(open_price, close_price) * (1 + high_offset)
            low_price = min(open_price, close_price) * (1 - low_offset)
            
            # Generate volume
            volume = random.uniform(1000, 5000)
            
            # Create row in CSV format
            row = {
                'timestamp': str(timestamp),
                'open': f"{open_price:.2f}",
                'high': f"{high_price:.2f}",
                'low': f"{low_price:.2f}",
                'close': f"{close_price:.2f}",
                'volume': f"{volume:.2f}"
            }
            data.append(row)
            
            current_price = close_price
        
        log.info(f"Generated {len(data)} candles for {product_name}, price range: {start_price:.2f} to {current_price:.2f}")
        return data
    
    def _load_csv_data(self, csv_file_path):
        """
        Load CSV data. Expected format:
        timestamp,open,high,low,close,volume
        or
        timestamp,price,volume
        """
        data = []
        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            log.error(f"Error loading CSV file {csv_file_path}: {e}")
        return data
    
    def __str__(self):
        return "{Message: PaperTrader Exchange}"
    
    ######## Feed Generation #######
    def _feed_generator_thread(self):
        """
        Thread that generates feed messages from CSV data
        """
        log.info("Starting feed generator thread")
        
        # Track current index for each product
        data_indices = {prod['id']: 0 for prod in self.papertrader_products}
        
        while not self.stop_feed:
            for product in self.papertrader_products:
                product_id = product['id']
                
                if product_id not in self.csv_data:
                    continue
                
                csv_data = self.csv_data[product_id]
                idx = data_indices[product_id]
                
                if idx >= len(csv_data):
                    log.info(f"Reached end of data for {product_id}")
                    continue
                
                row = csv_data[idx]
                
                # Generate trade message
                try:
                    # Skip empty rows or header rows
                    if not row.get('timestamp') or row['timestamp'].lower() == 'timestamp':
                        data_indices[product_id] += 1
                        continue
                    
                    # Check if it's OHLC format or simple price format
                    if 'open' in row and 'high' in row:
                        # OHLC format - generate candle
                        msg = {
                            'e': 'kline',
                            's': product['symbol'],
                            'k': {
                                't': int(float(row['timestamp'])),
                                'T': int(float(row['timestamp'])),
                                'o': row['open'],
                                'h': row['high'],
                                'l': row['low'],
                                'c': row['close'],
                                'v': row['volume'],
                                'x': True  # candle closed
                            }
                        }
                    else:
                        # Simple price format - generate trade
                        msg = {
                            'e': 'trade',
                            's': product['symbol'],
                            'p': row.get('price', row.get('close')),
                            'q': row.get('volume', '1.0'),
                            'T': int(float(row['timestamp']))
                        }
                    
                    market = get_market_by_product(self.name, product_id)
                    if market:
                        feed_enQ(market, msg)
                    
                    data_indices[product_id] += 1
                    
                except Exception as e:
                    log.error(f"Error processing row {idx} for {product_id}: {e}")
                    data_indices[product_id] += 1
            
            # Sleep based on candle interval or a fraction of it
            time.sleep(self.candle_interval / 10)  # Process data faster than real-time
        
        log.info("Feed generator thread stopped")
    
    def _papertrader_consume_feed(self, market, msg):
        """
        Feed callback for PaperTrader
        """
        msg_type = msg.get('e')
        if msg_type == 'trade':
            self._papertrader_consume_trade_feed(market, msg)
        elif msg_type == 'kline':
            self._papertrader_consume_candle_feed(market, msg)
        elif msg_type == 'executionReport':
            log.debug("Feed: executionReport msg: %s" % (msg))
            self._papertrader_consume_order_update_feed(market, msg)
    
    def _papertrader_consume_trade_feed(self, market, msg):
        """Process trade feed"""
        price = float(msg.get('p'))
        last_size = float(msg.get('q'))
        log.debug("Trade feed: price: %f size: %f" % (price, last_size))
        market.tick(price, last_size)
    
    def _papertrader_consume_candle_feed(self, market, msg):
        """Process candle feed"""
        k = msg.get('k')
        t = int(k.get('T'))
        o = float(k.get('o'))
        h = float(k.get('h'))
        l = float(k.get('l'))
        c = float(k.get('c'))
        v = float(k.get('v'))
        
        candle = OHLC(int(t), o, h, l, c, v)
        log.debug("New candle identified %s" % (candle))
        market.O = market.V = market.H = market.L = 0
        market.add_new_candle(candle)
        market.set_market_rate(c)
    
    def _papertrader_consume_order_update_feed(self, market, msg):
        """Process order status update feed"""
        order = self._normalized_order(msg)
        if order == None:
            log.error("order update ignored")
            return None
        log.debug("Order Status Update id:%s side: %s status: %s" % (order.id, order.side, order.status))
        market.order_status_update(order)
    
    #### Feed consume done #####
    def market_init(self, market):
        """Initialize market with account balances"""
        usd_acc = self.papertrader_accounts.get(market.get_fund_type())
        crypto_acc = self.papertrader_accounts.get(market.get_asset_type())
        
        if (usd_acc == None or crypto_acc == None):
            log.error("No account available for product: %s" % (market.product_id))
            return None
        
        # Setup the initial params
        market.fund.set_initial_value(float(usd_acc['free']))
        market.fund.set_hold_value(float(usd_acc['locked']))
        market.asset.set_initial_size(float(crypto_acc['free']))
        market.asset.set_hold_size(float(crypto_acc['locked']))
        
        ## Feed Cb
        market.register_feed_processor(self._papertrader_consume_feed)
        
        ## Init Exchange specific private state variables
        market.set_candle_interval(self.candle_interval)
        
        # Start feed generator thread if not already started
        if self.feed_thread is None:
            self.stop_feed = False
            self.feed_thread = threading.Thread(target=self._feed_generator_thread, daemon=True)
            self.feed_thread.start()
        
        log.info("Market init complete: %s" % (market.product_id))
        return market
    
    def close(self):
        """Close exchange and stop feed thread"""
        log.debug("Closing exchange...")
        self.stop_feed = True
        if self.feed_thread:
            self.feed_thread.join(timeout=2)
        log.debug("Closed PaperTrader exchange")
    
    def get_products(self):
        log.debug("products num %d" % (len(self.papertrader_products)))
        return self.papertrader_products
    
    def get_accounts(self):
        log.debug("get accounts")
        return self.papertrader_accounts
    
    def get_historic_rates(self, product_id, start=None, end=None):
        """
        Get historic rates from CSV data
        """
        log.debug("Getting historic rates for %s" % product_id)
        
        if product_id not in self.csv_data:
            log.error("No CSV data for product: %s" % product_id)
            return None
        
        csv_data = self.csv_data[product_id]
        candles_list = []
        
        log.info(f"Processing {len(csv_data)} rows for {product_id}")
        skipped = 0
        errors = 0
        
        for i, row in enumerate(csv_data):
            try:
                # Skip empty rows or header rows
                if not row.get('timestamp') or row['timestamp'].lower() == 'timestamp':
                    skipped += 1
                    continue
                    
                timestamp = int(float(row['timestamp']))
                
                # Check if it's OHLC format
                if 'open' in row and 'high' in row:
                    candle = OHLC(
                        time=timestamp,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=float(row['volume'])
                    )
                else:
                    # Simple price format - create OHLC with same price
                    price = float(row.get('price', row.get('close')))
                    volume = float(row.get('volume', 0))
                    candle = OHLC(
                        time=timestamp,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=volume
                    )
                
                candles_list.append(candle)
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only log first 5 errors
                    log.error(f"Error processing row {i} for {product_id}: {e}")
                continue
        
        log.info(f"Retrieved {len(candles_list)} candles for {product_id} (skipped: {skipped}, errors: {errors})")
        return candles_list
    
    def _normalized_order(self, order):
        """
        Normalize order format for paper trading
        """
        log.debug("Order msg: %s" % (order))
        
        # For paper trading, we simulate instant fills
        order_id = order.get('id', str(time.time()))
        product_id = order.get('product')
        side = order.get('side', 'buy').lower()
        status_type = order.get('status', 'filled')
        order_type = order.get('type', 'market')
        
        request_size = float(order.get('size', 0))
        filled_size = float(order.get('filled_size', request_size))
        remaining_size = float(order.get('remaining_size', 0))
        price = float(order.get('price', 0))
        funds = float(order.get('funds', 0))
        fees = float(order.get('fees', 0))
        
        create_time = datetime.now().isoformat()
        update_time = datetime.now().isoformat()
        
        norm_order = Order(
            order_id, product_id, status_type, order_type=order_type,
            side=side, request_size=request_size, filled_size=filled_size,
            remaining_size=remaining_size, price=price, funds=funds, fees=fees,
            create_time=create_time, update_time=update_time
        )
        return norm_order
    
    def get_product_order_book(self, product, level=1):
        log.debug("get_product_order_book: Paper trading - returning None")
        return None
    
    def buy(self, trade_req):
        """
        Simulate buy order
        """
        log.debug("BUY - Simulating Order --")
        
        # Get current market price
        market = get_market_by_product(self.name, trade_req.product)
        if market:
            price = market.get_market_rate()
        else:
            price = trade_req.price if trade_req.price > 0 else 100.0
        
        # Simulate order
        order = {
            'id': f"paper_buy_{int(time.time() * 1000)}",
            'product': trade_req.product,
            'side': 'buy',
            'status': 'filled',
            'type': trade_req.type,
            'size': trade_req.size,
            'filled_size': trade_req.size,
            'remaining_size': 0,
            'price': price,
            'funds': trade_req.size * price,
            'fees': trade_req.size * price * 0.001  # 0.1% fee
        }
        
        return self._normalized_order(order)
    
    def sell(self, trade_req):
        """
        Simulate sell order
        """
        log.debug("SELL - Simulating Order --")
        
        # Get current market price
        market = get_market_by_product(self.name, trade_req.product)
        if market:
            price = market.get_market_rate()
        else:
            price = trade_req.price if trade_req.price > 0 else 100.0
        
        # Simulate order
        order = {
            'id': f"paper_sell_{int(time.time() * 1000)}",
            'product': trade_req.product,
            'side': 'sell',
            'status': 'filled',
            'type': trade_req.type,
            'size': trade_req.size,
            'filled_size': trade_req.size,
            'remaining_size': 0,
            'price': price,
            'funds': trade_req.size * price,
            'fees': trade_req.size * price * 0.001  # 0.1% fee
        }
        
        return self._normalized_order(order)
    
    def get_order(self, prod_id, order_id):
        log.debug("GET - order (%s)" % (order_id))
        # For paper trading, return a filled order
        order = {
            'id': order_id,
            'product': prod_id,
            'status': 'filled'
        }
        return self._normalized_order(order)
    
    def cancel_order(self, prod_id, order_id):
        log.debug("CANCEL - order (%s)" % (order_id))
        return None


######### ******** MAIN ****** #########
if __name__ == '__main__':
    print("Testing PaperTrader exchange:")
    
    config = {
        "config": "config/papertrader.yml",
        'candle_interval': 300,  # 5 minutes
    }
    
    pt = PaperTrader(config)
    print("PaperTrader initialized successfully")
    
    time.sleep(5)
    pt.close()
    print("Done")
# EOF
