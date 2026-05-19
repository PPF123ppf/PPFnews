import os
from src.models import PushConfig


def load_config() -> PushConfig:
    return PushConfig(
        serverchan_key=os.getenv("SERVERCHAN_KEY", ""),
        pushplus_token=os.getenv("PUSHPLUS_TOKEN", ""),
    )
