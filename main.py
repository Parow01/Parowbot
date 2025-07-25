import asyncio
import logging
from telegram_bot import TelegramNotifier
from whale_detector import WhaleDetector
from config import Config
from keepalive import keep_alive  # optional, if you use it
import datetime

class WhaleAlertBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.notifier = TelegramNotifier(self.config)
        self.detector = WhaleDetector(self.config, self.notifier)
        self.running = True
        self.start_time = datetime.datetime.now()

    async def run_monitoring_loop(self):
        self.logger.info("Whale monitor started.")
        while self.running:
            try:
                await self.detector.check_whale_activity()
            except Exception as e:
                self.logger.error(f"Error in whale monitoring: {e}")
            await asyncio.sleep(self.config.CHECK_INTERVAL)

    async def handle_telegram_commands(self):
        """Poll Telegram for /start, /status, /summary commands."""
        last_update_id = None
        while self.running:
            try:
                session = await self.notifier._get_session()
                url = f"{self.notifier.base_url}/getUpdates"
                params = {"timeout": 10, "offset": last_update_id + 1 if last_update_id else None}
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    updates = data.get("result", [])
                    for update in updates:
                        last_update_id = update["update_id"]
                        message = update.get("message", {})
                        if not message:
                            continue
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        if str(chat_id) != str(self.config.TELEGRAM_CHAT_ID):
                            continue  # Only respond to owner's chat
                        if text == "/start":
                            await self.notifier.send_message("👋 Welcome to *Parowbot*!\nTracking whales in real time.", parse_mode="Markdown")
                        elif text == "/status":
                            uptime = datetime.datetime.now() - self.start_time
                            formatted = f"{uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
                            await self.notifier.send_message(f"✅ Bot is live!\nUptime: {formatted}", parse_mode="Markdown")
                        elif text == "/summary":
                            await self.notifier.send_message("📊 *Top 3 alerts today:*\n1. BTC 10M in\n2. ETH 5M out\n3. XRP_

