from urllib.parse import quote_plus

import discord

from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def placeholder(ctx: FunctionContext, *, width: int = 600, height: int = 400, text: str = "sample") -> str:
    """Return an image directive for a placeholder image.

    Standard package function.

    Sample:
        func://standard.image.placeholder?width=600&height=400&text=%22Hello%22

    Args:
        width: Image width from 1 to 2000.
        height: Image height from 1 to 2000.
        text: Text shown in the placeholder image.

    Returns:
        imgs:// URL. The renderer will re-parse it into an image embed.
    """
    if width < 1 or width > 2000 or height < 1 or height > 2000:
        raise FunctionDirectiveError("width と height は1から2000の範囲で指定してください。")

    return f"imgs://placehold.co/{width}x{height}.png?text={quote_plus(text)}"


def embed(ctx: FunctionContext, *, url: str, title: str = "") -> discord.Embed:
    """Return a Discord embed with an image directly.

    Standard package function.

    Sample:
        func://standard.image.embed?url=%22https%3A%2F%2Fexample.com%2Fimage.png%22&title=%22Sample%22

    Args:
        url: Full http or https image URL.
        title: Optional embed title.
    """
    if not url.startswith(("http://", "https://")):
        raise FunctionDirectiveError("url は http:// または https:// で始めてください。")

    embed = discord.Embed(title=title or None)
    embed.set_image(url=url)
    return embed
