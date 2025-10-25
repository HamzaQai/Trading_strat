"""
Strategy 6: Seasonality + Trend Alignment
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import ema, atr
from utils.helpers import get_seasonal_bias


class SeasonalityStrategy(BaseStrategy):
    """Seasonality-based strategy with trend alignment."""

    def __init__(self, params: Dict):
        super().__init__("Seasonality", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate seasonality signals."""
        daily_tf = self.params.get('timeframes', {}).get('daily', 'D')
        h4_tf = self.params.get('timeframes', {}).get('h4', 'H4')

        if daily_tf not in data or data[daily_tf].empty:
            return pd.DataFrame()

        df_daily = data[daily_tf].copy()

        # Calculate trend indicators
        df_daily['ema50'] = ema(df_daily['close'], self.params.get('ema_fast', 50))
        df_daily['ema200'] = ema(df_daily['close'], self.params.get('ema_slow', 200))
        df_daily['atr'] = atr(df_daily['high'], df_daily['low'], df_daily['close'], self.params.get('atr_period', 14))

        # Determine trend
        df_daily['trend'] = np.where(df_daily['ema50'] > df_daily['ema200'], 1,
                                     np.where(df_daily['ema50'] < df_daily['ema200'], -1, 0))

        # Get seasonal bias
        seasonal_config = self.params.get('seasonal_bias', {})
        df_daily['month'] = df_daily.index.month
        df_daily['seasonal_bias'] = df_daily['month'].apply(
            lambda m: get_seasonal_bias(instrument, m, seasonal_config)
        )

        # Use H4 for entry timing if available
        if h4_tf in data and not data[h4_tf].empty:
            df_h4 = data[h4_tf].copy()
            df_h4['ema21'] = ema(df_h4['close'], self.params.get('ema_entry', 21))

            # Merge daily data to H4
            df_h4 = df_h4.join(df_daily[['trend', 'seasonal_bias', 'atr']].add_suffix('_daily'), how='left')
            df_h4['trend_daily'].ffill(inplace=True)
            df_h4['seasonal_bias_daily'].ffill(inplace=True)
            df_h4['atr_daily'].ffill(inplace=True)

            df = df_h4
        else:
            df = df_daily
            df['ema21'] = ema(df['close'], self.params.get('ema_entry', 21))
            df['trend_daily'] = df['trend']
            df['seasonal_bias_daily'] = df['seasonal_bias']
            df['atr_daily'] = df.get('atr', 0)

        # Initialize signal columns
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # Pullback to EMA 21
        df['pullback'] = df['close'] <= df['ema21']

        # Long: seasonal bias bullish + trend bullish + pullback
        long_condition = (
            (df['seasonal_bias_daily'] == 1) &
            (df['trend_daily'] == 1) &
            df['pullback']
        )

        # Short: seasonal bias bearish + trend bearish + pullback above EMA
        short_condition = (
            (df['seasonal_bias_daily'] == -1) &
            (df['trend_daily'] == -1) &
            (df['close'] >= df['ema21'])
        )

        atr_stop_mult = self.params.get('stop_loss_atr', 2)
        atr_tp_mult = self.params.get('take_profit_atr', 3)

        # Set long signals
        df.loc[long_condition, 'signal'] = 1
        df.loc[long_condition, 'entry_price'] = df.loc[long_condition, 'close']
        df.loc[long_condition, 'stop_loss'] = df.loc[long_condition, 'close'] - (df.loc[long_condition, 'atr_daily'] * atr_stop_mult)
        df.loc[long_condition, 'take_profit'] = df.loc[long_condition, 'close'] + (df.loc[long_condition, 'atr_daily'] * atr_tp_mult)

        # Set short signals
        df.loc[short_condition, 'signal'] = -1
        df.loc[short_condition, 'entry_price'] = df.loc[short_condition, 'close']
        df.loc[short_condition, 'stop_loss'] = df.loc[short_condition, 'close'] + (df.loc[short_condition, 'atr_daily'] * atr_stop_mult)
        df.loc[short_condition, 'take_profit'] = df.loc[short_condition, 'close'] - (df.loc[short_condition, 'atr_daily'] * atr_tp_mult)

        return df[['signal', 'entry_price', 'stop_loss', 'take_profit']]
