"""
Strategy 5: Range Trading with Probability Zones
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import rsi, atr
from utils.helpers import detect_range


class RangeTradingStrategy(BaseStrategy):
    """Range trading with probability zones."""

    def __init__(self, params: Dict):
        super().__init__("RangeTrading", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate range trading signals."""
        timeframe = self.params.get('timeframe', 'D')

        if timeframe not in data or data[timeframe].empty:
            return pd.DataFrame()

        df = data[timeframe].copy()

        # Calculate indicators
        df['rsi'] = rsi(df['close'], self.params.get('rsi_period', 14))
        df['atr'] = atr(df['high'], df['low'], df['close'], self.params.get('atr_period', 14))

        # Detect range
        min_days = self.params.get('range_min_days', 15)
        max_variation = self.params.get('range_variation_threshold', 0.02)

        df['range_top'] = np.nan
        df['range_bottom'] = np.nan

        for i in range(min_days, len(df)):
            range_high = df['high'].iloc[i-min_days:i].max()
            range_low = df['low'].iloc[i-min_days:i].min()

            range_size = range_high - range_low
            range_mid = (range_high + range_low) / 2

            variation = range_size / range_mid if range_mid != 0 else 1

            if variation <= max_variation:
                df.at[df.index[i], 'range_top'] = range_high
                df.at[df.index[i], 'range_bottom'] = range_low

        df['range_top'].ffill(inplace=True)
        df['range_bottom'].ffill(inplace=True)

        # Calculate zones
        df['range_size'] = df['range_top'] - df['range_bottom']
        df['zone_1_top'] = df['range_bottom'] + (df['range_size'] * 0.2)  # 0-20%
        df['zone_5_bottom'] = df['range_top'] - (df['range_size'] * 0.2)  # 80-100%

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # Long in bottom zone (0-20%)
        in_bottom_zone = df['close'] <= df['zone_1_top']
        long_condition = in_bottom_zone & (df['rsi'] < self.params.get('rsi_oversold', 30))

        # Short in top zone (80-100%)
        in_top_zone = df['close'] >= df['zone_5_bottom']
        short_condition = in_top_zone & (df['rsi'] > self.params.get('rsi_overbought', 70))

        atr_stop_mult = self.params.get('stop_loss_atr', 1)

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'range_bottom'] - (df.loc[long_condition, 'atr'] * atr_stop_mult)
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'range_bottom'] + (df.loc[long_condition, 'range_size'] * 0.5)

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'range_top'] + (df.loc[short_condition, 'atr'] * atr_stop_mult)
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'range_bottom'] + (df.loc[short_condition, 'range_size'] * 0.5)

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
