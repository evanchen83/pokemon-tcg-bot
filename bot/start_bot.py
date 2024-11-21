import logging

import discord
from discord.ext import commands

from bot.cogs.pokemontcg import PokemonTCG
from bot.config import config

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    logger.info(f"Bot is ready as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.event
async def setup_hook():
    await bot.add_cog(PokemonTCG(bot))


bot.run(config.discord_token)
