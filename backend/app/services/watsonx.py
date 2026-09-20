import json
import re
import time
import requests
from ..config import settings


class WatsonxClient:
    def _token(self) -> str:
        if not settings.watsonx_api_key:
            raise RuntimeError("WATSONX_API_KEY is required in watsonx mode")
        r = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.watsonx_api_key,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["access_token"]

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise

    def chat_json(self, system_prompt: str, user_prompt: str) -> tuple[dict, int]:
        started = time.perf_counter()
        token = self._token()
        url = f"{settings.watsonx_url.rstrip('/')}/ml/v1/text/chat"
        params = {"version": settings.watsonx_api_version}
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "project_id": settings.watsonx_project_id,
            "model_id": settings.watsonx_model_id,
            "max_completion_tokens": 3500,
            "temperature": 0.1,
        }
        r = requests.post(
            url,
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        body = r.json()
        content = body["choices"][0]["message"]["content"]
        latency_ms = int((time.perf_counter() - started) * 1000)
        return self._extract_json(content), latency_ms
