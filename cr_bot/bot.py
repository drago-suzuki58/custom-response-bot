import re

import discord
from discord.app_commands import describe
from loguru import logger

import cr_bot.env as env
import cr_bot.response as response
from cr_bot.function_context import FunctionContext
from cr_bot.function_catalog import FunctionCatalog
from cr_bot.render_types import RenderedResponse
from cr_bot.response_renderer import ResponseRenderer
from cr_bot.ui.function_browser import FunctionBrowserView
from cr_bot.ui.response_browser import ResponseBrowserView


class BotManager:
    def __init__(
        self,
        bot: discord.Client,
        tree: discord.app_commands.CommandTree,
        response_manager: response.ResponseManager,
    ):
        self.bot = bot
        self.tree = tree
        self.response_manager = response_manager
        self.response_renderer = ResponseRenderer()

        self.bot_setup()

    def bot_setup(self) -> None:
        @self.bot.event
        async def on_ready():
            logger.info(f"Logged in as {self.bot.user}")

            if env.COMMAND_ENABLED:
                self.setup_commands()
                await self.tree.sync()
                logger.info("Synced commands Successfully")
            else:
                logger.info("Command functionality is disabled.")

            response_count = len(self.response_manager.list())
            logger.info(f"Loaded {response_count} responses.")

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author == self.bot.user:
                return

            for idx, resp in enumerate(self.response_manager.list()):
                match = re.search(resp["trigger"], message.content, re.IGNORECASE)
                if match:
                    context = FunctionContext(
                        bot=self.bot,
                        message=message,
                        author=message.author,
                        channel=message.channel,
                        guild=message.guild,
                        trigger_match=match,
                    )
                    rendered = await self.response_renderer.render(
                        resp["response"], context
                    )

                    if rendered.content is None and not rendered.embeds:
                        logger.warning(f"Response {idx} rendered empty and was skipped.")
                        break

                    await self.send_rendered_response(message.channel, rendered)
                    break

    async def send_rendered_response(
        self, channel: discord.abc.Messageable, rendered: RenderedResponse
    ) -> None:
        if not rendered.embeds:
            await channel.send(content=rendered.content)
            return

        embeds_per_message = 10
        embed_chunks = [
            rendered.embeds[idx : idx + embeds_per_message]
            for idx in range(0, len(rendered.embeds), embeds_per_message)
        ]

        for idx, embed_chunk in enumerate(embed_chunks):
            content = rendered.content if idx == 0 else None
            await channel.send(content=content, embeds=embed_chunk)

    def setup_commands(self) -> None:
        logger.info("Setting up commands...")

        @self.tree.command(
            name="add_response",
            description="Add a new response trigger",
        )
        @describe(
            trigger="The trigger word or phrase",
            response="The response message",
        )
        async def add_event(
            interaction: discord.Interaction, trigger: str, response: str
        ):
            logger.debug(f"{interaction.guild_id} - add_response")
            await interaction.response.defer()

            self.response_manager.add(trigger, response)

            await interaction.followup.send(
                content=f"Trigger added successfully!\n`{trigger}`\n-> {response}"
            )

        @self.tree.command(
            name="remove_response",
            description="Remove a response trigger by its ID",
        )
        @describe(id="The ID of the response to remove")
        async def remove_event(interaction: discord.Interaction, id: int):
            logger.debug(f"{interaction.guild_id} - remove_response")
            await interaction.response.defer()

            try:
                deleted_response = self.response_manager.get(id)
                if deleted_response is None:
                    raise IndexError("Response ID out of range")

                self.response_manager.remove(id)
                await interaction.followup.send(
                    content=f"Trigger removed successfully! \n`{deleted_response['trigger']}`\n-> {deleted_response['response']}"
                )
            except IndexError:
                await interaction.followup.send(
                    content="Error: Response ID out of range."
                )

        @self.tree.command(
            name="list_responses",
            description="List all response triggers",
        )
        async def list_event(interaction: discord.Interaction):
            logger.debug(f"{interaction.guild_id} - list_responses")

            responses = self.response_manager.list()
            if not responses:
                await interaction.response.send_message(
                    "No response triggers found.", ephemeral=True
                )
                return

            view = ResponseBrowserView(responses, interaction.user.id)
            await interaction.response.send_message(
                content=view.build_content(),
                embeds=view.build_embeds(),
                view=view,
                ephemeral=True,
            )

        @self.tree.command(
            name="list_functions",
            description="Browse available func:// functions",
        )
        async def list_functions_event(interaction: discord.Interaction):
            logger.debug(f"{interaction.guild_id} - list_functions")

            catalog = FunctionCatalog()
            view = FunctionBrowserView(catalog, interaction.user.id)
            await interaction.response.send_message(
                content=view.build_content(),
                embeds=view.build_embeds(),
                view=view,
                ephemeral=True,
            )

        logger.info("Commands set up successfully!")

    def run(self, token: str | None = env.DISCORD_TOKEN) -> None:
        logger.info("Running bot...")
        if token is None:
            logger.error("DISCORD_TOKEN is not set. Cannot run the bot.")
            return
        else:
            self.bot.run(token)
