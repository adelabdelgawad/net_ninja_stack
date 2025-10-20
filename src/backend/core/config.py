from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API configuration settings."""

    title: str
    description: str
    version: str

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    username: str
    password: SecretStr
    server: str
    name: str

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class EmailSettings(BaseSettings):
    """Email configuration settings."""

    subject: str
    server: str
    port: int
    username: str
    password: SecretStr
    sender_alias: str

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    api: APISettings = APISettings()
    database: DatabaseSettings = DatabaseSettings()
    email: EmailSettings = EmailSettings()

    # Celery configuration
    celery_broker_url: str
    celery_result_backend: str

    # Flower configuration
    flower_port: int

    # Elasticsearch configuration
    elasticsearch_connection_url: str

    encryption_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
