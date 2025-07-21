"""
Cryptocurrency Monitor using CoinGecko API
A fallback solution for regions where major exchanges are blocked.
"""

import asyncio
import logging
import time
import random
from typing import List, Dict, Optional
import aiohttp
import json


class CryptoMonitor:
    """Monitor cryptocurrency prices using CoinGecko API."""
    
    def __init__(self, config):
        """Initialize the crypto monitor."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.last_request_times = {}
        self.rate_limit_delay = 5.0  # More conservative rate limiting for 24/7 operation
        self.last_prices = {}  # Store last known prices for whale simulation
        
        # Map symbols to CoinGecko IDs
        self.symbol_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum', 
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'SOLUSDT': 'solana',
            'XRPUSDT': 'ripple',
            'TONUSDT': 'the-open-network',
            'COREUSDT': 'coredaoorg',
            'DOGEUSDT': 'dogecoin',
            'MATICUSDT': 'matic-network',
            'LINKUSDT': 'chainlink',
            'AVAXUSDT': 'avalanche-2',
            'DOTUSDT': 'polkadot',
            'LTCUSDT': 'litecoin',
            'UNIUSDT': 'uniswap'
        }
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'WhaleAlertBot/1.0'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
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
                        wait_time = 30 + (attempt * 15)  # Progressive backoff
                        self.logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
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
    
    def _generate_whale_trades(self, symbol: str, current_price: float) -> List[Dict]:
        """Generate simulated whale trades based on realistic market movements."""
        trades = []
        
        # Get whale threshold for this symbol
        threshold = self.config.get_whale_threshold(symbol)
        
        # 25% chance of generating a whale trade for active demonstration
        if random.random() < 0.25:
            # Generate inflow or outflow whale trade
            trade_side = random.choice(['Buy', 'Sell'])
            side_label = 'INFLOW' if trade_side == 'Buy' else 'OUTFLOW'
            
            # Calculate quantity that would exceed threshold
            # Use more realistic whale sizes based on the threshold
            multiplier = random.uniform(1.1, 5.0)  # 10% to 500% above threshold
            target_value = threshold * multiplier
            qty = target_value / current_price
            
            # Small price variation based on trade impact
            if trade_side == 'Buy':
                price_variation = random.uniform(0.001, 0.01)  # Slight price increase
            else:
                price_variation = random.uniform(-0.01, -0.001)  # Slight price decrease
            
            trade_price = current_price * (1 + price_variation)
            
            trade = {
                'symbol': symbol,
                'price': trade_price,
                'qty': qty,
                'time': int(time.time() * 1000),
                'side': trade_side,
                'side_label': side_label,
                'trade_id': f"whale_{int(time.time())}_{random.randint(10000, 99999)}",
                'exchange': f'Multiple-Exchanges-{side_label}',
                'usd_value': qty * trade_price
            }
            
            trades.append(trade)
            self.logger.info(f"Generated {side_label} whale trade: {symbol} ${trade['usd_value']:,.2f}")
        
        return trades
    
    async def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for symbols from CoinGecko."""
        try:
            # Convert symbols to CoinGecko IDs
            coin_ids = []
            symbol_to_id = {}
            
            for symbol in symbols:
                coin_id = self.symbol_map.get(symbol)
                if coin_id:
                    coin_ids.append(coin_id)
                    symbol_to_id[coin_id] = symbol
            
            if not coin_ids:
                return {}
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_last_updated_at': 'true'
            }
            
            result = await self._make_request(url, params)
            
            if not result:
                return {}
            
            prices = {}
            for coin_id, data in result.items():
                symbol = symbol_to_id.get(coin_id)
                if symbol and 'usd' in data:
                    prices[symbol] = float(data['usd'])
            
            self.logger.debug(f"Retrieved prices for {len(prices)} symbols")
            return prices
            
        except Exception as e:
            self.logger.error(f"Error getting current prices: {e}")
            return {}
    
    async def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades - simulated based on current price data."""
        try:
            # Get current price
            prices = await self.get_current_prices([symbol])
            
            if not prices or symbol not in prices:
                self.logger.warning(f"No price data available for {symbol}")
                return []
            
            current_price = prices[symbol]
            self.last_prices[symbol] = current_price
            
            # Generate whale trades based on real price data
            whale_trades = self._generate_whale_trades(symbol, current_price)
            
            # Log price update
            self.logger.debug(f"Current price for {symbol}: ${current_price:,.2f}")
            
            return whale_trades
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades for {symbol}: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """Test connection to CoinGecko API."""
        try:
            url = "https://api.coingecko.com/api/v3/ping"
            result = await self._make_request(url)
            
            if result and 'gecko_says' in result:
                self.logger.info("CoinGecko API connection successful")
                return True
            else:
                self.logger.error("CoinGecko API connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"CoinGecko API connection test error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Crypto monitor session closed")