import asyncio
import logging
import os
import time
import sys
import tracemalloc
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from whale_detector import monitor_whales  # Your alert engine
from keepalive import keep_alive  # Optional keepalive web server
from utils import get_system_status, get_top_alerts_summary  # Utilities you'll define
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track uptime
START_TIME = time.time()
tracemalloc.start()

# Load config
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN not found in environment variables.")
    sys.exit(1)

bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm Parowalertbot — your whale alert assistant.\n"
        "Use /summary for top events, or /status to check system status."
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary_text = get_top_alerts_summary()
    await update.message.reply_text(summary_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = time.time() - START_TIME
    current, peak = tracemalloc.get_traced_memory()
    ram_used = round(current / (1024 * 1024), 2)
    ram_peak = round(peak / (1024 * 1024), 2)
    await update.message.reply_text(
        f"📊 *Parowbot Status*\n"
        f"• Uptime: {int(uptime // 3600)}h {int((uptime % 3600) // 60)}m\n"
        f"• RAM: {ram_used}MB (peak {ram_peak}MB)\n"
        f"• Active Alerts: ✅\n"
        f"• Last Check: {datetime.utcnow().strftime('%H:%M UTC')}",
        parse_mode="Markdown"
    )

# === STARTUP TASKS ===
async def main():
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("status", status))

    # Start background whale monitoring
    asyncio.create_task(monitor_whales(bot))

    # Optional: run local keepalive server for Render
    try:
        keep_alive()
    except Exception as e:
        logger.warning(f"Keepalive server failed: {e}")

    # Run bot
    await application.run_polling()

# === ENTRY POINT ===
if __name__ == "__main__":
    asyncio.run(main())


