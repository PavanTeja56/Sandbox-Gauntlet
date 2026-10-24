import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PORT: int = 8080
    DATABASE_URL: str = "postgresql://ledger:ledger@ledger:5432/ledger"
    CELESTO_PROVIDER: str = "cloud"
    CELESTO_API_KEY: str = ""
    CELESTO_BACKEND: str = "firecracker"
    LLM_BASE_URL: str = "https://example-llm-host/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "replace-with-a-model-name"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
