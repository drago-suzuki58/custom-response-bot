from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def add(ctx: FunctionContext, *, a: int | float, b: int | float) -> int | float:
    """Return a + b.

    Standard package function.

    Sample:
        func://standard.math.add?a=2&b=3
    """
    return a + b


def multiply(ctx: FunctionContext, *, a: int | float, b: int | float) -> int | float:
    """Return a * b.

    Standard package function.

    Sample:
        func://standard.math.multiply?a=4&b=5
    """
    return a * b


def clamp(ctx: FunctionContext, *, value: int | float, min: int | float, max: int | float) -> int | float:
    """Clamp a number to a min/max range.

    Standard package function.

    Sample:
        func://standard.math.clamp?value=120&min=0&max=100

    Raises:
        FunctionDirectiveError: If min is greater than max.
    """
    if min > max:
        raise FunctionDirectiveError("min は max 以下で指定してください。")

    return min if value < min else max if value > max else value
