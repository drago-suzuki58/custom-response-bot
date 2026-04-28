from dataclasses import dataclass
import re
from typing import Any

import discord


@dataclass(slots=True)
class FunctionContext:
    bot: discord.Client
    message: discord.Message
    author: discord.User | discord.Member
    channel: discord.abc.Messageable
    guild: discord.Guild | None
    trigger_match: re.Match[str] | None = None

    def group(self, key: int | str, default: Any = None) -> Any:
        if self.trigger_match is None:
            return default

        try:
            value = self.trigger_match.group(key)
        except IndexError:
            return default

        return default if value is None else value

    def groupdict(self) -> dict[str, str | None]:
        if self.trigger_match is None:
            return {}

        return self.trigger_match.groupdict()
