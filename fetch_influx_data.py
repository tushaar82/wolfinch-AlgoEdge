#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetch and display data from InfluxDB
Shows candles, trades, and performance metrics
"""

import yaml
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from tabulate import tabulate
import sys

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def load_config():
    """Load InfluxDB configuration"""
    try:
        with open('config/cache_db.yml') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config['influxdb']
    except Exception as e:
        print(f"{Colors.RED}Error loading config: {e}{Colors.END}")
        sys.exit(1)

def create_client(config):
    """Create InfluxDB client"""
    return InfluxDBClient(
        url=config['url'],
        token=config['token'],
        org=config['org']
    )

def fetch_candles(client, config, hours=24, product='BANKNIFTY-FUT'):
    """Fetch candle data"""
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "candle")
      |> filter(fn: (r) => r.product == "{product}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 20)
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    candles = []
    for table in result:
        for record in table.records:
            candles.append({
                'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                'open': record.values.get('open', 0),
                'high': record.values.get('high', 0),
                'low': record.values.get('low', 0),
                'close': record.values.get('close', 0),
                'volume': record.values.get('volume', 0),
            })
    
    return candles

def fetch_trades(client, config, hours=24):
    """Fetch trade events"""
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "order_filled")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    trades = []
    for table in result:
        for record in table.records:
            trades.append({
                'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                'product': record.values.get('product', 'N/A'),
                'side': record.values.get('side', 'N/A'),
                'fill_price': record.values.get('fill_price', 0),
                'fill_size': record.values.get('fill_size', 0),
                'fee': record.values.get('fee', 0),
                'total_cost': record.values.get('total_cost', 0),
            })
    
    return trades

def fetch_positions(client, config, hours=24):
    """Fetch closed positions with P&L"""
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    positions = []
    for table in result:
        for record in table.records:
            pnl = record.values.get('pnl', 0)
            positions.append({
                'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                'product': record.values.get('product', 'N/A'),
                'entry_price': record.values.get('entry_price', 0),
                'exit_price': record.values.get('exit_price', 0),
                'pnl': pnl,
                'pnl_pct': record.values.get('pnl_percent', 0),
                'duration_min': record.values.get('duration_minutes', 0),
                'result': 'WIN' if pnl > 0 else 'LOSS'
            })
    
    return positions

def fetch_stats(client, config, hours=24):
    """Fetch trading statistics"""
    # Total trades
    query_total = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "order_filled")
      |> count()
    '''
    
    # Total P&L
    query_pnl = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "pnl")
      |> sum()
    '''
    
    # Win rate
    query_wins = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "win")
      |> mean()
    '''
    
    # Total fees
    query_fees = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "order_filled")
      |> filter(fn: (r) => r._field == "fee")
      |> sum()
    '''
    
    query_api = client.query_api()
    
    stats = {
        'total_trades': 0,
        'total_pnl': 0,
        'win_rate': 0,
        'total_fees': 0
    }
    
    try:
        result = query_api.query(query_total)
        for table in result:
            for record in table.records:
                stats['total_trades'] = record.get_value()
                break
    except:
        pass
    
    try:
        result = query_api.query(query_pnl)
        for table in result:
            for record in table.records:
                stats['total_pnl'] = record.get_value()
                break
    except:
        pass
    
    try:
        result = query_api.query(query_wins)
        for table in result:
            for record in table.records:
                stats['win_rate'] = record.get_value() * 100
                break
    except:
        pass
    
    try:
        result = query_api.query(query_fees)
        for table in result:
            for record in table.records:
                stats['total_fees'] = record.get_value()
                break
    except:
        pass
    
    return stats

def fetch_candle_count(client, config):
    """Get total candle count"""
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -30d)
      |> filter(fn: (r) => r._measurement == "candle")
      |> filter(fn: (r) => r._field == "close")
      |> count()
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    for table in result:
        for record in table.records:
            return record.get_value()
    
    return 0

def main():
    """Main function"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}Wolfinch InfluxDB Data Viewer{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    # Load config
    print(f"{Colors.YELLOW}Loading configuration...{Colors.END}")
    config = load_config()
    print(f"{Colors.GREEN}✓ Connected to: {config['url']}{Colors.END}")
    print(f"{Colors.GREEN}✓ Bucket: {config['bucket']}{Colors.END}\n")
    
    # Create client
    client = create_client(config)
    
    # Get command line arguments
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    product = sys.argv[2] if len(sys.argv) > 2 else 'BANKNIFTY-FUT'
    
    print(f"{Colors.BLUE}Fetching data for last {hours} hours...{Colors.END}\n")
    
    # 1. Statistics
    print(f"{Colors.BOLD}{Colors.CYAN}📊 Trading Statistics (Last {hours}h){Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")
    stats = fetch_stats(client, config, hours)
    candle_count = fetch_candle_count(client, config)
    
    stats_table = [
        ['Total Candles', f"{candle_count:,}"],
        ['Total Trades', f"{int(stats['total_trades']):,}"],
        ['Total P&L', f"{Colors.GREEN if stats['total_pnl'] >= 0 else Colors.RED}₹{stats['total_pnl']:,.2f}{Colors.END}"],
        ['Win Rate', f"{stats['win_rate']:.1f}%"],
        ['Total Fees', f"₹{stats['total_fees']:,.2f}"],
    ]
    print(tabulate(stats_table, tablefmt='simple'))
    print()
    
    # 2. Recent Candles
    print(f"\n{Colors.BOLD}{Colors.CYAN}📈 Recent Candles - {product} (Last 20){Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")
    candles = fetch_candles(client, config, hours, product)
    
    if candles:
        candle_headers = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        candle_data = [
            [
                c['time'],
                f"₹{c['open']:,.2f}",
                f"₹{c['high']:,.2f}",
                f"₹{c['low']:,.2f}",
                f"₹{c['close']:,.2f}",
                f"{c['volume']:,.0f}"
            ]
            for c in candles
        ]
        print(tabulate(candle_data, headers=candle_headers, tablefmt='grid'))
    else:
        print(f"{Colors.YELLOW}No candle data found{Colors.END}")
    
    # 3. Recent Trades
    print(f"\n{Colors.BOLD}{Colors.CYAN}💰 Recent Trades{Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")
    trades = fetch_trades(client, config, hours)
    
    if trades:
        trade_headers = ['Time', 'Product', 'Side', 'Price', 'Size', 'Fee', 'Total']
        trade_data = [
            [
                t['time'],
                t['product'],
                f"{Colors.GREEN if t['side'] == 'BUY' else Colors.RED}{t['side']}{Colors.END}",
                f"₹{t['fill_price']:,.2f}",
                f"{t['fill_size']:.2f}",
                f"₹{t['fee']:.2f}",
                f"₹{t['total_cost']:,.2f}"
            ]
            for t in trades
        ]
        print(tabulate(trade_data, headers=trade_headers, tablefmt='grid'))
    else:
        print(f"{Colors.YELLOW}No trade data found{Colors.END}")
    
    # 4. Closed Positions
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Closed Positions (P&L){Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")
    positions = fetch_positions(client, config, hours)
    
    if positions:
        pos_headers = ['Time', 'Product', 'Entry', 'Exit', 'P&L', 'P&L %', 'Duration', 'Result']
        pos_data = [
            [
                p['time'],
                p['product'],
                f"₹{p['entry_price']:,.2f}",
                f"₹{p['exit_price']:,.2f}",
                f"{Colors.GREEN if p['pnl'] >= 0 else Colors.RED}₹{p['pnl']:,.2f}{Colors.END}",
                f"{Colors.GREEN if p['pnl_pct'] >= 0 else Colors.RED}{p['pnl_pct']:.2f}%{Colors.END}",
                f"{p['duration_min']:.0f}m",
                f"{Colors.GREEN if p['result'] == 'WIN' else Colors.RED}{p['result']}{Colors.END}"
            ]
            for p in positions
        ]
        print(tabulate(pos_data, headers=pos_headers, tablefmt='grid'))
    else:
        print(f"{Colors.YELLOW}No position data found{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    client.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
