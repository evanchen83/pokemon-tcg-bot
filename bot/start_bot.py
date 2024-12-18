import logging

import discord
from discord.ext import commands

from bot.cogs.agent import Agent
from bot.cogs.pokebox import PokeBox
from bot.cogs.poketcg import PokemonTCGBot
from bot.config import config

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    logger.debug(f"Bot is ready as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.debug(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.event
async def setup_hook():
    await bot.add_cog(PokemonTCGBot(bot))
    await bot.add_cog(PokeBox())
    await bot.add_cog(Agent())


bot.run(config.discord_token)
