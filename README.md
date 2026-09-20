# Enterprise AI Sales Opportunity Copilot

A portfolio proof-of-concept for enterprise technical selling. The application turns seller-submitted account context into a seller-reviewed discovery brief: known facts, unknowns, buyer/stakeholder hypotheses, discovery questions, technical constraints, solution hypotheses, proof of value, a consultative conversation angle, and a CRM-ready opportunity summary.

This is a **bounded opportunity-analysis agent / agent-assisted workflow**. It does not autonomously act on customers, write mass email, or replace seller judgment.

## Truthful project status

This repository is a portfolio proof-of-concept. It is not a production CRM, autonomous seller, or deployed customer system.

- **Local implemented behavior:** deterministic mock generation, SQLite persistence, human review states, JSON export, simulated CRM handoff.
- **Live IBM integration path:** IBM Cloud IAM → watsonx.ai chat API → configured Granite model. The adapter, status endpoint, and ping endpoint are implemented.
- **Live inference:** IBM watsonx.ai / Granite 4 H Small inference was tested successfully against the Dallas endpoint.

The seller remains in control. AI output starts as `pending` and is never auto-approved.

## Architecture

- React/Vite frontend
- FastAPI backend
- SQLite for the local demo (PostgreSQL-compatible URL already supported)
- Bounded agent steps: load account context → generate brief → validate schema → ground facts → persist run
- IBM watsonx.ai + IBM Granite when `COPILOT_MODE=watsonx` and credentials are present
- Deterministic mock mode otherwise
- REST API boundary, human review, CRM-ready export simulation

## What the PoC demonstrates

1. Structured customer-discovery intake
2. Deterministic known facts vs AI hypotheses
3. Buyer/stakeholder persona hypotheses
4. Discovery-question generation
5. Technical-constraint mapping
6. Solution-hypothesis generation
7. Consultative conversation angle (not an email generator)
8. Proof-of-value and business-value measurement planning
9. CRM-ready opportunity brief and simulated webhook export
10. Human review before downstream use

## Explicit non-goals

- No autonomous customer outreach
- No mass-email or email-campaign product
- No automatic pricing or commercial commitments
- No live Salesforce/HubSpot write-back
- No claim of production readiness
- No claim of measured sales uplift

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env   # Windows
# cp ../.env.example .env   # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

Default `COPILOT_MODE=mock` works without IBM credentials and uses SQLite.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### 3. Optional live watsonx.ai

Obtain from IBM Cloud and put them only in `.env` (never commit):

- IBM Cloud API key → `WATSONX_API_KEY`
- watsonx.ai project ID → `WATSONX_PROJECT_ID`
- Regional base URL → `WATSONX_URL` (example: `https://us-south.ml.cloud.ibm.com`)
- Model ID, default `ibm/granite-4-h-small`

Then either:

- keep `COPILOT_MODE=mock` for a reliable demo and use **Test IBM Connection**, or
- set `COPILOT_MODE=watsonx` so opportunity generation uses Granite.

`POST /api/ai/ping` always attempts a real IBM call. It never silently uses mock.

CLI check:

```bash
cd backend
python scripts/test_watsonx.py
```

## Deployed architecture

LOCAL:
React → localhost FastAPI → SQLite or configured Postgres

DEPLOYED:
Vercel React frontend
→ Vercel FastAPI backend
→ Neon PostgreSQL
→ IBM Cloud IAM
→ watsonx.ai Dallas
→ Granite 4 H Small

- **Vercel** hosts the frontend and backend applications.
- **Neon** is persistent PostgreSQL for the deployed backend. SQLite is local development only and is not used as production storage on Vercel.
- **watsonx.ai** performs live inference when `COPILOT_MODE=watsonx`.
- IBM secrets, bearer tokens, and `DATABASE_URL` exist only on the backend. They are never sent to the frontend.
- This PoC may create missing tables with SQLAlchemy `create_all`. A production enterprise system would use proper migrations such as Alembic.

### Vercel setup (two projects, same GitHub repo)

Do not deploy secrets in Git. Create two Vercel projects from this repository.

**Backend project**

1. Import the GitHub repository in Vercel.
2. Set Root Directory to `backend`.
3. Framework / runtime: Python / FastAPI. Python version is pinned to 3.12 via `.python-version`.
4. Vercel discovers the existing FastAPI app via `backend/pyproject.toml` (`tool.vercel.entrypoint = "app.main:app"`).
5. Set Environment Variables (backend only):
   - `COPILOT_MODE`
   - `WATSONX_API_KEY`
   - `WATSONX_PROJECT_ID`
   - `WATSONX_URL`
   - `WATSONX_MODEL_ID`
   - `WATSONX_API_VERSION`
   - `DATABASE_URL` (Neon PostgreSQL URI)
   - `CORS_ORIGINS` (deployed frontend origin, no wildcard)
6. Deploy. Confirm `GET /health`, `GET /api/ai/status`, and `POST /api/ai/ping`.
7. Granite generation is about 15 seconds and uses Vercel’s native FastAPI / Fluid Compute duration. No custom `vercel.json` function routing is required.

**Frontend project**

1. Import the same GitHub repository as a second Vercel project.
2. Set Root Directory to `frontend`.
3. Framework: Vite. Output directory: `dist`.
4. Set Environment Variable:
   - `VITE_API_BASE_URL` = the deployed backend origin, for example `https://your-backend.vercel.app`
5. Deploy.
6. Copy the frontend origin into the backend `CORS_ORIGINS` value and redeploy the backend if needed.

Do not add `WATSONX_API_KEY`, IBM tokens, or `DATABASE_URL` to the frontend project.

## Interview-safe one-liner

> I designed a bounded opportunity-analysis agent that turns seller-submitted account context into a seller-reviewed discovery and proof-of-value brief. Mock mode is the reliable local demo; IBM watsonx.ai and Granite are the live inference path when credentials are present and tested.
