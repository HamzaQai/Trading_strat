"""
Strategy 8: Breakout with Retest
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import atr
from utils.helpers import detect_pin_bar


class BreakoutRetestStrategy(BaseStrategy):
    """Breakout with retest confirmation."""

    def __init__(self, params: Dict):
        super().__init__("BreakoutRetest", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate breakout retest signals."""
        timeframe = self.params.get('timeframe', 'D')

        if timeframe not in data or data[timeframe].empty:
            return pd.DataFrame()

        df = data[timeframe].copy()

        # Calculate ATR
        df['atr'] = atr(df['high'], df['low'], df['close'], self.params.get('atr_period', 14))
        df['atr_avg'] = df['atr'].rolling(window=20).mean()

        # Detect consolidation
        consolidation_days = self.params.get('consolidation_days', 10)
        consolidation_atr_ratio = self.params.get('consolidation_atr_ratio', 1.5)

        df['consolidation'] = False

        for i in range(consolidation_days, len(df)):
            recent_range = df['high'].iloc[i-consolidation_days:i].max() - df['low'].iloc[i-consolidation_days:i].min()
            avg_atr = df['atr_avg'].iloc[i]

            if recent_range < (avg_atr * consolidation_atr_ratio):
                df.at[df.index[i], 'consolidation'] = True

        # Find consolidation levels
        df['consol_high'] = np.nan
        df['consol_low'] = np.nan

        for i in range(consolidation_days, len(df)):
            if df['consolidation'].iloc[i]:
                df.at[df.index[i], 'consol_high'] = df['high'].iloc[i-consolidation_days:i].max()
                df.at[df.index[i], 'consol_low'] = df['low'].iloc[i-consolidation_days:i].min()

        df['consol_high'].ffill(inplace=True)
        df['consol_low'].ffill(inplace=True)

        # Detect breakout
        breakout_atr_ratio = self.params.get('breakout_atr_ratio', 1.5)
        df['candle_range'] = df['high'] - df['low']

        df['breakout_up'] = (
            (df['close'] > df['consol_high']) &
            (df['candle_range'] > df['atr_avg'] * breakout_atr_ratio)
        )

        df['breakout_down'] = (
            (df['close'] < df['consol_low']) &
            (df['candle_range'] > df['atr_avg'] * breakout_atr_ratio)
        )

        # Track breakout levels
        df['breakout_level_up'] = np.where(df['breakout_up'], df['consol_high'], np.nan)
        df['breakout_level_down'] = np.where(df['breakout_down'], df['consol_low'], np.nan)
        df['breakout_level_up'].ffill(inplace=True, limit=5)
        df['breakout_level_down'].ffill(inplace=True, limit=5)

        # Detect retest
        df['pin_bar'] = detect_pin_bar(df['open'], df['high'], df['low'], df['close'], 0.6)

        retest_tolerance = 0.001

        df['retest_up'] = (
            (abs(df['low'] - df['breakout_level_up']) / df['breakout_level_up'] < retest_tolerance) &
            ((df['pin_bar'] == 1) | (df['close'] > df['open']))  # Bullish rejection
        )

        df['retest_down'] = (
            (abs(df['high'] - df['breakout_level_down']) / df['breakout_level_down'] < retest_tolerance) &
            ((df['pin_bar'] == -1) | (df['close'] < df['open']))  # Bearish rejection
        )

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        atr_stop_mult = self.params.get('stop_loss_atr', 1)
        tp_ratio = self.params.get('take_profit_ratio', 2)

        # Long on bullish retest
        long_condition = df['retest_up']

        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'breakout_level_up'] - (df.loc[long_condition, 'atr'] * atr_stop_mult)

        # Take profit = consolidation height * ratio
        consol_height = df.loc[long_condition, 'consol_high'] - df.loc[long_condition, 'consol_low']
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'entry_price'] + (consol_height * tp_ratio)

        # Short on bearish retest
        short_condition = df['retest_down']

        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'breakout_level_down'] + (df.loc[short_condition, 'atr'] * atr_stop_mult)

        consol_height = df.loc[short_condition, 'consol_high'] - df.loc[short_condition, 'consol_low']
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'entry_price'] - (consol_height * tp_ratio)

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
