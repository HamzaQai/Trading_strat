"""
Technical indicators for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.

    Args:
        series: Price series
        period: EMA period

    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.

    Args:
        series: Price series
        period: SMA period

    Returns:
        SMA series
    """
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.

    Args:
        series: Price series
        period: RSI period

    Returns:
        RSI series (0-100)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period

    Returns:
        ATR series
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        series: Price series
        period: Period for SMA
        std_dev: Number of standard deviations

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle = sma(series, period)
    std = series.rolling(window=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return upper, middle, lower


def bb_width(upper: pd.Series, lower: pd.Series, middle: pd.Series) -> pd.Series:
    """
    Calculate Bollinger Band Width.

    Args:
        upper: Upper Bollinger Band
        lower: Lower Bollinger Band
        middle: Middle Bollinger Band

    Returns:
        BB Width series
    """
    return (upper - lower) / middle


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        series: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)

    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Lookback period

    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=3).mean()

    return k, d


def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
    """
    Calculate daily pivot points (Standard method).

    Args:
        high: High prices
        low: Low prices
        close: Close prices

    Returns:
        DataFrame with PP, R1, R2, S1, S2
    """
    pp = (high + low + close) / 3

    r1 = 2 * pp - low
    r2 = pp + (high - low)

    s1 = 2 * pp - high
    s2 = pp - (high - low)

    return pd.DataFrame({
        'PP': pp,
        'R1': r1,
        'R2': r2,
        'S1': s1,
        'S2': s2
    })


def zscore(series: pd.Series, period: int = 50) -> pd.Series:
    """
    Calculate Z-Score.

    Args:
        series: Price series
        period: Lookback period

    Returns:
        Z-Score series
    """
    mean = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()

    return (series - mean) / std


def correlation(series1: pd.Series, series2: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate rolling correlation between two series.

    Args:
        series1: First price series
        series2: Second price series
        period: Rolling window

    Returns:
        Correlation series
    """
    return series1.rolling(window=period).corr(series2)


def detect_higher_highs(high: pd.Series, period: int = 10) -> pd.Series:
    """
    Detect Higher Highs pattern.

    Args:
        high: High prices
        period: Lookback period

    Returns:
        Boolean series (True = Higher High)
    """
    rolling_max = high.rolling(window=period, min_periods=1).max()
    is_higher_high = high > rolling_max.shift(1)

    return is_higher_high


def detect_higher_lows(low: pd.Series, period: int = 10) -> pd.Series:
    """
    Detect Higher Lows pattern.

    Args:
        low: Low prices
        period: Lookback period

    Returns:
        Boolean series (True = Higher Low)
    """
    rolling_min = low.rolling(window=period, min_periods=1).min()
    is_higher_low = low > rolling_min.shift(1)

    return is_higher_low


def detect_lower_highs(high: pd.Series, period: int = 10) -> pd.Series:
    """
    Detect Lower Highs pattern.

    Args:
        high: High prices
        period: Lookback period

    Returns:
        Boolean series (True = Lower High)
    """
    rolling_max = high.rolling(window=period, min_periods=1).max()
    is_lower_high = high < rolling_max.shift(1)

    return is_lower_high


def detect_lower_lows(low: pd.Series, period: int = 10) -> pd.Series:
    """
    Detect Lower Lows pattern.

    Args:
        low: Low prices
        period: Lookback period

    Returns:
        Boolean series (True = Lower Low)
    """
    rolling_min = low.rolling(window=period, min_periods=1).min()
    is_lower_low = low < rolling_min.shift(1)

    return is_lower_low
