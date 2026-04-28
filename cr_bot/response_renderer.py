from collections.abc import Callable
from dataclasses import dataclass, field
import re

import discord
from loguru import logger


@dataclass(slots=True)
class DirectiveOutput:
    content: str = ""
    embeds: list[discord.Embed] = field(default_factory=list)


@dataclass(slots=True)
class RenderedResponse:
    content: str | None
    embeds: list[discord.Embed] = field(default_factory=list)


DirectiveHandler = Callable[[str], DirectiveOutput]

_DISCORD_URL_BODY = r"[^\s<]+[^<.,:;\"'\]\s]"


class ResponseRenderer:
    def __init__(self):
        self._handlers: dict[str, DirectiveHandler] = {}
        self._pattern: re.Pattern[str] | None = None

        self.register_handler("img", self._build_image_handler("http"))
        self.register_handler("imgs", self._build_image_handler("https"))

    def register_handler(self, name: str, handler: DirectiveHandler) -> None:
        self._handlers[name] = handler
        self._pattern = self._build_pattern()

    def render(self, text: str) -> RenderedResponse:
        if not text or self._pattern is None:
            return RenderedResponse(content=text or None)

        parts: list[str] = []
        embeds: list[discord.Embed] = []
        cursor = 0

        for match in self._pattern.finditer(text):
            parts.append(text[cursor : match.start()])

            handler = self._handlers[match.group("directive")]
            try:
                output = handler(match.group("target"))
            except Exception as exc:
                logger.warning(f"Failed to render directive `{match.group(0)}`: {exc}")
                parts.append(match.group(0))
            else:
                parts.append(output.content)
                embeds.extend(output.embeds)

            cursor = match.end()

        parts.append(text[cursor:])
        content = self._normalize_content("".join(parts))
        return RenderedResponse(content=content, embeds=embeds)

    def _build_pattern(self) -> re.Pattern[str] | None:
        if not self._handlers:
            return None

        directives = "|".join(re.escape(name) for name in self._handlers)
        pattern = rf"(?P<directive>{directives})://(?P<target>{_DISCORD_URL_BODY})"
        return re.compile(pattern)

    @staticmethod
    def _build_image_handler(protocol: str) -> DirectiveHandler:
        def handler(target: str) -> DirectiveOutput:
            embed = discord.Embed()
            embed.set_image(url=f"{protocol}://{target}")
            return DirectiveOutput(embeds=[embed])

        return handler

    @staticmethod
    def _normalize_content(content: str) -> str | None:
        normalized_lines = [re.sub(r"[ \t]{2,}", " ", line).strip() for line in content.splitlines()]
        normalized = "\n".join(normalized_lines).strip()
        return normalized or None
