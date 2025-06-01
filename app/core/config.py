# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field, ConfigDict

class Settings(BaseSettings):
    cockroach_database_url: AnyUrl = Field(..., env="COCKROACH_DATABASE_URL")
    mongo_uri:               str    = Field(..., env="MONGO_URI")

    secret_key:              str    = Field(..., env="SECRET_KEY")
    algorithm:               str    = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(60,    env="ACCESS_TOKEN_EXPIRE_MINUTES")


    # new email & frontend settings
    email_host:     str         = Field(..., env="EMAIL_HOST")
    email_port:     int         = Field(..., env="EMAIL_PORT")
    email_user:     str         = Field(..., env="EMAIL_USER")
    email_password: str         = Field(..., env="EMAIL_PASSWORD")
    email_from:     str         = Field(..., env="EMAIL_FROM")
    frontend_url:   AnyUrl      = Field(..., env="FRONTEND_URL")
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
