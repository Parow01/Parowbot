import aiohttp
import logging

WHALE_ALERT_API = "https://api.whale-alert.io/v1/transactions"
WHALE_ALERT_API_KEY = "your_api_key_here"  # Replace with your real Whale Alert API key

MIN_USD = 5_000_000  # Only alert transfers >= $5M

async def fetch_whale_transfers():
    url = f"{WHALE_ALERT_API}?api_key={WHALE_ALERT_API_KEY}&min_value={MIN_USD}&limit=10"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data.get("transactions", [])
    except Exception as e:
        logging.error(f"Whale Alert fetch failed: {e}")
        return []

async def get_whale_summary():
    txs = await fetch_whale_transfers()
    if not txs:
        return "🐋 No major whale transfers in the last few hours."

    lines = ["🐋 *Whale Transfers > $5M* (recent):\n"]
    for tx in txs[:3]:  # Show only top 3 for summary
        amount = f"{tx['amount']:,.0f} {tx['symbol']}"
        usd = f"${tx['amount_usd']:,.0f}"
        from_ex = tx['from']['owner'] or "Unknown"
        to_ex = tx['to']['owner'] or "Unknown"
        lines.append(f"{usd} ({amount})\n→ *{to_ex}*\n← *{from_ex}*\n")

    return "\n".join(lines)


