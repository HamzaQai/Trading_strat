"""
Helper functions for pattern detection and analysis.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def detect_pin_bar(open_price: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, min_wick_ratio: float = 0.6) -> pd.Series:
    """
    Detect pin bar candlestick pattern.

    Args:
        open_price: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        min_wick_ratio: Minimum wick to body ratio

    Returns:
        Series: 1 for bullish pin bar, -1 for bearish, 0 for none
    """
    body = abs(close - open_price)
    total_range = high - low
    upper_wick = high - pd.concat([open_price, close], axis=1).max(axis=1)
    lower_wick = pd.concat([open_price, close], axis=1).min(axis=1) - low

    # Avoid division by zero
    total_range = total_range.replace(0, np.nan)

    # Bullish pin bar: long lower wick
    bullish_pin = (lower_wick / total_range > min_wick_ratio) & (close > open_price)

    # Bearish pin bar: long upper wick
    bearish_pin = (upper_wick / total_range > min_wick_ratio) & (close < open_price)

    result = pd.Series(0, index=open_price.index)
    result[bullish_pin] = 1
    result[bearish_pin] = -1

    return result


def detect_engulfing(open_price: pd.Series, close: pd.Series) -> pd.Series:
    """
    Detect engulfing candlestick pattern.

    Args:
        open_price: Open prices
        close: Close prices

    Returns:
        Series: 1 for bullish engulfing, -1 for bearish, 0 for none
    """
    prev_open = open_price.shift(1)
    prev_close = close.shift(1)

    # Bullish engulfing
    bullish = (prev_close < prev_open) & (close > open_price) & (close > prev_open) & (open_price < prev_close)

    # Bearish engulfing
    bearish = (prev_close > prev_open) & (close < open_price) & (close < prev_open) & (open_price > prev_close)

    result = pd.Series(0, index=open_price.index)
    result[bullish] = 1
    result[bearish] = -1

    return result


def detect_divergence(price: pd.Series, indicator: pd.Series, lookback: int = 10) -> pd.Series:
    """
    Detect divergence between price and indicator (e.g., RSI).

    Args:
        price: Price series
        indicator: Indicator series (e.g., RSI)
        lookback: Lookback period for finding swings

    Returns:
        Series: 1 for bullish divergence, -1 for bearish, 0 for none
    """
    # Find local highs and lows
    price_highs = price.rolling(window=lookback, center=True).max() == price
    price_lows = price.rolling(window=lookback, center=True).min() == price

    indicator_highs = indicator.rolling(window=lookback, center=True).max() == indicator
    indicator_lows = indicator.rolling(window=lookback, center=True).min() == indicator

    result = pd.Series(0, index=price.index)

    # Bearish divergence: Price higher high, Indicator lower high
    for i in range(lookback, len(price)):
        if price_highs.iloc[i]:
            # Find previous high
            prev_highs = price_highs.iloc[max(0, i-lookback*2):i]
            if prev_highs.any():
                prev_idx = prev_highs[prev_highs].index[-1]
                if price.iloc[i] > price.loc[prev_idx] and indicator.iloc[i] < indicator.loc[prev_idx]:
                    result.iloc[i] = -1

        # Bullish divergence: Price lower low, Indicator higher low
        if price_lows.iloc[i]:
            prev_lows = price_lows.iloc[max(0, i-lookback*2):i]
            if prev_lows.any():
                prev_idx = prev_lows[prev_lows].index[-1]
                if price.iloc[i] < price.loc[prev_idx] and indicator.iloc[i] > indicator.loc[prev_idx]:
                    result.iloc[i] = 1

    return result


def detect_range(high: pd.Series, low: pd.Series, min_days: int = 15, max_variation: float = 0.02) -> Tuple[Optional[float], Optional[float]]:
    """
    Detect if price is in a range.

    Args:
        high: High prices
        low: Low prices
        min_days: Minimum days in range
        max_variation: Maximum allowed variation (as fraction)

    Returns:
        Tuple of (range_top, range_bottom) or (None, None)
    """
    if len(high) < min_days:
        return None, None

    recent_high = high.iloc[-min_days:].max()
    recent_low = low.iloc[-min_days:].min()

    range_size = recent_high - recent_low
    range_mid = (recent_high + recent_low) / 2

    variation = range_size / range_mid if range_mid != 0 else 0

    if variation <= max_variation:
        return recent_high, recent_low

    return None, None


def calculate_position_size(
    capital: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float,
    pip_value: float = 0.0001
) -> float:
    """
    Calculate position size based on risk management.

    Args:
        capital: Account capital
        risk_percent: Risk per trade (e.g., 0.01 for 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        pip_value: Value of one pip (default 0.0001 for most pairs)

    Returns:
        Position size in lots (standard lots)
    """
    risk_amount = capital * risk_percent
    stop_loss_pips = abs(entry_price - stop_loss) / pip_value

    if stop_loss_pips == 0:
        return 0

    # Position size in units (1 standard lot = 100,000 units)
    position_size_units = risk_amount / (stop_loss_pips * pip_value * 100000)

    return position_size_units


def pips_to_price(pips: float, pip_value: float = 0.0001) -> float:
    """
    Convert pips to price difference.

    Args:
        pips: Number of pips
        pip_value: Value of one pip

    Returns:
        Price difference
    """
    return pips * pip_value


def price_to_pips(price_diff: float, pip_value: float = 0.0001) -> float:
    """
    Convert price difference to pips.

    Args:
        price_diff: Price difference
        pip_value: Value of one pip

    Returns:
        Number of pips
    """
    return price_diff / pip_value


def align_timeframes(daily_df: pd.DataFrame, hourly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align higher timeframe data with lower timeframe.

    Args:
        daily_df: Daily timeframe data
        hourly_df: Hourly timeframe data

    Returns:
        Hourly data with daily indicators merged
    """
    # Merge on date (forward fill daily values to hourly)
    daily_df_copy = daily_df.copy()
    daily_df_copy.index = daily_df_copy.index.normalize()  # Remove time component

    hourly_with_daily = hourly_df.copy()
    hourly_with_daily['date'] = hourly_with_daily.index.normalize()

    # Merge
    result = pd.merge_asof(
        hourly_with_daily.reset_index(),
        daily_df_copy.reset_index(),
        left_on='time',
        right_on='time',
        direction='backward',
        suffixes=('', '_daily')
    )

    result.set_index('time', inplace=True)
    result.drop('date', axis=1, inplace=True, errors='ignore')

    return result


def resample_to_higher_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample OHLCV data to higher timeframe.

    Args:
        df: OHLCV DataFrame
        timeframe: Target timeframe ('D', 'W', 'M', '4H', etc.)

    Returns:
        Resampled DataFrame
    """
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })

    resampled.dropna(inplace=True)
    return resampled


def get_seasonal_bias(instrument: str, month: int, seasonal_config: dict) -> int:
    """
    Get seasonal bias for an instrument and month.

    Args:
        instrument: Forex pair (e.g., 'EUR_USD')
        month: Month number (1-12)
        seasonal_config: Dictionary with seasonal biases

    Returns:
        1 (bullish), -1 (bearish), or 0 (neutral)
    """
    if instrument in seasonal_config:
        return seasonal_config[instrument].get(month, 0)

    return 0


def calculate_spread_zscore(pair1_prices: pd.Series, pair2_prices: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate z-score of spread between two correlated pairs.

    Args:
        pair1_prices: Prices of first pair
        pair2_prices: Prices of second pair
        period: Rolling period

    Returns:
        Z-score of spread
    """
    # Normalize prices to same starting point
    pair1_norm = pair1_prices / pair1_prices.iloc[0]
    pair2_norm = pair2_prices / pair2_prices.iloc[0]

    spread = pair1_norm - pair2_norm

    mean = spread.rolling(window=period).mean()
    std = spread.rolling(window=period).std()

    zscore = (spread - mean) / std

    return zscore
