from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API CCC
    CCC_API_URL: str = "https://api.ccc.bzctoons.net"
    CCC_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/watchtower"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Monitoring
    METRICS_COLLECTION_INTERVAL: int = 60  # secondes
    ALERT_THRESHOLDS: dict = {
        "low_activity": 10,
        "high_failure_rate": 0.15,
        "resource_warning": 0.8
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
