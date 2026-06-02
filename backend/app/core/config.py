from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    log_level: str = "INFO"
    database_url: str
    redis_url: str
    model_path: str = "/app/models/model.bin"
    max_file_size_mb: int = 5
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
