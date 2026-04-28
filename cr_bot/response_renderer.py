from collections.abc import Awaitable, Callable
import re

import discord
from loguru import logger

import cr_bot.env as env
from cr_bot.function_context import FunctionContext
from cr_bot.function_invoker import FunctionInvoker
from cr_bot.render_types import DirectiveOutput, RenderedResponse


DirectiveHandler = Callable[[str, FunctionContext | None], Awaitable[DirectiveOutput]]

_DISCORD_URL_BODY = r"[^\s<]+[^<.,:;\"'\]\s]"


class ResponseRenderer:
    def __init__(self):
        self._handlers: dict[str, DirectiveHandler] = {}
        self._pattern: re.Pattern[str] | None = None
        self.function_invoker = FunctionInvoker()

        self.register_handler("img", self._build_image_handler("http"))
        self.register_handler("imgs", self._build_image_handler("https"))
        self.register_handler("func", self._handle_function)

    def register_handler(self, name: str, handler: DirectiveHandler) -> None:
        self._handlers[name] = handler
        self._pattern = self._build_pattern()

    async def render(
        self, text: str, context: FunctionContext | None = None
    ) -> RenderedResponse:
        if not text or self._pattern is None:
            return RenderedResponse(content=text or None)

        content = text
        embeds: list[discord.Embed] = []

        for _ in range(env.RESPONSE_RENDER_RECURSION_LIMIT):
            rendered, changed = await self._render_once(content, context)
            content = rendered.content or ""
            embeds.extend(rendered.embeds)

            if not changed or not self._has_directive(content):
                return RenderedResponse(
                    content=self._normalize_content(content), embeds=embeds
                )

        if self._has_directive(content):
            logger.warning("Response render recursion limit reached.")
            content = f"{content}\n{env.RESPONSE_RENDER_LIMIT_ERROR_MESSAGE}"

        return RenderedResponse(content=self._normalize_content(content), embeds=embeds)

    async def _render_once(
        self, text: str, context: FunctionContext | None
    ) -> tuple[RenderedResponse, bool]:
        if self._pattern is None:
            return RenderedResponse(content=text or None), False

        parts: list[str] = []
        embeds: list[discord.Embed] = []
        cursor = 0
        changed = False

        for match in self._pattern.finditer(text):
            changed = True
            parts.append(text[cursor : match.start()])

            handler = self._handlers[match.group("directive")]
            try:
                output = await handler(match.group("target"), context)
            except Exception as exc:
                logger.warning(f"Failed to render directive `{match.group(0)}`: {exc}")
                parts.append(match.group(0))
            else:
                parts.append(output.content)
                embeds.extend(output.embeds)

            cursor = match.end()

        parts.append(text[cursor:])
        content = self._normalize_content("".join(parts))
        return RenderedResponse(content=content, embeds=embeds), changed

    def _build_pattern(self) -> re.Pattern[str] | None:
        if not self._handlers:
            return None

        directives = "|".join(re.escape(name) for name in self._handlers)
        pattern = rf"(?P<directive>{directives})://(?P<target>{_DISCORD_URL_BODY})"
        return re.compile(pattern)

    @staticmethod
    def _build_image_handler(protocol: str) -> DirectiveHandler:
        async def handler(
            target: str, context: FunctionContext | None
        ) -> DirectiveOutput:
            embed = discord.Embed()
            embed.set_image(url=f"{protocol}://{target}")
            return DirectiveOutput(embeds=[embed])

        return handler

    async def _handle_function(
        self, target: str, context: FunctionContext | None
    ) -> DirectiveOutput:
        return await self.function_invoker.invoke(target, context)

    def _has_directive(self, content: str) -> bool:
        return self._pattern is not None and self._pattern.search(content) is not None

    @staticmethod
    def _normalize_content(content: str) -> str | None:
        normalized_lines = [
            re.sub(r"[ \t]{2,}", " ", line).strip()
            for line in content.splitlines()
        ]
        normalized = "\n".join(normalized_lines).strip()
        return normalized or None
