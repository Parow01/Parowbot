"""
Telegram Bot Module
Handles sending notifications via Telegram Bot API.
"""

import asyncio
import logging
from typing import Optional
import aiohttp
import json


class TelegramNotifier:
    """Handles Telegram notifications for whale alerts."""
    
    def __init__(self, config):
        """Initialize the Telegram notifier."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.base_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def initialize(self) -> bool:
        """Initialize and test the Telegram bot."""
        try:
            # Test bot token by getting bot info
            if await self.test_connection():
                self.logger.info("Telegram bot initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize Telegram bot")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing Telegram bot: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test the Telegram bot connection."""
        try:
            url = f"{self.base_url}/getMe"
            
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        bot_name = bot_info.get('username', 'Unknown')
                        self.logger.info(f"Connected to Telegram bot: @{bot_name}")
                        return True
                    else:
                        self.logger.error(f"Telegram API error: {data.get('description', 'Unknown')}")
                        return False
                else:
                    self.logger.error(f"HTTP {response.status}: {await response.text()}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Telegram connection test error: {e}")
            return False
    
    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to the configured Telegram chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            
            data = {
                'chat_id': self.config.TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            for attempt in range(self.config.MAX_RETRIES):
                try:
                    session = await self._get_session()
                    
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            if response_data.get('ok'):
                                self.logger.debug("Message sent successfully")
                                return True
                            else:
                                error_desc = response_data.get('description', 'Unknown error')
                                self.logger.error(f"Telegram API error: {error_desc}")
                                
                                # Don't retry for certain errors
                                if 'chat not found' in error_desc.lower():
                                    return False
                                    
                        elif response.status == 429:  # Rate limited
                            retry_after = int(response.headers.get('Retry-After', 1))
                            self.logger.warning(f"Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
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
            
            self.logger.error(f"Failed to send message after {self.config.MAX_RETRIES} attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_whale_alert(self, trade_data: dict, symbol: str) -> bool:
        """Send a formatted whale alert message."""
        try:
            # Format the message with emojis and styling
            message = self._format_whale_alert(trade_data, symbol)
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending whale alert: {e}")
            return False
    
    def _format_whale_alert(self, trade: dict, symbol: str) -> str:
        """Format a whale alert message with proper styling."""
        try:
            qty = float(trade.get('qty', 0))
            price = float(trade.get('price', 0))
            side = trade.get('side', 'Unknown')
            timestamp = trade.get('time', 0)
            
            # Calculate USD value
            usd_value = qty * price
            
            # Format timestamp
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp / 1000)
            time_str = dt.strftime('%H:%M:%S UTC')
            
            # Determine styling based on trade side
            if side.lower() == 'buy':
                side_emoji = "🟢"
                side_text = "BUY"
            else:
                side_emoji = "🔴"
                side_text = "SELL"
            
            # Extract base currency
            base_currency = symbol.replace('USDT', '').replace('USDC', '')
            
            message = f"🐋 <b>WHALE ALERT</b> 🐋\n\n"
            message += f"{side_emoji} <b>{side_text}</b> {symbol}\n"
            message += f"💰 <b>Amount:</b> {qty:,.4f} {base_currency}\n"
            message += f"💵 <b>Price:</b> ${price:,.2f}\n"
            message += f"💸 <b>Value:</b> ${usd_value:,.2f}\n"
            message += f"⏰ <b>Time:</b> {time_str}\n"
            message += f"🏢 <b>Exchange:</b> Bybit"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting whale alert: {e}")
            return f"🐋 Whale transaction detected for {symbol}"
    
    async def send_status_update(self, status: str, details: str = "") -> bool:
        """Send a status update message."""
        try:
            message = f"🤖 <b>Bot Status Update</b>\n\n"
            message += f"Status: {status}\n"
            if details:
                message += f"Details: {details}\n"
            
            import datetime
            message += f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
            return False
    
    async def send_error_alert(self, error_msg: str) -> bool:
        """Send an error alert message."""
        try:
            message = f"⚠️ <b>Bot Error Alert</b>\n\n"
            message += f"Error: {error_msg}\n"
            
            import datetime
            message += f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending error alert: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()


            self.logger.info("Telegram notifier session closed")
Fix syntax error in telegram_bot.py


