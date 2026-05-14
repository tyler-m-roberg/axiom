from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "axiom"
    postgres_password: str = "axiom"
    postgres_db: str = "axiom"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    keycloak_url: str = "http://localhost:8080"
    keycloak_public_url: str = "http://localhost:8080"
    keycloak_realm: str = "axiom"
    keycloak_client_id: str = "axiom-bff"
    keycloak_client_secret: str = "axiom-bff-secret-change-me"
    keycloak_admin_username: str = "admin"
    keycloak_admin_password: str = "admin"

    api_public_url: str = "http://localhost:8000"
    web_public_url: str = "http://localhost:5173"

    session_encryption_key: str = ""
    session_cookie_name: str = "axiom_sid"
    session_cookie_secure: bool = False
    session_lifetime_seconds: int = 43200

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def keycloak_realm_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_public_realm_url(self) -> str:
        return f"{self.keycloak_public_url}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
