from ..config import settings
from ..services.watsonx import WatsonxClient


def main() -> None:
    client = WatsonxClient()
    missing = client.missing_config()
    if missing:
        print(f"CONFIG ERROR: missing {', '.join(missing)}")
        raise SystemExit(1)
    try:
        latency = client.ping()
    except Exception as exc:
        print(f"IBM CONNECTIVITY FAILED: {exc}")
        raise SystemExit(2) from exc
    print("connected=true")
    print("provider=watsonx.ai")
    print(f"model_id={settings.watsonx_model_id}")
    print(f"base_url={settings.watsonx_url}")
    print(f"latency_ms={latency}")


if __name__ == "__main__":
    main()
