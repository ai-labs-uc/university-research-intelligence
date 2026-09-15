from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "University Research Call for Paper Opportunity and Grants"
    app_env: str = "development"
    secret_key: str = "change-this-secret"
    database_url: str = (
        "mysql+pymysql://researchapp:researchapp@localhost:3306/"
        "research_intelligence"
    )
    cors_origins: str = "http://localhost:5173"

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    # Google OAuth client ID (from Google Cloud Console — see docs/AUTH.md).
    # Only the ID is needed server-side, to verify the "aud" claim on the
    # ID token the frontend receives from Google Identity Services; the
    # client secret is not used by this flow at all.
    google_client_id: str = ""

    model_config = SettingsConfigDict(
        env_file="../.env",
        extra="ignore",
    )

settings = Settings()
