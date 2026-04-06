from __future__ import annotations

from fastapi import FastAPI, Query

from config.settings import API_DEFAULT_LIMIT
from db.database import fetch_latest_signal, fetch_recent_signals, init_db

app = FastAPI(title="Pump Scanner API", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest_signal():
    row = fetch_latest_signal()
    return {"data": row}


@app.get("/signals")
def signals(limit: int = Query(API_DEFAULT_LIMIT, ge=1, le=500)):
    rows = fetch_recent_signals(limit=limit)
    return {"count": len(rows), "data": rows}
