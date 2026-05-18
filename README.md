# BetBot AI

> AI-powered sports betting analysis platform — value bet detection, match integrity scoring, and predictive analytics delivered via a web dashboard and Telegram bot.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          BetBot AI System                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐        ┌───────────────────────────────────┐    │
│   │  Telegram    │        │          Next.js Frontend          │    │
│   │     Bot      │        │        (http://localhost:3000)     │    │
│   └──────┬───────┘        └────────────────┬──────────────────┘    │
│          │  HTTP                           │  HTTP / REST           │
│          ▼                                 ▼                        │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                FastAPI Backend (Port 8000)                │     │
│   │  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐  │     │
│   │  │  Auth / JWT  │  │  Predictions   │  │  Integrity  │  │     │
│   │  │   Service    │  │    Service     │  │   Service   │  │     │
│   │  └──────────────┘  └───────┬────────┘  └──────┬──────┘  │     │
│   │                            │                   │         │     │
│   │                    ┌───────▼───────────────────▼──────┐  │     │
│   │                    │         ML Engine (scikit-learn)  │  │     │
│   │                    │   XGBoost · Poisson · Ensemble   │  │     │
│   │                    └──────────────────────────────────┘  │     │
│   └──────────────────────────────────────────────────────────┘     │
│          │                        │                                 │
│          ▼                        ▼                                 │
│   ┌─────────────┐        ┌────────────────┐                        │
│   │  PostgreSQL │        │     Redis      │                        │
│   │   (Port     │        │  (Port 6379)   │                        │
│   │    5432)    │        │  Cache + Queue │                        │
│   └─────────────┘        └────────┬───────┘                        │
│                                   │                                 │
│                          ┌────────▼───────────────────┐            │
│                          │     Celery Workers          │            │
│                          │  • Prediction scheduler     │            │
│                          │  • Odds fetcher             │            │
│                          │  • Integrity analyzer       │            │
│                          └────────────────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

External Data Sources:
  ┌────────────────────┐   ┌──────────────────────┐
  │  API-Football.com  │   │   The Odds API        │
  │  (Match data &     │   │  (Real-time odds &    │
  │   team stats)      │   │   line movements)     │
  └────────────────────┘   └──────────────────────┘
```

---

## Features

- **Value Bet Detection** — Proprietary EV model compares our predicted probabilities against bookmaker lines; flags bets with positive expected value above a configurable threshold.
- **Match Integrity Scoring** — Anomaly detection on odds movements, booking patterns, and historical data to surface potentially fixed matches.
- **Multi-sport Coverage** — Premier League, La Liga, Bundesliga, Serie A, Ligue 1, UEFA Champions League, and more.
- **Real-time Odds Tracking** — Polls live odds from multiple bookmakers and alerts on significant line movement.
- **Predictive Analytics** — XGBoost ensemble model trained on 5+ years of match data; outputs 1X2 probabilities, over/under, and BTTS predictions.
- **Telegram Bot** — Receive daily value bet summaries, match alerts, and ad-hoc prediction queries directly in Telegram.
- **User Subscription Tiers** — Free (3 predictions/day), Pro (unlimited), and Admin access levels.
- **Historical Backtesting** — Review model performance metrics and ROI over past periods.
- **REST API** — Fully documented OpenAPI/Swagger interface for programmatic access.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Docker | 24.x |
| Docker Compose | 2.x (plugin) |
| GNU Make | 3.81 |
| Git | 2.x |

> **Optional:** Python 3.11+ and Node.js 20+ if you want to run services outside Docker.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/betbot-ai.git
cd betbot-ai

# 2. Run the one-command setup (copies .env, builds images, runs migrations, seeds data)
make setup

# 3. Open the app
#   Web dashboard: http://localhost:3000
#   API docs:      http://localhost:8000/docs
```

---

## Environment Setup

```bash
# Copy the example environment file
cp .env.example .env

# Open and edit with your real credentials
nano .env   # or vim, code, etc.
```

### Required Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password — change from default |
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `API_FOOTBALL_KEY` | API key from [api-football.com](https://www.api-football.com/) |
| `ODDS_API_KEY` | API key from [the-odds-api.com](https://the-odds-api.com/) |

---

## Common Commands

```bash
make up              # Start all services
make down            # Stop all services
make build           # Rebuild Docker images
make logs            # Tail all service logs
make logs-backend    # Tail backend logs only
make migrate         # Run database migrations
make seed            # Seed sample data
make test            # Run test suite
make test-coverage   # Run tests with HTML coverage report
make shell-backend   # bash shell inside backend container
make shell-db        # psql shell inside postgres container
make restart         # Stop then start all services
make clean           # Remove containers AND volumes (destructive)
make setup           # First-time full setup
```

---

## API Documentation

Once the backend is running, interactive API docs are available at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create new user account |
| POST | `/api/v1/auth/login` | Obtain JWT token |
| GET | `/api/v1/leagues` | List all tracked leagues |
| GET | `/api/v1/matches/today` | Get today's matches |
| GET | `/api/v1/matches/{id}/prediction` | Get AI prediction for a match |
| GET | `/api/v1/value-bets` | List current value bet opportunities |
| GET | `/api/v1/integrity/{match_id}` | Get integrity risk score for a match |
| GET | `/health` | Service health check |

---

## Telegram Bot Commands

Start the bot by messaging [@YourBotHandle](https://t.me/YourBotHandle) on Telegram.

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick guide |
| `/help` | List all available commands |
| `/today` | Today's matches with predictions |
| `/valuebets` | Current value bet opportunities |
| `/match <id>` | Detailed prediction for a specific match |
| `/leagues` | List supported leagues |
| `/subscribe` | Subscribe to daily prediction digest |
| `/unsubscribe` | Stop daily digests |
| `/stats` | Your personal prediction tracking stats |
| `/alerts on\|off` | Toggle real-time bet alerts |
| `/setthreshold <pct>` | Set your minimum EV threshold for alerts |

---

## Project Structure

```
betbot-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (predictions, integrity, odds)
│   │   ├── ml/           # ML model wrappers and feature engineering
│   │   ├── tasks/        # Celery task definitions
│   │   └── core/         # Config, database, security utilities
│   ├── alembic/          # Database migration files
│   ├── ml_models/        # Trained model artifacts (.pkl)
│   ├── tests/            # pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # Reusable React components
│   │   └── lib/          # API client and utilities
│   └── package.json
├── telegram_bot/
│   └── bot/              # Telegram bot handlers
├── scripts/
│   ├── seed_db.py        # Sample data seeder
│   └── check_health.sh   # Service health checker
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Development

### Running Backend Locally (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Point DATABASE_URL at a local postgres instance
export DATABASE_URL=postgresql://betbot:betbot_secret@localhost:5432/betbot
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=$(openssl rand -hex 32)

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Running Frontend Locally (without Docker)

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Adding a Migration

```bash
# Auto-generate from model changes
docker-compose exec backend alembic revision --autogenerate -m "describe_your_change"

# Apply
make migrate
```

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/).
4. Ensure all tests pass: `make test`.
5. Open a pull request against `main`.

Please read `CONTRIBUTING.md` for full guidelines on code style, commit messages, and the review process.

---

## Legal Disclaimer

**BetBot AI is intended strictly for informational and educational purposes.**

- This platform does **not** constitute financial or gambling advice.
- Sports betting involves significant financial risk. You may lose money.
- Always gamble responsibly. Never bet more than you can afford to lose.
- Users are solely responsible for compliance with the laws of their jurisdiction. Online sports betting is illegal in some countries and regions.
- The authors and contributors of this project accept no liability for losses incurred as a result of using this software.
- If you or someone you know has a gambling problem, please seek help: [BeGambleAware](https://www.begambleaware.org/) | [GamCare](https://www.gamcare.org.uk/) | National Problem Gambling Helpline: 1-800-522-4700.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
