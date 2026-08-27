from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Production Control API"
    database_url: str
    celery_broker_url: str
    celery_result_backend: str
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()