"""
Utility functions for the Whale Alert Bot.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: str = "whale_bot.log") -> None:
    """Set up logging configuration for the bot."""
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
        
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")


def format_number(number: float, precision: int = 2) -> str:
    """Format a number with proper thousands separators."""
    try:
        if precision == 0:
            return f"{number:,.0f}"
        else:
            return f"{number:,.{precision}f}"
    except (ValueError, TypeError):
        return str(number)


def format_currency(amount: float, currency: str = "USD", precision: int = 2) -> str:
    """Format an amount as currency."""
    try:
        if currency.upper() == "USD":
            return f"${format_number(amount, precision)}"
        else:
            return f"{format_number(amount, precision)} {currency}"
    except (ValueError, TypeError):
        return f"{amount} {currency}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    try:
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def validate_symbol(symbol: str) -> bool:
    """Validate if a symbol has the correct format."""
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Basic validation for crypto symbols
    symbol = symbol.upper().strip()
    
    # Should be alphanumeric and 4-12 characters
    if not symbol.isalnum() or len(symbol) < 4 or len(symbol) > 12:
        return False
    
    # Should end with USDT, USDC, or BTC
    valid_quote_currencies = ['USDT', 'USDC', 'BTC', 'ETH']
    
    for quote in valid_quote_currencies:
        if symbol.endswith(quote):
            return True
    
    return False


def parse_timeframe(timeframe_str: str) -> int:
    """Parse timeframe string to seconds."""
    try:
        timeframe_str = timeframe_str.strip().lower()
        
        if timeframe_str.endswith('s'):
            return int(timeframe_str[:-1])
        elif timeframe_str.endswith('m'):
            return int(timeframe_str[:-1]) * 60
        elif timeframe_str.endswith('h'):
            return int(timeframe_str[:-1]) * 3600
        elif timeframe_str.endswith('d'):
            return int(timeframe_str[:-1]) * 86400
        else:
            # Assume seconds if no unit specified
            return int(timeframe_str)
            
    except (ValueError, TypeError):
        return 30  # Default to 30 seconds


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return None


def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure a directory exists, create if it doesn't."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except OSError as e:
        logging.getLogger(__name__).error(f"Could not create directory {directory_path}: {e}")
        return False


def safe_float_conversion(value, default: float = 0.0) -> float:
    """Safely convert a value to float with a default fallback."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_conversion(value, default: int = 0) -> int:
    """Safely convert a value to int with a default fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to a maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_crypto_emoji(symbol: str) -> str:
    """Get emoji for common cryptocurrencies."""
    symbol = symbol.upper().replace('USDT', '').replace('USDC', '')
    
    emoji_map = {
        'BTC': '₿',
        'ETH': 'Ξ',
        'BNB': '🔶',
        'ADA': '💎',
        'SOL': '☀️',
        'DOT': '🔴',
        'MATIC': '🟣',
        'AVAX': '🏔️',
        'LINK': '🔗',
        'UNI': '🦄'
    }
    
    return emoji_map.get(symbol, '💰')


class RateLimiter:
    """Simple rate limiter utility."""
    
    def __init__(self, max_calls: int, time_window: int):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed under the rate limit."""
        import time
        current_time = time.time()
        
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if current_time - call_time < self.time_window]
        
        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(current_time)
            return True
        
        return False
    
    def time_until_allowed(self) -> float:
        """Get time in seconds until next call is allowed."""
        if not self.calls:
            return 0.0
        
        import time
        current_time = time.time()
        oldest_call = min(self.calls)
        
        return max(0.0, self.time_window - (current_time - oldest_call))
