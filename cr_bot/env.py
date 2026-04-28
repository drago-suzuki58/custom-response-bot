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


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid integer for {name}: {value!r}. Using {default}.")
        return default


# Discord
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN", None)
COMMAND_ENABLED = _get_bool_env("COMMAND_ENABLED", True)

# Response rendering
RESPONSE_RENDER_RECURSION_LIMIT = max(
    0, _get_int_env("RESPONSE_RENDER_RECURSION_LIMIT", 5)
)
RESPONSE_RENDER_LIMIT_ERROR_MESSAGE = os.getenv(
    "RESPONSE_RENDER_LIMIT_ERROR_MESSAGE",
    "レスポンスの展開回数が上限に達しました。",
)
FUNCTION_UNKNOWN_ERROR_MESSAGE = os.getenv(
    "FUNCTION_UNKNOWN_ERROR_MESSAGE",
    "関数の実行に失敗しました。",
)
