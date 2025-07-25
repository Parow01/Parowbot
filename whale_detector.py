import aiohttp
import datetime

WHALE_ALERT_URL = "https://api.whale-alert.io/v1/transactions"
API_KEY = os.getenv("WHALE_ALERT_API_KEY")  # Put your key in Render environment variables

async def fetch_whale_alerts():
    params = {
        "api_key": API_KEY,
        "min_value": 5000000,
        "start": int(datetime.datetime.now().timestamp()) - 300,
        "limit": 10,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(WHALE_ALERT_URL, params=params) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("transactions", [])

def format_whale_message(tx):
    symbol = tx.get("symbol", "crypto")
    amount = tx.get("amount", 0)
    from_exchange = tx.get("from", {}).get("owner", "unknown")
    to_exchange = tx.get("to", {}).get("owner", "unknown")
    timestamp = datetime.datetime.fromtimestamp(tx.get("timestamp"))
    direction = "⬅️ *IN* to Exchange" if "exchange" in to_exchange.lower() else "➡️ *OUT* from Exchange"

    return (
        f"🐋 *Whale Alert*\n"
        f"Asset: {symbol.upper()}\n"
        f"Amount: ${amount:,.2f}\n"
        f"From: {from_exchange}\n"
        f"To: {to_exchange}\n"
        f"Time: {timestamp.strftime('%H:%M UTC')}\n"
        f"{direction}"
    )

