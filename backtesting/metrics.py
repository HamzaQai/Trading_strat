"""
Performance metrics calculator for backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from pathlib import Path


class MetricsCalculator:
    """Calculate and visualize backtest performance metrics."""

    def __init__(self, trades_df: pd.DataFrame, equity_curve: pd.DataFrame, initial_capital: float):
        """
        Initialize metrics calculator.

        Args:
            trades_df: DataFrame of all trades
            equity_curve: DataFrame with equity over time
            initial_capital: Initial capital
        """
        self.trades_df = trades_df
        self.equity_curve = equity_curve
        self.initial_capital = initial_capital

    def calculate_metrics(self) -> Dict:
        """
        Calculate comprehensive performance metrics.

        Returns:
            Dictionary of metrics
        """
        if self.trades_df.empty:
            return self._empty_metrics()

        # Filter closed trades only
        closed_trades = self.trades_df[self.trades_df['status'] != 'open'].copy()

        if closed_trades.empty:
            return self._empty_metrics()

        # Basic stats
        total_trades = len(closed_trades)
        winning_trades = closed_trades[closed_trades['pnl'] > 0]
        losing_trades = closed_trades[closed_trades['pnl'] < 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)

        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

        # P&L stats
        total_pnl = closed_trades['pnl'].sum()
        avg_pnl = closed_trades['pnl'].mean()

        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0

        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0

        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        largest_win = winning_trades['pnl'].max() if not winning_trades.empty else 0
        largest_loss = losing_trades['pnl'].min() if not losing_trades.empty else 0

        # Returns
        final_capital = self.equity_curve['equity'].iloc[-1] if not self.equity_curve.empty else self.initial_capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # Drawdown
        max_drawdown, max_drawdown_pct = self._calculate_drawdown()

        # Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio()

        # Sortino ratio
        sortino_ratio = self._calculate_sortino_ratio()

        # CAGR
        cagr = self._calculate_cagr()

        # Consecutive losses
        max_consecutive_losses = self._calculate_max_consecutive_losses(closed_trades)

        # Average trade duration
        avg_trade_duration = self._calculate_avg_trade_duration(closed_trades)

        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': avg_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': risk_reward_ratio,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return_pct': total_return,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'cagr': cagr,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_trade_duration_days': avg_trade_duration
        }

    def _empty_metrics(self) -> Dict:
        """Return metrics structure with zeros for empty results."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl_per_trade': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'risk_reward_ratio': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'initial_capital': self.initial_capital,
            'final_capital': self.initial_capital,
            'total_return_pct': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'cagr': 0,
            'max_consecutive_losses': 0,
            'avg_trade_duration_days': 0
        }

    def _calculate_drawdown(self) -> tuple:
        """Calculate maximum drawdown."""
        if self.equity_curve.empty:
            return 0, 0

        equity = self.equity_curve['equity'].values
        running_max = np.maximum.accumulate(equity)
        drawdown = running_max - equity
        drawdown_pct = (drawdown / running_max) * 100

        max_dd = drawdown.max()
        max_dd_pct = drawdown_pct.max()

        return max_dd, max_dd_pct

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio."""
        if self.equity_curve.empty or len(self.equity_curve) < 2:
            return 0

        # Calculate daily returns
        equity = self.equity_curve['equity'].values
        returns = np.diff(equity) / equity[:-1]

        if len(returns) == 0 or returns.std() == 0:
            return 0

        # Annualize
        avg_return = returns.mean() * 252  # Assuming daily data
        std_return = returns.std() * np.sqrt(252)

        sharpe = (avg_return - risk_free_rate) / std_return

        return sharpe

    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sortino ratio."""
        if self.equity_curve.empty or len(self.equity_curve) < 2:
            return 0

        equity = self.equity_curve['equity'].values
        returns = np.diff(equity) / equity[:-1]

        if len(returns) == 0:
            return 0

        # Only downside deviation
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 0

        avg_return = returns.mean() * 252
        downside_std = downside_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return 0

        sortino = (avg_return - risk_free_rate) / downside_std

        return sortino

    def _calculate_cagr(self) -> float:
        """Calculate Compound Annual Growth Rate."""
        if self.equity_curve.empty:
            return 0

        final_value = self.equity_curve['equity'].iloc[-1]
        initial_value = self.initial_capital

        # Calculate number of years
        start_date = self.equity_curve['time'].iloc[0]
        end_date = self.equity_curve['time'].iloc[-1]
        years = (end_date - start_date).days / 365.25

        if years == 0:
            return 0

        cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100

        return cagr

    def _calculate_max_consecutive_losses(self, trades_df: pd.DataFrame) -> int:
        """Calculate maximum consecutive losing trades."""
        if trades_df.empty:
            return 0

        trades_df = trades_df.sort_values('exit_time')
        is_loss = (trades_df['pnl'] < 0).astype(int)

        max_consecutive = 0
        current_consecutive = 0

        for loss in is_loss:
            if loss:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_avg_trade_duration(self, trades_df: pd.DataFrame) -> float:
        """Calculate average trade duration in days."""
        if trades_df.empty:
            return 0

        trades_with_exit = trades_df[trades_df['exit_time'].notna()].copy()

        if trades_with_exit.empty:
            return 0

        trades_with_exit['duration'] = (trades_with_exit['exit_time'] - trades_with_exit['entry_time']).dt.total_seconds() / 86400

        return trades_with_exit['duration'].mean()

    def plot_equity_curve(self, output_path: str = "results/equity_curve.png"):
        """
        Plot equity curve.

        Args:
            output_path: Output file path
        """
        if self.equity_curve.empty:
            print("No equity data to plot")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(self.equity_curve['time'], self.equity_curve['equity'], linewidth=2)
        plt.axhline(y=self.initial_capital, color='r', linestyle='--', label='Initial Capital')
        plt.title('Equity Curve', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Equity ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Equity curve saved to {output_path}")

    def plot_drawdown(self, output_path: str = "results/drawdown.png"):
        """
        Plot drawdown chart.

        Args:
            output_path: Output file path
        """
        if self.equity_curve.empty:
            print("No equity data to plot")
            return

        equity = self.equity_curve['equity'].values
        running_max = np.maximum.accumulate(equity)
        drawdown_pct = ((running_max - equity) / running_max) * 100

        plt.figure(figsize=(12, 6))
        plt.fill_between(self.equity_curve['time'], drawdown_pct, 0, alpha=0.3, color='red')
        plt.plot(self.equity_curve['time'], drawdown_pct, color='red', linewidth=2)
        plt.title('Drawdown', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Drawdown chart saved to {output_path}")

    def plot_monthly_returns(self, output_path: str = "results/monthly_returns_heatmap.png"):
        """
        Plot monthly returns heatmap.

        Args:
            output_path: Output file path
        """
        if self.trades_df.empty:
            print("No trades data to plot")
            return

        closed_trades = self.trades_df[self.trades_df['status'] != 'open'].copy()

        if closed_trades.empty:
            print("No closed trades to plot")
            return

        # Extract month and year
        closed_trades['year'] = pd.to_datetime(closed_trades['exit_time']).dt.year
        closed_trades['month'] = pd.to_datetime(closed_trades['exit_time']).dt.month

        # Aggregate by month
        monthly_pnl = closed_trades.groupby(['year', 'month'])['pnl'].sum().reset_index()

        # Pivot table
        pivot = monthly_pnl.pivot(index='year', columns='month', values='pnl')

        # Plot heatmap
        plt.figure(figsize=(14, 6))
        sns.heatmap(pivot, annot=True, fmt='.0f', cmap='RdYlGn', center=0, cbar_kws={'label': 'P&L ($)'})
        plt.title('Monthly Returns Heatmap', fontsize=16, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Year', fontsize=12)
        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Monthly returns heatmap saved to {output_path}")

    def plot_strategy_comparison(self, metrics_by_strategy: Dict, output_path: str = "results/strategy_comparison.png"):
        """
        Plot strategy comparison charts.

        Args:
            metrics_by_strategy: Dictionary of metrics by strategy name
            output_path: Output file path
        """
        if not metrics_by_strategy:
            print("No strategy metrics to plot")
            return

        strategies = list(metrics_by_strategy.keys())
        win_rates = [metrics_by_strategy[s]['win_rate'] for s in strategies]
        profit_factors = [metrics_by_strategy[s]['profit_factor'] for s in strategies]
        total_returns = [metrics_by_strategy[s]['total_return_pct'] for s in strategies]

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Win Rate
        axes[0].bar(strategies, win_rates, color='skyblue')
        axes[0].set_title('Win Rate by Strategy', fontweight='bold')
        axes[0].set_ylabel('Win Rate (%)')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(True, alpha=0.3)

        # Profit Factor
        axes[1].bar(strategies, profit_factors, color='lightgreen')
        axes[1].set_title('Profit Factor by Strategy', fontweight='bold')
        axes[1].set_ylabel('Profit Factor')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3)

        # Total Return
        axes[2].bar(strategies, total_returns, color='coral')
        axes[2].set_title('Total Return by Strategy', fontweight='bold')
        axes[2].set_ylabel('Return (%)')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Strategy comparison saved to {output_path}")
