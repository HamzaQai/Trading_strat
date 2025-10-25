"""
Strategy 3: Volatility Breakout (Bollinger Squeeze)
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import ema, bollinger_bands, bb_width


class VolatilityBreakoutStrategy(BaseStrategy):
    """Bollinger Band squeeze breakout strategy."""

    def __init__(self, params: Dict):
        super().__init__("VolatilityBreakout", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate volatility breakout signals."""
        timeframe = self.params.get('timeframe', 'D')

        if timeframe not in data or data[timeframe].empty:
            return pd.DataFrame()

        df = data[timeframe].copy()

        # Calculate Bollinger Bands
        bb_period = self.params.get('bb_period', 20)
        bb_std = self.params.get('bb_std', 2.0)

        df['bb_upper'], df['bb_middle'], df['bb_lower'] = bollinger_bands(df['close'], bb_period, bb_std)
        df['bb_width'] = bb_width(df['bb_upper'], df['bb_lower'], df['bb_middle'])

        # Calculate average BB width
        bb_width_period = self.params.get('bb_width_period', 20)
        df['bb_width_avg'] = df['bb_width'].rolling(window=bb_width_period).mean()

        # Detect squeeze
        bb_width_mult = self.params.get('bb_width_multiplier', 1.5)
        df['squeeze'] = df['bb_width'] < (df['bb_width_avg'] * bb_width_mult)

        # Trend filter
        df['ema50'] = ema(df['close'], self.params.get('ema_fast', 50))
        df['ema200'] = ema(df['close'], self.params.get('ema_slow', 200))
        df['bullish_trend'] = df['ema50'] > df['ema200']
        df['bearish_trend'] = df['ema50'] < df['ema200']

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # Breakout detection
        df['breakout_up'] = (df['close'] > df['bb_upper']) & (df['close'].shift(1) <= df['bb_upper'].shift(1))
        df['breakout_down'] = (df['close'] < df['bb_lower']) & (df['close'].shift(1) >= df['bb_lower'].shift(1))

        # Long on upward breakout with bullish trend
        long_condition = df['squeeze'].shift(1) & df['breakout_up'] & df['bullish_trend']

        # Short on downward breakout with bearish trend
        short_condition = df['squeeze'].shift(1) & df['breakout_down'] & df['bearish_trend']

        stop_loss_ratio = self.params.get('stop_loss_ratio', 0.5)
        risk_reward = self.params.get('risk_reward', 2)

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'bb_middle']
        stop_distance = df.loc[long_condition, 'entry_price'] - df.loc[long_condition, 'stop_loss']
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'entry_price'] + (stop_distance * risk_reward)

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'bb_middle']
        stop_distance = df.loc[short_condition, 'stop_loss'] - df.loc[short_condition, 'entry_price']
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'entry_price'] - (stop_distance * risk_reward)

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
