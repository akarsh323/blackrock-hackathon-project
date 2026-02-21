from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "INFO"
    workers: int = 1

    # ── Interest Rates ─────────────────────────────────────────────────────────────
    # 7.11% annual return for NPS
    # 14.49% annual return for Index Fund

    NPS_RATE: float = 0.0711
    INDEX_RATE: float = 0.1449
    MIN_YEARS_TO_RETIREMENT: int = 5
    RETIREMENT_AGE: int = 60


settings = Settings()
