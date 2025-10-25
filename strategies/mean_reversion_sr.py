"""
Strategy 2: Mean Reversion on Support/Resistance
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import rsi, atr, pivot_points
from utils.helpers import detect_pin_bar


class MeanReversionSRStrategy(BaseStrategy):
    """Mean Reversion on key support/resistance levels using pivots."""

    def __init__(self, params: Dict):
        super().__init__("MeanReversionSR", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate mean reversion signals."""
        daily_tf = self.params.get('timeframes', {}).get('daily', 'D')

        if daily_tf not in data or data[daily_tf].empty:
            return pd.DataFrame()

        df = data[daily_tf].copy()

        # Calculate indicators
        df['rsi'] = rsi(df['close'], self.params.get('rsi_period', 14))
        df['atr'] = atr(df['high'], df['low'], df['close'], self.params.get('atr_period', 14))

        # Calculate pivot points
        pivots = pivot_points(df['high'], df['low'], df['close'])
        df = pd.concat([df, pivots], axis=1)

        # Detect pin bars
        df['pin_bar'] = detect_pin_bar(df['open'], df['high'], df['low'], df['close'], 0.6)

        # RSI divergence (simplified)
        df['rsi_oversold'] = df['rsi'] < 30
        df['rsi_overbought'] = df['rsi'] > 70

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        tolerance = self.params.get('pivot_tolerance', 0.003)
        atr_stop_mult = self.params.get('stop_loss_atr', 1)

        # Long at S1/S2 support
        at_s1 = abs(df['close'] - df['S1']) / df['close'] < tolerance
        at_s2 = abs(df['close'] - df['S2']) / df['close'] < tolerance

        long_condition = (
            ((at_s1) | (at_s2)) &
            ((df['pin_bar'] == 1) | (df['rsi_oversold']))
        )

        # Short at R1/R2 resistance
        at_r1 = abs(df['close'] - df['R1']) / df['close'] < tolerance
        at_r2 = abs(df['close'] - df['R2']) / df['close'] < tolerance

        short_condition = (
            ((at_r1) | (at_r2)) &
            ((df['pin_bar'] == -1) | (df['rsi_overbought']))
        )

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'S2'] - (df.loc[long_condition, 'atr'] * atr_stop_mult)
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'PP']

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'R2'] + (df.loc[short_condition, 'atr'] * atr_stop_mult)
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'PP']

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
