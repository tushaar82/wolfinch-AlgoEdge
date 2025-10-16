# PaperTrader Exchange

The PaperTrader exchange is a CSV-based data feed simulator for Wolfinch. It allows you to backtest and paper trade strategies using historical data stored in CSV files.

## Features

- **CSV-based data feeds**: Load historical market data from CSV files
- **Multiple data formats**: Supports both OHLC (Open, High, Low, Close, Volume) and simple price/volume formats
- **Simulated order execution**: Instantly fills orders at current market prices
- **Configurable products**: Trade multiple cryptocurrency pairs simultaneously
- **Thread-based feed generation**: Asynchronous data feed processing
- **Historical data support**: Provides historic rates for backtesting

## Installation

The PaperTrader exchange is already integrated into Wolfinch. No additional installation is required.

## Configuration

### 1. Exchange Configuration (`config/papertrader.yml`)

```yaml
exchange:
  # Directory containing CSV data files
  raw_data_dir: 'raw_data'
  
  # Initial account balances
  initial_fund: 10000.0  # USD
  initial_asset: 0.0     # BTC/ETH/etc
  
  # Products to trade
  products:
    - 'BTCUSD':
        id: 'BTC-USD'
        asset_type: 'BTC'
        fund_type: 'USD'
        csv_file: 'btc_usd.csv'
    
    - 'ETHUSD':
        id: 'ETH-USD'
        asset_type: 'ETH'
        fund_type: 'USD'
        csv_file: 'eth_usd.csv'
```

### 2. Wolfinch Configuration (`config/wolfinch_papertrader_btc.yml`)

```yaml
exchanges:
   - 'papertrader' : 
      role: 'primary'
      config: 'config/papertrader.yml'
      products:
         - 'BTC-USD':
            active: true         
            fund_max_liquidity : 9000
            fund_max_per_buy_value : 100
            asset_max_per_trade_size: 10
            asset_min_per_trade_size: .001
            stop_loss:
               enabled: true
               kind : strategy
               rate : 3
            take_profit:
               enabled: true 
               kind : strategy
               rate: 5
            decision:
               model    : simple
               config   :
                  strategy: EMA_RSI
                  params : {'period': 120, 'ema_s': 5, 'ema_m': 13, 'ema_l': 21, 'ema_ll': 80, 'rsi': 21, 'rsi_bullish_mark': 50}
      order_type    : market
      fee     : 
         maker : 0.1
         taker : 0.1

candle_interval : 300  # 5 minutes

simulator:
   enabled : true
   backtesting : false

ui:
   enabled : true
   port : 8080
```

## CSV Data Format

### Format 1: OHLC (Recommended)

```csv
timestamp,open,high,low,close,volume
1609459200,29000.00,29500.00,28800.00,29200.00,150.5
1609459500,29200.00,29600.00,29100.00,29400.00,200.3
1609459800,29400.00,29800.00,29300.00,29700.00,180.7
```

**Fields:**
- `timestamp`: Unix timestamp (seconds since epoch)
- `open`: Opening price for the period
- `high`: Highest price during the period
- `low`: Lowest price during the period
- `close`: Closing price for the period
- `volume`: Trading volume for the period

### Format 2: Simple Price/Volume

```csv
timestamp,price,volume
1609459200,29000.00,150.5
1609459500,29200.00,200.3
1609459800,29400.00,180.7
```

**Fields:**
- `timestamp`: Unix timestamp (seconds since epoch)
- `price`: Price at this timestamp
- `volume`: Trading volume

## Usage

### 1. Prepare Your Data

Create a `raw_data` directory in the project root and add your CSV files:

```bash
mkdir raw_data
cp raw_data_sample/btc_usd.csv raw_data/
```

Or generate sample data:

```bash
cd raw_data_sample
python3 generate_sample_data.py
cp *.csv ../raw_data/
```

### 2. Run Wolfinch

```bash
./Wolfinch.py --config config/wolfinch_papertrader_btc.yml
```

### 3. Access the UI

Open your browser and navigate to:
```
http://localhost:8080
```

## Generating Sample Data

Use the provided `generate_sample_data.py` script:

```python
from generate_sample_data import generate_ohlc_data, generate_trending_data

# Generate random walk data
generate_ohlc_data(
    'my_data.csv',
    start_price=30000.0,
    num_candles=1000,
    interval=300
)

# Generate trending data
generate_trending_data(
    'trending_data.csv',
    start_price=30000.0,
    num_candles=1000,
    interval=300,
    trend='up',  # 'up', 'down', or 'sideways'
    trend_strength=0.0005
)
```

## How It Works

1. **Initialization**: PaperTrader loads CSV files specified in the configuration
2. **Feed Generation**: A background thread reads CSV data sequentially and generates trade/candle messages
3. **Market Processing**: Wolfinch processes these messages just like real exchange feeds
4. **Order Execution**: Buy/sell orders are instantly filled at the current market price
5. **Strategy Evaluation**: Your trading strategies run against the historical data

## Features & Limitations

### Features ✅
- Full integration with Wolfinch's strategy and indicator system
- Support for multiple trading pairs
- Configurable initial balances
- Realistic order simulation with fees
- Historical data support for backtesting
- Thread-safe feed processing

### Limitations ⚠️
- Orders are filled instantly at market price (no order book simulation)
- No slippage simulation
- No partial fills
- Data is processed sequentially (not real-time)
- Limited to data available in CSV files

## Troubleshooting

### Issue: "CSV file not found"
**Solution**: Ensure your CSV files are in the `raw_data` directory and the paths in `config/papertrader.yml` are correct.

### Issue: "No data being processed"
**Solution**: Check that your CSV files have the correct format and timestamps are in Unix epoch format.

### Issue: "Feed thread not starting"
**Solution**: Check the logs for errors. Ensure CSV files are readable and properly formatted.

## Advanced Usage

### Custom Data Processing Speed

Modify the sleep time in `papertrader.py`:

```python
# In _feed_generator_thread method
time.sleep(self.candle_interval / 10)  # Adjust divisor for speed
```

### Adding Custom Products

Edit `config/papertrader.yml`:

```yaml
products:
  - 'CUSTOMUSD':
      id: 'CUSTOM-USD'
      asset_type: 'CUSTOM'
      fund_type: 'USD'
      csv_file: 'custom_usd.csv'
```

## Contributing

To improve the PaperTrader exchange:

1. Add support for more CSV formats
2. Implement order book simulation
3. Add slippage and latency simulation
4. Support for real-time data streaming
5. Add data validation and error handling

## License

GNU General Public License v3.0 or later

See [LICENSE](../../LICENSE) for the full text.
