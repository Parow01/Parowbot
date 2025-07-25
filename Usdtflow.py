import aiohttp
import datetime
import logging

EXCHANGE_LABELS = ["Binance", "OKX", "Huobi", "Bybit", "KuCoin"]
TRONSCAN_API = "https://apilist.tronscanapi.com/api/transfer/trc20"

async def fetch_trc20_transfers():
    now = int(datetime.datetime.utcnow().timestamp() * 1000)
    four_hours_ago = now - (4 * 60 * 60 * 1000)
    url = f"{TRONSCAN_API}?limit=50&start=0&sort=-timestamp&count=true&start_timestamp={four_hours_ago}&end_timestamp={now}&token=USDT"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data.get("data", [])
    except Exception as e:
        logging.error(f"TRONSCAN error: {e}")
        return []

def is_exchange(wallet_label):
    if not wallet_label:
        return False
    return any(name.lower() in wallet_label.lower() for name in EXCHANGE_LABELS)

async def get_usdt_summary():
    txs = await fetch_trc20_transfers()
    inflow, outflow = 0, 0

    for tx in txs:
        amount = int(tx["quant"]) / 1_000_000
        from_label = tx.get("fromAddressTag", "")
        to_label = tx.get("toAddressTag", "")

        if is_exchange(from_label) and not is_exchange(to_label):
            outflow += amount
        elif is_exchange(to_label) and not is_exchange(from_label):
            inflow += amount

    net = inflow - outflow
    trend = "⬇️ More Outflow" if net < 0 else "⬆️ More Inflow"
    emoji = "🔻" if net < 0 else "🟢"

    summary = (
        f"💵 *TRC20 USDT Flow (Last 4h)*\n\n"
        f"🔺 *Outflow*: ${outflow:,.2f}\n"
        f"🔻 *Inflow*: ${inflow:,.2f}\n"
        f"{emoji} *Net*: ${net:,.2f} ({trend})"
    )

    return summary
