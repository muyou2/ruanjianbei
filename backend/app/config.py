from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
RUNTIME_DIR = BASE_DIR / "runtime"


class Settings(BaseSettings):
    app_name: str = "智学方舟 API"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"
    llm_provider: str = "auto"

    spark_api_key: str = ""
    spark_base_url: str = ""
    spark_model: str = "generalv3.5"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return RUNTIME_DIR / "zhixue.db"

    @property
    def uploads_dir(self) -> Path:
        return RUNTIME_DIR / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return RUNTIME_DIR / "chroma"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return settings
