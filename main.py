import telebot
import requests
import threading
import time
import os
from usdtflow import get_usdtflow_summary

BOT_TOKEN = os.getenv("BOT_TOKEN") or "your_token_here"
bot = telebot.TeleBot(BOT_TOKEN)

# START command
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.reply_to(message, "👋 *Parowalertbot is live!*\nUse /usdtflow to get TRC20 USDT inflow/outflow summary.", parse_mode="Markdown")

# USDTFLOW command
@bot.message_handler(commands=["usdtflow"])
def handle_usdtflow(message):
    bot.send_chat_action(message.chat.id, "typing")
    try:
        summary = get_usdtflow_summary()
        bot.send_message(message.chat.id, summary, parse_mode="Markdown")
    except Exception as e:
        print("Error in /usdtflow:", e)
        bot.send_message(message.chat.id, "⚠️ Couldn't fetch USDT flow data.")

# Dummy whale alert loop (replace with your actual whale logic if needed)
def whale_alert_loop():
    while True:
        time.sleep(30)  # Placeholder for whale alert timing
        # Example whale alert (you can comment/remove)
        # bot.send_message(CHAT_ID, "🐋 Example Whale Transfer Alert")

# Start whale alert in background
threading.Thread(target=whale_alert_loop, daemon=True).start()

# Start polling
print("Bot is running...")
bot.infinity_polling()





