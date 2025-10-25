"""
Base strategy class for all trading strategies.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Tuple, Optional
import logging


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str, params: Dict):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            params: Strategy parameters
        """
        self.name = name
        self.params = params
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame], instrument: str) -> pd.DataFrame:
        """
        Generate trading signals.

        Args:
            data: Dictionary of DataFrames by timeframe
            instrument: Instrument being traded

        Returns:
            DataFrame with columns: ['signal', 'entry_price', 'stop_loss', 'take_profit']
            signal: 1 (long), -1 (short), 0 (no signal), 2 (close)
        """
        pass

    def prepare_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Prepare and validate data.

        Args:
            data: Raw data dictionary

        Returns:
            Prepared data dictionary
        """
        # Can be overridden by subclasses for custom data preparation
        return data

    def validate_signal(self, signal: int, current_position: Optional[str]) -> bool:
        """
        Validate if signal should be acted upon.

        Args:
            signal: Signal value (1, -1, 0, 2)
            current_position: Current position ('long', 'short', None)

        Returns:
            True if signal is valid
        """
        # Don't open same direction position if already in position
        if signal == 1 and current_position == 'long':
            return False
        if signal == -1 and current_position == 'short':
            return False

        # Can only close if in position
        if signal == 2 and current_position is None:
            return False

        return True

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
