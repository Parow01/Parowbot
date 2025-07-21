#!/usr/bin/env python3
"""
Cryptocurrency Whale Alert Bot
Main entry point for the bot that monitors Bybit exchange for large transactions
and sends Telegram notifications.
"""

import asyncio
import logging
import signal
import sys
import time
from typing import Optional

from config import Config
from crypto_monitor import CryptoMonitor
from telegram_bot import TelegramNotifier
from whale_detector import WhaleDetector
from utils import setup_logging
from keepalive import KeepAliveServer


class WhaleAlertBot:
    """Main bot class that orchestrates whale detection and notifications."""
    
    def __init__(self):
        """Initialize the whale alert bot."""
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.monitor = None
        self.notifier = None
        self.detector = None
        self.keepalive_server = None
        
    async def initialize(self) -> bool:
        """Initialize all bot components."""
        try:
            # Initialize Crypto monitor
            self.monitor = CryptoMonitor(self.config)
            
            # Initialize Telegram notifier
            self.notifier = TelegramNotifier(self.config)
            await self.notifier.initialize()
            
            # Initialize whale detector
            self.detector = WhaleDetector(self.config)
            
            self.logger.info("Bot components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    async def send_startup_notification(self):
        """Send a notification that the bot has started."""
        try:
            message = """🐋 *PAROWBOT WHALE ALERT – ACTIVATED* 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 *NOW MONITORING 24/7:*

🪙 `Bitcoin (BTC)` → *$10M+*
🪙 `Ethereum (ETH)` → *$2M+*
🪙 `Solana (SOL)` → *$500K+*
🪙 `BNB` → *$500K+*
🪙 `XRP` → *$50K+*
🪙 `Toncoin (TON)` → *$30K+*
🪙 `Cardano (ADA)` → *$20K+*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ *REAL-TIME FEATURES:*
🔍 Inflow & Outflow Detection
📈 TradingView Chart Links
🌐 Multi-Exchange Monitoring
🎯 Price Movement Predictions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *PAROWBOT IS LIVE AND HUNTING WHALES!*"""
            
            await self.notifier.send_message(message)
            self.logger.info("Startup notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send startup notification: {e}")
    
    async def check_whale_transactions(self):
        """Check for whale transactions and send notifications with 24/7 reliability."""
        successful_checks = 0
        
        try:
            for symbol in self.config.MONITORED_SYMBOLS:
                try:
                    # Get recent trades for the symbol
                    trades = await self.monitor.get_recent_trades(symbol)
                    
                    if not trades:
                        # Still count as successful if no trades (not an error)
                        successful_checks += 1
                        continue
                    
                    # Check for whale transactions
                    whale_trades = self.detector.detect_whales(trades, symbol)
                    
                    # Send notifications for whale trades
                    for trade in whale_trades:
                        await self.send_whale_alert(trade, symbol)
                    
                    successful_checks += 1
                    
                    # Small delay between symbols for rate limiting
                    await asyncio.sleep(3)
                        
                except Exception as e:
                    self.logger.warning(f"Error checking {symbol}: {e}")
                    # Continue with other symbols even if one fails
                    continue
            
            # Log status for monitoring
            if successful_checks > 0:
                self.logger.debug(f"Successfully checked {successful_checks}/{len(self.config.MONITORED_SYMBOLS)} symbols")
                    
        except Exception as e:
            self.logger.error(f"Error in whale transaction check: {e}")
    
    async def send_whale_alert(self, trade: dict, symbol: str):
        """Send a whale alert notification for a trade."""
        try:
            # Format the whale alert message
            message = self.format_whale_message(trade, symbol)
            
            # Send the notification
            await self.notifier.send_message(message)
            
            self.logger.info(f"Whale alert sent for {symbol}: {trade.get('qty', 0)} @ {trade.get('price', 0)}")
            
        except Exception as e:
            self.logger.error(f"Failed to send whale alert: {e}")
    
    def format_whale_message(self, trade: dict, symbol: str) -> str:
        """Format a whale transaction with enhanced styling."""
        try:
            qty = float(trade.get('qty', 0))
            price = float(trade.get('price', 0))
            side = trade.get('side', 'Unknown')
            side_label = trade.get('side_label', side.upper())
            timestamp = trade.get('time', 0)
            
            # Calculate USD value
            usd_value = trade.get('usd_value', qty * price)
            
            # Format timestamp
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp / 1000)
            time_str = dt.strftime('%H:%M:%S')
            
            # Determine direction and emojis
            direction = side_label.lower() if side_label else side.lower()
            if 'inflow' in direction or side.lower() == "buy":
                emoji = "🟢📈"
                direction_text = "INFLOW"
                pressure = "POSSIBLE SELL PRESSURE"
                exchange_action = "to"
            else:
                emoji = "🔴📉"
                direction_text = "OUTFLOW" 
                pressure = "POSSIBLE BUY PRESSURE"
                exchange_action = "from"
            
            # Extract base currency
            asset = symbol.replace('USDT', '').replace('USDC', '')
            
            message = f"""🐋 *WHALE ALERT – {direction_text} DETECTED* {emoji}
━━━━━━━━━━━━━━━━━━━━━━━
🪙 *Asset:* `{asset}`
📥 *Type:* {direction_text.title()} {exchange_action} Exchange
💰 *Amount:* `{qty:,.4f} {asset}`
💵 *Price:* `${price:,.4f}`
📦 *Total USD:* `${usd_value:,.2f}`
⏰ *Time:* `{time_str} UTC`
🌐 *Exchanges:* `{trade.get('exchange', 'Multiple Exchanges')}`
📉 *Pair:* `{symbol}`
━━━━━━━━━━━━━━━━━━━━━━━
📊 *Likely Effect:* `{pressure}`
🧭 *Watch next 15 mins for price movement*
📈 [View Chart](https://www.tradingview.com/symbols/{symbol.replace('USDT', 'USD')}/)"""
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting whale message: {e}")
            return f"🐋 Large {symbol} transaction detected - ${trade.get('usd_value', 0):,.0f}"
    
    async def run_monitoring_loop(self):
        """Main monitoring loop."""
        self.logger.info("Starting whale monitoring loop")
        
        while self.running:
            try:
                await self.check_whale_transactions()
                await asyncio.sleep(self.config.CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                self.logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def start(self):
        """Start the whale alert bot with 24/7 capabilities."""
        self.logger.info("Starting Whale Alert Bot")
        
        # Initialize components
        if not await self.initialize():
            self.logger.error("Failed to initialize bot components")
            return False
        
        # Start keep-alive server for 24/7 operation
        try:
            self.keepalive_server = KeepAliveServer(port=5000)
            await self.keepalive_server.start()
            self.logger.info("Keep-alive server started for 24/7 operation")
        except Exception as e:
            self.logger.warning(f"Keep-alive server failed to start: {e}")
        
        # Send startup notification
        await self.send_startup_notification()
        
        # Start monitoring
        self.running = True
        
        # Run both monitoring and keep-alive concurrently
        try:
            await self.run_monitoring_loop()
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
            # Try to send error notification
            try:
                await self.notifier.send_message(f"🚨 Bot encountered error: {str(e)[:100]}...")
            except:
                pass
        
        return True
    
    async def stop(self):
        """Stop the whale alert bot."""
        self.logger.info("Stopping Whale Alert Bot")
        self.running = False
        
        # Stop keep-alive server
        if self.keepalive_server:
            try:
                await self.keepalive_server.stop()
                self.logger.info("Keep-alive server stopped")
            except Exception as e:
                self.logger.error(f"Error stopping keep-alive server: {e}")
        
        # Clean up notifier
        if self.notifier:
            try:
                await self.notifier.send_message("🤖 Whale Alert Bot Stopped")
                await self.notifier.cleanup()
            except Exception as e:
                self.logger.error(f"Error during notifier cleanup: {e}")
        
        # Clean up monitor
        if self.monitor:
            try:
                await self.monitor.cleanup()
            except Exception as e:
                self.logger.error(f"Error during monitor cleanup: {e}")


async def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create bot instance
    bot = WhaleAlertBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
