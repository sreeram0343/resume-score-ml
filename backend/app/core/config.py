from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./resume_db.db"
    redis_url: str = "redis://localhost:6379/0"
    model_path: str = "app/models/scorer.pkl"
    max_file_size_mb: int = 5
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
