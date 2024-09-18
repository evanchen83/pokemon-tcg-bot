import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.connect4 import Connect4
from cogs.pkmncards import PkmnCards
from cogs.poke2spy import Poke2Spy
from cogs.tetris import Tetris
from cogs.wordle import Wordle

load_dotenv()

bot = commands.Bot(
    command_prefix="poketcg ",
    intents=discord.Intents.all(),
    owner_id=int(os.environ["OWNER_ID"]),
)


@bot.event
async def on_ready():
    await bot.add_cog(PkmnCards())
    await bot.add_cog(Poke2Spy())
    await bot.add_cog(Wordle(bot))
    await bot.add_cog(Connect4(bot))
    await bot.add_cog(Tetris(bot))


bot.run(os.environ["DISCORD_TOKEN"])
