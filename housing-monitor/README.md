# 🏠 Housing Monitor Germany

Automated housing monitor for German housing providers. Periodically scrapes
listing pages, filters by your criteria, and sends **Telegram** notifications
for new matching apartments. Built to run 24/7 on a **Raspberry Pi 5** in
**Docker**.

Initial provider: **WWS Herford**
(`https://www.wws-herford.de/wohnen/wohnungsangebote`). The architecture is
extensible — new providers are added by dropping a scraper in `scrapers/` and
registering it, no core changes needed.

---

## Features

- ⏱️ Periodic scanning (default every 15 min, configurable 5 min – 24 h)
- 🧱 Pluggable scraper architecture (`BaseScraper` + registry)
- 🧮 Rule-based filtering: rooms, area, rent, availability, WBS, keywords
- 🔁 Duplicate detection (URL → listing-id → title+address fingerprint)
- 💾 SQLite history of all listings + notifications
- 📨 Telegram alerts + bot commands `/status` `/stats` `/test` `/latest`
- 🔌 Auto-retry with exponential backoff on network/website errors
- 🪵 Structured rotating logs (`logs/app.log`)
- 📊 Optional FastAPI dashboard on port 8080
- 🐳 Docker / docker-compose deployment, multi-arch (arm64 + x86_64)
- ✅ Test suite with >80% coverage

---

## Quick start (local)

```bash
cd housing-monitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml      # edit filters & sources
export TELEGRAM_BOT_TOKEN="123:abc"      # from @BotFather
export TELEGRAM_CHAT_ID="your-chat-id"   # from @userinfobot

python app.py
```

## Deploy on Raspberry Pi 5 with Docker

1. Install Docker on Raspberry Pi OS (64-bit):
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER   # re-login afterwards
   ```
2. Copy the `housing-monitor/` folder to the Pi (e.g. via `git clone` or `scp`).
3. Configure:
   ```bash
   cp config.example.yaml config.yaml   # edit your filters
   cp .env.example .env                 # add your Telegram token + chat id
   ```
4. Build & run:
   ```bash
   docker compose up -d --build
   docker compose logs -f               # watch it work
   ```

The container restarts automatically (`restart: unless-stopped`) and survives
reboots. `database/` and `logs/` are mounted as volumes so data persists across
rebuilds.

---

## Configuration (`config.yaml`)

Secrets (bot token / chat id) are best provided via the
`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` environment variables, which override
the YAML values. All other behaviour lives in `config.yaml` — see
`config.example.yaml` for the fully documented template.

Key filter options:

| Key | Meaning |
|-----|---------|
| `min_rooms` / `max_rooms` | room count range |
| `min_area` / `max_area` | living area (sqm) |
| `min_rent` / `max_rent` | rent in € (warm if known, else cold) |
| `available_within_months` | accept listings available now or within N months |
| `exclude_wbs` | drop listings requiring a WBS |
| `keywords_include` | listing must contain at least one (if list non-empty) |
| `keywords_exclude` | listing must contain none of these |

> Unknown values never cause a reject: if a field couldn't be parsed, the
> listing still passes numeric rules (better a false alert than a missed home).

---

## Telegram bot commands

| Command | Action |
|---------|--------|
| `/status` | uptime, last scan, interval, source count |
| `/stats` | listing + notification counters |
| `/test` | confirm the bot is wired up |
| `/latest` | last 5 stored listings |

---

## Optional dashboard

Enable in `config.yaml` (`dashboard.enabled: true`), expose port 8080 in
`docker-compose.yml`, then run:

```bash
uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
```

Browse to `http://<pi-ip>:8080`. JSON endpoints: `/api/stats`, `/api/latest`.

---

## Adding a new provider

```python
# scrapers/my_provider.py
from models import Listing
from .base_scraper import BaseScraper
from .registry import register

@register("my_provider")
class MyProviderScraper(BaseScraper):
    def parse(self, html: str) -> list[Listing]:
        ...  # return normalized Listing objects
```

Import it in `scrapers/__init__.py`, then reference `type: my_provider` under
`sources:` in `config.yaml`. Done.

---

## Tests

```bash
pip install -r requirements.txt
pytest                  # runs suite with coverage report
```

---

## Project layout

```
housing-monitor/
├── app.py                 # entry point (scheduler + signal handling)
├── monitor.py             # scrape → store → filter → notify orchestration
├── config.example.yaml
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── core/                  # config loading + logging
├── models/                # Listing dataclass + parsing helpers
├── scrapers/              # base_scraper, registry, wws_herford
├── filters/               # filter_engine
├── storage/               # SQLite database + dedup
├── notifications/         # telegram_notifier (+ base)
├── scheduler/             # APScheduler wrapper
├── dashboard/             # optional FastAPI UI
└── tests/                 # pytest suite (>80% coverage)
```

---

## A note on the WWS Herford scraper

The live site blocks unauthenticated requests, so exact CSS selectors could
not be verified at build time. `scrapers/wws_herford.py` therefore uses a
**resilient heuristic parser** (candidate containers + labelled regex). When
you run it against the real page, check the logs — if it finds 0 listings,
pin the container selector to the real markup (`_CANDIDATE_SELECTORS` in that
file). Everything downstream is fully tested and provider-agnostic.
```
