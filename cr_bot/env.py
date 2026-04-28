import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.debug("Loading environment variables...")


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


# Discord
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN", None)
COMMAND_ENABLED = _get_bool_env("COMMAND_ENABLED", True)
