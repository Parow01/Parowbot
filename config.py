"""
Configuration module for the Whale Alert Bot.
Handles environment variables and bot settings.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the whale alert bot."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # Exchange API Configuration - Using Binance as fallback
        self.BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
        self.BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")
        self.BYBIT_BASE_URL = os.getenv("BYBIT_BASE_URL", "https://api.bybit.com")
        self.BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
        
        # Monitoring Configuration
        self.CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds - optimized for 24/7
        self.MONITORED_SYMBOLS = self._parse_symbols(
            os.getenv("MONITORED_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT,SOLUSDT")
        )
        
        # Whale Detection Thresholds (in USD)
        self.WHALE_THRESHOLDS = self._parse_thresholds(
            os.getenv("WHALE_THRESHOLDS", "BTC:100000,ETH:50000,BNB:25000,ADA:10000,SOL:15000")
        )
        
        # Default threshold for symbols not explicitly configured
        self.DEFAULT_WHALE_THRESHOLD = float(os.getenv("DEFAULT_WHALE_THRESHOLD", "10000"))
        
        # API Rate Limiting
        self.MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100"))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "whale_bot.log")
        
        # Bot Settings
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
        
        # Validate required configuration
        self._validate_config()
    
    def _parse_symbols(self, symbols_str: str) -> List[str]:
        """Parse comma-separated symbols string into a list."""
        if not symbols_str:
            return ["BTCUSDT", "ETHUSDT"]
        
        symbols = [symbol.strip().upper() for symbol in symbols_str.split(",")]
        return [symbol for symbol in symbols if symbol]
    
    def _parse_thresholds(self, thresholds_str: str) -> Dict[str, float]:
        """Parse threshold configuration string into a dictionary."""
        thresholds = {}
        
        if not thresholds_str:
            return thresholds
        
        try:
            for threshold_pair in thresholds_str.split(","):
                if ":" in threshold_pair:
                    symbol, threshold = threshold_pair.strip().split(":", 1)
                    symbol = symbol.strip().upper()
                    # Remove USDT suffix for threshold mapping
                    if symbol.endswith("USDT"):
                        symbol = symbol[:-4]
                    thresholds[symbol] = float(threshold.strip())
        except ValueError as e:
            print(f"Warning: Error parsing thresholds: {e}")
        
        return thresholds
    
    def get_whale_threshold(self, symbol: str) -> float:
        """Get the whale threshold for a specific symbol."""
        # Remove USDT suffix for threshold lookup
        base_symbol = symbol.replace("USDT", "").replace("USDC", "")
        return self.WHALE_THRESHOLDS.get(base_symbol, self.DEFAULT_WHALE_THRESHOLD)
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        errors = []
        
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not self.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        
        if self.CHECK_INTERVAL < 1:
            errors.append("CHECK_INTERVAL must be at least 1 second")
        
        if not self.MONITORED_SYMBOLS:
            errors.append("At least one symbol must be monitored")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def __str__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        return f"""
        Whale Alert Bot Configuration:
        - Telegram Bot Token: {'*' * 10 if self.TELEGRAM_BOT_TOKEN else 'NOT SET'}
        - Chat ID: {self.TELEGRAM_CHAT_ID}
        - Check Interval: {self.CHECK_INTERVAL}s
        - Monitored Symbols: {', '.join(self.MONITORED_SYMBOLS)}
        - Default Threshold: ${self.DEFAULT_WHALE_THRESHOLD:,}
        - Custom Thresholds: {len(self.WHALE_THRESHOLDS)} configured
        - Log Level: {self.LOG_LEVEL}
        """
