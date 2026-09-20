import json
import logging
import re
import time

import requests

from ..config import settings

logger = logging.getLogger("copilot.granite")


class WatsonxError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.message = message


def extract_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WatsonxError("parse", "Model response was not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise WatsonxError("parse", "Model JSON was not an object.")
    return parsed


class WatsonxClient:
    def missing_config(self) -> list[str]:
        missing = []
        if not settings.watsonx_api_key.strip():
            missing.append("WATSONX_API_KEY")
        if not settings.watsonx_project_id.strip():
            missing.append("WATSONX_PROJECT_ID")
        if not settings.watsonx_url.strip():
            missing.append("WATSONX_URL")
        if not settings.watsonx_model_id.strip():
            missing.append("WATSONX_MODEL_ID")
        return missing

    def _token(self) -> str:
        missing = self.missing_config()
        if missing:
            raise WatsonxError("config", f"Missing IBM configuration: {', '.join(missing)}")
        try:
            response = requests.post(
                "https://iam.cloud.ibm.com/identity/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": settings.watsonx_api_key,
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise WatsonxError("iam", f"IBM Cloud IAM request failed: {exc}") from exc
        if response.status_code >= 400:
            raise WatsonxError(
                "iam",
                f"IBM Cloud IAM rejected authentication (HTTP {response.status_code}).",
            )
        token = response.json().get("access_token")
        if not token:
            raise WatsonxError("iam", "IBM Cloud IAM response did not include an access token.")
        return token

    @staticmethod
    def _message_text(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(item.get("text") or item.get("content") or "")
            return "\n".join(part for part in parts if part)
        if content is None:
            return ""
        return str(content)

    def _chat(self, payload: dict):
        started = time.perf_counter()
        token = self._token()
        url = f"{settings.watsonx_url.rstrip('/')}/ml/v1/text/chat"
        params = {"version": settings.watsonx_api_version}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.post(url, params=params, headers=headers, json=payload, timeout=180)
        except requests.RequestException as exc:
            raise WatsonxError("watsonx", f"watsonx.ai request failed: {exc}") from exc
        if response.status_code >= 400:
            raise WatsonxError(
                "watsonx",
                f"watsonx.ai inference failed (HTTP {response.status_code}).",
            )
        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise WatsonxError("watsonx", "watsonx.ai response did not contain chat content.") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        return body, latency_ms, self._message_text(content)

    def ping(self) -> int:
        payload = {
            "messages": [
                {"role": "user", "content": "Reply with the single word pong."},
            ],
            "project_id": settings.watsonx_project_id,
            "model_id": settings.watsonx_model_id,
            "max_completion_tokens": 8,
            "temperature": 0,
        }
        try:
            _body, latency_ms, _text = self._chat(payload)
            return latency_ms
        except WatsonxError as exc:
            if exc.stage == "watsonx" and "HTTP" in exc.message and "max_completion_tokens" in payload:
                payload["max_tokens"] = payload.pop("max_completion_tokens")
                _body, latency_ms, _text = self._chat(payload)
                return latency_ms
            raise

    def chat_text(self, system_prompt: str, user_prompt: str, max_completion_tokens: int = 6000) -> tuple[str, int]:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "project_id": settings.watsonx_project_id,
            "model_id": settings.watsonx_model_id,
            "max_completion_tokens": max_completion_tokens,
            "temperature": 0,
        }
        try:
            _body, latency_ms, text = self._chat(payload)
        except WatsonxError as exc:
            if exc.stage == "watsonx" and "HTTP" in exc.message and "max_completion_tokens" in payload:
                payload["max_tokens"] = payload.pop("max_completion_tokens")
                _body, latency_ms, text = self._chat(payload)
            else:
                raise
        if "authorization" not in text.lower() and "apikey" not in text.lower():
            logger.info("granite_raw_chars=%s latency_ms=%s", len(text), latency_ms)
            logger.info("granite_raw_response=%s", text)
        return text, latency_ms

    def chat_json(self, system_prompt: str, user_prompt: str, max_completion_tokens: int = 6000) -> tuple[dict, int]:
        text, latency_ms = self.chat_text(system_prompt, user_prompt, max_completion_tokens)
        return extract_json(text), latency_ms
