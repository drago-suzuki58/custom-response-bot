import hashlib
import uuid

from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def uuid4(ctx: FunctionContext) -> str:
    """Return a random UUID v4.

    Standard package function.

    Sample:
        func://standard.utility.uuid4
    """
    return str(uuid.uuid4())


def sha256(ctx: FunctionContext, *, text: str) -> str:
    """Return a SHA-256 hash for text.

    Standard package function.

    Sample:
        func://standard.utility.sha256?text=%22hello%22

    Args:
        text: Source text.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pick_by_user(ctx: FunctionContext, *, items: list[object]) -> object:
    """Pick a stable item based on the current user's Discord ID.

    Standard package function.

    Sample:
        func://standard.utility.pick_by_user?items=%5B%22A%22%2C%22B%22%2C%22C%22%5D

    Args:
        items: Non-empty list of values.

    Returns:
        The same user will get the same item while the list order stays unchanged.
    """
    if not items:
        raise FunctionDirectiveError("items には1件以上の値を指定してください。")

    return items[ctx.author.id % len(items)]
