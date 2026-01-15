import requests
from typing import Any


SILO_RATES_URL = "https://app.silo.finance/api/lending-market/avalanche/142/rates"
SILO_MARKET_KEY = "silo1"
SILO_SERIES = "24h"

SILO_SCALE = 1e18  # borrowApr is scaled by 1e18


def _to_int(x: Any) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("__bigint__"):
            s = s.replace("__bigint__", "")
        if s.startswith("0x"):
            return int(s, 16)
        return int(s)
    raise TypeError(f"Cannot convert to int: {x}")


def fetch_usdc_borrow_rate() -> dict:
    """
    Returns borrow APR as a decimal (e.g. 0.089 for 8.9%)
    """
    r = requests.get(SILO_RATES_URL, timeout=20)
    r.raise_for_status()
    data = r.json()

    market = data.get(SILO_MARKET_KEY)
    if not market:
        raise RuntimeError(f"Silo payload missing key '{SILO_MARKET_KEY}'")

    series = market.get("data", {}).get(SILO_SERIES)
    if not isinstance(series, list) or not series:
        raise RuntimeError("Silo rates series missing or empty")

    # pick latest non-zero borrowApr
    chosen = series[-1]
    for pt in reversed(series):
        try:
            raw = _to_int(pt.get("borrowApr", "0"))
            if raw != 0:
                chosen = pt
                break
        except Exception:
            continue

    raw = _to_int(chosen.get("borrowApr", "0"))
    rate_pct = (raw / SILO_SCALE) * 100.0

    return {
        "key": "silo:usdc:borrow",
        "name": "Silo USDC Borrow APR",
        "rate": rate_pct / 100.0,  # decimal for rest of app
    }