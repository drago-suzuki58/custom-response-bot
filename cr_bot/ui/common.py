import discord


PAGE_SIZE = 25
VIEW_TIMEOUT = 900


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1] + "…"


def code_block(text: str, language: str = "") -> str:
    return f"```{language}\n{text}\n```"


async def reject_other_user(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "このブラウザはコマンド実行者だけが操作できます。",
        ephemeral=True,
    )
