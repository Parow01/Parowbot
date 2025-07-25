import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.exceptions import TelegramAPIError
from whale_detector import fetch_whale_alerts, format_whale_message
from usdt_flow import get_usdt_summary  # Next file
from system_status import get_status_summary  # Optional, if you add it
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

last_alert_ids = set()

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.reply("👋 Welcome to *Parowalertbot*! I'm live and monitoring whales 🐋, USDT flow 💸, and market news 📊. Use /summary to get today's top alerts.")

@dp.message_handler(commands=["status"])
async def handle_status(message: types.Message):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    await message.reply(f"✅ Bot is live.\n🕒 Time: {now}")

@dp.message_handler(commands=["summary"])
async def handle_summary(message: types.Message):
    try:
        whales = await fetch_whale_alerts()
        if not whales:
            await message.reply("🔍 No major whale activity in the last 5 minutes.")
        else:
            msg = "\n\n".join([format_whale_message(tx) for tx in whales[:3]])
            await message.reply(f"📊 *Top Whale Alerts*\n\n{msg}")
    except Exception as e:
        logging.error(f"Summary error: {e}")
        await message.reply("⚠️ Failed to get summary.")

@dp.message_handler(commands=["usdtflow"])
async def handle_usdtflow(message: types.Message):
    try:
        summary = await get_usdt_summary()
        await message.reply(summary)
    except Exception as e:
        logging.error(f"USDT flow error: {e}")
        await message.reply("⚠️ Couldn't fetch USDT data.")

async def send_whale_alerts_periodically(chat_id):
    global last_alert_ids
    while True:
        try:
            alerts = await fetch_whale_alerts()
            new_alerts = [tx for tx in alerts if tx["id"] not in last_alert_ids]
            for tx in new_alerts:
                text = format_whale_message(tx)
                await bot.send_message(chat_id=chat_id, text=text)
                last_alert_ids.add(tx["id"])
            await asyncio.sleep(60)
        except TelegramAPIError as tg_err:
            logging.error(f"Telegram Error: {tg_err}")
        except Exception as e:
            logging.error(f"Background loop error: {e}")
            await asyncio.sleep(120)

def start_bot(chat_id):
    loop = asyncio.get_event_loop()
    loop.create_task(send_whale_alerts_periodically(chat_id))
    loop.run_until_complete(dp.start_polling())
