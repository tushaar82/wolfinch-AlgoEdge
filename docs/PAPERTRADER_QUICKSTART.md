# PaperTrader Exchange - Quick Start Guide

This guide will help you get started with the PaperTrader exchange in Wolfinch.

## What is PaperTrader?

PaperTrader is a CSV-based exchange simulator that allows you to:
- Test trading strategies with historical data
- Paper trade without connecting to real exchanges
- Backtest strategies using your own data
- Learn Wolfinch without risking real money

## Quick Start (5 minutes)

### Step 1: Prepare Sample Data

The `raw_data` directory is gitignored for your actual trading data. Copy the sample data there:

```bash
# Create raw_data directory (gitignored)
mkdir -p raw_data

# Copy sample CSV files from raw_data_sample
cp raw_data_sample/btc_usd.csv raw_data/
cp raw_data_sample/eth_usd.csv raw_data/
```

Or generate more comprehensive data:

```bash
cd raw_data_sample
python3 generate_sample_data.py
cp *.csv ../raw_data/
cd ..
```

### Step 2: Run Wolfinch with PaperTrader

```bash
./Wolfinch.py --config config/wolfinch_papertrader_btc.yml
```

### Step 3: Access the UI

Open your browser and go to:
```
http://localhost:8080
```

You should see the Wolfinch UI with your paper trading session running!

## What's Happening?

1. **Data Loading**: PaperTrader loads CSV files from `raw_data/`
2. **Feed Generation**: A background thread simulates market data feeds
3. **Strategy Execution**: The EMA_RSI strategy analyzes the data
4. **Order Simulation**: Buy/sell orders are executed instantly at market price
5. **Performance Tracking**: Results are displayed in the UI

## File Structure

```
wolfinch/
├── exchanges/
│   └── papertrader/
│       ├── __init__.py
│       ├── papertrader.py          # Main exchange implementation
│       └── README.md                # Detailed documentation
├── config/
│   ├── papertrader.yml              # Exchange configuration
│   └── wolfinch_papertrader_btc.yml # Wolfinch configuration
├── raw_data/                        # Your CSV data files (GITIGNORED - create this!)
│   ├── btc_usd.csv                  # Copy from raw_data_sample or add your own
│   └── eth_usd.csv
└── raw_data_sample/                 # Sample data and tools (committed to git)
    ├── README.md
    ├── btc_usd.csv                  # Sample data
    ├── eth_usd.csv                  # Sample data
    └── generate_sample_data.py      # Data generation script
```

**Note**: The `raw_data/` directory is gitignored so your actual trading data stays private. Always copy or generate files into `raw_data/`, not `raw_data_sample/`.

## CSV Data Format

### OHLC Format (Recommended)
```csv
timestamp,open,high,low,close,volume
1609459200,29000.00,29500.00,28800.00,29200.00,150.5
1609459500,29200.00,29600.00,29100.00,29400.00,200.3
```

### Simple Format
```csv
timestamp,price,volume
1609459200,29000.00,150.5
1609459500,29200.00,200.3
```

**Important**: Timestamps must be Unix epoch time (seconds since Jan 1, 1970)

## Configuration

### Exchange Config (`config/papertrader.yml`)

```yaml
exchange:
  raw_data_dir: 'raw_data'        # Where CSV files are stored
  initial_fund: 10000.0           # Starting USD balance
  initial_asset: 0.0              # Starting crypto balance
  
  products:
    - 'BTCUSD':
        id: 'BTC-USD'
        asset_type: 'BTC'
        fund_type: 'USD'
        csv_file: 'btc_usd.csv'   # CSV file to use
```

### Strategy Config (`config/wolfinch_papertrader_btc.yml`)

Key settings:
- `candle_interval: 300` - 5-minute candles
- `fund_max_liquidity: 9000` - Max $9000 to trade
- `fund_max_per_buy_value: 100` - Max $100 per order
- `strategy: EMA_RSI` - Trading strategy to use

## Common Use Cases

### 1. Test a New Strategy

Edit the strategy in `config/wolfinch_papertrader_btc.yml`:

```yaml
decision:
  model: simple
  config:
    strategy: TRABOS  # Change to your strategy
    params: {...}     # Strategy parameters
```

### 2. Use Your Own Data

1. Export data from your exchange to CSV format
2. Place CSV files in `raw_data/` directory (gitignored)
3. Update `config/papertrader.yml` with your filenames
4. Run Wolfinch

**Important**: Always put your actual data in `raw_data/`, not `raw_data_sample/`. The `raw_data/` directory is gitignored to keep your data private.

### 3. Backtest Multiple Timeframes

Generate data with different intervals:

```python
# 1-minute candles
generate_ohlc_data('btc_1m.csv', interval=60, num_candles=10000)

# 15-minute candles
generate_ohlc_data('btc_15m.csv', interval=900, num_candles=5000)
```

Update `candle_interval` in config to match.

### 4. Compare Strategies

Run multiple instances with different configs:

```bash
# Terminal 1
./Wolfinch.py --config config/wolfinch_papertrader_ema.yml

# Terminal 2
./Wolfinch.py --config config/wolfinch_papertrader_rsi.yml
```

## Generating Custom Data

### Random Walk Data
```python
from raw_data_sample.generate_sample_data import generate_ohlc_data

generate_ohlc_data(
    'my_random_data.csv',
    start_price=30000.0,
    num_candles=2000,
    interval=300
)
```

### Trending Data
```python
from raw_data_sample.generate_sample_data import generate_trending_data

generate_trending_data(
    'my_uptrend.csv',
    start_price=30000.0,
    num_candles=2000,
    trend='up',
    trend_strength=0.0005
)
```

## Troubleshooting

### "CSV file not found"
- Check that `raw_data/` directory exists
- Verify CSV filename matches config
- Use absolute paths if needed

### "No trades happening"
- Check strategy parameters
- Verify CSV data has enough rows
- Look at logs for strategy signals

### "Feed thread not starting"
- Check CSV format is correct
- Ensure timestamps are valid Unix epoch
- Check file permissions

## Next Steps

1. **Read the docs**: Check `exchanges/papertrader/README.md` for detailed info
2. **Try different strategies**: Explore `strategy/strategies/` directory
3. **Customize indicators**: Modify strategy parameters in config
4. **Export real data**: Get historical data from exchanges
5. **Optimize parameters**: Use genetic optimizer with your data

## Tips & Best Practices

✅ **Do:**
- Start with small datasets to test
- Use realistic price movements
- Sort CSV data by timestamp
- Keep backups of your data
- Test strategies before live trading

❌ **Don't:**
- Use unsorted CSV data
- Mix different timeframes in one file
- Forget to set realistic initial balances
- Skip data validation
- Trade live without paper trading first

## Getting Help

- Check logs in the console for errors
- Review `exchanges/papertrader/README.md` for details
- Examine sample CSV files in `raw_data_sample/`
- Test with provided sample data first

## Example Session

```bash
# 1. Setup
mkdir raw_data
cp raw_data_sample/btc_usd.csv raw_data/

# 2. Run
./Wolfinch.py --config config/wolfinch_papertrader_btc.yml

# 3. Watch the output
# You should see:
# - "Init PaperTrader exchange"
# - "Loaded X rows from raw_data/btc_usd.csv"
# - "Starting feed generator thread"
# - Strategy signals and trades

# 4. Open UI
# Browser: http://localhost:8080
```

## Advanced Features

- **Multiple products**: Trade BTC and ETH simultaneously
- **Custom intervals**: Use any candle interval
- **Strategy chaining**: Combine multiple strategies
- **ML models**: Use machine learning decision engines
- **Genetic optimization**: Auto-tune strategy parameters

Happy paper trading! 🚀
