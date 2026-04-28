import ast
import importlib
import inspect
import json
from collections.abc import Iterable
from urllib.parse import parse_qsl

import discord
from loguru import logger

import cr_bot.env as env
from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError
from cr_bot.render_types import DirectiveOutput


class FunctionInvoker:
    def __init__(self, root_package: str = "function"):
        self.root_package = root_package

    async def invoke(
        self, target: str, context: FunctionContext | None
    ) -> DirectiveOutput:
        try:
            if context is None:
                raise FunctionDirectiveError("関数実行コンテキストがありません。")

            module_name, function_name, kwargs = self._parse_target(target)
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as exc:
                if exc.name != module_name:
                    raise

                raise FunctionDirectiveError(
                    "指定された関数が見つかりません。",
                    log_message=f"Function module not found: {module_name}",
                ) from exc

            func = getattr(module, function_name, None)
            if not callable(func):
                raise FunctionDirectiveError(
                    "指定された関数が見つかりません。",
                    log_message=f"Function is not callable: {module_name}.{function_name}",
                )

            result = func(context, **kwargs)
            if inspect.isawaitable(result):
                result = await result

            return self._normalize_result(result)
        except FunctionDirectiveError as exc:
            logger.warning(exc.log_message or exc.public_message)
            return DirectiveOutput(content=exc.public_message)
        except Exception as exc:
            logger.exception(f"Unexpected function directive error: {target}: {exc}")
            return DirectiveOutput(content=env.FUNCTION_UNKNOWN_ERROR_MESSAGE)

    def _parse_target(self, target: str) -> tuple[str, str, dict[str, object]]:
        call_path, separator, query = target.partition("?")
        if not call_path:
            raise FunctionDirectiveError("関数名が指定されていません。")

        parts = call_path.split(".")
        if len(parts) < 2:
            raise FunctionDirectiveError(
                "関数は module.function の形式で指定してください。"
            )

        for part in parts:
            self._validate_identifier(part, "関数パス")

        module_path = ".".join(parts[:-1])
        function_name = parts[-1]
        kwargs = self._parse_query(query) if separator else {}
        return f"{self.root_package}.{module_path}", function_name, kwargs

    def _parse_query(self, query: str) -> dict[str, object]:
        kwargs: dict[str, object] = {}
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True)

        for key, value in pairs:
            self._validate_identifier(key, "引数名")
            if key in kwargs:
                raise FunctionDirectiveError(
                    f"引数 `{key}` が重複しています。",
                    log_message=f"Duplicate function argument: {key}",
                )

            try:
                kwargs[key] = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise FunctionDirectiveError(
                    f"引数 `{key}` はPythonリテラルで指定してください。",
                    log_message=f"Invalid function argument literal: {key}={value!r}",
                ) from exc

        return kwargs

    @staticmethod
    def _validate_identifier(value: str, label: str) -> None:
        if not value.isidentifier() or value.startswith("_"):
            raise FunctionDirectiveError(
                f"{label} `{value}` は使用できません。",
                log_message=f"Invalid identifier for {label}: {value}",
            )

    def _normalize_result(self, result: object) -> DirectiveOutput:
        if isinstance(result, DirectiveOutput):
            return result

        if isinstance(result, discord.Embed):
            return DirectiveOutput(embeds=[result])

        embeds = self._collect_embed_iterable(result)
        if embeds is not None:
            return DirectiveOutput(embeds=embeds)

        if result is None:
            return DirectiveOutput()

        if isinstance(result, str):
            return DirectiveOutput(content=result)

        if isinstance(result, int | float | bool):
            return DirectiveOutput(content=str(result))

        return DirectiveOutput(content=self._stringify_object(result))

    @staticmethod
    def _collect_embed_iterable(result: object) -> list[discord.Embed] | None:
        if isinstance(result, str | bytes):
            return None
        if not isinstance(result, Iterable):
            return None

        items = list(result)
        if not items or not all(isinstance(item, discord.Embed) for item in items):
            return None

        return items

    @staticmethod
    def _stringify_object(result: object) -> str:
        try:
            return json.dumps(result, ensure_ascii=False, default=str)
        except TypeError:
            return str(result)
