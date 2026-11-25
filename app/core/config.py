
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Cloud Document Processing Engine"

    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:password@localhost:5432/document_engine"
    )

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    TIKA_SERVER_URL: str = "http://localhost:9998"

    S3_ENDPOINT_URL: str = "http://127.0.0.1:8333"

    AWS_ACCESS_KEY_ID: str = "localadmin"

    AWS_SECRET_ACCESS_KEY: str = "localpassword"

    AWS_DEFAULT_REGION: str = "us-east-1"

    S3_BUCKET_NAME: str = "document-bucket"

    AZURE_STORAGE_CONNECTION_STRING: str = "UseDevelopmentStorage=true"

    AZURE_CONTAINER_NAME: str = "document-container"

    MAX_FILE_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
