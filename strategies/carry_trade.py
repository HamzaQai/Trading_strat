"""
Strategy 9: Carry Trade + Technical Filter
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import ema, atr


class CarryTradeStrategy(BaseStrategy):
    """Carry trade with technical filter."""

    def __init__(self, params: Dict):
        super().__init__("CarryTrade", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate carry trade signals."""
        weekly_tf = self.params.get('timeframes', {}).get('weekly', 'W')
        h4_tf = self.params.get('timeframes', {}).get('h4', 'H4')

        # Check if instrument has carry bias
        carry_pairs = self.params.get('carry_pairs', {})
        if instrument not in carry_pairs:
            # No carry bias for this instrument
            return pd.DataFrame()

        carry_bias = carry_pairs[instrument]  # 1 for long, -1 for short

        if weekly_tf not in data or data[weekly_tf].empty:
            return pd.DataFrame()

        df_weekly = data[weekly_tf].copy()

        # Calculate weekly trend
        df_weekly['ema50'] = ema(df_weekly['close'], self.params.get('ema_fast', 50))
        df_weekly['ema200'] = ema(df_weekly['close'], self.params.get('ema_slow', 200))
        df_weekly['atr'] = atr(df_weekly['high'], df_weekly['low'], df_weekly['close'], self.params.get('atr_period', 14))

        df_weekly['trend'] = np.where(df_weekly['ema50'] > df_weekly['ema200'], 1,
                                      np.where(df_weekly['ema50'] < df_weekly['ema200'], -1, 0))

        # Use H4 for entry timing
        if h4_tf in data and not data[h4_tf].empty:
            df_h4 = data[h4_tf].copy()
            df_h4['ema21'] = ema(df_h4['close'], self.params.get('ema_entry', 21))

            # Merge weekly trend
            df_h4 = df_h4.join(df_weekly[['trend', 'atr']].add_suffix('_weekly'), how='left')
            df_h4['trend_weekly'].ffill(inplace=True)
            df_h4['atr_weekly'].ffill(inplace=True)

            df = df_h4
        else:
            df = df_weekly
            df['ema21'] = ema(df['close'], self.params.get('ema_entry', 21))
            df['trend_weekly'] = df['trend']
            df['atr_weekly'] = df.get('atr', 0)

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # Entry on pullback to EMA 21 in direction of carry
        df['pullback'] = df['close'] <= df['ema21']

        if carry_bias == 1:  # Long bias
            long_condition = (df['trend_weekly'] == 1) & df['pullback']

            atr_stop_mult = self.params.get('stop_loss_atr', 3)

            df.loc[long_condition, 'signal'] = 1
            df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
            df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'close'] - (df.loc[long_condition, 'atr_weekly'] * atr_stop_mult)
            # Trailing stop exit handled by backtest engine
            df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'close'] * 1.1  # 10% gain

            # Exit signal when trend reverses
            exit_condition = df['trend_weekly'] == -1
            df.loc[exit_condition, 'signal'] = 2  # Close signal

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
