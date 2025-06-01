from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cockroach_database_url: str
    mongo_uri: str
    secret_key: str

    email_host: str
    email_port: int
    email_user: str
    email_password: str
    email_from: str

    frontend_url: str

    class Config:
        env_file = ".env"   # or similar
