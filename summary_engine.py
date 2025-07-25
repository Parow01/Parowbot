from whale_detector import get_whale_summary
from usdt_flow import get_usdt_summary

async def generate_daily_summary():
    parts = []

    whale_summary = await get_whale_summary()
    parts.append(whale_summary)

    usdt_summary = await get_usdt_summary()
    parts.append(usdt_summary)

    # TODO: Add macro/stock/heatmap summaries later

    return "\n\n".join(parts)
