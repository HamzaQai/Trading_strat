"""
Main script to run backtests.
"""

import argparse
import yaml
from pathlib import Path
import sys

from utils.logger import setup_logger
from data.oanda_client import OandaClient
from data.data_manager import DataManager
from backtesting.backtest_engine import BacktestEngine

# Import all strategies
from strategies.mttf import MTTFStrategy
from strategies.mean_reversion_sr import MeanReversionSRStrategy
from strategies.volatility_breakout import VolatilityBreakoutStrategy
from strategies.rsi_divergence import RSIDivergenceStrategy
from strategies.range_trading import RangeTradingStrategy
from strategies.seasonality import SeasonalityStrategy
from strategies.correlation_arb import CorrelationArbStrategy
from strategies.breakout_retest import BreakoutRetestStrategy
from strategies.carry_trade import CarryTradeStrategy
from strategies.zscore_meanrev import ZScoreMeanRevStrategy


# Strategy mapping
STRATEGY_MAP = {
    'mttf': MTTFStrategy,
    'mean_reversion_sr': MeanReversionSRStrategy,
    'volatility_breakout': VolatilityBreakoutStrategy,
    'rsi_divergence': RSIDivergenceStrategy,
    'range_trading': RangeTradingStrategy,
    'seasonality': SeasonalityStrategy,
    'correlation_arb': CorrelationArbStrategy,
    'breakout_retest': BreakoutRetestStrategy,
    'carry_trade': CarryTradeStrategy,
    'zscore_meanrev': ZScoreMeanRevStrategy
}


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_strategy_params(params_path: str = "config/strategies_params.yaml") -> dict:
    """Load strategy parameters from YAML file."""
    with open(params_path, 'r') as f:
        return yaml.safe_load(f)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Oanda Forex Backtest Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all strategies on all instruments
  python main.py --strategies all

  # Run specific strategies
  python main.py --strategies mttf,volatility_breakout

  # Run on specific instruments
  python main.py --strategies all --instruments EUR_USD,GBP_USD

  # Custom date range
  python main.py --strategies all --start 2025-01-01 --end 2025-06-30

  # Custom output directory
  python main.py --strategies all --output my_results/
        """
    )

    parser.add_argument(
        '--strategies',
        type=str,
        default='all',
        help='Comma-separated list of strategies or "all" (default: all)'
    )

    parser.add_argument(
        '--instruments',
        type=str,
        default=None,
        help='Comma-separated list of instruments (default: from config)'
    )

    parser.add_argument(
        '--start',
        type=str,
        default=None,
        help='Start date YYYY-MM-DD (default: from config)'
    )

    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='End date YYYY-MM-DD (default: from config)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='results',
        help='Output directory (default: results/)'
    )

    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear data cache before running'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to config file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default=None,
        help='Log level: DEBUG, INFO, WARNING, ERROR (default: from config)'
    )

    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    try:
        config = load_config(args.config)
        strategy_params = load_strategy_params()
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration: {e}")
        sys.exit(1)

    # Setup logging
    log_level = args.log_level or config['logging']['level']
    log_file = config['logging']['file']
    logger = setup_logger(log_level, log_file)

    logger.info("="*60)
    logger.info("Oanda Forex Backtest Framework")
    logger.info("="*60)

    # Initialize Oanda client
    try:
        oanda_config = config['oanda']
        oanda_client = OandaClient(
            api_key=oanda_config['api_key'],
            account_id=oanda_config.get('account_id', 'AUTO'),
            environment=oanda_config.get('environment', 'practice')
        )
    except Exception as e:
        logger.error(f"Failed to initialize Oanda client: {e}")
        sys.exit(1)

    # Initialize data manager
    data_manager = DataManager(oanda_client)

    # Clear cache if requested
    if args.clear_cache:
        logger.info("Clearing data cache...")
        data_manager.clear_cache()

    # Get instruments
    if args.instruments:
        instruments = [i.strip() for i in args.instruments.split(',')]
    else:
        instruments = config['instruments']

    logger.info(f"Instruments: {', '.join(instruments)}")

    # Get date range
    start_date = args.start or config['backtest']['start_date']
    end_date = args.end or config['backtest']['end_date']

    logger.info(f"Date range: {start_date} to {end_date}")

    # Get strategies to run
    if args.strategies.lower() == 'all':
        strategy_names = list(STRATEGY_MAP.keys())
    else:
        strategy_names = [s.strip() for s in args.strategies.split(',')]

    # Validate strategy names
    invalid_strategies = [s for s in strategy_names if s not in STRATEGY_MAP]
    if invalid_strategies:
        logger.error(f"Invalid strategy names: {', '.join(invalid_strategies)}")
        logger.error(f"Available strategies: {', '.join(STRATEGY_MAP.keys())}")
        sys.exit(1)

    logger.info(f"Strategies: {', '.join(strategy_names)}")

    # Initialize strategies
    strategies = []
    for strategy_name in strategy_names:
        strategy_class = STRATEGY_MAP[strategy_name]
        params = strategy_params.get(strategy_name, {})
        strategy = strategy_class(params)
        strategies.append(strategy)
        logger.info(f"  - {strategy.name}")

    # Initialize backtest engine
    backtest_config = config['backtest']
    engine = BacktestEngine(
        data_manager=data_manager,
        initial_capital=backtest_config['initial_capital'],
        risk_per_trade=backtest_config['risk_per_trade'],
        slippage_pips=backtest_config['slippage_pips'],
        commission_pips=backtest_config['commission_pips'],
        max_positions=backtest_config['max_positions']
    )

    # Run backtests
    logger.info("\n" + "="*60)
    logger.info("Starting backtests...")
    logger.info("="*60 + "\n")

    try:
        results = engine.run_multiple_strategies(
            strategies=strategies,
            instruments=instruments,
            start_date=start_date,
            end_date=end_date,
            output_dir=args.output
        )

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("BACKTEST SUMMARY")
        logger.info("="*60)

        for strategy_name, result in results.items():
            metrics = result['metrics']
            logger.info(f"\n{strategy_name}:")
            logger.info(f"  Total Trades: {metrics['total_trades']}")
            logger.info(f"  Win Rate: {metrics['win_rate']:.2f}%")
            logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
            logger.info(f"  Total Return: {metrics['total_return_pct']:.2f}%")
            logger.info(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
            logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        logger.info("\n" + "="*60)
        logger.info(f"Results saved to: {args.output}/")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
