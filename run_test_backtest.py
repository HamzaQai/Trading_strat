"""
Run backtest with synthetic data for testing.
"""

import yaml
import pandas as pd
from pathlib import Path

from utils.logger import setup_logger
from data.synthetic_data import SyntheticDataGenerator
from backtesting.backtest_engine import BacktestEngine
from backtesting.portfolio import Portfolio

# Import strategies
from strategies.mttf import MTTFStrategy
from strategies.mean_reversion_sr import MeanReversionSRStrategy
from strategies.volatility_breakout import VolatilityBreakoutStrategy
from strategies.rsi_divergence import RSIDivergenceStrategy
from strategies.breakout_retest import BreakoutRetestStrategy
from strategies.zscore_meanrev import ZScoreMeanRevStrategy


def main():
    """Run test backtest."""
    # Setup logger
    logger = setup_logger("INFO", "results/test_backtest.log")

    logger.info("="*60)
    logger.info("OANDA BACKTEST FRAMEWORK - TEST RUN WITH SYNTHETIC DATA")
    logger.info("="*60)

    # Load strategy parameters
    with open('config/strategies_params.yaml', 'r') as f:
        strategy_params = yaml.safe_load(f)

    # Generate synthetic data
    logger.info("\n📊 Generating synthetic forex data...")
    generator = SyntheticDataGenerator(seed=42)

    instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY']
    start_date = '2024-01-01'
    end_date = '2024-12-31'

    # Simple data manager class for synthetic data
    class SyntheticDataManager:
        def __init__(self, generator):
            self.generator = generator
            self.cache = {}

        def get_data(self, instrument, granularity, start_date, end_date, use_cache=True):
            key = f"{instrument}_{granularity}_{start_date}_{end_date}"
            if key in self.cache:
                return self.cache[key]

            df = self.generator.generate_ohlcv(instrument, start_date, end_date, granularity)
            self.cache[key] = df
            return df

    data_manager = SyntheticDataManager(generator)

    # Test 6 strategies (most robust ones)
    strategies_to_test = [
        ('volatility_breakout', VolatilityBreakoutStrategy),
        ('mean_reversion_sr', MeanReversionSRStrategy),
        ('zscore_meanrev', ZScoreMeanRevStrategy),
        ('rsi_divergence', RSIDivergenceStrategy),
        ('breakout_retest', BreakoutRetestStrategy),
        ('mttf', MTTFStrategy)
    ]

    strategies = []
    for strat_key, strat_class in strategies_to_test:
        params = strategy_params.get(strat_key, {})
        strategy = strat_class(params)
        strategies.append(strategy)

    logger.info(f"✓ Testing {len(strategies)} strategies on {len(instruments)} instruments")
    logger.info(f"  Period: {start_date} to {end_date}")
    logger.info(f"  Strategies: {', '.join([s.name for s in strategies])}")

    # Initialize backtest engine
    engine = BacktestEngine(
        data_manager=data_manager,
        initial_capital=100000,
        risk_per_trade=0.01,
        slippage_pips=1,
        commission_pips=0.5,
        max_positions=1
    )

    # Run backtests
    logger.info("\n🚀 Running backtests...\n")

    results = engine.run_multiple_strategies(
        strategies=strategies,
        instruments=instruments,
        start_date=start_date,
        end_date=end_date,
        output_dir="results/test_run"
    )

    # Print detailed summary
    logger.info("\n" + "="*80)
    logger.info("📈 BACKTEST RESULTS SUMMARY")
    logger.info("="*80)

    summary_data = []
    for strategy_name, result in results.items():
        metrics = result['metrics']

        logger.info(f"\n{'─'*80}")
        logger.info(f"Strategy: {strategy_name}")
        logger.info(f"{'─'*80}")
        logger.info(f"  Total Trades:        {metrics['total_trades']}")
        logger.info(f"  Winning Trades:      {metrics['winning_trades']}")
        logger.info(f"  Losing Trades:       {metrics['losing_trades']}")
        logger.info(f"  Win Rate:            {metrics['win_rate']:.2f}%")
        logger.info(f"  Profit Factor:       {metrics['profit_factor']:.2f}")
        logger.info(f"  Total Return:        {metrics['total_return_pct']:.2f}%")
        logger.info(f"  Total P&L:           ${metrics['total_pnl']:,.2f}")
        logger.info(f"  Max Drawdown:        {metrics['max_drawdown_pct']:.2f}% (${metrics['max_drawdown']:,.2f})")
        logger.info(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Sortino Ratio:       {metrics['sortino_ratio']:.2f}")
        logger.info(f"  Average Win:         ${metrics['avg_win']:,.2f}")
        logger.info(f"  Average Loss:        ${metrics['avg_loss']:,.2f}")
        logger.info(f"  Risk/Reward Ratio:   {metrics['risk_reward_ratio']:.2f}")
        logger.info(f"  CAGR:                {metrics['cagr']:.2f}%")
        logger.info(f"  Max Consecutive Loss:{metrics['max_consecutive_losses']}")

        summary_data.append({
            'Strategy': strategy_name,
            'Trades': metrics['total_trades'],
            'Win Rate %': f"{metrics['win_rate']:.1f}",
            'Profit Factor': f"{metrics['profit_factor']:.2f}",
            'Return %': f"{metrics['total_return_pct']:.2f}",
            'Max DD %': f"{metrics['max_drawdown_pct']:.2f}",
            'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
            'CAGR %': f"{metrics['cagr']:.2f}"
        })

    # Create summary table
    logger.info("\n" + "="*80)
    logger.info("📊 COMPARISON TABLE")
    logger.info("="*80 + "\n")

    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))

    # Save summary
    summary_df.to_csv("results/test_run/summary_table.csv", index=False)

    logger.info("\n" + "="*80)
    logger.info("✅ BACKTEST COMPLETE")
    logger.info("="*80)
    logger.info(f"\n📁 All results saved to: results/test_run/")
    logger.info("   - summary_table.csv")
    logger.info("   - all_trades.csv")
    logger.info("   - strategy_metrics.csv")
    logger.info("   - portfolio_metrics.csv")
    logger.info("   - equity_curve.png (per strategy)")
    logger.info("   - drawdown.png (per strategy)")
    logger.info("   - strategy_comparison.png")

    return results


if __name__ == "__main__":
    main()
