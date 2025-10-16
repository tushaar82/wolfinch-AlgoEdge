#! /usr/bin/env python3
# '''
#  Wolfinch Auto trading Bot
#  Desc: Robinhood exchange interactions for Wolfinch
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
import pprint
from datetime import datetime, timedelta
from time import sleep
import time
from dateutil.tz import tzlocal, tzutc

from utils import getLogger, readConf
from market import  OHLC, feed_enQ, get_market_by_product, Order
from exchanges import Exchange
import logging
import pyrh
# import exchanges.robinhood.yahoofin as yahoofin
from exchanges.robinhood.yahoofin import Yahoofin

log = getLogger ('Robinhood')
log.setLevel(log.DEBUG)
# logging.getLogger("urllib3").setLevel(logging.WARNING)

# ROBINHOOD CONFIG FILE
ROBINHOOD_CONF = 'config/robinhood.yml'
RBH_INTERVAL_MAPPING_TO_STR = {1*60: '1m', 5*60 :'5m', 15*60: '15m'}
API_BASE="https://api.robinhood.com"

class Robinhood (Exchange):
    name = "robinhood"
    robinhood_conf = {}
    robinhood_products = []
    robinhood_accounts = {}
    rbh_client = None
    yahoofin_client = None    

    primary = False
    def __init__(self, config, primary=False, stream=True, auth=True):
        log.info ("Init Robinhood exchange")
        self.instr_to_symbol_map = {}
        self.symbol_to_instr_map = {}
        self.option_id_map = {}
        self.stream = stream
        self.auth = auth
        exch_cfg_file = config['config']
        
        conf = readConf (exch_cfg_file)
        if (conf != None and len(conf)):
            self.robinhood_conf = conf['exchange']
        else:
            return None
        
        self.primary = True if primary else False
        # get config
        if config.get('candle_interval'):
            # map interval in to robinhood format
            self.candle_interval = int(config['candle_interval'])
                
        # get config
        backfill = config.get('backfill')
        if not backfill:
            log.fatal("Invalid backfill config")            
            return None
    
        if backfill.get('enabled'):
            self.robinhood_conf['backfill_enabled'] = backfill['enabled']
        if backfill.get('period'):
            self.robinhood_conf['backfill_period'] = int(backfill['period'])

        self.yahoofin_client = Yahoofin()
        
        #get data from exch conf
        self.user = self.robinhood_conf.get('user')
        self.password = self.robinhood_conf.get('password')
        self.mfa_key = self.robinhood_conf.get('MFAcode')
        
        if ((self.user and self.password) == False):
            log.critical ("Invalid API Credentials in robinhood Config!! ")
            return None
        
        try :
            self.rbh_client = pyrh.Robinhood()
            if auth==False:
                log.info ("init success. auth init skipped")
                return
            if self.rbh_client.login(username=self.user, password=self.password, qr_code=self.mfa_key) == False:
                log.critical("Unable to Authenticate with robinhood exchange. Abort!!")
                raise Exception("login failed")
        except Exception as e:
            log.critical ("exception while logging in e:%s"%(e))        
            raise e
#         global robinhood_products
#         exch_info = self.public_client.get_exchange_info()
#         serverTime = int(exch_info['serverTime'])
#         localTime = int(time.time() * 1000)
#         self.timeOffset = (serverTime - localTime) // 1000

#TODO: FIXME: RH is in EDT. Adjust with local time
# (datetime.datetime.now(pytz.timezone('America/New_York')) - datetime.datetime(1970,1,1).).total_seconds()
        self.timeOffset = 0
        # if time diff is less the 5s, ignore.         
        if abs(self.timeOffset) < 5: 
            self.timeOffset = 0
            
        log.info ("**********TODO: FIXME: fix time offset ********\n")# servertime: %d localtime: %d offset: %d" % (serverTime, localTime, self.timeOffset))
        
        self.robinhood_conf['products'] = []
        for p in config['products']:
#             # add the product ids
            self.robinhood_conf['products'] += p.keys()
                    
        portforlio = self.rbh_client.portfolios()
        log.info ("products: %s" % (pprint.pformat(portforlio, 4)))
                
        for p_id in self.robinhood_conf['products']:
            instr = self.get_instrument_from_symbol(p_id)
            prod = {"id": p_id}
            prod['asset_type'] = p_id
            prod['fund_type'] = "USD"
            prod['display_name'] = instr['simple_name']
            prod["instrument"] = instr
            self.robinhood_products.append(prod)
        
        # EXH supported in spectator mode.                    
        
        portfolio = self.rbh_client.portfolios()
        if (portfolio == None):
            log.critical("Unable to get portfolio details!!")
            return False
        log.debug ("Exchange portfolio: %s" % (pprint.pformat(portfolio, 4)))
        
        # Popoulate the account details for each interested currencies
        accounts = self.rbh_client.get_account()
        if (accounts == None):
            log.critical("Unable to get account details!!")
            return False
        log.debug ("Exchange Accounts: %s" % (pprint.pformat(accounts, 4)))
        self.robinhood_accounts["USD"] = accounts 
                
        positions = self.rbh_client.positions()
        if (positions == None):
            log.critical("Unable to get positions details!!")
            return False
#         log.debug ("Exchange positions: %s" % (pprint.pformat(positions, 4)))

        balances = positions ['results']
        for prod in self.robinhood_products:
            log.debug ("prod_id: %s" % (prod['id']))
            instr = prod['instrument']
            for balance in balances:
                if balance['instrument'] == instr['url']:
                    self.robinhood_accounts[prod['id']] = balance
                    log.debug ("Interested Account Found for asset: %s size: %s"%( prod['id'], balance['quantity']))
                    break
        #for the instuments we never traded before, there may be no account in RBH. so create a dummy here
        for prod in self.robinhood_products:
            if not self.robinhood_accounts.get(prod["id"]):
                log.error ("unable to find prod(%s) account in robinhood. creating one local"%(prod["id"]))
                self.robinhood_accounts[prod["id"]] = {
                    'average_buy_price': '0.0000',
                    'instrument': prod["instrument"],
                    'intraday_average_buy_price': '0.0000',
                    'intraday_quantity': '0.00000000',
                    'pending_average_buy_price': '0.0000',
                    'quantity': '0.00000000',
                    'shares_held_for_buys': '0.00000000',
                    'shares_held_for_options_collateral': '0.00000000',
                    'shares_held_for_options_events': '0.00000000',
                    'shares_held_for_sells': '0.00000000',
                    'shares_held_for_stock_grants': '0.00000000',
                    'shares_pending_from_options_events': '0.00000000'
                }

        ### Start WebSocket Streams ###
        if self.stream == True:
            self.yahoofin_client.start_feed(self.robinhood_conf['products'], self._feed_enQ_msg)
        
        log.info("**Robinhood init success**\n Products: %s\n Accounts: %s" % (
                        pprint.pformat(self.robinhood_products, 4), pprint.pformat(self.robinhood_accounts, 4)))
        
    def __str__ (self):
        return "{Message: Robinhood Exchange }"

######## WS Feed Helper routines ##############
    def _feed_enQ_msg(self, msg):
#         log.debug ("feed msg: %s"%msg)
        product_id = msg.id
        if (product_id == None):
            log.error ("Feed Thread: Invalid Product-id:  msg - \n %s"%(msg))
            return
        market = get_market_by_product (self.name, product_id)
        if (market == None):
            log.error ("Feed Thread: Unknown market: %s"%(msg))
            return                
        feed_enQ(market, msg)        
######## Feed Consume #######
    def _robinhood_consume_feed (self, market, msg):
#         '''
# msg: id: "SPY"
# price: 288.8450012207031
# time: 1588875362000
# exchange: "PCX"
# quoteType: ETF
# marketHours: REGULAR_MARKET
# changePercent: 1.6165351867675781
# dayVolume: 49010892
# change: 4.595001220703125
# priceHint: 2
# --
# msg: id: "LYFT"
# price: 33.04999923706055
# time: 1588869571000
# exchange: "NMS"
# quoteType: EQUITY
# marketHours: REGULAR_MARKET
# changePercent: 26.531387329101562
# dayVolume: 18366337
# change: 6.929998397827148
# priceHint: 2
# price: 3.609999895095825
# time: 1588881702000
# exchange: "NYQ"
# quoteType: EQUITY
# marketHours: POST_MARKET
# changePercent: -0.550970196723938
# change: -0.020000219345092773
# priceHint: 4
#         '''
        log.debug ("Ticker Feed:%s"%(msg))
        
        #log.debug ("consuming ticker feed")
        price = float(msg.price)
        if price == 0 or msg.dayVolume == 0:
            log.error("invalid feed msg: %s"%(msg))
            return
        if market.dayVolume == 0:
            #first tick after we came up, initialize
            market.dayVolume = msg.dayVolume
            return
        last_size = msg.dayVolume - market.dayVolume
        market.dayVolume = msg.dayVolume
        if last_size <=0:
            #cases of Pre,After hours. where yahoofin don't give us vol. So we ignore these. We don't handle PH,AH trades.
            return
        
        market.tick (price, last_size)

######## WS Feed ###################
    def market_init (self, market):
        #init the day volume
        market.dayVolume = 0
        market.trading_hrs = 6.5
        usd_acc = self.robinhood_accounts[market.get_fund_type()]
        asset_acc = self.robinhood_accounts.get(market.get_asset_type())
        if (usd_acc == None or asset_acc == None): 
            log.error ("No account available for product: %s"%(market.product_id))
            return None
        
#         #Setup the initial params
        market.fund.set_initial_value(float(usd_acc['buying_power']))
        market.fund.set_hold_value(float(usd_acc['cash_held_for_orders']))
        market.asset.set_initial_size(float( asset_acc['quantity']))
        market.asset.set_hold_size( float(asset_acc['shares_held_for_sells']))
        
        ## Feed Cb
        market.register_feed_processor(self._robinhood_consume_feed)
        
        ## Init Exchange specific private state variables
        market.set_candle_interval (self.candle_interval)
        
#         #set whether primary or secondary
        log.info ("Market init complete: %s" % (market.product_id))
                
        return market

    def close (self):
        log.debug("Closing exchange...")
        if (self.yahoofin_client):
            log.debug("Closing yahoofin_client")
            if self.stream == True:
                self.yahoofin_client.stop_feed ()        
        log.info ("exch being closed")
        if self.auth:
            #log out now. 
            self.rbh_client.logout()

    def get_products (self):
        log.debug ("products num %d" % (len(self.robinhood_products)))
        return self.robinhood_products    

    def get_accounts (self):
    #     log.debug (pprint.pformat(self.robinhood_accounts))
        log.debug ("get accounts")
        return self.robinhood_accounts
    def get_historic_rates (self, product_id, start=None, end=None):
        '''
            Args:
        product_id (str): Product
        start (Optional[str]): Start time in ISO 8601
        end (Optional[str]): End time in ISO 8601
        interval (Optional[str]): Desired time slice in 
         seconds
         '''
        # Max Candles in one call
        epoch = datetime.utcfromtimestamp(0).replace(tzinfo=tzutc())
        max_candles = 500
        candles_list = []
        
        # get config
        enabled = self.robinhood_conf.get('backfill_enabled')
        period = int(self.robinhood_conf.get('backfill_period'))
        interval_str = RBH_INTERVAL_MAPPING_TO_STR[self.candle_interval]
        
        if not enabled:
            log.debug ("Historical data retrieval not enabled")
            return None
        interval = self.candle_interval
        product = None
        for p in self.get_products():
            if p['id'] == product_id:
                product = p
        if product is None:
            log.error ("Invalid Product Id: %s" % product_id)
            return None
        if not end:
            # if no end, use current time
            end = datetime.now()
            end = end.replace(tzinfo=tzlocal())
        if not start:
            # if no start given, use the config
            start = end - timedelta(days=period) - timedelta(seconds=interval)
            #get a whole day
            real_start = start = start.replace(hour=0, minute=0, second=0, microsecond=0) 
        else:
            real_start = start
        real_start = start = start.replace(tzinfo=tzlocal())
        
        log.debug ("Retrieving Historic candles for period: %s to %s" % (
                    real_start.isoformat(), end.isoformat()))
        
        td = max_candles * interval
        tmp_end = start + timedelta(seconds=td)
        tmp_end = min(tmp_end, end)
        
        # adjust time with server time
        start = start + timedelta(seconds=self.timeOffset)
        tmp_end = tmp_end + timedelta(seconds=self.timeOffset)
        
        count = 0
        while (start < end):
            # # looks like there is a rate=limiting in force, we will have to slow down
            count += 1
            if (count > 3):
                # rate-limiting
                count = 0
                sleep (2)
            
            start_ts = int((start - epoch).total_seconds())
            end_ts = int((tmp_end - epoch).total_seconds())
            
            log.debug ("Start: %s end: %s" % (start_ts, end_ts))
            candles, err = self.yahoofin_client.get_historic_candles (
                symbol=product['id'],
                interval=interval_str,
                start_time=start_ts,
                end_time=end_ts
            )
            if candles :
                # candles are of struct [[time, o, h, l,c, V]]
                ind = candles['indicators']['quote'][0]
                t = candles.get('timestamp')
                if t and ind:
                    o = ind['open']
                    h = ind['high']
                    l = ind['low']
                    c = ind['close']
                    v = ind['volume']
                    candles_list += [OHLC(time=int(t[i]) or 0,
                                            low=l[i] or 0, high=h[i] or 0, open=o[i] or 0,
                                            close=c[i] or 0, volume=v[i] or 0) for i in range(len(t))]
    #                 log.debug ("%s"%(candles))
                    log.debug ("Historic candles for period: %s to %s num_candles: %d " % (
                        start.isoformat(), tmp_end.isoformat(), (0 if not candles else len(t))))
                else:
                    #may be market holiday period
                    log.error ("no historic candles available on period: %s to %s " % (
                        start.isoformat(), tmp_end.isoformat()))
                # new period, start from the (last +1)th position
                start = tmp_end  # + timedelta(seconds = (interval//1000))
                tmp_end = start + timedelta(seconds=td)
                tmp_end = min(tmp_end, end)

#                 log.debug ("c: %s"%(candles_list))
            else:
                log.error ("Error While Retrieving Historic candles for period: %s to %s num: %d err: %s" % (
                    start.isoformat(), tmp_end.isoformat(), (0 if not candles else len(candles)), err))
                return None
        
        log.debug ("Retrieved Historic candles for period: %s to %s num: %d" % (
                    real_start.isoformat(), end.isoformat(), (0 if not candles_list else len(candles_list))))
    #     log.debug ("%s"%(candles_list))
        #attempt a de-duplication, not sure if this is really required here. 
        dedu_dict = {}
        for cdl in candles_list:
            if cdl.open == 0 or cdl.high == 0 or cdl.low == 0 or cdl.close == 0 :
                log.error("invalid candle in history :%s"%(cdl))
                continue
            dedu_dict[cdl.time] = cdl
        candles_list = [cdl for _, cdl in dedu_dict.items()]
        log.info ("de-duplicated candle list len %d"%(len(candles_list)))
        return candles_list
        
    def _normalized_order (self, order):
#         '''
#         Desc:
#          Error Handle and Normalize the order json returned by RBH
#           to return the normalized order detail back to callers
#           Handles -
#           1. Initial Order Creation/Order Query
#         Sample order:
# {
# id: "a5a7b4d8-7f16-44d5-9448-fa09a341e77b", ref_id: "<orig_ref_id>",…}
# account: "https://api.robinhood.com/accounts/id/"
# average_price: null
# cancel: "https://api.robinhood.com/orders/<id>/cancel/"
# created_at: "2020-05-05T04:02:49.045521Z"
# cumulative_quantity: "0.00000000"
# executed_notional: null
# executions: []
# extended_hours: false
# fees: "0.00"
# id: "a5a7buuidb"
# instrument: "https://api.robinhood.com/instruments/uuid/"
# investment_schedule_id: null
# last_trail_price: null
# last_trail_price_updated_at: null
# last_transaction_at: "2020-05-05T04:02:49.045521Z"
# override_day_trade_checks: false
# override_dtbp_checks: false
# position: "https://api.robinhood.com/positions/xxx/xxx"
# price: "3.54000000"
# quantity: "1.00000000"
# ref_id: "4uuid6"
# reject_reason: null
# response_category: null
# side: "buy"
# state: "unconfirmed"
# stop_price: null
# stop_triggered_at: null
# time_in_force: "gfd"
# total_notional: {amount: "3.54", currency_code: "USD", currency_id: "1072fc76-1862-41ab-82c2-485837590762"}
# amount: "3.54"
# currency_code: "USD"
# currency_id: "1072fc76-1862-41ab-82c2-485837590762"
# trigger: "immediate"
# type: "market"
# updated_at: "2020-05-05T04:02:49.045534Z"
# url: "https://api.robinhood.com/orders/uuid/"
# }
#         Known Errors: 
#           1. {u'message': u'request timestamp expired'}
#           2. {u'message': u'Insufficient funds'}
#           3. {'status' : 'rejected', 'reject_reason': 'post-only'}
#         '''
#         error_status_codes = ['rejected']
#        status = [unconfirmed, queued]
        log.critical ("Order msg: \n%s" % (pprint.pformat(order, 4)))
        
        status = order.get('state')
        
        # Valid Order
        instr = self._get_symbol_from_instrument(order.get('instrument'))
        product_id = instr['symbol'] if instr != None else None
        order_id = order.get('id')
        order_type = order.get('type')
        
        if order_id == "" or order_id == None or product_id == "" or product_id == None:
            log.critical ("order placing failed %s"%(pprint.pformat(order, 4)))
        
        if order_type == "market":
            order_type = "market"
        elif order_type == "limit":
            order_type = 'limit'
                
        if status in ['open', 'confirmed', 'unconfirmed', 'queued', 'cancelled', 'filled', 'rejected', 'expired' ]:
            if status in ["open", 'unconfirmed', 'queued', 'confirmed']:
                status_type = "open"
            elif status == 'filled':
                status_type = "filled"
            elif status in ['cancelled', 'expired']:
                # order status update message
                status_type = "canceled"
            elif status == 'rejected':
                log.error ("order rejected msg:%s" % (order))
                return None
            else: #, 'PARTIALLY_FILLED'
                log.critical ('unhandled order status(%s)' % (status))
                return None
#             order_type = order.get('order_type') #could be None
        else:
            s = "****** unknown order status: %s ********" % (status)
            log.critical (s)
            raise Exception (s)
            
        create_time = order.get('created_at') or None
        if create_time:
            create_time = datetime.fromisoformat(create_time.rstrip("Z")).replace(tzinfo=tzutc()).astimezone(tzlocal()).isoformat()

        update_time = order.get('updated_at') or None
        if update_time:
            update_time = datetime.fromisoformat(update_time.rstrip("Z")).replace(tzinfo=tzutc()).astimezone(tzlocal()).isoformat()
        else:
            update_time = datetime.now().isoformat()
                    
        side = order.get('side') or None
        if side == None:
            log.critical("unable to get order side %s(%s)"%(product_id, order_id))
            raise Exception ("unable to get order side")
        
        # Money matters
        price = float(order.get('average_price') or order.get('price') or 0)
        request_size = float(order.get('quantity') or 0)
        filled_size = 0
        for exe in order["executions"]:
            filled_size += float(exe.get('quantity') or 0)
        remaining_size = float(request_size - filled_size)
        funds = float(price * request_size)
        fees = float(order.get('fees') or 0)
            
        log.debug ("price: %g fund: %g req_size: %g filled_size: %g remaining_size: %g fees: %g" % (
            price, funds, request_size, filled_size, remaining_size, fees))
        norm_order = Order (order_id, product_id, status_type, order_type=order_type,
                            side=side, request_size=request_size, filled_size=filled_size, remaining_size=remaining_size,
                             price=price, funds=funds, fees=fees, create_time=create_time, update_time=update_time)
        return norm_order        
        
    def get_product_order_book (self, product, level=1):
        log.debug ("get_product_order_book: ***********Not-Implemented******")
        return None

    def buy (self, trade_req) :
        log.debug ("BUY - Placing Order on exchange --")
        try:
            instr = self.get_instrument_from_symbol(trade_req.product)
            params = {'symbol':trade_req.product, 'side' : "buy", 'quantity':trade_req.size, "instrument_URL": instr["url"],
                      "time_in_force": "GTC", 'trigger':"immediate" }  # asset
            if trade_req.type == "market":
                params['order_type'] = "market"
            else:
                params['order_type'] = "limit"
                params['price'] = trade_req.price,  # USD
            order = self.rbh_client.submit_buy_order(**params).json()
        except Exception as e:
            log.error ("exception while placing order - %s"%(e))
            return None
        return self._normalized_order (order);
    
    def sell (self, trade_req) :
        log.debug ("SELL - Placing Order on exchange --")
        try:
            instr = self.get_instrument_from_symbol(trade_req.product)
            params = {'symbol':trade_req.product, 'side' : "sell", 'quantity':trade_req.size, "instrument_URL": instr["url"],
                  "time_in_force": "GTC", 'trigger':"immediate" }  # asset
            if trade_req.type == "market":
                params['order_type'] = "market"
            else:
                params['order_type'] = "limit"
                params['price'] = trade_req.price,  # USD
            order = self.rbh_client.submit_sell_order(**params).json()
        except Exception as e:
            log.error ("exception while placing order - %s"%(e))
            return None
        return self._normalized_order (order);
    
    def get_order (self, prod_id, order_id):
        log.debug ("GET - prod(%s) order (%s) " % (prod_id, order_id))
        try:
            order = self.rbh_client.order_history(orderId=order_id)
        except Exception as e:
            log.error ("exception while placing order - %s"%(e))
            return None        
        return self._normalized_order (order);
    
    def cancel_order (self, prod_id, order_id):
        log.debug ("CANCEL - prod(%s) order (%s) " % (prod_id, order_id))
        try:
            return self.rbh_client.client.cancel_order(order_id)
        except Exception as e:
            log.error ("exception while canceling order - %s"%(e))
            return None
    
    def get_market_hrs(self, date=None):
        if date==None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        api = API_BASE+"/markets/XASE/hours/"+date_str
        m_hrs = self._fetch_json_by_url(api)
        log.debug ("market hrs for %s is %s"%(date_str, m_hrs))
        return m_hrs["is_open"], m_hrs
    
    def get_quote (self, sym):
        try:
            return self.rbh_client.get_quote(sym.upper())
        except Exception as e:        
            log.error ("exception calling rh api - %s"%(e))
            return None         
    def _fetch_json_by_url(self, url):
        try:
            return self.rbh_client.get_url(url)
        except Exception as e:        
            log.error ("exception calling rh api - %s"%(e))
            return None        
    
    def get_instrument_from_symbol(self, symbol):
        instr = self.symbol_to_instr_map.get(symbol)
        if instr:
            log.debug ("found cached instr for id: %s symbol: %s"%(symbol, instr['id']))
            return instr
        else:
            try:
                instr = self.rbh_client.instrument(symbol)
                if instr :
                    log.debug("got symbol for id %s symbol: %s"%(symbol, instr['id']))   
                    self.instr_to_symbol_map[symbol] = instr
                    return instr
                else:
                    log.error("unable to get symbol for id %s"%(symbol))
            except Exception as e:        
                log.error ("exception calling rh api - %s"%(e))
                return None                
        return None
        
    def _get_symbol_from_instrument(self, instr):
        i_id = instr.rstrip('/').split('/')[-1]
        sym = self.instr_to_symbol_map.get(i_id)
        if sym:
            log.debug ("found cached symbol for id: %s symbol: %s"%(i_id, sym['symbol']))
            return sym
        else:
            sym = self._fetch_json_by_url(instr)
            if sym :
                log.debug("got symbol for id %s symbol: %s"%(i_id, sym))   
                self.instr_to_symbol_map[i_id] = sym
                return sym
            else:
                log.error("unable to get symbol for id %s"%(i_id))
    
    def get_order_history(self, symbol=None, from_date=None, to_date=None):
        #TODO: FIXME: this is the shittiest way of doing this. There must be another way
        all_orders = self.get_all_history_orders(symbol)
        orders = []
        if symbol == None or symbol == "":
            orders = all_orders
        else:
            for order in all_orders:
                if order['symbol'] == symbol.upper():
                    orders.append(order)
        #TODO: FIXME: filter time
        return orders
    def get_all_history_orders(self, symbol=None):
        orders = []
        if symbol == None:
            past_orders = self.rbh_client.order_history()
        else:
            instr = self.get_instrument_from_symbol(symbol)
            if not instr:
                log.error("unable to get instrument from symbol")
            instr_url = instr['url']
            url = API_BASE +"/orders/?instrument="+instr_url
            past_orders = self._fetch_json_by_url(url)
        orders.extend(past_orders['results'])
        log.debug("%d order fetched first page"%(len(orders)))    
        while past_orders['next']:
            next_url = past_orders['next']
            past_orders = self._fetch_json_by_url(next_url)
            orders.extend(past_orders['results'])
        log.info("%d  order fetched"%(len(orders)))
        for order in orders:
            instrument = order['instrument']
            symbol = self._get_symbol_from_instrument(instrument)
            if symbol:
                order['symbol'] = symbol['symbol']
                order['bloomberg_unique'] = symbol['bloomberg_unique']
            else:
                log.error ('unable to get symbol for instrument')  
        return orders
    ##################### OPTIONS######################
    def get_option_from_instrument(self, instr):
        i_id = instr.rstrip('/').split('/')[-1]
        sym = self.option_id_map.get(i_id)
        if sym:
            log.debug ("found cached option for id: %s symbol: %s"%(i_id, sym['chain_symbol']))
            return sym
        else:
            sym = self._fetch_json_by_url(instr)
            if sym :
                log.debug("got option for id %s symbol: %s"%(i_id, sym))   
                self.option_id_map[i_id] = sym
                return sym
            else:
                log.error("unable to get option for id %s"%(i_id))
    def get_option_chains_summary(self, chain_id):
        options_api_url = API_BASE+"/options/chains/"+chain_id
        options_l = self._fetch_json_by_url(options_api_url)
        log.debug("option chain summary: \n %s"%(pprint.pformat(options_l, 4)))        
        return options_l
    def get_option_chain(self, chain_id, exp_date, opt_type):
        option_chain = []
        options_api_url = API_BASE+"/options/instruments/?chain_id=%s&expiration_dates=%s&state=active&type=%s"%(chain_id, exp_date, opt_type)
        options_l = self._fetch_json_by_url(options_api_url)
        option_chain.extend(options_l['results'])
        while options_l['next']:
            # print("{} order fetched".format(len(orders)))
            next_url = options_l['next']
            options_l = self._fetch_json_by_url(next_url)
            option_chain.extend(options_l['results'])
        log.info("%d options fetched from chain"%(len(option_chain)))
        
        log.debug("option chain: \n %s"%(pprint.pformat(option_chain, 4)))
        return option_chain
    def get_option_marketdata(self, instr_list):     
        if type(instr_list) != list:
            instr_list = [instr_list]
        B_SIZE = 50
        i = 0
        res_list = []
        while i < len(instr_list):
            i_list = instr_list[i:i+B_SIZE]
            res = self.get_option_mdata(i_list)
            res_list.extend(res["results"])
            i += B_SIZE
        return res_list
    def get_option_mdata(self, instrument_l):
        i_str = ",".join(instrument_l)
#         i_str = "https://api.robinhood.com/options/instruments/ef40903c-377c-448e-8f9b-ecea19e7b97f/"
        options_api_url = API_BASE+"/marketdata/options/?instruments="+i_str
        mdata_l = self._fetch_json_by_url(options_api_url)        
        return mdata_l  
    def get_option_positions (self, symbol=None):
        options_api_url = API_BASE+"/options/positions/?nonzero=true"
        option_positions = []
        options_l = self._fetch_json_by_url(options_api_url)
        option_positions.extend(options_l['results'])
        while options_l['next']:
            # print("{} order fetched".format(len(orders)))
            next_url = options_l['next']
            options_l = self._fetch_json_by_url(next_url)
            option_positions.extend(options_l['results'])
        positions_l = []
        if symbol == None or symbol == "":
            positions_l = option_positions
        else:
            for pos in option_positions:
                if pos['chain_symbol'] == symbol.upper():
                    #filter noise 
                    if int(float(pos["quantity"])) != 0 : 
                        positions_l.append(pos)            
        log.info("%d option positions fetched"%(len(positions_l)))
        for pos in positions_l:
            pos["option_det"] = self.get_option_from_instrument(pos["option"])         
        log.debug ("options owned: %s"%(pprint.pformat(positions_l, 4)))
        return positions_l
    def get_options_order_history(self, symbol=None, from_date=None, to_date=None):
        #TODO: FIXME: this is the shittiest way of doing this. There must be another way
        all_orders = self.get_all_history_options_orders(symbol)
        orders = []
        if symbol == None or symbol == "":
            orders = all_orders
        else:
            for order in all_orders:
                if order['chain_symbol'] == symbol.upper():
                    orders.append(order)
        #TODO: FIXME: filter time
        #get option details
        for order in orders:
            for leg in order["legs"]:
                leg["option_det"] = self.get_option_from_instrument(leg["option"])        
        log.debug ("order: %s"%(pprint.pformat(orders, 4)))
        return orders
    def options_order_history(self, symbol=None):
        options_api_url = API_BASE+"/options/orders/"
        if symbol == None:
            return self._fetch_json_by_url(options_api_url)
        else:
            instr = self.get_instrument_from_symbol(symbol)
            if not instr:
                log.error("unable to get instrument from symbol")
            instr_url = instr['url']
            url = options_api_url +"?instrument="+instr_url
            return self._fetch_json_by_url(url)        
    def get_all_history_options_orders(self, symbol=None):
        options_orders = []
        past_options_orders = self.options_order_history(symbol)
        options_orders.extend(past_options_orders['results'])
        while past_options_orders['next']:
            # print("{} order fetched".format(len(orders)))
            next_url = past_options_orders['next']
            past_options_orders = self._fetch_json_by_url(next_url)
            options_orders.extend(past_options_orders['results'])
        log.info("%d order fetched"%(len(options_orders)))
        return options_orders

######### ******** MAIN ****** #########
if __name__ == '__main__':
    import argparse

    print ("Testing Robinhood exch:")

    print ("Done")
# EOF