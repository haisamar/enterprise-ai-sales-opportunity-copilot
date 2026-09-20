from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./copilot.db"
    copilot_mode: str = "mock"
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = ""
    watsonx_model_id: str = "ibm/granite-4-h-small"
    watsonx_api_version: str = "2025-10-25"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @property
    def watsonx_configured(self) -> bool:
        return bool(
            self.watsonx_api_key.strip()
            and self.watsonx_project_id.strip()
            and self.watsonx_url.strip()
            and self.watsonx_model_id.strip()
        )


settings = Settings()
