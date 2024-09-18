import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import cogs

load_dotenv()

bot = commands.Bot(
    command_prefix="poketcg ",
    intents=discord.Intents.all(),
    owner_id=int(os.environ["OWNER_ID"]),
)


@bot.event
async def on_ready():
    await bot.add_cog(cogs.PkmnCards())
    await bot.add_cog(cogs.Poke2Spy())
    await bot.add_cog(cogs.Wordle(bot))
    await bot.add_cog(cogs.Connect4(bot))
    await bot.add_cog(cogs.Tetris(bot))


bot.run(os.environ["DISCORD_TOKEN"])
