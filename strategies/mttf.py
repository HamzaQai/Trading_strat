"""
Strategy 1: Multi-Timeframe Trend Following (MTTF)
"""

import pandas as pd
import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy
from utils.indicators import ema, rsi, atr, detect_higher_highs, detect_higher_lows, detect_lower_highs, detect_lower_lows


class MTTFStrategy(BaseStrategy):
    """
    Multi-Timeframe Trend Following Strategy.

    - Daily: EMA 50 > EMA 200 = bullish bias
    - 4H: Confirm Higher Highs/Higher Lows
    - 1H: Entry on pullback to EMA 21 + RSI confirmation
    """

    def __init__(self, params: Dict):
        super().__init__("MTTF", params)

    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """Generate MTTF signals."""
        # Get timeframes
        daily_tf = self.params.get('timeframes', {}).get('daily', 'D')
        h4_tf = self.params.get('timeframes', {}).get('h4', 'H4')
        h1_tf = self.params.get('timeframes', {}).get('h1', 'H1')

        if h1_tf not in data or not data[h1_tf].empty:
            df_h1 = data.get(h1_tf, pd.DataFrame()).copy()
        else:
            return pd.DataFrame()

        if df_h1.empty:
            return pd.DataFrame()

        # Calculate indicators on H1
        df_h1['ema21'] = ema(df_h1['close'], self.params.get('ema_entry', 21))
        df_h1['rsi'] = rsi(df_h1['close'], self.params.get('rsi_period', 14))
        df_h1['atr'] = atr(df_h1['high'], df_h1['low'], df_h1['close'], self.params.get('atr_period', 14))

        # Get daily data for bias
        if daily_tf in data and not data[daily_tf].empty:
            df_daily = data[daily_tf].copy()
            df_daily['ema50'] = ema(df_daily['close'], self.params.get('ema_fast', 50))
            df_daily['ema200'] = ema(df_daily['close'], self.params.get('ema_slow', 200))
            df_daily['bias'] = np.where(df_daily['ema50'] > df_daily['ema200'], 1, -1)

            # Merge daily bias to H1
            df_h1 = df_h1.join(df_daily[['bias']].add_suffix('_daily'), how='left')
            df_h1['bias_daily'].ffill(inplace=True)
        else:
            df_h1['bias_daily'] = 0

        # Get H4 structure
        if h4_tf in data and not data[h4_tf].empty:
            df_h4 = data[h4_tf].copy()
            df_h4['hh'] = detect_higher_highs(df_h4['high'], 10)
            df_h4['hl'] = detect_higher_lows(df_h4['low'], 10)
            df_h4['lh'] = detect_lower_highs(df_h4['high'], 10)
            df_h4['ll'] = detect_lower_lows(df_h4['low'], 10)

            df_h4['structure'] = np.where((df_h4['hh']) | (df_h4['hl']), 1,
                                         np.where((df_h4['lh']) | (df_h4['ll']), -1, 0))

            # Merge structure to H1
            df_h1 = df_h1.join(df_h4[['structure']].add_suffix('_h4'), how='left')
            df_h1['structure_h4'].ffill(inplace=True)
        else:
            df_h1['structure_h4'] = 0

        # Generate signals
        df_h1['signal'] = 0
        df_h1['entry_price'] = np.nan
        df_h1['stop_loss'] = np.nan
        df_h1['take_profit'] = np.nan

        # Long conditions
        long_condition = (
            (df_h1['bias_daily'] == 1) &
            (df_h1['structure_h4'] == 1) &
            (df_h1['close'] <= df_h1['ema21']) &
            (df_h1['rsi'] < self.params.get('rsi_oversold', 40))
        )

        # Short conditions
        short_condition = (
            (df_h1['bias_daily'] == -1) &
            (df_h1['structure_h4'] == -1) &
            (df_h1['close'] >= df_h1['ema21']) &
            (df_h1['rsi'] > self.params.get('rsi_overbought', 60))
        )

        atr_stop_mult = self.params.get('stop_loss_atr', 2)
        atr_tp_mult = self.params.get('take_profit_atr', 3)

        # Set long signals
        df_h1.loc[long_condition, 'signal'] = 1
        df_h1.loc[long_condition, 'entry_price'] = df_h1.loc[long_condition, 'close']
        df_h1.loc[long_condition, 'stop_loss'] = df_h1.loc[long_condition, 'close'] - (df_h1.loc[long_condition, 'atr'] * atr_stop_mult)
        df_h1.loc[long_condition, 'take_profit'] = df_h1.loc[long_condition, 'close'] + (df_h1.loc[long_condition, 'atr'] * atr_tp_mult)

        # Set short signals
        df_h1.loc[short_condition, 'signal'] = -1
        df_h1.loc[short_condition, 'entry_price'] = df_h1.loc[short_condition, 'close']
        df_h1.loc[short_condition, 'stop_loss'] = df_h1.loc[short_condition, 'close'] + (df_h1.loc[short_condition, 'atr'] * atr_stop_mult)
        df_h1.loc[short_condition, 'take_profit'] = df_h1.loc[short_condition, 'close'] - (df_h1.loc[short_condition, 'atr'] * atr_tp_mult)

        return df_h1[['signal', 'entry_price', 'stop_loss', 'take_profit']]
