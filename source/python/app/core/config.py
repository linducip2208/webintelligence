import os
from dataclasses import dataclass, field
def _csv(name):
    v = os.getenv(name, "")
    return [x.strip() for x in v.split(",") if x.strip()]
@dataclass
class Settings:
    env: str = os.getenv("ENV", "dev")
    app_env: str = os.getenv("APP_ENV", os.getenv("ENV", "development"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./webintel.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me-0123456789")
    credentials_key: str = os.getenv("CREDENTIALS_KEY", "")
    muse_base_url: str = os.getenv("MUSE_SPARK_BASE_URL", "")
    muse_api_key: str = os.getenv("MUSE_SPARK_API_KEY", "")
    muse_model: str = os.getenv("MUSE_SPARK_MODEL", "muse-spark-1.3")
    brightdata_api_key: str = os.getenv("BRIGHTDATA_API_KEY", "")
    brightdata_zone: str = os.getenv("BRIGHTDATA_ZONE", "")
    brightdata_endpoint: str = os.getenv("BRIGHTDATA_ENDPOINT", "https://api.brightdata.com")
    own_proxy_urls: list = field(default_factory=lambda: _csv("OWN_PROXY_URLS"))
    trusted_egress_cidrs: list = field(default_factory=lambda: _csv("TRUSTED_EGRESS_CIDRS"))
settings = Settings()
