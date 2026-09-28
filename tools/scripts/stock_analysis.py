import os
import json

DEFAULT_STOCKS = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "base_price": 118.50, "change_pct": 5.82},
    {"symbol": "AAPL", "name": "Apple Inc.", "base_price": 224.30, "change_pct": 1.25},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "base_price": 432.10, "change_pct": -0.84},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "base_price": 164.75, "change_pct": 3.14},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "base_price": 186.20, "change_pct": 2.45},
    {"symbol": "TSLA", "name": "Tesla Inc.", "base_price": 242.60, "change_pct": -4.68},
    {"symbol": "META", "name": "Meta Platforms Inc.", "base_price": 512.90, "change_pct": 4.10},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "base_price": 149.80, "change_pct": 6.35},
    {"symbol": "INTC", "name": "Intel Corporation", "base_price": 19.45, "change_pct": -5.92},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "base_price": 168.20, "change_pct": 3.75},
    {"symbol": "CRM", "name": "Salesforce Inc.", "base_price": 252.10, "change_pct": -1.15},
    {"symbol": "PLTR", "name": "Palantir Technologies", "base_price": 36.40, "change_pct": 8.42},
    {"symbol": "SMCI", "name": "Super Micro Computer", "base_price": 44.50, "change_pct": -7.85},
    {"symbol": "QCOM", "name": "Qualcomm Inc.", "base_price": 165.90, "change_pct": -2.30},
    {"symbol": "ARM", "name": "Arm Holdings plc", "base_price": 138.70, "change_pct": 5.12},
]

def analyze_stocks(criterion="highest", limit=5):
    """
    Get the list of stocks with highest percentage increase or lowest percentage decrease.
    criterion: 'highest' / 'gainers' or 'lowest' / 'losers'
    """
    stocks = list(DEFAULT_STOCKS)
    crit = (criterion or "highest").lower()

    if "low" in crit or "drop" in crit or "decreas" in crit or "loser" in crit:
        # Lowest percentage decrease (most negative change)
        sorted_stocks = sorted(stocks, key=lambda x: x["change_pct"])
    else:
        # Highest percentage increase (most positive change)
        sorted_stocks = sorted(stocks, key=lambda x: x["change_pct"], reverse=True)

    limit = max(1, min(int(limit), len(sorted_stocks)))
    return sorted_stocks[:limit]

if __name__ == "__main__":
    print("Highest gainers:")
    print(json.dumps(analyze_stocks("highest", 3), indent=2))
    print("Lowest losers:")
    print(json.dumps(analyze_stocks("lowest", 3), indent=2))
