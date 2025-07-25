import requests
from datetime import datetime, timedelta

def get_usdtflow_summary():
    try:
        base_url = "https://apilist.tronscanapi.com/api/token_trc20/transfers"
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(hours=4)).timestamp() * 1000)

        params = {
            "limit": 100,
            "start_timestamp": start_time,
            "end_timestamp": end_time,
            "token": "Tether USD",
            "sort": "-timestamp"
        }

        inflow, outflow = 0, 0
        exchanges = ["binance", "kucoin", "okx", "huobi", "mexc", "coinbase", "bybit"]

        resp = requests.get(base_url, params=params)
        data = resp.json()

        for tx in data.get("token_transfers", []):
            to_addr = tx.get("to_address_tag", "").lower()
            from_addr = tx.get("from_address_tag", "").lower()
            amount = int(tx.get("quant")) / 1e6

            if any(ex in to_addr for ex in exchanges):
                inflow += amount
            elif any(ex in from_addr for ex in exchanges):
                outflow += amount

        net = inflow - outflow
        symbol = "📈" if net > 0 else "📉"

        return (
            f"*USDT Flow Summary (TRC20)*\n\n"
            f"🔹 *Inflow:* ${inflow:,.0f}\n"
            f"🔸 *Outflow:* ${outflow:,.0f}\n"
            f"{symbol} *Net:* ${net:,.0f}"
        )
    except Exception as e:
        print("Error in get_usdtflow_summary:", e)
        return "⚠️ Error fetching USDT data."


