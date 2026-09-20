from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import Base, engine
from .routers.opportunities import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise AI Sales Opportunity Copilot",
    version="0.1.0",
    description="Portfolio proof-of-concept for structured enterprise technical-sales discovery.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.copilot_mode}
