#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export InfluxDB data to CSV files
Creates separate CSV files for candles, trades, and positions
"""

import yaml
import csv
from datetime import datetime
from influxdb_client import InfluxDBClient
import sys
import os

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

def export_candles(client, config, output_dir='exports', product='BANKNIFTY-FUT', days=7):
    """Export candle data to CSV"""
    print(f"Exporting candles for {product} (last {days} days)...")
    
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "candle")
      |> filter(fn: (r) => r.product == "{product}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    filename = f"{output_dir}/candles_{product}_{days}d.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'time', 'open', 'high', 'low', 'close', 'volume', 'exchange', 'product'])
        
        count = 0
        for table in result:
            for record in table.records:
                writer.writerow([
                    record.get_time().timestamp(),
                    record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                    record.values.get('open', 0),
                    record.values.get('high', 0),
                    record.values.get('low', 0),
                    record.values.get('close', 0),
                    record.values.get('volume', 0),
                    record.values.get('exchange', 'N/A'),
                    record.values.get('product', 'N/A')
                ])
                count += 1
    
    print(f"  ✓ Exported {count} candles to {filename}")
    return count

def export_trades(client, config, output_dir='exports', days=7):
    """Export trade data to CSV"""
    print(f"Exporting trades (last {days} days)...")
    
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "order_filled")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    filename = f"{output_dir}/trades_{days}d.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'time', 'exchange', 'product', 'order_id', 'side', 
            'fill_price', 'fill_size', 'fee', 'total_cost', 'market_price', 'slippage'
        ])
        
        count = 0
        for table in result:
            for record in table.records:
                writer.writerow([
                    record.get_time().timestamp(),
                    record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                    record.values.get('exchange', 'N/A'),
                    record.values.get('product', 'N/A'),
                    record.values.get('order_id', 'N/A'),
                    record.values.get('side', 'N/A'),
                    record.values.get('fill_price', 0),
                    record.values.get('fill_size', 0),
                    record.values.get('fee', 0),
                    record.values.get('total_cost', 0),
                    record.values.get('market_price', 0),
                    record.values.get('slippage', 0)
                ])
                count += 1
    
    print(f"  ✓ Exported {count} trades to {filename}")
    return count

def export_positions(client, config, output_dir='exports', days=7):
    """Export position data to CSV"""
    print(f"Exporting positions (last {days} days)...")
    
    query = f'''
    from(bucket: "{config['bucket']}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "trade_event")
      |> filter(fn: (r) => r.event_type == "position_closed")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''
    
    query_api = client.query_api()
    result = query_api.query(query)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    filename = f"{output_dir}/positions_{days}d.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'time', 'exchange', 'product', 'position_id', 
            'entry_price', 'exit_price', 'size', 'pnl', 'pnl_percent', 
            'duration_seconds', 'duration_minutes', 'close_reason', 'win', 'loss'
        ])
        
        count = 0
        for table in result:
            for record in table.records:
                writer.writerow([
                    record.get_time().timestamp(),
                    record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                    record.values.get('exchange', 'N/A'),
                    record.values.get('product', 'N/A'),
                    record.values.get('position_id', 'N/A'),
                    record.values.get('entry_price', 0),
                    record.values.get('exit_price', 0),
                    record.values.get('size', 0),
                    record.values.get('pnl', 0),
                    record.values.get('pnl_percent', 0),
                    record.values.get('duration_seconds', 0),
                    record.values.get('duration_minutes', 0),
                    record.values.get('close_reason', 'N/A'),
                    record.values.get('win', 0),
                    record.values.get('loss', 0)
                ])
                count += 1
    
    print(f"  ✓ Exported {count} positions to {filename}")
    return count

def main():
    """Main function"""
    print("\n" + "="*70)
    print("Wolfinch InfluxDB Data Exporter")
    print("="*70 + "\n")
    
    # Parse arguments
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    product = sys.argv[2] if len(sys.argv) > 2 else 'BANKNIFTY-FUT'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'exports'
    
    print(f"Configuration:")
    print(f"  - Days: {days}")
    print(f"  - Product: {product}")
    print(f"  - Output directory: {output_dir}")
    print()
    
    # Load config and create client
    config = load_config()
    client = create_client(config)
    
    print(f"Connected to InfluxDB: {config['url']}")
    print(f"Bucket: {config['bucket']}\n")
    
    # Export data
    candle_count = export_candles(client, config, output_dir, product, days)
    trade_count = export_trades(client, config, output_dir, days)
    position_count = export_positions(client, config, output_dir, days)
    
    print("\n" + "="*70)
    print("Export Summary:")
    print(f"  ✓ {candle_count} candles")
    print(f"  ✓ {trade_count} trades")
    print(f"  ✓ {position_count} positions")
    print(f"\nFiles saved to: {output_dir}/")
    print("="*70 + "\n")
    
    client.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
