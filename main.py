import logging
import os
import telegram
from telegram.ext import Updater, CommandHandler
from usdtflow import get_usdtflow_summary
from keepalive import keep_alive

# Telegram bot token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing!")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Command: /start
def start(update, context):
    update.message.reply_text("👋 Welcome to Parowalertbot!\nUse /usdtflow to get TRC20 USDT inflow/outflow summary.")

# Command: /usdtflow
def usdtflow(update, context):
    summary = get_usdtflow_summary()
    update.message.reply_text(summary, parse_mode=telegram.ParseMode.MARKDOWN)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("usdtflow", usdtflow))

    # Start bot
    updater.start_polling()
    logger.info("Bot started...")
    updater.idle()

if __name__ == '__main__':
    keep_alive()
    main()






