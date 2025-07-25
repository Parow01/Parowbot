import time
start_time = time.time()

def handle_start():
    return "👋 *Welcome to Parowalertbot!*\nI'm watching the whales..."

def handle_status():
    uptime = int(time.time() - start_time)
    return f"📡 Bot live. Uptime: {uptime // 3600}h {(uptime % 3600) // 60}m"

def handle_summary():
    return "📊 Summary coming soon..."

def handle_usdtflow():
    return "💸 USDT flow tracker is coming soon..."
