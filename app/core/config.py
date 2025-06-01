# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    cockroach_database_url: str
    mongo_uri: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    email_host: str
    email_port: int
    email_user: str
    email_password: str
    email_from: str

    frontend_url: str

    # Tell Pydantic to also read a “.env” file if it exists
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

# At the bottom of this file, you must actually instantiate it:
settings = Settings()
