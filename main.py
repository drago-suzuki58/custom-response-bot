import discord
from loguru import logger

from cr_bot.bot import BotManager
from cr_bot.response import ResponseManager

if __name__ == "__main__":
    logger.add("logs/file_{time}.log", rotation="1 week", enqueue=True)

    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=intents)
    tree = discord.app_commands.CommandTree(bot)

    response_manager = ResponseManager("data/responses.json5")
    bot_manager = BotManager(bot, tree, response_manager)

    try:
        logger.info("Starting bot...")
        bot_manager.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
