import os
import json
from typing import Dict, Any


class Settings:
    def __init__(self):
        # Dynamic
        self.CCC_API_URL = os.environ["CCC_API_URL"]
        self.CCC_API_KEY = None
        self.DATABASE_URL = os.environ["DATABASE_URL"]
        # Integers
        try:
            self.METRICS_COLLECTION_INTERVAL = int(os.environ["METRICS_COLLECTION_INTERVAL"])
        except KeyError as e:
            raise KeyError("METRICS_COLLECTION_INTERVAL is required") from e
        except ValueError as e:
            raise ValueError("METRICS_COLLECTION_INTERVAL must be an integer") from e

        # Static
        self.ALERT_THRESHOLDS = {
            "low_activity": 10,
            "high_failure_rate": 0.15,
            "resource_warning": 0.8
        }


settings = Settings()
