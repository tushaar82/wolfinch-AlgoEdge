#! /usr/bin/env python
# '''
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
import pprint
from decimal import Decimal
from datetime import datetime, timedelta
from time import sleep
import time
from dateutil.tz import tzlocal, tzutc
from twisted.internet import reactor

from binance.client import Client
import binance.helpers
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceRequestException

from utils import getLogger, readConf
from market import Market, OHLC, feed_enQ, get_market_by_product, Order
from exchanges import Exchange

log = getLogger ('Binance')
log.setLevel(log.INFO)

#BINANCE CONFIG FILE
BINANCE_CONF = 'config/binance.yml'
BNC_INTERVAL_MAPPING = {300 :'5m', 600: '10m'}

class Binance (Exchange):
    name = "binanceClient"
    binance_conf = {}
    binance_products = []
    binance_accounts = {}
    public_client = None
    auth_client   = None
    ws_client = None
    symbol_to_id = {}
    primary = False
    def __init__ (self, config, primary=False):
        log.info ("Init Binance exchange")
        
        exch_cfg_file = config.get('config')
        if exch_cfg_file == None:
            exch_cfg_file = BINANCE_CONF
        conf = readConf (exch_cfg_file)
        if (conf != None and len(conf)):
            self.binance_conf = conf['exchange']
        else:
            return None
        
        self.primary = True if primary else False
        # get config
        if config.get('candle_interval'):
            # map interval in to binance format
            interval = BNC_INTERVAL_MAPPING[int(config['candle_interval']) ]
            self.binance_conf['backfill_interval'] =  interval
            self.candle_interval = int(config['candle_interval'])        
                
        # get config
        backfill = config.get('backfill')
        if not backfill:
            log.fatal("Invalid backfill config")            
            return None
    
        if backfill.get('enabled'):
            self.binance_conf['backfill_enabled'] = backfill['enabled']
        if backfill.get('period'):
            self.binance_conf['backfill_period'] = int(backfill['period'])

        # for public client, no need of api key
        self.public_client = Client("", "")
        if (self.public_client) == None :
            log.critical("binance public client init failed")
            return None
        
        key = self.binance_conf.get('apiKey')
        b64secret = self.binance_conf.get('apiSecret')
        self.test_mode = self.binance_conf.get('test_mode') or False
                
        if ((key and b64secret ) == False):
            log.critical ("Invalid API Credentials in binance Config!! ")
            return None
        
        self.auth_client = Client(key, b64secret)
        
        if self.auth_client == None:
            log.critical("Unable to Authenticate with binance exchange. Abort!!")
            return None
            
#         global binance_products
        exch_info = self.public_client.get_exchange_info()
        serverTime = int(exch_info['serverTime'])
        localTime = int(time.time()*1000)
        self.timeOffset = (serverTime - localTime)//1000
        #if time diff is less the 5s, ignore. 
        if abs(self.timeOffset) < 5: 
            self.timeOffset = 0
        
        log.info ("servertime: %d localtime: %d offset: %d"%(serverTime, localTime, self.timeOffset))
        
        products = exch_info.get("symbols")
        log.info ("products: %s" % (pprint.pformat(products, 4)))
                
        if (len(products) and len (self.binance_conf['products'])):
            for prod in products:
                for p in self.binance_conf['products']:
                    for k, v in p.items():
#                         log.debug ("pk: %s s: %s"%(k, prod['symbol']))
                        if prod['symbol'] == k:
                            log.debug ("product found: %s v: %s" % (prod, v))
                            prod['id'] = v['id']
                            prod['display_name'] = k
                            self.symbol_to_id[k] = prod['id']
                            prod ['asset_type'] = prod['baseAsset']
                            prod ['fund_type'] = prod['quoteAsset']
                                                  
                            self.binance_products.append(prod)
                                    
        # EXH supported in spectator mode. 
#         # Popoulate the account details for each interested currencies
#         accounts =  self.auth_client.get_account()
#         if (accounts == None):
#             log.critical("Unable to get account details!!")
#             return False
#         #log.debug ("Exchange Accounts: %s"%(pprint.pformat(accounts, 4)))
#         for account in accounts:
#             for prod in self.binance_conf['products']:
#                 for prod_id in prod.keys():
#                     currency = prod[prod_id][0]['currency']            
#                     if account['currency'] in currency:
#                         log.debug ("Interested Account Found for Currency: "+account['currency'])
#                         self.binance_accounts[account['currency']] = account
#                         break  
        
        self.ws_client = bm = BinanceSocketManager(self.public_client)
        for prod in self.get_products():
            # Start Kline socket
            backfill_interval = self.binance_conf.get('backfill_interval')
            bm.start_kline_socket(prod['symbol'], self._feed_enQ_msg, interval=backfill_interval)
        bm.start()
                
        log.info( "**Binance init success**\n Products: %s\n Accounts: %s"%(
                        pprint.pformat(self.binance_products, 4), pprint.pformat(self.binance_accounts, 4)))
        
    def __str__ (self):
        return "{Message: Binance Exchange }"
    ######## Feed Consume #######
    def _feed_enQ_msg (self, msg):
            log.debug("message :%s "%msg)      
            msg_type = msg.get('e') 
            symbol = msg.get("s")
            product_id = self.symbol_to_id[symbol]
            if (msg_type == 'kline'):
                log.debug ("kline")
                market = get_market_by_product (self.name, product_id)
                if (market == None):
                    log.error ("Feed Thread: Unknown market product: %s: msg %s"%(product_id, json.dumps(msg, indent=4, sort_keys=True)))
                    return
                k = msg.get('k')
                if k.get('x') == True:
                    #This kline closed, this is a candle
                    feed_enQ(market, msg)
                else:
                    # not interested
                    pass                            
            else:
                log.error ("Unknown feed. message type: %s prod: %s"%(msg_type, product_id))
            return
                
    def _binance_consume_feed (self, market, msg):
        ''' 
        Feed Call back for Binance    
        This is where we do all the useful stuff with Feed
        '''
        log.info ("msg: %s"%msg)
#         msg_type = msg.get('e')
        k = msg.get('k')
        t = int(k.get('T')+1)//1000 + self.timeOffset
        o = Decimal(k.get('o'))
        h = Decimal(k.get('h'))
        l = Decimal(k.get('l'))
        c = Decimal(k.get('c'))
        v = Decimal(k.get('v'))
        
#         if now >= market.cur_candle_time + interval:
            # close the current candle period and start a new candle period
        candle = OHLC(int(t), o, h, l, c, v)
        log.debug ("New candle identified %s"%(candle))        
        market.O = market.V = market.H = market.L = 0
        market.add_new_candle (candle)
        
        #TODO: FIXME: jork: might need to rate-limit the logic here after
        market.set_market_rate (c)
#         market.update_market_states()        
            
    #### Feed consume done #####    
    
    #TODO: FIXME: Spectator mode, make full operational    
    def market_init (self, market):
#         usd_acc = self.binance_accounts['USD']
#         crypto_acc = self.binance_accounts.get(product['base_currency'])
#         if (usd_acc == None or crypto_acc == None): 
#             log.error ("No account available for product: %s"%(product['id']))
#             return None
        #Setup the initial params
#         log.debug ("product: %s"%product)
#         market = Market(product=product, exchange=self)    
        market.fund.set_initial_value(Decimal(0))#usd_acc['available']))
        market.fund.set_hold_value(Decimal(0))#usd_acc['hold']))
#         market.fund.set_fund_liquidity_percent(10)       #### Limit the fund to 10%
#         market.fund.set_max_per_buy_fund_value(100)
        market.asset.set_initial_size(Decimal(0)) #crypto_acc['available']))
        market.asset.set_hold_size(0) #Decimal(crypto_acc['hold']))
    
        ## Feed Cb
        market.register_feed_processor(self._binance_consume_feed)
        
        ## Init Exchange specific private state variables
        market.O = market.H = market.L = market.C = market.V = 0
        market.set_candle_interval (self.candle_interval)
        log.info ("Market init complete: %s" % (market.product_id))
        
        #set whether primary or secondary
        market.primary = self.primary
        
        return market
    def close (self):
        log.debug("Closing exchange...")    
#         global self.ws_client
        if (self.ws_client):
            log.debug("Closing WebSocket Client")
            self.ws_client.close ()
            self.ws_client.join(1)
            if not reactor._stopped:
                reactor.stop()
            log.debug("Closed websockets")
    def get_products (self):
        log.debug ("products num %s"%((self.binance_products)))
        return self.binance_products    
    def get_accounts (self):
    #     log.debug (pprint.pformat(self.binance_accounts))
        log.debug ("get accounts")
        return self.binance_accounts    
    def get_historic_rates (self, product_id, start=None, end=None):
        '''
            Args:
        product_id (str): Product
        start (Optional[str]): Start time in ISO 8601
        end (Optional[str]): End time in ISO 8601
        interval (Optional[str]): Desired time slice in 
         seconds
         '''
        #Max Candles in one call
        epoch = datetime.utcfromtimestamp(0).replace(tzinfo=tzutc())
        max_candles = 200
        candles_list = []
        
        #get config
        enabled = self.binance_conf.get('backfill_enabled')
        period = int(self.binance_conf.get('backfill_period'))
        interval_str = self.binance_conf.get('backfill_interval')
        
        interval = binance.helpers.interval_to_milliseconds(interval_str)
        if (interval == None):
            log.error ("Invalid Interval - %s"%interval_str)
        
        product = None
        for p in self.get_products():
            if p['id'] == product_id:
                product = p
        
        if product is None:
            log.error ("Invalid Product Id: %s"%product_id)
            return None
        
        if not enabled:
            log.debug ("Historical data retrieval not enabled")
            return None
    
        if not end:
            # if no end, use current time
            end = datetime.now()
            end = end.replace(tzinfo=tzlocal())
             
        if not start:
            # if no start given, use the config
            real_start = start = end - timedelta(days = period) - timedelta(seconds = interval//1000)
        else:
            real_start = start
            
        real_start = start = start.replace(tzinfo=tzlocal())
        
        log.debug ("Retrieving Historic candles for period: %s to %s"%(
                    real_start.isoformat(), end.isoformat()))
        
        td = max_candles*interval//1000
        tmp_end = start + timedelta(seconds = td)
        tmp_end = min(tmp_end, end)
        
        #adjust time with server time
        start = start + timedelta(seconds = self.timeOffset)
        tmp_end = tmp_end + timedelta(seconds = self.timeOffset)
        
        count = 0
        while (start < end):
            ## looks like there is a rate=limiting in force, we will have to slow down
            count += 1
            if (count > 3):
                #rate-limiting
                count = 0
                sleep (2)
            
            start_ts = int((start - epoch).total_seconds() * 1000.0)
            end_ts = int((tmp_end - epoch).total_seconds() * 1000.0)
            
            log.debug ("Start: %s end: %s"%(start_ts, end_ts))
            candles = self.public_client.get_klines (
                symbol=product['symbol'],
                interval=Client.KLINE_INTERVAL_5MINUTE,
                limit=max_candles,
                startTime=start_ts,
                endTime=end_ts
            )
            if candles:
                if isinstance(candles, dict):
                    ## Error Case
                    err_msg = candles.get('message')
                    if (err_msg):
                        log.error ("Error while retrieving Historic rates: msg: %s\n will retry.."%(err_msg))
                else:
                    #candles are of struct [[time, o, h, l,c, V]]
                    candles_list += [OHLC(time=int(candle[6] + 1)//1000, 
                                            low=candle[3], high=candle[2], open=candle[1], 
                                            close=candle[4], volume=candle[5]) for candle in candles]
    #                 log.debug ("%s"%(candles))
                    log.debug ("Historic candles for period: %s to %s num_candles: %d "%(
                        start.isoformat(), tmp_end.isoformat(), (0 if not candles else len(candles))))
                    
                    # new period, start from the (last +1)th position
                    start = tmp_end #+ timedelta(seconds = (interval//1000))
                    tmp_end = start + timedelta(seconds = td)
                    tmp_end = min(tmp_end, end)

#                     log.debug ("c: %s"%(candles))
            else:
                log.error ("Error While Retrieving Historic candles for period: %s to %s num: %d"%(
                    start.isoformat(), tmp_end.isoformat(), (0 if not candles else len(candles))))
                return None
        
        log.debug ("Retrieved Historic candles for period: %s to %s num: %d"%(
                    real_start.isoformat(), end.isoformat(), (0 if not candles_list else len(candles_list))))
    #     log.debug ("%s"%(candles_list))
        return candles_list
        
    def get_product_order_book (self, product, level = 1):
        """Get order book depth for a product"""
        try:
            product_info = None
            for p in self.get_products():
                if p['id'] == product:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product}")
                return None
            
            depth = self.public_client.get_order_book(symbol=product_info['symbol'], limit=level)
            return depth
        except Exception as e:
            log.error(f"Error getting order book: {e}")
            return None
    
    def buy(self, trade_req):
        """Place a buy order"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return None
            
            product = trade_req.product
            product_info = None
            for p in self.get_products():
                if p['id'] == product.get_name():
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product.get_name()}")
                return None
            
            symbol = product_info['symbol']
            quantity = float(trade_req.size)
            price = float(trade_req.price) if trade_req.price else None
            
            # Determine order type
            order_type = trade_req.type.upper() if hasattr(trade_req, 'type') else 'MARKET'
            
            log.info(f"Placing BUY order: {symbol}, quantity: {quantity}, price: {price}, type: {order_type}")
            
            # Place order based on type
            if order_type == 'MARKET':
                response = self.auth_client.order_market_buy(
                    symbol=symbol,
                    quantity=quantity
                )
            elif order_type == 'LIMIT':
                if not price:
                    log.error("Price required for LIMIT order")
                    return None
                response = self.auth_client.order_limit_buy(
                    symbol=symbol,
                    quantity=quantity,
                    price=str(price)
                )
            else:
                log.error(f"Unsupported order type: {order_type}")
                return None
            
            if response:
                order_id = response.get('orderId')
                status = response.get('status', 'NEW')
                executed_qty = float(response.get('executedQty', 0))
                
                log.info(f"Buy order placed successfully: {order_id}")
                
                # Log to trade logger
                try:
                    from db import get_trade_logger
                    trade_logger = get_trade_logger()
                    if trade_logger:
                        order_obj = Order(
                            order_id=str(order_id),
                            product_id=product.get_name(),
                            status=status.lower(),
                            order_type=order_type.lower(),
                            side='buy',
                            request_size=quantity,
                            filled_size=executed_qty,
                            price=price or 0
                        )
                        trade_logger.log_order_placed(self.name, product.get_name(), order_obj)
                except Exception as e:
                    log.warning(f"Failed to log order: {e}")
                
                return Order(
                    order_id=str(order_id),
                    product_id=product.get_name(),
                    status=status.lower(),
                    order_type=order_type.lower(),
                    side='buy',
                    request_size=quantity,
                    filled_size=executed_qty,
                    remaining_size=quantity - executed_qty,
                    price=price or float(response.get('price', 0)),
                    create_time=response.get('transactTime')
                )
            
            return None
            
        except BinanceAPIException as e:
            log.error(f"Binance API error placing buy order: {e}")
            return None
        except BinanceRequestException as e:
            log.error(f"Binance request error placing buy order: {e}")
            return None
        except Exception as e:
            log.error(f"Error placing buy order: {e}")
            return None
    
    def sell(self, trade_req):
        """Place a sell order"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return None
            
            product = trade_req.product
            product_info = None
            for p in self.get_products():
                if p['id'] == product.get_name():
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product.get_name()}")
                return None
            
            symbol = product_info['symbol']
            quantity = float(trade_req.size)
            price = float(trade_req.price) if trade_req.price else None
            
            # Determine order type
            order_type = trade_req.type.upper() if hasattr(trade_req, 'type') else 'MARKET'
            
            log.info(f"Placing SELL order: {symbol}, quantity: {quantity}, price: {price}, type: {order_type}")
            
            # Place order based on type
            if order_type == 'MARKET':
                response = self.auth_client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity
                )
            elif order_type == 'LIMIT':
                if not price:
                    log.error("Price required for LIMIT order")
                    return None
                response = self.auth_client.order_limit_sell(
                    symbol=symbol,
                    quantity=quantity,
                    price=str(price)
                )
            else:
                log.error(f"Unsupported order type: {order_type}")
                return None
            
            if response:
                order_id = response.get('orderId')
                status = response.get('status', 'NEW')
                executed_qty = float(response.get('executedQty', 0))
                
                log.info(f"Sell order placed successfully: {order_id}")
                
                # Log to trade logger
                try:
                    from db import get_trade_logger
                    trade_logger = get_trade_logger()
                    if trade_logger:
                        order_obj = Order(
                            order_id=str(order_id),
                            product_id=product.get_name(),
                            status=status.lower(),
                            order_type=order_type.lower(),
                            side='sell',
                            request_size=quantity,
                            filled_size=executed_qty,
                            price=price or 0
                        )
                        trade_logger.log_order_placed(self.name, product.get_name(), order_obj)
                except Exception as e:
                    log.warning(f"Failed to log order: {e}")
                
                return Order(
                    order_id=str(order_id),
                    product_id=product.get_name(),
                    status=status.lower(),
                    order_type=order_type.lower(),
                    side='sell',
                    request_size=quantity,
                    filled_size=executed_qty,
                    remaining_size=quantity - executed_qty,
                    price=price or float(response.get('price', 0)),
                    create_time=response.get('transactTime')
                )
            
            return None
            
        except BinanceAPIException as e:
            log.error(f"Binance API error placing sell order: {e}")
            return None
        except BinanceRequestException as e:
            log.error(f"Binance request error placing sell order: {e}")
            return None
        except Exception as e:
            log.error(f"Error placing sell order: {e}")
            return None
    
    def get_order(self, product_id, order_id):
        """Get order status"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return None
            
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return None
            
            response = self.auth_client.get_order(
                symbol=product_info['symbol'],
                orderId=order_id
            )
            
            if response:
                return Order(
                    order_id=str(response.get('orderId')),
                    product_id=product_id,
                    status=response.get('status', 'UNKNOWN').lower(),
                    order_type=response.get('type', 'MARKET').lower(),
                    side=response.get('side', 'UNKNOWN').lower(),
                    request_size=float(response.get('origQty', 0)),
                    filled_size=float(response.get('executedQty', 0)),
                    remaining_size=float(response.get('origQty', 0)) - float(response.get('executedQty', 0)),
                    price=float(response.get('price', 0)),
                    create_time=response.get('time'),
                    update_time=response.get('updateTime')
                )
            
            return None
            
        except BinanceAPIException as e:
            log.error(f"Binance API error getting order: {e}")
            return None
        except Exception as e:
            log.error(f"Error getting order: {e}")
            return None
    
    def cancel_order(self, product_id, order_id):
        """Cancel an order"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return False
            
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return False
            
            log.info(f"Canceling order: {order_id} for {product_id}")
            
            response = self.auth_client.cancel_order(
                symbol=product_info['symbol'],
                orderId=order_id
            )
            
            if response and response.get('status') == 'CANCELED':
                log.info(f"Order canceled successfully: {order_id}")
                return True
            
            return False
            
        except BinanceAPIException as e:
            log.error(f"Binance API error canceling order: {e}")
            return False
        except Exception as e:
            log.error(f"Error canceling order: {e}")
            return False
    
    def cancel_all_orders(self, product_id):
        """Cancel all open orders for a product"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return False
            
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return False
            
            log.info(f"Canceling all orders for: {product_id}")
            
            response = self.auth_client.cancel_open_orders(
                symbol=product_info['symbol']
            )
            
            log.info(f"Canceled {len(response) if response else 0} orders")
            return True
            
        except BinanceAPIException as e:
            log.error(f"Binance API error canceling all orders: {e}")
            return False
        except Exception as e:
            log.error(f"Error canceling all orders: {e}")
            return False
    
    def get_account_info(self):
        """Get account information"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return None
            
            account = self.auth_client.get_account()
            return account
            
        except BinanceAPIException as e:
            log.error(f"Binance API error getting account info: {e}")
            return None
        except Exception as e:
            log.error(f"Error getting account info: {e}")
            return None
    
    def get_balance(self, asset):
        """Get balance for specific asset"""
        try:
            account = self.get_account_info()
            if account and 'balances' in account:
                for balance in account['balances']:
                    if balance['asset'] == asset:
                        return {
                            'asset': asset,
                            'free': float(balance['free']),
                            'locked': float(balance['locked']),
                            'total': float(balance['free']) + float(balance['locked'])
                        }
            return None
            
        except Exception as e:
            log.error(f"Error getting balance: {e}")
            return None
    
    def get_open_orders(self, product_id=None):
        """Get all open orders"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return []
            
            if product_id:
                product_info = None
                for p in self.get_products():
                    if p['id'] == product_id:
                        product_info = p
                        break
                
                if not product_info:
                    log.error(f"Product not found: {product_id}")
                    return []
                
                orders = self.auth_client.get_open_orders(symbol=product_info['symbol'])
            else:
                orders = self.auth_client.get_open_orders()
            
            return orders
            
        except BinanceAPIException as e:
            log.error(f"Binance API error getting open orders: {e}")
            return []
        except Exception as e:
            log.error(f"Error getting open orders: {e}")
            return []
    
    def get_order_history(self, product_id, limit=500):
        """Get order history"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return []
            
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return []
            
            orders = self.auth_client.get_all_orders(
                symbol=product_info['symbol'],
                limit=limit
            )
            
            return orders
            
        except BinanceAPIException as e:
            log.error(f"Binance API error getting order history: {e}")
            return []
        except Exception as e:
            log.error(f"Error getting order history: {e}")
            return []
    
    def get_trade_history(self, product_id, limit=500):
        """Get trade history"""
        try:
            if not self.auth_client:
                log.error("Authenticated client not available")
                return []
            
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return []
            
            trades = self.auth_client.get_my_trades(
                symbol=product_info['symbol'],
                limit=limit
            )
            
            return trades
            
        except BinanceAPIException as e:
            log.error(f"Binance API error getting trade history: {e}")
            return []
        except Exception as e:
            log.error(f"Error getting trade history: {e}")
            return []
    
    def get_ticker(self, product_id):
        """Get 24h ticker statistics"""
        try:
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return None
            
            ticker = self.public_client.get_ticker(symbol=product_info['symbol'])
            return ticker
            
        except Exception as e:
            log.error(f"Error getting ticker: {e}")
            return None
    
    def get_order_book_depth(self, product_id, limit=100):
        """Get order book with depth"""
        try:
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return None
            
            depth = self.public_client.get_order_book(
                symbol=product_info['symbol'],
                limit=limit
            )
            return depth
            
        except Exception as e:
            log.error(f"Error getting order book depth: {e}")
            return None
    
    def get_recent_trades(self, product_id, limit=500):
        """Get recent trades"""
        try:
            product_info = None
            for p in self.get_products():
                if p['id'] == product_id:
                    product_info = p
                    break
            
            if not product_info:
                log.error(f"Product not found: {product_id}")
                return []
            
            trades = self.public_client.get_recent_trades(
                symbol=product_info['symbol'],
                limit=limit
            )
            return trades
            
        except Exception as e:
            log.error(f"Error getting recent trades: {e}")
            return []

######### ******** MAIN ****** #########
if __name__ == '__main__':
    
    print ("Testing Binance exch:")
    
    bnc = Binance ()
    
#     m = bnc.market_init('BTC-USD')
    
    bnc.get_historic_rates('BTC-USD')
    
    sleep(20)
    bnc.close()
    print ("Done")
#EOF    
