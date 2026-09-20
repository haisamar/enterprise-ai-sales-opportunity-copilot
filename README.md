# Enterprise AI Sales Opportunity Copilot

A portfolio proof-of-concept for enterprise technical selling. The application turns structured account and opportunity context into a seller-reviewed discovery brief containing business problems, stakeholder hypotheses, discovery questions, technical constraints, solution hypotheses, proof-of-value criteria, and a business-value measurement plan.

## Truthful project status

This repository is a portfolio proof-of-concept. It is not a production CRM, autonomous seller, or deployed customer system. The seller remains in control of the output and must review all generated content before it is used.

## Architecture

- React/Vite frontend
- FastAPI backend
- PostgreSQL persistence
- IBM watsonx.ai chat API
- IBM Granite model (configurable model ID)
- REST API boundary between UI and analysis service
- Model-call audit metadata: model, prompt version, latency, timestamp

## What the PoC demonstrates

1. Structured customer-discovery intake
2. Account/opportunity reasoning
3. Buyer/stakeholder hypotheses
4. Discovery-question generation
5. Technical-constraint mapping
6. Solution-hypothesis generation
7. Proof-of-value planning
8. Business-value measurement plan
9. CRM-ready opportunity brief
10. Human review before downstream use

## Explicit non-goals

- No autonomous customer outreach
- No automatic pricing or commercial commitments
- No automatic CRM writes in the baseline build
- No claim of production readiness
- No claim of measured sales uplift

## Run locally

### 1. PostgreSQL

```bash
docker compose up -d db
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

The default `COPILOT_MODE=mock` works without IBM credentials.

For live watsonx.ai inference, set:

```env
COPILOT_MODE=watsonx
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-4-h-small
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Interview-safe one-liner

> I designed and implemented a portfolio proof-of-concept that structures account context into a seller-reviewed discovery and proof-of-value brief, with IBM watsonx.ai/Granite as the AI layer when live credentials are enabled.
