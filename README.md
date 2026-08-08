# M9E Backend

FastAPI gateway + agent layer for the M9E marketplace, per the Technical Development Plan v1.0
(Sections 3, 4, 9). Lovable never calls agents directly — it calls this gateway over the versioned
`/v1` REST contract (Section 3).

## Status

Session 1 (Section 9): repo scaffolded, `/v1` contract stubbed with the Truth Layer envelope shape
(Section 3.3) on every response. No real agent logic, EKG reads/writes, or Truth Layer invariant
checks yet — those land in Session 2 (EKG + Emma 01) and Session 3 (Truth Layer + James 07).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_* values
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/v1/health` and `http://localhost:8000/docs`.

## Contract

See Section 3 of `M9E_Technical_Development_Plan_v1.0.pdf` for the full `/v1` endpoint list and the
canonical request/response envelope. Every agent-produced response carries a `truth` object
(`invariants_passed`, `invariants_failed`, `confidence`, `provenance`, `audit_ref`); the gateway will
reject any agent payload missing one once the Session 3 Truth Layer middleware
(`app/truth/gate.py`) lands.

## EKG

The Equipment Knowledge Graph schema (Section 4.2, pgvector-in-Supabase) lives in
`supabase/migrations/`. Apply with the Supabase CLI or MCP `apply_migration`.
