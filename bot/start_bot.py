import os
from discord.ext import commands
from dotenv import load_dotenv
from cogs.tetris import Tetris
from cogs.poke2spy import Poke2Spy
import discord

from cogs.connect4 import Connect4
from cogs.pkmncards import PkmnCards
from cogs.wordle import Wordle


load_dotenv()
has_loaded_cogs = False

bot = commands.Bot(
    command_prefix="poketcg ",
    intents=discord.Intents.all(),
    owner_id=int(os.environ["OWNER_ID"]),
)


@bot.event
async def on_ready():
    global has_loaded_cogs
    if has_loaded_cogs:
        return

    await bot.add_cog(PkmnCards())
    await bot.add_cog(Poke2Spy())
    await bot.add_cog(Wordle(bot))
    await bot.add_cog(Connect4(bot))
    await bot.add_cog(Tetris(bot))

    has_loaded_cogs = True


bot.run(os.environ["DISCORD_TOKEN"])
