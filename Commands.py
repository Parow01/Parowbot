import time

start_time = time.time()

def handle_start():
    return (
        "👋 *Welcome to Parowalertbot!*\n\n"
        "I'm live and monitoring:\n"
        "🐋 Whale alerts\n"
        "💸 USDT flows\n"
        "📉 Liquidation heatmaps\n"
        "📊 Macro & NASDAQ events\n\n"
        "Use /status, /summary, or /usdtflow."
    )

def handle_status():
    uptime = int(time.time() - start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    return f"📡 Bot is online.\nUptime: {hours}h {minutes}m"

def handle_summary():
    return "📊 Summary not ready yet.\n(Coming soon: top 3 market alerts of the day)"

def handle_usdtflow():
    return "💸 USDT flow report is coming soon...\n(This will detect net in/out from exchanges)"
