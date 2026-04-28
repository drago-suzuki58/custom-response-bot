from cr_bot.function_context import FunctionContext


def user_mention(ctx: FunctionContext) -> str:
    """Return the message author's mention.

    Standard package function.

    Sample:
        func://standard.discord_info.user_mention
    """
    return ctx.author.mention


def user_name(ctx: FunctionContext) -> str:
    """Return the message author's display name.

    Standard package function.

    Sample:
        func://standard.discord_info.user_name
    """
    return ctx.author.display_name


def channel_name(ctx: FunctionContext) -> str:
    """Return the current channel name, or DM for direct messages.

    Standard package function.

    Sample:
        func://standard.discord_info.channel_name
    """
    return getattr(ctx.channel, "name", "DM")


def guild_name(ctx: FunctionContext) -> str:
    """Return the current guild name, or DM for direct messages.

    Standard package function.

    Sample:
        func://standard.discord_info.guild_name
    """
    return ctx.guild.name if ctx.guild is not None else "DM"


async def async_user_summary(ctx: FunctionContext) -> str:
    """Return a small async sample using Discord context.

    Standard package function.

    Sample:
        func://standard.discord_info.async_user_summary

    This is intentionally async to show that async def functions are supported.
    """
    return f"{ctx.author.display_name} in {guild_name(ctx)}"
