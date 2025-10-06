from pydantic_settings import BaseSettings, SettingsConfigDict
# I am used to using typescript which is why I chose to use pydantic for settings management. It is a great library for managing type safe validations in python especially using JSON schema.


class Settings(BaseSettings):
    database_url: str  # from env var DATABASE_URL
    app_name: str = "AbleIoTIngest"  # this is what I chose to name this app
    provision_secret: str = "ABLE-SECRET"   # shared HMAC for device_startup
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()
