"""
Strategy 10: Z-Score Mean Reversion
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import sma, rsi, atr, zscore


class ZScoreMeanRevStrategy(BaseStrategy):
    """Statistical arbitrage using Z-Score mean reversion."""

    def __init__(self, params: Dict):
        super().__init__("ZScoreMeanRev", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate Z-Score mean reversion signals."""
        timeframe = self.params.get('timeframe', 'D')

        if timeframe not in data or data[timeframe].empty:
            return pd.DataFrame()

        df = data[timeframe].copy()

        # Calculate indicators
        sma_period = self.params.get('sma_period', 50)
        df['sma'] = sma(df['close'], sma_period)
        df['zscore'] = zscore(df['close'], sma_period)
        df['rsi'] = rsi(df['close'], self.params.get('rsi_period', 14))
        df['atr'] = atr(df['high'], df['low'], df['close'], self.params.get('atr_period', 14))

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        zscore_threshold = self.params.get('zscore_threshold', 2)
        rsi_oversold = self.params.get('rsi_oversold', 30)
        rsi_overbought = self.params.get('rsi_overbought', 70)

        # Long when oversold (z-score < -2 and RSI < 30)
        long_condition = (df['zscore'] < -zscore_threshold) & (df['rsi'] < rsi_oversold)

        # Short when overbought (z-score > 2 and RSI > 70)
        short_condition = (df['zscore'] > zscore_threshold) & (df['rsi'] > rsi_overbought)

        # Exit when z-score returns to 0 (mean)
        exit_condition = abs(df['zscore']) < 0.5
        df.loc[exit_condition, 'signal'] = 2  # Close signal

        atr_stop_mult = self.params.get('stop_loss_atr', 2)

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'close'] - (df.loc[long_condition, 'atr'] * atr_stop_mult)
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'sma']  # Target mean

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'close'] + (df.loc[short_condition, 'atr'] * atr_stop_mult)
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'sma']  # Target mean

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
