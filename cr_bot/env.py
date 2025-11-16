import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.debug("Loading environment variables...")

# Discord
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN", None)
