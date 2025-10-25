"""
Data Manager with caching for Oanda forex data.
"""

import os
import pickle
import hashlib
import pandas as pd
from typing import Dict, List, Optional
import logging
from pathlib import Path

from data.oanda_client import OandaClient


class DataManager:
    """Manages data fetching and caching for backtesting."""

    def __init__(self, oanda_client: OandaClient, cache_dir: str = "data/cache"):
        """
        Initialize DataManager.

        Args:
            oanda_client: OandaClient instance
            cache_dir: Directory for caching data
        """
        self.client = oanda_client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def _get_cache_key(self, instrument: str, granularity: str, start_date: str, end_date: str) -> str:
        """Generate unique cache key for dataset."""
        key_str = f"{instrument}_{granularity}_{start_date}_{end_date}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.pkl"

    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load data from cache if exists."""
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    df = pickle.load(f)
                self.logger.info(f"Loaded data from cache: {cache_key}")
                return df
            except Exception as e:
                self.logger.warning(f"Failed to load cache {cache_key}: {e}")
                return None

        return None

    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        """Save data to cache."""
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(df, f)
            self.logger.info(f"Saved data to cache: {cache_key}")
        except Exception as e:
            self.logger.warning(f"Failed to save cache {cache_key}: {e}")

    def get_data(
        self,
        instrument: str,
        granularity: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get data with caching support.

        Args:
            instrument: Forex pair
            granularity: Timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cache

        Returns:
            DataFrame with OHLCV data
        """
        cache_key = self._get_cache_key(instrument, granularity, start_date, end_date)

        # Try loading from cache
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

        # Fetch from API
        self.logger.info(f"Fetching {instrument} {granularity} from API ({start_date} to {end_date})")
        df = self.client.get_candles_range(instrument, granularity, start_date, end_date)

        # Handle missing data
        if df.empty:
            self.logger.warning(f"No data returned for {instrument} {granularity}")
            return df

        # Forward fill missing values
        df = df.ffill()

        # Save to cache
        if use_cache:
            self._save_to_cache(cache_key, df)

        return df

    def get_multiple_timeframes(
        self,
        instrument: str,
        granularities: List[str],
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes.

        Args:
            instrument: Forex pair
            granularities: List of timeframes
            start_date: Start date
            end_date: End date
            use_cache: Whether to use cache

        Returns:
            Dictionary mapping granularity to DataFrame
        """
        data = {}

        for granularity in granularities:
            df = self.get_data(instrument, granularity, start_date, end_date, use_cache)
            data[granularity] = df

        return data

    def get_multiple_instruments(
        self,
        instruments: List[str],
        granularity: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple instruments.

        Args:
            instruments: List of forex pairs
            granularity: Timeframe
            start_date: Start date
            end_date: End date
            use_cache: Whether to use cache

        Returns:
            Dictionary mapping instrument to DataFrame
        """
        data = {}

        for instrument in instruments:
            df = self.get_data(instrument, granularity, start_date, end_date, use_cache)
            data[instrument] = df

        return data

    def clear_cache(self):
        """Clear all cached data."""
        cache_files = list(self.cache_dir.glob("*.pkl"))

        for cache_file in cache_files:
            try:
                cache_file.unlink()
                self.logger.info(f"Deleted cache file: {cache_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {cache_file.name}: {e}")

        self.logger.info(f"Cleared {len(cache_files)} cache files")
