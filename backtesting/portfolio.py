"""
Portfolio manager for backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class Trade:
    """Represents a single trade."""
    entry_time: datetime
    exit_time: Optional[datetime]
    instrument: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    position_size: float  # in lots
    pnl: Optional[float] = None
    pnl_pips: Optional[float] = None
    status: str = 'open'  # 'open', 'closed', 'stopped', 'tp_hit'
    strategy: str = ''


class Portfolio:
    """Manages portfolio state during backtesting."""

    def __init__(
        self,
        initial_capital: float,
        risk_per_trade: float = 0.01,
        slippage_pips: float = 1,
        commission_pips: float = 0.5,
        max_positions: int = 1
    ):
        """
        Initialize portfolio.

        Args:
            initial_capital: Starting capital
            risk_per_trade: Risk per trade as fraction (0.01 = 1%)
            slippage_pips: Slippage in pips
            commission_pips: Commission in pips (round-trip)
            max_positions: Maximum concurrent positions per strategy
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.slippage_pips = slippage_pips
        self.commission_pips = commission_pips
        self.max_positions = max_positions

        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}  # key: (strategy, instrument)
        self.equity_curve: List[Dict] = []

        self.logger = logging.getLogger(__name__)

    def can_open_position(self, strategy: str, instrument: str) -> bool:
        """
        Check if we can open a new position.

        Args:
            strategy: Strategy name
            instrument: Instrument name

        Returns:
            True if position can be opened
        """
        key = f"{strategy}_{instrument}"

        # Check if position already open for this strategy-instrument
        if key in self.open_positions:
            return False

        # Count positions for this strategy
        strategy_positions = sum(1 for k in self.open_positions.keys() if k.startswith(strategy))

        return strategy_positions < self.max_positions

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        instrument: str
    ) -> float:
        """
        Calculate position size based on risk management.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            instrument: Instrument name

        Returns:
            Position size in lots
        """
        # Determine pip value (JPY pairs have different pip value)
        if 'JPY' in instrument:
            pip_value = 0.01
        else:
            pip_value = 0.0001

        risk_amount = self.capital * self.risk_per_trade
        stop_loss_pips = abs(entry_price - stop_loss) / pip_value

        if stop_loss_pips == 0:
            return 0

        # Position size in lots (1 lot = 100,000 units)
        # Risk per pip = pip_value * position_size_in_units
        # risk_amount = stop_loss_pips * pip_value * position_size_in_units
        position_size_units = risk_amount / (stop_loss_pips * pip_value)
        position_size_lots = position_size_units / 100000

        # Minimum 0.01 lots (micro lot)
        return max(0.01, round(position_size_lots, 2))

    def open_position(
        self,
        timestamp: datetime,
        instrument: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        strategy: str
    ) -> Optional[Trade]:
        """
        Open a new position.

        Args:
            timestamp: Entry timestamp
            instrument: Instrument name
            direction: 'long' or 'short'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            strategy: Strategy name

        Returns:
            Trade object if opened, None otherwise
        """
        key = f"{strategy}_{instrument}"

        if not self.can_open_position(strategy, instrument):
            self.logger.debug(f"Cannot open position for {key} - already exists or max positions reached")
            return None

        # Calculate position size
        position_size = self.calculate_position_size(entry_price, stop_loss, instrument)

        if position_size == 0:
            self.logger.warning(f"Position size is 0 for {key}")
            return None

        # Apply slippage
        pip_value = 0.01 if 'JPY' in instrument else 0.0001
        slippage_amount = self.slippage_pips * pip_value

        if direction == 'long':
            adjusted_entry = entry_price + slippage_amount
        else:
            adjusted_entry = entry_price - slippage_amount

        # Create trade
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            instrument=instrument,
            direction=direction,
            entry_price=adjusted_entry,
            exit_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            status='open',
            strategy=strategy
        )

        self.open_positions[key] = trade
        self.trades.append(trade)

        self.logger.debug(f"Opened {direction} position: {key} @ {adjusted_entry}, Size: {position_size} lots")

        return trade

    def close_position(
        self,
        timestamp: datetime,
        instrument: str,
        exit_price: float,
        strategy: str,
        reason: str = 'closed'
    ) -> Optional[Trade]:
        """
        Close an open position.

        Args:
            timestamp: Exit timestamp
            instrument: Instrument name
            exit_price: Exit price
            strategy: Strategy name
            reason: Reason for closing ('closed', 'stopped', 'tp_hit')

        Returns:
            Closed trade object
        """
        key = f"{strategy}_{instrument}"

        if key not in self.open_positions:
            self.logger.debug(f"No open position to close for {key}")
            return None

        trade = self.open_positions[key]

        # Apply slippage
        pip_value = 0.01 if 'JPY' in instrument else 0.0001
        slippage_amount = self.slippage_pips * pip_value

        if trade.direction == 'long':
            adjusted_exit = exit_price - slippage_amount
        else:
            adjusted_exit = exit_price + slippage_amount

        # Calculate P&L
        if trade.direction == 'long':
            price_change = adjusted_exit - trade.entry_price
        else:
            price_change = trade.entry_price - adjusted_exit

        # P&L in pips
        pnl_pips = price_change / pip_value

        # Apply commission
        pnl_pips -= self.commission_pips

        # P&L in currency
        position_size_units = trade.position_size * 100000
        pnl = pnl_pips * pip_value * position_size_units

        # Update trade
        trade.exit_time = timestamp
        trade.exit_price = adjusted_exit
        trade.pnl = pnl
        trade.pnl_pips = pnl_pips
        trade.status = reason

        # Update capital
        self.capital += pnl

        # Remove from open positions
        del self.open_positions[key]

        self.logger.debug(f"Closed {trade.direction} position: {key} @ {adjusted_exit}, P&L: ${pnl:.2f} ({pnl_pips:.1f} pips)")

        return trade

    def update_positions(self, timestamp: datetime, prices: Dict[str, Dict[str, float]]):
        """
        Update open positions (check stop loss and take profit).

        Args:
            timestamp: Current timestamp
            prices: Dictionary of {instrument: {'high': X, 'low': Y, 'close': Z}}
        """
        positions_to_close = []

        for key, trade in self.open_positions.items():
            if trade.instrument not in prices:
                continue

            price_data = prices[trade.instrument]
            high = price_data.get('high', trade.entry_price)
            low = price_data.get('low', trade.entry_price)
            close = price_data.get('close', trade.entry_price)

            # Check stop loss
            if trade.direction == 'long':
                if low <= trade.stop_loss:
                    positions_to_close.append((trade.strategy, trade.instrument, trade.stop_loss, 'stopped'))
                elif high >= trade.take_profit:
                    positions_to_close.append((trade.strategy, trade.instrument, trade.take_profit, 'tp_hit'))
            else:  # short
                if high >= trade.stop_loss:
                    positions_to_close.append((trade.strategy, trade.instrument, trade.stop_loss, 'stopped'))
                elif low <= trade.take_profit:
                    positions_to_close.append((trade.strategy, trade.instrument, trade.take_profit, 'tp_hit'))

        # Close positions that hit SL or TP
        for strategy, instrument, exit_price, reason in positions_to_close:
            self.close_position(timestamp, instrument, exit_price, strategy, reason)

    def record_equity(self, timestamp: datetime):
        """
        Record current equity.

        Args:
            timestamp: Current timestamp
        """
        self.equity_curve.append({
            'time': timestamp,
            'equity': self.capital,
            'open_positions': len(self.open_positions)
        })

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        return pd.DataFrame(self.equity_curve)

    def get_trades_df(self) -> pd.DataFrame:
        """Get all trades as DataFrame."""
        trades_data = []

        for trade in self.trades:
            trades_data.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'instrument': trade.instrument,
                'strategy': trade.strategy,
                'direction': trade.direction,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'position_size': trade.position_size,
                'pnl': trade.pnl,
                'pnl_pips': trade.pnl_pips,
                'status': trade.status
            })

        return pd.DataFrame(trades_data)

    def get_stats(self) -> Dict:
        """Get portfolio statistics."""
        closed_trades = [t for t in self.trades if t.status != 'open']

        if not closed_trades:
            return {
                'total_trades': 0,
                'final_capital': self.capital,
                'total_return': 0,
                'total_pnl': 0
            }

        pnls = [t.pnl for t in closed_trades]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]

        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(closed_trades) if closed_trades else 0,
            'final_capital': self.capital,
            'total_pnl': sum(pnls),
            'total_return': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'avg_win': np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t.pnl for t in losing_trades]) if losing_trades else 0,
            'largest_win': max([t.pnl for t in winning_trades]) if winning_trades else 0,
            'largest_loss': min([t.pnl for t in losing_trades]) if losing_trades else 0,
        }
