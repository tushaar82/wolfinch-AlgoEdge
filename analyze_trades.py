#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze trading performance from InfluxDB
Shows detailed statistics and insights
"""

import yaml
from datetime import datetime
from influxdb_client import InfluxDBClient
import sys

def load_config():
    """Load InfluxDB configuration"""
    with open('config/cache_db.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config['influxdb']

def create_client(config):
    """Create InfluxDB client"""
    return InfluxDBClient(
        url=config['url'],
        token=config['token'],
        org=config['org']
    )

def analyze_performance(client, config, days=7):
    """Analyze trading performance"""
    query_api = client.query_api()
    
    print("\n" + "="*70)
    print(f"Trading Performance Analysis (Last {days} days)")
    print("="*70 + "\n")
    
    # 1. Total Trades
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> count()
    '''
    result = query_api.query(query)
    total_trades = 0
    for table in result:
        for record in table.records:
            total_trades = record.get_value()
            break
    
    print(f"📊 Total Trades: {total_trades}")
    
    if total_trades == 0:
        print("\n⚠️  No trades found in the specified period")
        return
    
    # 2. Win/Loss Analysis
    query_wins = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "win")
      |> sum()
    '''
    result = query_api.query(query_wins)
    wins = 0
    for table in result:
        for record in table.records:
            wins = int(record.get_value())
            break
    
    losses = total_trades - wins
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    print(f"✅ Wins: {wins}")
    print(f"❌ Losses: {losses}")
    print(f"📈 Win Rate: {win_rate:.2f}%")
    print()
    
    # 3. P&L Analysis
    query_pnl = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "pnl")
    '''
    result = query_api.query(query_pnl)
    
    pnl_values = []
    for table in result:
        for record in table.records:
            pnl_values.append(record.get_value())
    
    if pnl_values:
        total_pnl = sum(pnl_values)
        avg_pnl = total_pnl / len(pnl_values)
        max_win = max(pnl_values)
        max_loss = min(pnl_values)
        
        print(f"💰 Total P&L: ₹{total_pnl:,.2f}")
        print(f"📊 Average P&L per trade: ₹{avg_pnl:,.2f}")
        print(f"🎯 Best Trade: ₹{max_win:,.2f}")
        print(f"⚠️  Worst Trade: ₹{max_loss:,.2f}")
        print()
    
    # 4. Duration Analysis
    query_duration = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "duration_minutes")
    '''
    result = query_api.query(query_duration)
    
    durations = []
    for table in result:
        for record in table.records:
            durations.append(record.get_value())
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        print(f"⏱️  Average Trade Duration: {avg_duration:.1f} minutes ({avg_duration/60:.2f} hours)")
        print(f"⏱️  Longest Trade: {max_duration:.1f} minutes ({max_duration/60:.2f} hours)")
        print(f"⏱️  Shortest Trade: {min_duration:.1f} minutes")
        print()
    
    # 5. Fees Analysis
    query_fees = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "order_filled")
      |> filter(fn: (r) => r._field == "fee")
      |> sum()
    '''
    result = query_api.query(query_fees)
    total_fees = 0
    for table in result:
        for record in table.records:
            total_fees = record.get_value()
            break
    
    print(f"💸 Total Fees Paid: ₹{total_fees:,.2f}")
    
    if total_pnl != 0:
        fee_percentage = (total_fees / abs(total_pnl)) * 100
        print(f"💸 Fees as % of P&L: {fee_percentage:.2f}%")
    print()
    
    # 6. Product Analysis
    query_products = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> group(columns: ["product"])
      |> count()
    '''
    result = query_api.query(query_products)
    
    print("📦 Trades by Product:")
    for table in result:
        for record in table.records:
            product = record.values.get('product', 'Unknown')
            count = record.get_value()
            print(f"   - {product}: {count} trades")
    print()
    
    # 7. Risk Metrics
    if pnl_values and len(pnl_values) > 1:
        # Calculate Sharpe-like ratio (simplified)
        import statistics
        std_dev = statistics.stdev(pnl_values)
        sharpe = (avg_pnl / std_dev) if std_dev > 0 else 0
        
        print(f"📊 Risk Metrics:")
        print(f"   - P&L Std Dev: ₹{std_dev:,.2f}")
        print(f"   - Risk-Adjusted Return: {sharpe:.2f}")
        print()
    
    # 8. Recent Performance
    query_recent = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> filter(fn: (r) => r._field == "pnl")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 5)
    '''
    result = query_api.query(query_recent)
    
    print("🕐 Last 5 Trades:")
    for table in result:
        for record in table.records:
            time = record.get_time().strftime('%Y-%m-%d %H:%M:%S')
            pnl = record.get_value()
            product = record.values.get('product', 'N/A')
            result_emoji = "✅" if pnl > 0 else "❌"
            print(f"   {result_emoji} {time} | {product} | ₹{pnl:,.2f}")
    
    print("\n" + "="*70 + "\n")

def main():
    """Main function"""
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    
    config = load_config()
    client = create_client(config)
    
    analyze_performance(client, config, days)
    
    client.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
