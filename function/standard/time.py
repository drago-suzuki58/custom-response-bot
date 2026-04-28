from datetime import UTC, datetime, timedelta, timezone

from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def now(ctx: FunctionContext, *, offset_hours: int = 0, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return the current time with an optional hour offset.

    Standard package function.

    Sample:
        func://standard.time.now?offset_hours=9&format=%22%25Y-%25m-%25d%20%25H%3A%25M%22

    Args:
        offset_hours: Hour offset from UTC. Use 9 for JST.
        format: strftime format string.
    """
    if offset_hours < -24 or offset_hours > 24:
        raise FunctionDirectiveError("offset_hours は -24 から 24 の範囲で指定してください。")

    tz = timezone(timedelta(hours=offset_hours))
    return datetime.now(tz).strftime(format)


def unix(ctx: FunctionContext) -> int:
    """Return the current Unix timestamp.

    Standard package function.

    Sample:
        func://standard.time.unix
    """
    return int(datetime.now(UTC).timestamp())
