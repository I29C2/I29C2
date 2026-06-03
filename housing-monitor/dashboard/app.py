"""Optional local FastAPI dashboard (MVP+).

Run standalone:  uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from core.config import Config
from storage import Database

app = FastAPI(title="Housing Monitor Dashboard")


def _db() -> Database:
    cfg = Config.load("config.yaml")
    return Database(cfg.database_path)


@app.get("/api/stats")
def api_stats():
    db = _db()
    try:
        return db.stats()
    finally:
        db.close()


@app.get("/api/latest")
def api_latest(limit: int = 10):
    db = _db()
    try:
        return [dict(r) for r in db.latest(limit)]
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def index():
    db = _db()
    try:
        s = db.stats()
        rows = db.latest(10)
    finally:
        db.close()
    items = "".join(
        f"<tr><td>{r['title']}</td><td>{r['rooms'] or ''}</td>"
        f"<td>{r['area'] or ''}</td><td>{r['rent_warm'] or r['rent_cold'] or ''}</td>"
        f"<td><a href='{r['listing_url']}'>open</a></td></tr>"
        for r in rows
    )
    return f"""
    <html><head><title>Housing Monitor</title>
    <style>body{{font-family:sans-serif;margin:2rem}}
    table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:6px}}</style>
    </head><body>
    <h1>🏠 Housing Monitor</h1>
    <p>Last scan: {s['last_scan'] or 'n/a'} |
       Total: {s['total_listings']} |
       Notified: {s['notified_listings']} |
       Sent: {s['notifications_sent']}</p>
    <h2>Latest listings</h2>
    <table><tr><th>Title</th><th>Rooms</th><th>Area</th><th>Rent</th><th>Link</th></tr>
    {items}</table>
    </body></html>
    """
