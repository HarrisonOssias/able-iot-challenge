"""
Configuration settings for the IoT Ingest Service.

This module uses pydantic_settings to manage application configuration with:
- Type validation (similar to TypeScript interfaces)
- Environment variable loading (.env file support)
- Default values where appropriate

Configuration values can be provided via environment variables or .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Attributes:
        database_url: PostgreSQL connection string (required)
        app_name: Name of the application (defaults to "AbleIoTIngest")
        provision_secret: Shared secret for HMAC device provisioning token verification
    """
    database_url: str  # Required, loaded from DATABASE_URL env var
    app_name: str = "AbleIoTIngest"  # Default application name
    provision_secret: str = "ABLE-SECRET"  # Shared HMAC secret for device_startup auth
    
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file if present
        env_prefix="",    # No prefix on env vars
        case_sensitive=False  # Case-insensitive env var matching
    )


# Create a global settings instance for import throughout the application
settings = Settings()
