"""Configuration module for loading environment variables."""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable value."""
    return os.getenv(key, default)


# Blockfrost API Configuration
BLOCKFROST_API_KEY: Optional[str] = get_env('BLOCKFROST_API_KEY')

# Polling Configuration
POLLING_INTERVAL: int = int(get_env('POLLING_INTERVAL', '2'))

# Retry Configuration
MAX_RETRIES: int = int(get_env('MAX_RETRIES', '3'))
RATE_LIMIT_BACKOFF: int = int(get_env('RATE_LIMIT_BACKOFF', '1'))


def validate_config():
    """Validate that required configuration is present."""
    if not BLOCKFROST_API_KEY:
        raise ValueError(
            "BLOCKFROST_API_KEY is required. "
            "Set it in .env file or as environment variable."
        )

