import requests
from datetime import datetime, timedelta

TRON_API = "https://apilist.tronscanapi.com/api/token_trc20/transfers"
EXCHANGE_ADDRESSES = [
    "binance", "huobi", "kucoin", "okx", "bybit", "bitfinex", "gate", "mexc"
]

def get_recent_usdt_transfers(hours=4, limit=100):
    now = datetime.utcnow()
    start_time = int((now - timedelta(hours=hours)).timestamp() * 1000)
    transfers = []
    offset = 0

    while len(transfers) < 1000:  # cap to avoid large memory use
        params = {
            "limit": limit,
            "start": offset,
            "sort": "-timestamp",
            "start_timestamp": start_time,
            "token": "Tether USD",
            "trc20Id": "1002000"  # USDT
        }

        try:
            res = requests.get(TRON_API, params=params, timeout=10)
            data = res.json()
            items = data.get("token_transfers", [])

            if not items:
                break

            transfers.extend(items)
            offset += limit
        except Exception as e:
            print("USDT scrape error:", e)
            break

    return transfers


def summarize_usdt_flows(transfers):
    inflow = 0
    outflow = 0

    for tx in transfers:
        to = tx.get("to_address_tag", "").lower()
        from_ = tx.get("from_address_tag", "").lower()
        amount = float(tx.get("quant", 0)) / 1e6  # USDT has 6 decimals

        if any(exchange in to for exchange in EXCHANGE_ADDRESSES):
            inflow += amount
        elif any(exchange in from_ for exchange in EXCHANGE_ADDRESSES):
            outflow += amount

    net = inflow - outflow
    return inflow, outflow, net


def get_usdtflow_summary():
    transfers = get_recent_usdt_transfers()
    inflow, outflow, net = summarize_usdt_flows(transfers)

    summary = f"""
📊 *USDT Flow (TRC20, last 4h)*

🔻 Outflow: ${outflow:,.2f}
🔺 Inflow: ${inflow:,.2f}
🧮 Net Flow: {'+' if net > 0 else ''}${net:,.2f}

{("🔵 Net Inflow to Exchanges" if net > 0 else "🔴 Net Outflow from Exchanges")}
""".strip()
    return summary

