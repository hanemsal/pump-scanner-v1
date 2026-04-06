from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

EXCHANGE_ID = os.getenv("EXCHANGE_ID", "binance")
QUOTE_ASSET = os.getenv("QUOTE_ASSET", "USDT")
ONLY_PERPETUAL = _get_bool("ONLY_PERPETUAL", True)

TIMEFRAME = os.getenv("TIMEFRAME", "5m")
OHLCV_LIMIT = _get_int("OHLCV_LIMIT", 120)
SCAN_LOOP_SECONDS = _get_int("SCAN_LOOP_SECONDS", 60)
SYMBOL_PAUSE_SECONDS = _get_float("SYMBOL_PAUSE_SECONDS", 0.10)
MAX_SYMBOLS = _get_int("MAX_SYMBOLS", 150)

MIN_QUOTE_VOLUME_24H = _get_float("MIN_QUOTE_VOLUME_24H", 10_000_000)
MIN_LAST_PRICE = _get_float("MIN_LAST_PRICE", 0.00001)

EMA_FAST = _get_int("EMA_FAST", 9)
EMA_SLOW = _get_int("EMA_SLOW", 21)
RSI_MIN = _get_float("RSI_MIN", 55)
RSI_MAX = _get_float("RSI_MAX", 68)

BREAKOUT_LOOKBACK = _get_int("BREAKOUT_LOOKBACK", 20)
VOLUME_MULTIPLIER = _get_float("VOLUME_MULTIPLIER", 1.8)

ALERT_COOLDOWN_MINUTES = _get_int("ALERT_COOLDOWN_MINUTES", 90)
API_DEFAULT_LIMIT = _get_int("API_DEFAULT_LIMIT", 50)
