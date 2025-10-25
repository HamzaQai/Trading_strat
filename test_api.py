"""Quick test of Oanda API connection."""

import sys
import yaml
from data.oanda_client import OandaClient
from utils.logger import setup_logger

# Setup logger
logger = setup_logger("INFO")

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

try:
    # Initialize client
    logger.info("Initializing Oanda client...")
    oanda_config = config['oanda']
    client = OandaClient(
        api_key=oanda_config['api_key'],
        account_id=oanda_config['account_id'],
        environment=oanda_config['environment']
    )

    logger.info(f"✓ Connected successfully! Account ID: {client.account_id}")

    # Try to fetch some recent data
    logger.info("\nTesting data fetch for EUR_USD (last 100 daily candles)...")
    df = client.get_candles(
        instrument="EUR_USD",
        granularity="D",
        count=100
    )

    if not df.empty:
        logger.info(f"✓ Successfully fetched {len(df)} candles")
        logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")
        logger.info(f"  Latest close: {df['close'].iloc[-1]:.5f}")
        logger.info("\nFirst 5 rows:")
        print(df.head())
        logger.info("\nLast 5 rows:")
        print(df.tail())
    else:
        logger.error("✗ No data returned")
        sys.exit(1)

    logger.info("\n✓ API test successful!")

except Exception as e:
    logger.error(f"✗ API test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
