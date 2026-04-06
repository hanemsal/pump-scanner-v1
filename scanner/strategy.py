from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from config.settings import BREAKOUT_LOOKBACK, EMA_FAST, EMA_SLOW, RSI_MAX, RSI_MIN, VOLUME_MULTIPLIER


@dataclass
class SignalResult:
    should_alert: bool
    score: int
    reason: str
    payload: Dict[str, float | int | str | dict]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["ema_fast"] = out["close"].ewm(span=EMA_FAST, adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=EMA_SLOW, adjust=False).mean()

    delta = out["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
    rs = gain / loss
    out["rsi"] = 100 - (100 / (1 + rs))

    out["vol_sma20"] = out["volume"].rolling(20).mean()
    out["vol_ratio"] = out["volume"] / out["vol_sma20"].replace(0, np.nan)

    out["breakout_level"] = out["high"].rolling(BREAKOUT_LOOKBACK).max().shift(1)

    return out


def evaluate_symbol(symbol: str, timeframe: str, df: pd.DataFrame) -> SignalResult:
    if len(df) < 50:
        return SignalResult(False, 0, "insufficient_data", {})

    x = add_indicators(df)
    row = x.iloc[-1]

    ema_bull = bool(row["ema_fast"] > row["ema_slow"])
    rsi_ok = bool(pd.notna(row["rsi"]) and RSI_MIN <= row["rsi"] <= RSI_MAX)
    vol_ok = bool(pd.notna(row["vol_ratio"]) and row["vol_ratio"] >= VOLUME_MULTIPLIER)
    breakout_ok = bool(pd.notna(row["breakout_level"]) and row["close"] > row["breakout_level"])

    score = int(ema_bull) + int(rsi_ok) + int(vol_ok) + int(breakout_ok)

    should_alert = ema_bull and rsi_ok and vol_ok and breakout_ok
    reason = "ema_bull + rsi_ready + vol_spike + breakout" if should_alert else "no_setup"

    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "entry_price": float(row["close"]),
        "score": score,
        "reason": reason,
        "vol_ratio": float(row["vol_ratio"]) if pd.notna(row["vol_ratio"]) else None,
        "rsi": float(row["rsi"]) if pd.notna(row["rsi"]) else None,
        "breakout_level": float(row["breakout_level"]) if pd.notna(row["breakout_level"]) else None,
        "raw_payload": {
            "ema_fast": float(row["ema_fast"]) if pd.notna(row["ema_fast"]) else None,
            "ema_slow": float(row["ema_slow"]) if pd.notna(row["ema_slow"]) else None,
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        },
    }

    return SignalResult(should_alert, score, reason, payload)
