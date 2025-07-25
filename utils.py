import os
import time
import psutil
import requests
import datetime

start_time = time.time()
alert_counter = 0

def get_system_status():
    uptime_seconds = int(time.time() - start_time)
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
    ram_usage = psutil.virtual_memory().percent
    return f"📊 *Bot Status*\nUptime: `{uptime_str}`\nRAM Usage: `{ram_usage}%`\nAlerts Sent: `{alert_counter}`"

def get_summary():
    return (
        "📈 *Daily Summary*\n"
        "1. Top Whale Transfer ✅\n"
        "2. Net USDT Flow: $48M outflow 🟥\n"
        "3. BTC Exchange Supply ⬇️\n"
        "4. Liquidation Risk Cluster: $90M @ $59.2k\n"
        "5. Tesla -5.7% crash ⚠️\n"
        "—\n"
        "_Market cautious. Potential volatility ahead._"
    )

async def get_usdt_flow():
    try:
        url = "https://apilist.tronscanapi.com/api/token_trc20/transfers?limit=50&start=0&sort=-timestamp&count=true&filterTokenValue=1000000&relatedAddress=Binance"
        response = requests.get(url)
        data = response.json().get("data", [])
        
        inflow = outflow = 0
        for tx in data:
            value = int(tx["amount_str"]) / 1e6
            if "Binance" in tx["toAddress"] or "binance" in tx.get("toAddressTag", ""):
                inflow += value
            elif "Binance" in tx["fromAddress"] or "binance" in tx.get("fromAddressTag", ""):
                outflow += value

        net = inflow - outflow
        return (
            f"💸 *USDT Flows (TRC20)*\n"
            f"Inflow: ${inflow:,.2f}\n"
            f"Outflow: ${outflow:,.2f}\n"
            f"Net Flow: `${net:,.2f}`"
        )
    except Exception as e:
        return f"Error fetching USDT data: {str(e)}"

