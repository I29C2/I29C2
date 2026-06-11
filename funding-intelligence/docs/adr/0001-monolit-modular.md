# ADR 0001 — Monolit modular, nu microservicii

**Status:** acceptat
**Dată:** 2026-06-11

## Context
Echipă de 1-2 oameni. Ghidul Tehnic V2.0 recomandă monolit modular.

## Decizie
Un singur deployment FastAPI cu module separate (`scraping/`, `documents/`,
`ai/`). Granițele de modul se respectă strict, astfel încât extragerea ulterioară
într-un serviciu separat să fie posibilă fără rescriere.

## Consecințe
- (+) Zero overhead de orchestrare, un singur `docker compose up`.
- (+) Deploy simplu pe VPS.
- (−) Scalare doar verticală la început — acceptabil pentru testare internă.

---

> Restul ADR-urilor de înregistrat în Faza 0 (din Ghidul Tehnic §9):
> 0002 pgvector vs Qdrant · 0003 furnizor+model LLM per use-case ·
> 0004 self-hosted vs cloud · 0005 versionarea schemei canonice ·
> 0006 org_id ca pre-decizie multi-tenancy ·
> **0007 (nou, din feedback): model de embeddings pentru română** ·
> **0008 (nou): strategie dacă Docling nu acoperă o clasă de documente scanate**
