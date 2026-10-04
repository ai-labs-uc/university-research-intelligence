from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "University Research Call for Paper Opportunity and Grants"
    app_env: str = "development"
    secret_key: str = "change-this-secret"

    # MongoDB Atlas connection. Set MONGODB_URI (and optionally
    # MONGODB_DB_NAME) in the environment / .env file. The database and
    # its collections/indexes are created automatically on first run —
    # there is no schema migration step to run by hand.
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "research_intelligence"

    cors_origins: str = "http://localhost:5173"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    google_client_id: str = ""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
