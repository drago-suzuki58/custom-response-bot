from dataclasses import dataclass, field

import discord


@dataclass(slots=True)
class DirectiveOutput:
    content: str = ""
    embeds: list[discord.Embed] = field(default_factory=list)


@dataclass(slots=True)
class RenderedResponse:
    content: str | None
    embeds: list[discord.Embed] = field(default_factory=list)
