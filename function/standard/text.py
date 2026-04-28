from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def upper(ctx: FunctionContext, *, text: str) -> str:
    """Convert text to uppercase.

    Standard package function.

    Sample:
        func://standard.text.upper?text=%22hello%20world%22

    Args:
        text: Source text.
    """
    return text.upper()


def lower(ctx: FunctionContext, *, text: str) -> str:
    """Convert text to lowercase.

    Standard package function.

    Sample:
        func://standard.text.lower?text=%22HELLO%20WORLD%22

    Args:
        text: Source text.
    """
    return text.lower()


def repeat(ctx: FunctionContext, *, text: str, count: int, separator: str = "") -> str:
    """Repeat text a limited number of times.

    Standard package function.

    Sample:
        func://standard.text.repeat?text=%22ha%22&count=3&separator=%22%20%22

    Args:
        text: Text to repeat.
        count: Repeat count from 1 to 20.
        separator: Text inserted between repeated values.
    """
    if count < 1 or count > 20:
        raise FunctionDirectiveError("count は1から20の範囲で指定してください。")

    return separator.join([text] * count)


def template(ctx: FunctionContext, *, text: str) -> str:
    """Format text with simple Discord context placeholders.

    Standard package function.

    Sample:
        func://standard.text.template?text=%22Hello%20%7Buser%7D%22

    Placeholders:
        {user}: Author display name.
        {mention}: Author mention.
        {channel}: Channel name if available.
        {guild}: Guild name if available.
    """
    return text.format(
        user=ctx.author.display_name,
        mention=ctx.author.mention,
        channel=getattr(ctx.channel, "name", "DM"),
        guild=ctx.guild.name if ctx.guild is not None else "DM",
    )
