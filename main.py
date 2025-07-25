import logging
import time
import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from whale_detector import check_whale_activity
from utils import get_system_status, get_summary, get_usdt_flow
from keepalive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Optional: hardcoded fallback
ALERT_INTERVAL = 120  # seconds between whale checks
LAST_ALERT_TIME = 0

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Telegram Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to Parowalertbot!\nUse /summary, /status, /usdtflow")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_system_status()
    await update.message.reply_text(status)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = get_summary()
    await update.message.reply_text(summary)

async def usdtflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = await get_usdt_flow()
    await update.message.reply_text(flow)

# Whale Alert Loop
async def alert_loop(application):
    global LAST_ALERT_TIME
    while True:
        now = time.time()
        if now - LAST_ALERT_TIME >= ALERT_INTERVAL:
            try:
                message = check_whale_activity()
                if message:
                    await application.bot.send_message(chat_id=CHAT_ID, text=message)
                    LAST_ALERT_TIME = now
            except Exception as e:
                logging.error(f"Error sending alert: {e}")
        await asyncio.sleep(10)

# Main app start
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("usdtflow", usdtflow))

    # Keepalive for Render
    keep_alive()

    # Start whale alerts
    asyncio.create_task(alert_loop(application))

    # Run bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())



