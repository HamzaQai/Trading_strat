"""
Backtest engine for running trading strategies.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import logging
from pathlib import Path

from backtesting.portfolio import Portfolio
from backtesting.metrics import MetricsCalculator
from strategies.base_strategy import BaseStrategy
from data.data_manager import DataManager


class BacktestEngine:
    """Main backtesting engine."""

    def __init__(
        self,
        data_manager: DataManager,
        initial_capital: float = 100000,
        risk_per_trade: float = 0.01,
        slippage_pips: float = 1,
        commission_pips: float = 0.5,
        max_positions: int = 1
    ):
        """
        Initialize backtest engine.

        Args:
            data_manager: DataManager instance
            initial_capital: Starting capital
            risk_per_trade: Risk per trade (fraction)
            slippage_pips: Slippage in pips
            commission_pips: Commission in pips
            max_positions: Max concurrent positions per strategy
        """
        self.data_manager = data_manager
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.slippage_pips = slippage_pips
        self.commission_pips = commission_pips
        self.max_positions = max_positions

        self.logger = logging.getLogger(__name__)

    def run_backtest(
        self,
        strategy: BaseStrategy,
        instruments: List[str],
        start_date: str,
        end_date: str,
        timeframes: List[str] = None
    ) -> Dict:
        """
        Run backtest for a strategy on given instruments.

        Args:
            strategy: Strategy instance
            instruments: List of instruments to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframes: List of timeframes needed

        Returns:
            Dictionary with results
        """
        self.logger.info(f"Running backtest: {strategy.name}")
        self.logger.info(f"Instruments: {instruments}")
        self.logger.info(f"Period: {start_date} to {end_date}")

        # Initialize portfolio
        portfolio = Portfolio(
            initial_capital=self.initial_capital,
            risk_per_trade=self.risk_per_trade,
            slippage_pips=self.slippage_pips,
            commission_pips=self.commission_pips,
            max_positions=self.max_positions
        )

        # Default timeframes if not provided
        if timeframes is None:
            timeframes = ['D']

        all_trades = []

        # Run backtest for each instrument
        for instrument in instruments:
            self.logger.info(f"Processing {instrument}...")

            try:
                # Fetch data for all timeframes
                data = {}
                for tf in timeframes:
                    df = self.data_manager.get_data(instrument, tf, start_date, end_date)
                    if not df.empty:
                        data[tf] = df

                if not data:
                    self.logger.warning(f"No data available for {instrument}")
                    continue

                # Generate signals
                signals_df = strategy.generate_signals(data, instrument)

                if signals_df.empty:
                    self.logger.warning(f"No signals generated for {instrument}")
                    continue

                # Execute trades based on signals
                self._execute_signals(
                    portfolio=portfolio,
                    signals_df=signals_df,
                    data=data,
                    instrument=instrument,
                    strategy_name=strategy.name
                )

            except Exception as e:
                self.logger.error(f"Error processing {instrument}: {e}", exc_info=True)
                continue

        # Calculate metrics
        trades_df = portfolio.get_trades_df()
        equity_curve = portfolio.get_equity_curve()

        metrics_calc = MetricsCalculator(trades_df, equity_curve, self.initial_capital)
        metrics = metrics_calc.calculate_metrics()

        self.logger.info(f"Backtest completed: {strategy.name}")
        self.logger.info(f"Total trades: {metrics['total_trades']}")
        self.logger.info(f"Win rate: {metrics['win_rate']:.2f}%")
        self.logger.info(f"Total return: {metrics['total_return_pct']:.2f}%")

        return {
            'strategy_name': strategy.name,
            'metrics': metrics,
            'trades': trades_df,
            'equity_curve': equity_curve,
            'portfolio': portfolio
        }

    def _execute_signals(
        self,
        portfolio: Portfolio,
        signals_df: pd.DataFrame,
        data: Dict[str, pd.DataFrame],
        instrument: str,
        strategy_name: str
    ):
        """
        Execute trades based on signals.

        Args:
            portfolio: Portfolio instance
            signals_df: DataFrame with signals
            data: Market data
            instrument: Instrument name
            strategy_name: Strategy name
        """
        # Get primary timeframe data for price updates
        primary_tf = list(data.keys())[0]
        price_data = data[primary_tf]

        # Merge signals with price data
        combined = price_data.join(signals_df, how='left', rsuffix='_signal')

        # Fill NaN signals with 0
        if 'signal' not in combined.columns:
            return

        combined['signal'].fillna(0, inplace=True)

        current_position = None
        position_key = f"{strategy_name}_{instrument}"

        for timestamp, row in combined.iterrows():
            signal = row.get('signal', 0)

            # Update portfolio with current prices
            prices = {
                instrument: {
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close']
                }
            }

            portfolio.update_positions(timestamp, prices)

            # Record equity
            portfolio.record_equity(timestamp)

            # Check if position exists
            if position_key in portfolio.open_positions:
                current_position = portfolio.open_positions[position_key].direction
            else:
                current_position = None

            # Handle signals
            if signal == 1 and current_position is None:
                # Open long
                entry_price = row.get('entry_price', row['close'])
                stop_loss = row.get('stop_loss', entry_price * 0.98)
                take_profit = row.get('take_profit', entry_price * 1.02)

                portfolio.open_position(
                    timestamp=timestamp,
                    instrument=instrument,
                    direction='long',
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy=strategy_name
                )

            elif signal == -1 and current_position is None:
                # Open short
                entry_price = row.get('entry_price', row['close'])
                stop_loss = row.get('stop_loss', entry_price * 1.02)
                take_profit = row.get('take_profit', entry_price * 0.98)

                portfolio.open_position(
                    timestamp=timestamp,
                    instrument=instrument,
                    direction='short',
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy=strategy_name
                )

            elif signal == 2 and current_position is not None:
                # Close position
                portfolio.close_position(
                    timestamp=timestamp,
                    instrument=instrument,
                    exit_price=row['close'],
                    strategy=strategy_name,
                    reason='signal_exit'
                )

    def run_multiple_strategies(
        self,
        strategies: List[BaseStrategy],
        instruments: List[str],
        start_date: str,
        end_date: str,
        output_dir: str = "results"
    ) -> Dict:
        """
        Run backtest for multiple strategies.

        Args:
            strategies: List of strategy instances
            instruments: List of instruments
            start_date: Start date
            end_date: End date
            output_dir: Output directory for results

        Returns:
            Dictionary with all results
        """
        results = {}
        all_metrics = {}

        for strategy in strategies:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Starting backtest: {strategy.name}")
            self.logger.info(f"{'='*60}\n")

            # Determine required timeframes for this strategy
            timeframes = self._get_strategy_timeframes(strategy)

            # Run backtest
            result = self.run_backtest(
                strategy=strategy,
                instruments=instruments,
                start_date=start_date,
                end_date=end_date,
                timeframes=timeframes
            )

            results[strategy.name] = result
            all_metrics[strategy.name] = result['metrics']

        # Save results
        self._save_results(results, all_metrics, output_dir)

        return results

    def _get_strategy_timeframes(self, strategy: BaseStrategy) -> List[str]:
        """Get required timeframes for a strategy."""
        # Check strategy params for timeframe requirements
        if 'timeframes' in strategy.params:
            tf_dict = strategy.params['timeframes']
            if isinstance(tf_dict, dict):
                return list(tf_dict.values())
            else:
                return [tf_dict]
        elif 'timeframe' in strategy.params:
            return [strategy.params['timeframe']]
        else:
            return ['D']  # Default to daily

    def _save_results(self, results: Dict, all_metrics: Dict, output_dir: str):
        """Save backtest results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save all trades
        all_trades_list = []
        for strategy_name, result in results.items():
            if not result['trades'].empty:
                all_trades_list.append(result['trades'])

        if all_trades_list:
            all_trades = pd.concat(all_trades_list, ignore_index=True)
            trades_file = output_path / "all_trades.csv"
            all_trades.to_csv(trades_file, index=False)
            self.logger.info(f"Saved all trades to {trades_file}")

        # Save strategy metrics
        metrics_df = pd.DataFrame(all_metrics).T
        metrics_file = output_path / "strategy_metrics.csv"
        metrics_df.to_csv(metrics_file)
        self.logger.info(f"Saved strategy metrics to {metrics_file}")

        # Calculate portfolio-level metrics (combined)
        combined_equity = []
        for strategy_name, result in results.items():
            if not result['equity_curve'].empty:
                equity = result['equity_curve'].copy()
                equity['strategy'] = strategy_name
                combined_equity.append(equity)

        if combined_equity:
            combined_equity_df = pd.concat(combined_equity, ignore_index=True)

            # Aggregate equity by time
            portfolio_equity = combined_equity_df.groupby('time')['equity'].sum().reset_index()

            # Calculate portfolio metrics
            all_trades_combined = pd.concat(all_trades_list, ignore_index=True) if all_trades_list else pd.DataFrame()

            portfolio_metrics_calc = MetricsCalculator(
                all_trades_combined,
                portfolio_equity,
                self.initial_capital * len(results)  # Total capital across strategies
            )

            portfolio_metrics = portfolio_metrics_calc.calculate_metrics()
            portfolio_metrics_df = pd.DataFrame([portfolio_metrics])
            portfolio_file = output_path / "portfolio_metrics.csv"
            portfolio_metrics_df.to_csv(portfolio_file, index=False)
            self.logger.info(f"Saved portfolio metrics to {portfolio_file}")

        # Generate visualizations
        for strategy_name, result in results.items():
            if not result['equity_curve'].empty:
                metrics_calc = MetricsCalculator(
                    result['trades'],
                    result['equity_curve'],
                    self.initial_capital
                )

                # Generate plots
                metrics_calc.plot_equity_curve(
                    output_path / f"{strategy_name}_equity_curve.png"
                )
                metrics_calc.plot_drawdown(
                    output_path / f"{strategy_name}_drawdown.png"
                )
                metrics_calc.plot_monthly_returns(
                    output_path / f"{strategy_name}_monthly_returns.png"
                )

        # Strategy comparison plot
        if all_metrics:
            metrics_calc = MetricsCalculator(
                pd.DataFrame(),
                pd.DataFrame(),
                self.initial_capital
            )
            metrics_calc.plot_strategy_comparison(
                all_metrics,
                output_path / "strategy_comparison.png"
            )

        self.logger.info(f"\nAll results saved to {output_dir}/")
