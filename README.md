# Oanda Forex Backtest Framework

A professional Python framework for backtesting advanced forex trading strategies using Oanda API historical data.

## Features

- **10 Advanced Trading Strategies** implemented and ready to backtest
- **Oanda API Integration** for fetching real historical forex data
- **Robust Backtesting Engine** with realistic slippage and commission modeling
- **Comprehensive Performance Metrics** (Sharpe ratio, profit factor, max drawdown, etc.)
- **Professional Visualizations** (equity curves, drawdown charts, monthly returns heatmaps)
- **Data Caching** for faster repeated backtests
- **Modular Architecture** - easily add your own strategies
- **CLI Interface** for easy execution

## Project Structure

```
oanda-backtest-framework/
├── config/
│   ├── config.yaml                 # Main configuration (API keys, backtest params)
│   └── strategies_params.yaml      # Strategy-specific parameters
├── data/
│   ├── oanda_client.py            # Oanda API client
│   └── data_manager.py            # Data fetching and caching
├── strategies/
│   ├── base_strategy.py           # Abstract base class
│   ├── mttf.py                    # Multi-Timeframe Trend Following
│   ├── mean_reversion_sr.py       # Mean Reversion on S/R
│   ├── volatility_breakout.py     # Bollinger Squeeze Breakout
│   ├── rsi_divergence.py          # RSI Divergence + Break of Structure
│   ├── range_trading.py           # Range Trading with Zones
│   ├── seasonality.py             # Seasonality + Trend Alignment
│   ├── correlation_arb.py         # Correlation Arbitrage
│   ├── breakout_retest.py         # Breakout with Retest
│   ├── carry_trade.py             # Carry Trade + Technical Filter
│   └── zscore_meanrev.py          # Z-Score Mean Reversion
├── backtesting/
│   ├── backtest_engine.py         # Main backtesting engine
│   ├── portfolio.py               # Portfolio and position management
│   └── metrics.py                 # Performance metrics and visualization
├── utils/
│   ├── indicators.py              # Technical indicators (EMA, RSI, ATR, etc.)
│   ├── helpers.py                 # Helper functions
│   └── logger.py                  # Logging configuration
├── results/                        # Output directory (created automatically)
├── main.py                         # Main entry point
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Trading_strat
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- pandas
- numpy
- requests
- pyyaml
- matplotlib
- plotly
- scipy

### 3. Configure API Credentials

Edit `config/config.yaml` and add your Oanda API credentials:

```yaml
oanda:
  api_key: "YOUR_API_KEY_HERE"
  account_id: "AUTO"  # Will auto-detect from API
  environment: "practice"  # or "live"
  base_url: "https://api-fxpractice.oanda.com"
```

**How to get Oanda API credentials:**
1. Sign up at [Oanda fxTrade Practice](https://www.oanda.com/demo-account/)
2. Go to Manage API Access
3. Generate a Personal Access Token
4. Copy the token to `config.yaml`

## Usage

### Basic Usage

Run all strategies on all configured instruments:

```bash
python main.py --strategies all
```

### Run Specific Strategies

```bash
# Single strategy
python main.py --strategies mttf

# Multiple strategies
python main.py --strategies mttf,volatility_breakout,rsi_divergence
```

### Run on Specific Instruments

```bash
python main.py --strategies all --instruments EUR_USD,GBP_USD
```

### Custom Date Range

```bash
python main.py --strategies all --start 2025-01-01 --end 2025-06-30
```

### Custom Output Directory

```bash
python main.py --strategies all --output my_backtest_results/
```

### Clear Data Cache

```bash
python main.py --strategies all --clear-cache
```

### All Options

```bash
python main.py --help
```

## Available Strategies

| Strategy | Key | Description |
|----------|-----|-------------|
| Multi-Timeframe Trend Following | `mttf` | Uses Daily/4H/1H timeframes for trend identification and entry |
| Mean Reversion S/R | `mean_reversion_sr` | Trades bounces off pivot points with pin bar confirmation |
| Volatility Breakout | `volatility_breakout` | Bollinger Band squeeze breakouts with trend filter |
| RSI Divergence | `rsi_divergence` | RSI divergence with break of structure confirmation |
| Range Trading | `range_trading` | Trades support/resistance in ranging markets |
| Seasonality | `seasonality` | Seasonal patterns aligned with technical trends |
| Correlation Arbitrage | `correlation_arb` | Pairs trading on correlated instruments |
| Breakout Retest | `breakout_retest` | Consolidation breakouts with retest confirmation |
| Carry Trade | `carry_trade` | Interest rate differential trades with trend filter |
| Z-Score Mean Reversion | `zscore_meanrev` | Statistical mean reversion using z-scores |

## Output Files

After running a backtest, the following files are generated in the output directory:

### CSV Files

- `all_trades.csv` - Every individual trade with entry/exit details
- `strategy_metrics.csv` - Performance metrics for each strategy
- `portfolio_metrics.csv` - Combined portfolio performance

### Visualizations

- `{strategy}_equity_curve.png` - Equity curve over time
- `{strategy}_drawdown.png` - Drawdown chart
- `{strategy}_monthly_returns.png` - Monthly returns heatmap
- `strategy_comparison.png` - Side-by-side strategy comparison

### Log Files

- `backtest_YYYYMMDD_HHMMSS.log` - Detailed execution log

## Performance Metrics

The framework calculates comprehensive performance metrics:

- **Total Trades** - Number of completed trades
- **Win Rate** - Percentage of winning trades
- **Profit Factor** - Gross profit / Gross loss
- **Average Win/Loss** - Mean P&L of winning/losing trades
- **Risk:Reward Ratio** - Avg win / Avg loss
- **Total Return** - Overall percentage return
- **Max Drawdown** - Largest peak-to-trough decline
- **Sharpe Ratio** - Risk-adjusted return (annualized)
- **Sortino Ratio** - Return adjusted for downside risk
- **CAGR** - Compound Annual Growth Rate
- **Max Consecutive Losses** - Longest losing streak
- **Average Trade Duration** - Mean holding period in days

## Configuration

### Main Configuration (`config/config.yaml`)

```yaml
backtest:
  start_date: "2025-01-01"
  end_date: "2025-10-25"
  initial_capital: 100000
  risk_per_trade: 0.01  # 1% risk per trade
  slippage_pips: 1
  commission_pips: 0.5
  max_positions: 1  # Per strategy

instruments:
  - EUR_USD
  - GBP_USD
  - USD_JPY
  # ... add more pairs
```

### Strategy Parameters (`config/strategies_params.yaml`)

Each strategy has customizable parameters. Example:

```yaml
mttf:
  ema_fast: 50
  ema_slow: 200
  ema_entry: 21
  rsi_period: 14
  atr_period: 14
  stop_loss_atr: 2
  take_profit_atr: 3
```

## Adding a New Strategy

1. Create a new file in `strategies/` (e.g., `my_strategy.py`)
2. Inherit from `BaseStrategy`:

```python
from strategies.base_strategy import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, params: dict):
        super().__init__("MyStrategy", params)

    def generate_signals(self, data: dict, instrument: str) -> pd.DataFrame:
        df = data['D'].copy()  # Daily timeframe

        # Your logic here
        df['signal'] = 0  # 0=no signal, 1=long, -1=short, 2=close
        df['entry_price'] = df['close']
        df['stop_loss'] = df['close'] * 0.98
        df['take_profit'] = df['close'] * 1.02

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
```

3. Add to `main.py`:

```python
from strategies.my_strategy import MyStrategy

STRATEGY_MAP = {
    # ... existing strategies
    'my_strategy': MyStrategy
}
```

4. Add parameters to `config/strategies_params.yaml`:

```yaml
my_strategy:
  name: "My Custom Strategy"
  timeframe: "D"
  # ... your parameters
```

5. Run:

```bash
python main.py --strategies my_strategy
```

## Data Caching

The framework automatically caches fetched data in `data/cache/` to avoid redundant API calls. Cache files are keyed by instrument, timeframe, and date range.

To clear cache:
```bash
python main.py --clear-cache
```

## Troubleshooting

### API Connection Issues

**Problem:** `Failed to initialize Oanda client`

**Solution:**
- Check API key in `config/config.yaml`
- Verify internet connection
- Ensure you're using the practice API URL for practice accounts

### No Data Returned

**Problem:** `No data available for EUR_USD`

**Solution:**
- Check date range (must be within available data)
- Verify instrument name format (use underscore: `EUR_USD` not `EURUSD`)
- Check Oanda API status

### Import Errors

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
pip install -r requirements.txt
```

## Performance Tips

1. **Use Data Cache** - Don't use `--clear-cache` unless necessary
2. **Test on Smaller Date Ranges** - Start with 1-2 months before running full backtests
3. **Limit Instruments** - Test on 1-2 pairs first
4. **Adjust Log Level** - Use `--log-level WARNING` for faster execution

## Limitations

- **Practice Account Only** - Configured for Oanda practice environment
- **No Live Trading** - This is a backtesting framework only
- **Historical Data** - Limited to Oanda's available historical data
- **Simplified Correlation Strategy** - Strategy 7 requires paired instrument data (simplified implementation)

## Disclaimer

**This software is for educational and research purposes only.**

- Past performance does not guarantee future results
- Trading forex involves substantial risk of loss
- Never risk money you cannot afford to lose
- Always test strategies thoroughly before live trading
- The authors are not responsible for any financial losses

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in code comments
- Review the example backtests

## Roadmap

- [ ] Live trading integration
- [ ] Portfolio optimization
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Machine learning integration
- [ ] Multi-threading for faster backtests
- [ ] Web dashboard for results visualization

---

**Happy Backtesting!**
