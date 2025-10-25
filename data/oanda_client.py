"""
Oanda API Client for fetching historical forex data.
"""

import requests
import pandas as pd
from typing import Optional, List, Dict
import time
from datetime import datetime
import logging


class OandaClient:
    """Client for interacting with Oanda API v3."""

    def __init__(self, api_key: str, account_id: str = "AUTO", environment: str = "practice"):
        """
        Initialize Oanda API client.

        Args:
            api_key: Oanda API key
            account_id: Account ID (AUTO to fetch automatically)
            environment: 'practice' or 'live'
        """
        self.api_key = api_key
        self.environment = environment

        if environment == "practice":
            self.base_url = "https://api-fxpractice.oanda.com"
        else:
            self.base_url = "https://api-fxtrade.oanda.com"

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        self.logger = logging.getLogger(__name__)

        # Get account ID if AUTO
        if account_id == "AUTO":
            self.account_id = self._get_account_id()
        else:
            self.account_id = account_id

        self.logger.info(f"OandaClient initialized with account {self.account_id}")

    def _get_account_id(self) -> str:
        """Fetch account ID from Oanda API."""
        endpoint = f"{self.base_url}/v3/accounts"

        try:
            response = self._make_request(endpoint)
            accounts = response.get("accounts", [])

            if not accounts:
                raise ValueError("No accounts found")

            account_id = accounts[0]["id"]
            self.logger.info(f"Auto-detected account ID: {account_id}")
            return account_id

        except Exception as e:
            self.logger.error(f"Failed to get account ID: {e}")
            raise

    def _make_request(self, url: str, params: Optional[Dict] = None, retries: int = 3) -> Dict:
        """
        Make HTTP request with retry logic and rate limiting.

        Args:
            url: API endpoint URL
            params: Query parameters
            retries: Number of retries on failure

        Returns:
            JSON response as dictionary
        """
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)

                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Handle server errors
                if response.status_code >= 500:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    self.logger.error(f"Request failed after {retries} attempts: {e}")
                    raise

                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed. Retrying in {wait_time}s... ({e})")
                time.sleep(wait_time)

        raise Exception("Request failed after all retries")

    def get_candles(
        self,
        instrument: str,
        granularity: str = "D",
        count: Optional[int] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical candle data.

        Args:
            instrument: Forex pair (e.g., 'EUR_USD')
            granularity: Timeframe (S5, S10, S15, S30, M1, M2, M4, M5, M10, M15, M30, H1, H2, H3, H4, H6, H8, H12, D, W, M)
            count: Number of candles (max 5000)
            from_time: Start time (RFC3339 format)
            to_time: End time (RFC3339 format)

        Returns:
            DataFrame with OHLCV data
        """
        endpoint = f"{self.base_url}/v3/instruments/{instrument}/candles"

        params = {
            "granularity": granularity,
            "price": "M"  # Mid prices
        }

        if count:
            params["count"] = min(count, 5000)
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time

        try:
            self.logger.debug(f"Fetching {instrument} candles: {granularity}, count={count}")
            response = self._make_request(endpoint, params)

            candles = response.get("candles", [])

            if not candles:
                self.logger.warning(f"No candles returned for {instrument}")
                return pd.DataFrame()

            # Parse candles into DataFrame
            data = []
            for candle in candles:
                if not candle.get("complete", False):
                    continue  # Skip incomplete candles

                mid = candle["mid"]
                data.append({
                    "time": candle["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(candle["volume"])
                })

            df = pd.DataFrame(data)

            if df.empty:
                return df

            # Convert time to datetime and set as index
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
            df.sort_index(inplace=True)

            self.logger.info(f"Fetched {len(df)} candles for {instrument} ({granularity})")
            return df

        except Exception as e:
            self.logger.error(f"Failed to fetch candles for {instrument}: {e}")
            raise

    def get_candles_range(
        self,
        instrument: str,
        granularity: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch candles for a date range (handles pagination if > 5000 candles).

        Args:
            instrument: Forex pair (e.g., 'EUR_USD')
            granularity: Timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
        """
        # Convert dates to RFC3339 format
        start_dt = pd.to_datetime(start_date).isoformat() + "Z"
        end_dt = pd.to_datetime(end_date).isoformat() + "Z"

        all_data = []
        current_start = start_dt

        while True:
            df = self.get_candles(
                instrument=instrument,
                granularity=granularity,
                from_time=current_start,
                to_time=end_dt,
                count=5000
            )

            if df.empty:
                break

            all_data.append(df)

            # Check if we got all data
            if len(df) < 5000:
                break

            # Update start time for next batch
            last_time = df.index[-1]
            current_start = (last_time + pd.Timedelta(seconds=1)).isoformat() + "Z"

            # Rate limiting
            time.sleep(0.1)

        if not all_data:
            return pd.DataFrame()

        # Combine all data
        result = pd.concat(all_data)
        result = result[~result.index.duplicated(keep='first')]  # Remove duplicates
        result.sort_index(inplace=True)

        self.logger.info(f"Fetched {len(result)} total candles for {instrument} ({start_date} to {end_date})")
        return result

    def get_multiple_timeframes(
        self,
        instrument: str,
        granularities: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes.

        Args:
            instrument: Forex pair
            granularities: List of timeframes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary mapping granularity to DataFrame
        """
        data = {}

        for granularity in granularities:
            self.logger.info(f"Fetching {instrument} - {granularity}")
            df = self.get_candles_range(instrument, granularity, start_date, end_date)
            data[granularity] = df
            time.sleep(0.2)  # Rate limiting

        return data
