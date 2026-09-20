from fastapi import APIRouter

from ..config import settings
from ..schemas import AiPingOut, AiStatusOut
from ..services.watsonx import WatsonxClient, WatsonxError

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status", response_model=AiStatusOut)
def ai_status():
    return AiStatusOut(
        copilot_mode=settings.copilot_mode,
        credentials_present=settings.watsonx_configured,
        model_id=settings.watsonx_model_id,
        watsonx_url_configured=bool(settings.watsonx_url.strip()),
    )


@router.post("/ping", response_model=AiPingOut)
def ai_ping():
    client = WatsonxClient()
    missing = client.missing_config()
    if missing:
        return AiPingOut(
            connected=False,
            stage="config",
            error=f"Missing IBM configuration: {', '.join(missing)}",
            model_id=settings.watsonx_model_id or None,
            base_url=settings.watsonx_url or None,
        )
    try:
        latency_ms = client.ping()
        return AiPingOut(
            connected=True,
            provider="watsonx.ai",
            model_id=settings.watsonx_model_id,
            base_url=settings.watsonx_url,
            latency_ms=latency_ms,
            stage="ok",
        )
    except WatsonxError as exc:
        return AiPingOut(
            connected=False,
            provider="watsonx.ai",
            model_id=settings.watsonx_model_id,
            base_url=settings.watsonx_url,
            stage=exc.stage,
            error=exc.message,
        )
