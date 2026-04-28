import discord

from cr_bot.ui.common import code_block, truncate_text


def response_flags(resp: dict) -> list[str]:
    response_text = str(resp.get("response", ""))
    result = []
    if "func://" in response_text:
        result.append("func")
    if "func://preset." in response_text:
        result.append("preset")
    if "func://standard." in response_text:
        result.append("standard")
    if "img://" in response_text or "imgs://" in response_text:
        result.append("image")
    return result


def build_response_copy_text(resp: dict) -> str:
    trigger = str(resp.get("trigger", ""))
    response = str(resp.get("response", ""))
    return f"trigger:\n{trigger}\n\nresponse:\n{response}"


def build_response_detail_embed(
    idx: int,
    resp: dict,
    *,
    title: str | None = None,
    color: int = 6956287,
    filter_label: str | None = None,
) -> discord.Embed:
    trigger = str(resp.get("trigger", ""))
    response = str(resp.get("response", ""))
    flags = ", ".join(response_flags(resp)) or "plain"

    embed = discord.Embed(
        title=title or f"Response #{idx}",
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="ID", value=f"`{idx}`", inline=True)
    if filter_label is not None:
        embed.add_field(name="Filter", value=f"`{filter_label}`", inline=True)
    embed.add_field(name="Flags", value=f"`{flags}`", inline=True)
    embed.add_field(
        name="Trigger",
        value=code_block(truncate_text(trigger, 1000), "regex"),
        inline=False,
    )
    embed.add_field(
        name="Response",
        value=code_block(truncate_text(response, 1000), "text"),
        inline=False,
    )
    return embed
