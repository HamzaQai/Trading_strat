"""
Strategy 4: RSI Divergence + Break of Structure
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import rsi, atr
from utils.helpers import detect_divergence


class RSIDivergenceStrategy(BaseStrategy):
    """RSI divergence with break of structure confirmation."""

    def __init__(self, params: Dict):
        super().__init__("RSIDivergence", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate RSI divergence signals."""
        timeframe = self.params.get('timeframe', 'H4')

        if timeframe not in data or data[timeframe].empty:
            return pd.DataFrame()

        df = data[timeframe].copy()

        # Calculate indicators
        df['rsi'] = rsi(df['close'], self.params.get('rsi_period', 14))
        df['atr'] = atr(df['high'], df['low'], df['close'], self.params.get('atr_period', 14))

        # Detect divergence
        lookback = self.params.get('swing_lookback', 10)
        df['divergence'] = detect_divergence(df['close'], df['rsi'], lookback)

        # Detect swing highs and lows
        df['swing_high'] = df['high'].rolling(window=lookback, center=True).max() == df['high']
        df['swing_low'] = df['low'].rolling(window=lookback, center=True).min() == df['low']

        # Find last swing levels
        df['last_swing_high'] = df.loc[df['swing_high'], 'high'].reindex(df.index).ffill()
        df['last_swing_low'] = df.loc[df['swing_low'], 'low'].reindex(df.index).ffill()

        # Break of structure
        df['break_high'] = df['close'] > df['last_swing_high']
        df['break_low'] = df['close'] < df['last_swing_low']

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # Bearish divergence + break of swing low = short
        short_condition = (df['divergence'] == -1) & df['break_low']

        # Bullish divergence + break of swing high = long
        long_condition = (df['divergence'] == 1) & df['break_high']

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'last_swing_high']
        stop_distance = df.loc[short_condition, 'stop_loss'] - df.loc[short_condition, 'entry_price']
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'entry_price'] - (stop_distance * 1.5)

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'last_swing_low']
        stop_distance = df.loc[long_condition, 'entry_price'] - df.loc[long_condition, 'stop_loss']
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'entry_price'] + (stop_distance * 1.5)

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
