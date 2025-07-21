"""
Multi-Exchange Monitor
Handles interaction with multiple cryptocurrency exchanges with automatic fallback.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional
import aiohttp
import json


class ExchangeMonitor:
    """Monitor multiple cryptocurrency exchanges with automatic fallback."""
    
    def __init__(self, config):
        """Initialize the exchange monitor."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.last_request_times = {}
        self.rate_limit_delay = 60 / config.MAX_REQUESTS_PER_MINUTE
        self.current_exchange = "binance"  # Start with Binance as primary
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _rate_limit(self):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        if hasattr(self, '_last_request_time'):
            time_since_last = current_time - self._last_request_time
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self._last_request_time = time.time()
    
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request with error handling and retries."""
        params = params or {}
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                await self._rate_limit()
                
                session = await self._get_session()
                
                self.logger.debug(f"Making request to {url} with params: {params}")
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    
                    elif response.status == 429:  # Rate limited
                        self.logger.warning("Rate limited, waiting before retry")
                        await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                        continue
                    
                    else:
                        self.logger.error(f"HTTP {response.status}: {await response.text()}")
                        
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout on attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                self.logger.error(f"Client error on attempt {attempt + 1}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            if attempt < self.config.MAX_RETRIES - 1:
                await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
        
        self.logger.error(f"Failed to make request after {self.config.MAX_RETRIES} attempts")
        return None
    
    async def get_recent_trades_binance(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades from Binance."""
        try:
            url = f"{self.config.BINANCE_BASE_URL}/api/v3/trades"
            params = {
                'symbol': symbol,
                'limit': min(limit, 1000)
            }
            
            result = await self._make_request(url, params)
            
            if not result:
                self.logger.warning(f"No data received from Binance for {symbol}")
                return []
            
            # Process Binance trade data
            processed_trades = []
            for trade in result:
                try:
                    processed_trade = {
                        'symbol': symbol,
                        'price': float(trade.get('price', 0)),
                        'qty': float(trade.get('qty', 0)),
                        'time': int(trade.get('time', 0)),
                        'side': 'Buy' if trade.get('isBuyerMaker', False) else 'Sell',
                        'trade_id': trade.get('id', ''),
                        'exchange': 'Binance'
                    }
                    processed_trades.append(processed_trade)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error processing Binance trade data: {e}")
                    continue
            
            self.logger.debug(f"Retrieved {len(processed_trades)} trades from Binance for {symbol}")
            return processed_trades
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades from Binance for {symbol}: {e}")
            return []
    
    async def get_recent_trades_bybit(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades from Bybit."""
        try:
            url = f"{self.config.BYBIT_BASE_URL}/v5/market/recent-trade"
            params = {
                'category': 'spot',
                'symbol': symbol,
                'limit': min(limit, 1000)
            }
            
            result = await self._make_request(url, params)
            
            if not result:
                return []
            
            # Check Bybit response format
            if 'retCode' in result and result['retCode'] == 0:
                trades = result.get('result', {}).get('list', [])
            else:
                return []
            
            # Process Bybit trade data
            processed_trades = []
            for trade in trades:
                try:
                    processed_trade = {
                        'symbol': symbol,
                        'price': float(trade.get('price', 0)),
                        'qty': float(trade.get('size', 0)),
                        'time': int(trade.get('time', 0)),
                        'side': trade.get('side', 'Unknown'),
                        'trade_id': trade.get('execId', ''),
                        'exchange': 'Bybit'
                    }
                    processed_trades.append(processed_trade)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error processing Bybit trade data: {e}")
                    continue
            
            self.logger.debug(f"Retrieved {len(processed_trades)} trades from Bybit for {symbol}")
            return processed_trades
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades from Bybit for {symbol}: {e}")
            return []
    
    async def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades with automatic exchange fallback."""
        # Try Binance first (more reliable globally)
        trades = await self.get_recent_trades_binance(symbol, limit)
        
        if trades:
            self.current_exchange = "binance"
            return trades
        
        # Fallback to Bybit
        self.logger.info(f"Binance failed for {symbol}, trying Bybit...")
        trades = await self.get_recent_trades_bybit(symbol, limit)
        
        if trades:
            self.current_exchange = "bybit"
            return trades
        
        self.logger.warning(f"Both exchanges failed for {symbol}")
        return []
    
    async def test_connection(self) -> bool:
        """Test connection to available exchanges."""
        try:
            # Test Binance
            binance_url = f"{self.config.BINANCE_BASE_URL}/api/v3/ping"
            binance_result = await self._make_request(binance_url)
            
            if binance_result is not None:
                self.logger.info("Binance API connection successful")
                return True
            
            # Test Bybit
            bybit_url = f"{self.config.BYBIT_BASE_URL}/v5/market/time"
            bybit_result = await self._make_request(bybit_url)
            
            if bybit_result and bybit_result.get('retCode') == 0:
                self.logger.info("Bybit API connection successful")
                return True
            
            self.logger.error("Both exchange APIs failed")
            return False
                
        except Exception as e:
            self.logger.error(f"Exchange connection test error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Exchange monitor session closed")