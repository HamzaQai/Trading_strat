"""
Basic tests for strategies.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategies.mttf import MTTFStrategy
from strategies.volatility_breakout import VolatilityBreakoutStrategy


class TestStrategies(unittest.TestCase):
    """Test strategy implementations."""

    def setUp(self):
        """Create sample data for testing."""
        # Generate sample OHLCV data
        dates = pd.date_range(start='2025-01-01', end='2025-03-01', freq='D')
        n = len(dates)

        self.sample_data = pd.DataFrame({
            'open': np.random.uniform(1.08, 1.12, n),
            'high': np.random.uniform(1.10, 1.14, n),
            'low': np.random.uniform(1.06, 1.10, n),
            'close': np.random.uniform(1.08, 1.12, n),
            'volume': np.random.randint(1000, 10000, n)
        }, index=dates)

        # Ensure OHLC consistency
        self.sample_data['high'] = self.sample_data[['open', 'high', 'close']].max(axis=1)
        self.sample_data['low'] = self.sample_data[['open', 'low', 'close']].min(axis=1)

    def test_mttf_strategy_initialization(self):
        """Test MTTF strategy can be initialized."""
        params = {
            'timeframes': {'daily': 'D', 'h4': 'H4', 'h1': 'H1'},
            'ema_fast': 50,
            'ema_slow': 200,
            'ema_entry': 21,
            'rsi_period': 14
        }

        strategy = MTTFStrategy(params)
        self.assertEqual(strategy.name, "MTTF")
        self.assertIsNotNone(strategy.params)

    def test_volatility_breakout_initialization(self):
        """Test Volatility Breakout strategy can be initialized."""
        params = {
            'timeframe': 'D',
            'bb_period': 20,
            'bb_std': 2.0
        }

        strategy = VolatilityBreakoutStrategy(params)
        self.assertEqual(strategy.name, "VolatilityBreakout")

    def test_strategy_signal_generation(self):
        """Test that strategies can generate signals."""
        params = {
            'timeframe': 'D',
            'bb_period': 20,
            'bb_std': 2.0,
            'ema_fast': 50,
            'ema_slow': 200
        }

        strategy = VolatilityBreakoutStrategy(params)

        # Generate signals
        data = {'D': self.sample_data}
        signals = strategy.generate_signals(data, 'EUR_USD')

        # Check that signals DataFrame has required columns
        self.assertIn('signal', signals.columns)
        self.assertIn('entry_price', signals.columns)
        self.assertIn('stop_loss', signals.columns)
        self.assertIn('take_profit', signals.columns)


if __name__ == '__main__':
    unittest.main()
