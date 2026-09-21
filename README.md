# Enterprise AI Sales Opportunity Copilot

A public portfolio proof-of-concept that shows how AI can help a seller turn raw account context into a structured, reviewable opportunity brief.

The application takes seller-provided customer information and produces:

- known facts
- unknowns that still need discovery
- buyer and stakeholder hypotheses
- discovery questions
- technical constraints
- solution hypotheses
- proof-of-value ideas
- business-value measurement criteria
- a consultative conversation angle
- a CRM-ready opportunity summary

The goal is not to automate selling.

The goal is to help a seller prepare faster while keeping facts, assumptions, and AI-generated recommendations clearly separated.

**Live demo:**  
https://enterprise-ai-sales-opportunity-copilot.vercel.app/

**Source code:**  
https://github.com/haisamar/enterprise-ai-sales-opportunity-copilot

---

## What this project does

Technical sellers often start with scattered information:

```text
Company context
+
Customer objectives
+
Current problems
+
Technical environment
+
Business priorities
+
Unknowns
```

The hard part is turning that information into a useful discovery conversation.

This project structures that process.

```text
Seller enters account context
        ↓
Opportunity-analysis agent
        ↓
Structured AI generation
        ↓
Schema validation
        ↓
Fact grounding
        ↓
Seller review
        ↓
Approved opportunity brief
        ↓
CRM-ready handoff
```

The AI helps organize and interpret the information.

The seller remains responsible for deciding what should actually be used.

---

# Core principle

## AI assists the seller — it does not replace seller judgment

The application intentionally separates:

```text
Known facts
```

from:

```text
AI hypotheses
```

A model may suggest:

- a possible stakeholder
- a possible business problem
- a discovery question
- a solution direction
- a proof-of-value approach

But those suggestions are not automatically treated as customer facts.

AI-generated briefs begin in a review state and are not automatically approved.

---

# What the generated brief contains

A completed opportunity brief can include:

## Known facts

Information directly grounded in seller-provided account context.

---

## Unknowns

Important information that still needs to be discovered.

These help prevent the system from pretending that missing information is known.

---

## Stakeholder hypotheses

Possible buyer or stakeholder roles worth validating during discovery.

These are hypotheses, not claims about the customer.

---

## Discovery questions

Questions designed to help the seller understand:

- business objectives
- current pain
- technical environment
- constraints
- buying criteria
- success measures

---

## Technical constraints

A structured view of technical requirements or limitations that could affect solution design.

---

## Solution hypotheses

Possible solution directions connected to the customer's stated problems.

These remain hypotheses until validated through discovery.

---

## Proof-of-value plan

A proposed way to test whether the solution actually addresses the customer's problem.

The PoV can include:

- scope
- required data
- validation steps
- success criteria
- expected business outcome

---

## Business-value measurement

The project encourages measurable proof rather than vague claims.

Examples might include:

```text
Time saved
Reduced manual work
Faster response
Fewer process errors
Improved visibility
Higher workflow completion
```

The project does not claim measured customer uplift unless such results actually exist.

---

## Consultative conversation angle

The application helps prepare the next useful conversation.

It is intentionally **not a mass-email generator**.

The focus is:

> What should the seller understand, validate, and discuss next?

---

## CRM-ready summary

After seller review, the system can produce structured opportunity information suitable for a CRM workflow.

The current implementation demonstrates a **CRM-ready payload and simulated handoff**.

It does not claim a live Salesforce or HubSpot integration.

---

# Human review

Every AI-generated opportunity brief begins as:

```text
pending
```

The seller can review the content before downstream use.

The workflow supports review states such as:

```text
pending
approved
needs_revision
```

This creates a simple human-in-the-loop boundary.

```text
AI generates
    ↓
Seller reviews
    ↓
Approve
or
Needs revision
    ↓
Only approved output moves forward
```

---

# Live IBM Granite integration

The project includes a real IBM watsonx.ai integration path.

```text
FastAPI
   ↓
IBM Cloud IAM
   ↓
watsonx.ai
   ↓
IBM Granite
   ↓
Structured opportunity brief
   ↓
Pydantic validation
   ↓
Fact grounding
```

The tested model is:

```text
ibm/granite-4-h-small
```

The live integration was successfully validated against the IBM watsonx.ai Dallas endpoint.

The application also includes:

```text
GET /api/ai/status
```

for provider/configuration status and:

```text
POST /api/ai/ping
```

for a real connectivity test.

The ping endpoint never silently falls back to mock mode.

---

# Deterministic mock mode

The project also contains a deterministic mode for local development and reliable demonstrations.

```env
COPILOT_MODE=mock
```

Mock mode:

- requires no IBM credentials
- keeps the workflow fully usable locally
- returns predictable sample output
- still exercises persistence, review, validation, and export behavior

This means the project can be explored without external AI access while preserving a real watsonx.ai provider path.

---

# Architecture

```text
React / Vite frontend
        ↓
REST API
        ↓
FastAPI
        ↓
OpportunityCopilotAgent
        ↓
 ┌───────────────────────────┐
 │                           │
 ▼                           ▼
Deterministic Mock     IBM watsonx.ai
                            ↓
                       Granite model
 │                           │
 └──────────────┬────────────┘
                ↓
         Pydantic validation
                ↓
           Fact grounding
                ↓
         SQLAlchemy persistence
                ↓
           Seller review
                ↓
       CRM-ready handoff
```

The agent is intentionally bounded.

It does not autonomously contact customers or make commercial decisions.

---

# Public deployment

The deployed portfolio uses:

```text
Visitor
   ↓
Vercel React frontend
   ↓
Vercel FastAPI backend
   ↓
Neon PostgreSQL
   ↓
IBM Cloud IAM
   ↓
watsonx.ai
   ↓
Granite
```

## Frontend

Hosted on Vercel.

The browser contains no IBM credentials or database secrets.

---

## Backend

FastAPI is deployed separately through Vercel.

The backend handles:

- account intake
- AI generation
- IBM authentication
- validation
- persistence
- human review
- export behavior

---

## Persistence

Local development uses SQLite.

The deployed backend uses Neon PostgreSQL.

```text
LOCAL
→ SQLite

DEPLOYED
→ Neon PostgreSQL
```

The database boundary is handled through SQLAlchemy and `DATABASE_URL`.

---

# Security boundary

Sensitive values exist only on the backend.

Examples include:

```text
WATSONX_API_KEY
WATSONX_PROJECT_ID
DATABASE_URL
IBM access tokens
```

These values are never intentionally sent to the browser.

The frontend communicates only with the application API.

---

# What the project demonstrates

## Structured discovery

Raw seller notes become a more organized opportunity picture.

---

## Fact vs hypothesis separation

Customer facts and AI-generated ideas are deliberately treated differently.

---

## Bounded AI-agent behavior

The agent performs a defined workflow rather than receiving unlimited autonomy.

---

## Structured AI output

Granite output is validated against a defined Pydantic schema before successful persistence.

---

## Fact grounding

Known facts are checked against the submitted account information rather than blindly trusting model output.

---

## Human-in-the-loop review

AI output must be reviewed before downstream use.

---

## Proof-of-value thinking

The workflow connects technical solution ideas with measurable customer success criteria.

---

## CRM workflow design

Approved information can be transformed into a structured CRM-ready payload without pretending that a real CRM integration already exists.

---

# Technology stack

## Frontend

- React
- Vite

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

## Persistence

- SQLite — local development
- PostgreSQL / Neon — deployed environment

## AI

- IBM watsonx.ai
- IBM Granite
- `ibm/granite-4-h-small`

## Deployment

- Vercel
- Neon
- GitHub

---

# Run locally

## 1. Backend

From the repository root:

```powershell
cd backend

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

copy ..\.env.example .env

uvicorn app.main:app --reload --port 8000
```

For macOS or Linux:

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp ../.env.example .env

uvicorn app.main:app --reload --port 8000
```

The backend runs at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

By default:

```env
COPILOT_MODE=mock
```

works without IBM credentials.

---

# 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Vite may select another port if `5173` is already in use.

For local development, the frontend can use:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

# Run with live IBM Granite

Create a backend `.env` using your own IBM Cloud credentials.

```env
COPILOT_MODE=watsonx

WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-4-h-small
WATSONX_API_VERSION=2025-10-25
```

Never commit real credentials.

Then start the backend normally:

```bash
uvicorn app.main:app --reload --port 8000
```

Opportunity generation will use the watsonx.ai provider when:

```env
COPILOT_MODE=watsonx
```

and the required IBM configuration is available.

---

# Test IBM connectivity

The project includes a connection test endpoint:

```text
POST /api/ai/ping
```

You can also use the included CLI check:

```bash
cd backend
python scripts/test_watsonx.py
```

A successful ping confirms communication with IBM Cloud IAM and watsonx.ai.

---

# Vercel deployment

The repository is deployed as two Vercel projects from the same GitHub repository.

## Backend project

Use:

```text
Root Directory:
backend
```

The Python version is pinned to:

```text
3.12
```

The Vercel entrypoint is:

```text
backend/index.py
```

which exposes the existing FastAPI application.

Backend environment variables include:

```text
COPILOT_MODE
WATSONX_API_KEY
WATSONX_PROJECT_ID
WATSONX_URL
WATSONX_MODEL_ID
WATSONX_API_VERSION
DATABASE_URL
CORS_ORIGINS
```

These variables belong only on the backend project.

Useful deployment checks:

```text
GET  /health
GET  /api/ai/status
POST /api/ai/ping
```

---

## Frontend project

Use:

```text
Root Directory:
frontend

Framework:
Vite

Output Directory:
dist
```

The frontend routes `/api/...` requests through the deployed backend configuration.

Do not add:

```text
WATSONX_API_KEY
WATSONX_PROJECT_ID
DATABASE_URL
```

to the frontend deployment.

---

# Implementation status

| Capability | Status |
|---|---|
| Structured account intake | **IMPLEMENTED / TESTED** |
| Opportunity-analysis agent | **IMPLEMENTED / TESTED** |
| Deterministic mock mode | **IMPLEMENTED / TESTED** |
| Known facts vs hypotheses | **IMPLEMENTED / TESTED** |
| Stakeholder hypotheses | **IMPLEMENTED** |
| Discovery questions | **IMPLEMENTED** |
| Technical constraints | **IMPLEMENTED** |
| Solution hypotheses | **IMPLEMENTED** |
| Proof-of-value plan | **IMPLEMENTED** |
| Business-value criteria | **IMPLEMENTED** |
| Human review workflow | **IMPLEMENTED / TESTED** |
| JSON export | **IMPLEMENTED** |
| CRM-ready handoff simulation | **IMPLEMENTED** |
| watsonx.ai provider | **IMPLEMENTED / TESTED** |
| IBM Granite inference | **TESTED** |
| Public Vercel frontend | **DEPLOYED** |
| Public FastAPI backend | **DEPLOYED** |
| Neon PostgreSQL persistence | **DEPLOYED** |
| Live Salesforce integration | **NOT EXECUTED** |
| Live HubSpot integration | **NOT EXECUTED** |
| Autonomous customer outreach | **NOT IMPLEMENTED** |

---

# What this project does not do

This is a portfolio proof-of-concept, not a production sales platform.

It does not claim:

- autonomous selling
- automatic customer outreach
- mass-email generation
- automatic pricing
- automatic commercial commitments
- production CRM write-back
- measured customer revenue uplift
- production-scale multi-tenancy
- enterprise-grade identity and authorization

These boundaries are intentional.

---

# About this project

I built this project to explore how AI can support technical selling without turning the seller into a passive observer.

The central idea is:

> **Use AI to organize discovery, generate useful hypotheses, and prepare a stronger conversation — while keeping the seller responsible for facts, judgment, and approval.**

The project combines:

- structured discovery
- bounded AI-agent behavior
- IBM Granite
- schema validation
- fact grounding
- human review
- proof-of-value planning
- CRM-ready workflow design

into one end-to-end portfolio proof-of-concept.

---

# Explore

## Live project

https://enterprise-ai-sales-opportunity-copilot.vercel.app/

## Source code

https://github.com/haisamar/enterprise-ai-sales-opportunity-copilot
