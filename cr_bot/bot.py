import re

import discord
from discord.app_commands import describe
from loguru import logger

import cr_bot.env as env
import cr_bot.response as response


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

        self.bot_setup()

    def bot_setup(self) -> None:
        @self.bot.event
        async def on_ready():
            logger.info(f"Logged in as {self.bot.user}")

            self.setup_commands()
            await self.tree.sync()
            logger.info("Synced commands Successfully")

            response_count = len(self.response_manager.list())
            logger.info(f"Loaded {response_count} responses.")

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author == self.bot.user:
                return

            for idx, resp in enumerate(self.response_manager.list()):
                if re.search(resp["trigger"], message.content, re.IGNORECASE):
                    await message.channel.send(resp["response"])
                    break

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
            message = await interaction.followup.send("Adding trigger...", wait=True)

            self.response_manager.add(trigger, response)

            await message.edit(
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
            message = await interaction.followup.send("Removing trigger...", wait=True)

            try:
                deleted_response = self.response_manager.get(id)
                if deleted_response is None:
                    raise IndexError("Response ID out of range")

                self.response_manager.remove(id)
                await message.edit(
                    content=f"Trigger removed successfully! \n`{deleted_response['trigger']}`\n-> {deleted_response['response']}"
                )
            except IndexError:
                await message.edit(content="Error: Response ID out of range.")

        @self.tree.command(
            name="list_responses",
            description="List all response triggers",
        )
        async def list_event(interaction: discord.Interaction):
            logger.debug(f"{interaction.guild_id} - list_responses")

            await interaction.response.defer()
            message = await interaction.followup.send("Fetching triggers...", wait=True)

            responses = self.response_manager.list()
            if not responses:
                await interaction.response.send_message("No response triggers found.")
                return

            embed = discord.Embed(
                title="Trigger List", color=6956287, timestamp=discord.utils.utcnow()
            )

            for idx, resp in enumerate(self.response_manager.list()):
                embed.add_field(
                    name=f"{idx}: `{resp['trigger']}`",
                    value=resp["response"],
                    inline=False,
                )

            await message.edit(embed=embed)

        logger.info("Commands set up successfully!")

    def run(self, token: str | None = env.DISCORD_TOKEN) -> None:
        logger.info("Running bot...")
        if token is None:
            logger.error("DISCORD_TOKEN is not set. Cannot run the bot.")
            return
        else:
            self.bot.run(token)
