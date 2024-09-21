import discord
from discord.ext import commands

from bot import config
from bot.cogs.connect4 import Connect4
from bot.cogs.pkmncards import PkmnCards
from bot.cogs.poke2spy import Poke2Spy
from bot.cogs.tetris import Tetris
from bot.cogs.wordle import Wordle

has_loaded_cogs = False

bot = commands.Bot(
    command_prefix="poketcg ",
    intents=discord.Intents.all(),
    owner_id=int(config.OWNER_ID),
)


@bot.event
async def on_ready():
    global has_loaded_cogs
    if has_loaded_cogs:
        return

    await bot.add_cog(Poke2Spy())
    await bot.add_cog(PkmnCards(bot))
    await bot.add_cog(Wordle(bot))
    await bot.add_cog(Connect4(bot))
    await bot.add_cog(Tetris(bot))

    has_loaded_cogs = True


bot.run(config.DISCORD_TOKEN)
