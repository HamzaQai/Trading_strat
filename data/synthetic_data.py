"""
Generate synthetic forex data for testing without API access.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class SyntheticDataGenerator:
    """Generate realistic synthetic forex OHLCV data."""

    def __init__(self, seed: int = 42):
        """
        Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)

    def generate_price_series(
        self,
        start_price: float,
        num_periods: int,
        volatility: float = 0.01,
        drift: float = 0.0001,
        trend_strength: float = 0.3
    ) -> np.ndarray:
        """
        Generate realistic price series using geometric Brownian motion with trends.

        Args:
            start_price: Starting price
            num_periods: Number of periods to generate
            volatility: Price volatility (daily std dev)
            drift: Daily drift (trend)
            trend_strength: Strength of trending behavior (0-1)

        Returns:
            Array of prices
        """
        # Geometric Brownian Motion
        returns = np.random.normal(drift, volatility, num_periods)

        # Add trending behavior
        trend = np.cumsum(np.random.normal(0, volatility * trend_strength, num_periods))
        returns += trend / num_periods

        # Add mean reversion
        prices = [start_price]
        for i in range(num_periods - 1):
            # Mean reversion component
            deviation = (prices[-1] - start_price) / start_price
            mean_reversion = -deviation * 0.1

            price_change = returns[i] + mean_reversion
            new_price = prices[-1] * (1 + price_change)
            prices.append(new_price)

        return np.array(prices)

    def generate_ohlcv(
        self,
        instrument: str,
        start_date: str,
        end_date: str,
        granularity: str = "D",
        base_price: float = None
    ) -> pd.DataFrame:
        """
        Generate OHLCV data for an instrument.

        Args:
            instrument: Instrument name (e.g., 'EUR_USD')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: Timeframe (D, H4, H1, etc.)
            base_price: Base price (auto-determined if None)

        Returns:
            DataFrame with OHLCV data
        """
        # Default base prices for common pairs
        base_prices = {
            'EUR_USD': 1.0850,
            'GBP_USD': 1.2650,
            'USD_JPY': 149.50,
            'AUD_USD': 0.6550,
            'USD_CAD': 1.3650,
            'AUD_JPY': 97.50,
            'NZD_JPY': 89.50
        }

        if base_price is None:
            base_price = base_prices.get(instrument, 1.0000)

        # Determine frequency
        freq_map = {
            'D': 'D',
            'H4': '4H',
            'H1': 'H',
            'M1': 'T',
            'W': 'W'
        }
        freq = freq_map.get(granularity, 'D')

        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        num_periods = len(dates)

        if num_periods == 0:
            return pd.DataFrame()

        # Adjust volatility based on timeframe
        vol_map = {
            'D': 0.008,
            'H4': 0.004,
            'H1': 0.002,
            'M1': 0.0005,
            'W': 0.015
        }
        volatility = vol_map.get(granularity, 0.008)

        # Adjust for JPY pairs (different pip value)
        if 'JPY' in instrument:
            volatility *= 100

        # Generate close prices
        close_prices = self.generate_price_series(
            start_price=base_price,
            num_periods=num_periods,
            volatility=volatility,
            drift=0.0001,
            trend_strength=0.3
        )

        # Generate OHLC from close prices
        data = []
        for i, close in enumerate(close_prices):
            # Generate realistic OHLC
            intrabar_vol = volatility * 0.5
            high_offset = abs(np.random.normal(0, intrabar_vol))
            low_offset = abs(np.random.normal(0, intrabar_vol))

            high = close * (1 + high_offset)
            low = close * (1 - low_offset)

            # Open is previous close with small gap
            if i == 0:
                open_price = close * (1 + np.random.normal(0, volatility * 0.1))
            else:
                open_price = close_prices[i-1] * (1 + np.random.normal(0, volatility * 0.1))

            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Generate volume (random but realistic)
            base_volume = 10000
            volume = int(base_volume * (1 + np.random.uniform(-0.5, 0.5)))

            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })

        df = pd.DataFrame(data, index=dates)
        return df

    def generate_multiple_timeframes(
        self,
        instrument: str,
        start_date: str,
        end_date: str,
        timeframes: list
    ) -> dict:
        """
        Generate data for multiple timeframes.

        Args:
            instrument: Instrument name
            start_date: Start date
            end_date: End date
            timeframes: List of timeframes

        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        data = {}
        for tf in timeframes:
            df = self.generate_ohlcv(instrument, start_date, end_date, tf)
            data[tf] = df

        return data
