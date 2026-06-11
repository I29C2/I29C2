# TeamILabs Funding Intelligence — MVP

Platformă internă de monitorizare a apelurilor de finanțare. Acest repo este
**MVP-ul tăiat agresiv** pentru testare internă, derivat din Ghidul Tehnic V2.0.

## Scope MVP (ce construim ACUM)

Lanțul minim care validează produsul:

```
scraper → detectez apel nou/modificat → descarc ghidul → Docling parse
        → LLM extrage câmpurile → EU validez în UI → văd lista curată
```

Module incluse: `scraping/`, `documents/`, `ai/`, plus API + ecranul de validare.

## Ce am tăiat DELIBERAT din MVP (vezi Ghidul Tehnic pentru planul complet)

- Matching cu scoring / rules engine (Faza 4-5)
- Modul financiar VAN/RIR (track paralel)
- Generare propuneri / export docx (Faza 6)
- RAG / Q&A (a doua iterație — nu prima)
- MinIO / S3 → înlocuit cu **folder pe disc** (`./data/storage`)
- Multi-user auth → **un singur token static** (ești doar tu în testare internă)
- Grafana / Loki → endpoint `/health` + logging JSON în stdout

## Ce PĂSTRĂM din disciplina documentului (ieftin acum, scump retroactiv)

1. Istoricul modificărilor (`funding_call_version`)
2. `validation_status` + `source_page` + `confidence` pe câmpurile extrase
3. Migrații Alembic de la primul tabel — niciun `ALTER TABLE` manual
4. Doar câmpurile `validated`/`corrected` ar alimenta vreodată matching-ul (regulă în query)

## Rulare locală (dezvoltare, x86)

```bash
cp .env.example .env          # completează ANTHROPIC_API_KEY
docker compose up --build
# API:        http://localhost:8000/docs
# Frontend:   http://localhost:5173
```

Migrațiile rulează automat la pornirea containerului `api` (vezi `docker-compose.yml`).

## Deploy pe VPS (Hetzner CX42 sau echivalent, ~16€/lună)

Același `docker compose up -d --build`. Singura diferență față de local: `.env`
cu secrete reale și un reverse-proxy cu TLS (Caddy) în fața portului 8000 —
adăugat când e nevoie, nu acum.

## Structura proiectului

```
app/
  api/          # FastAPI: rute REST v1 + auth token + health
  models/       # SQLAlchemy: schema canonică
  schemas/      # Pydantic: contracte API
  scraping/     # un modul per sursă + change detection + taskuri Celery
  documents/    # storage pe disc + pipeline Docling
  ai/           # client LLM + extracție structurată
prompts/        # prompturi versionate în repo (NU inline în cod)
schemas/        # JSON Schema per câmp de eligibilitate
alembic/        # migrații
frontend/       # React + TS + Vite — ecranul de validare e prioritatea
tests/          # vezi strategia QA din Ghidul Tehnic
```

## Cost estimat testare internă

- VPS: ~16-20€/lună (cu backup)
- API LLM (Haiku la parsarea ghidurilor noi): ~5-15€/lună
- **Total: ~25-35€/lună**
