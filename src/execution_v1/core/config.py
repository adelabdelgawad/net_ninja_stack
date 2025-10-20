from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    username: str
    password: SecretStr
    server: str
    port: int = 1433
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
    cc_address: str

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    database: DatabaseSettings = DatabaseSettings()
    email: EmailSettings = EmailSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()


def get_settings():
    return Settings()
