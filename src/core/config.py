from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailSettings(BaseSettings):
    """Email configuration settings."""

    subject: str
    server: str
    port: int
    username: str
    password: SecretStr
    sender: str  # Added: Sender email address
    sender_alias: str
    cc_address: str

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ExecutionSettings(BaseSettings):
    """Execution control settings"""

    semaphore_limit: int = 2
    max_retry_attempts: int = 1

    model_config = SettingsConfigDict(
        env_prefix="EXEC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SpeedTestSettings(BaseSettings):
    """Speed test configuration"""

    download_chunk_size: int = 102400  # 100KB
    upload_chunk_size: int = 4194304  # 4MB
    test_count: int = 10
    latency_test_count: int = 3
    timeout: int = 30
    max_download_time: int = 15
    max_upload_time: int = 10

    model_config = SettingsConfigDict(
        env_prefix="SPEEDTEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    email: EmailSettings = EmailSettings()
    execution: ExecutionSettings = ExecutionSettings()
    speedtest: SpeedTestSettings = SpeedTestSettings()

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
