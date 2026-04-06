from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

from config.settings import DATABASE_URL


def _require_db_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing.")
    return DATABASE_URL


@contextmanager
def get_conn():
    conn = psycopg2.connect(_require_db_url())
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS pump_signals (
        id BIGSERIAL PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        symbol TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        entry_price DOUBLE PRECISION NOT NULL,
        score INTEGER NOT NULL,
        reason TEXT NOT NULL,
        vol_ratio DOUBLE PRECISION,
        rsi DOUBLE PRECISION,
        breakout_level DOUBLE PRECISION,
        raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
    );

    CREATE INDEX IF NOT EXISTS idx_pump_signals_created_at
    ON pump_signals (created_at DESC);

    CREATE INDEX IF NOT EXISTS idx_pump_signals_symbol_created_at
    ON pump_signals (symbol, created_at DESC);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def insert_signal(payload: Dict[str, Any]) -> None:
    sql = """
    INSERT INTO pump_signals (
        symbol, timeframe, entry_price, score, reason,
        vol_ratio, rsi, breakout_level, raw_payload
    )
    VALUES (
        %(symbol)s, %(timeframe)s, %(entry_price)s, %(score)s, %(reason)s,
        %(vol_ratio)s, %(rsi)s, %(breakout_level)s, %(raw_payload)s
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, payload)
        conn.commit()


def fetch_recent_signals(limit: int = 50) -> List[Dict[str, Any]]:
    sql = """
    SELECT
        id,
        created_at,
        symbol,
        timeframe,
        entry_price,
        score,
        reason,
        vol_ratio,
        rsi,
        breakout_level,
        raw_payload
    FROM pump_signals
    ORDER BY created_at DESC
    LIMIT %s;
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_latest_signal() -> Optional[Dict[str, Any]]:
    rows = fetch_recent_signals(limit=1)
    return rows[0] if rows else None


def signal_exists_recently(symbol: str, cooldown_minutes: int) -> bool:
    sql = """
    SELECT 1
    FROM pump_signals
    WHERE symbol = %s
      AND created_at >= NOW() - (%s || ' minutes')::interval
    LIMIT 1;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol, cooldown_minutes))
            row = cur.fetchone()
    return row is not None
