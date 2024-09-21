import asyncio
import random
from pathlib import Path

import discord
from discord.ext import commands

all_words = Path("bot/data/valid_wordle_words.txt").read_text().split("\n")
target = random.choice(all_words)


def make_board_embed(
    target: str, guesses: list[str], username: str, chances: int
) -> discord.Embed:
    board = ""
    for guess in guesses:
        for target_char, guess_char in zip(target, guess):
            if target_char == guess_char:
                board += "🟩"
            elif guess_char in target:
                board += "🟨"
            else:
                board += "⬛"
        board += "\n"

    return (
        discord.Embed(title=f"{username.capitalize()}'s Wordle")
        .add_field(name="", value=board, inline=False)
        .add_field(name="Guesses: ", value=",".join(guesses), inline=False)
        .add_field(name="Chances: ", value=chances)
    )


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_valid_guess(self, ctx) -> str:
        async def notify_invalid():
            await ctx.send("Guess not a valid word.")

        def check(message):
            if message.author.id != ctx.author.id:
                return False

            valid_guess = message.content.lower() in all_words
            if not valid_guess:
                asyncio.create_task(notify_invalid())
            return ctx.author.id == message.author.id and valid_guess

        guess = await self.bot.wait_for("message", check=check, timeout=60)
        return guess.content.lower()

    @commands.command()
    async def refresh_wordle_answer(self, ctx):
        """Refresh the Wordle game for new challenges."""
        global target
        target = random.choice(all_words)
        await ctx.reply("Refreshed Wordle answer!")

    @commands.command()
    @commands.is_owner()
    async def show_worlde_answer(self, ctx):
        """Reveal the answer to the current Wordle game."""
        await ctx.reply(f"Wordle answer: {target}")

    @commands.command()
    async def play_wordle(self, ctx):
        """Start a new game of Wordle."""
        chances = 5
        guesses = []

        await ctx.send(
            f"Welcome {ctx.author.name.capitalize()}! Please enter a 5 letter word, you have 60 seconds between to enter a valid guess."
        )
        while True:
            try:
                guess = await self._get_valid_guess(ctx)
            except asyncio.TimeoutError:
                await ctx.reply(f"Sorry {ctx.author.name.capitalize()}! Out of Time!")
                break

            guesses.append(guess)
            await ctx.reply(
                embed=make_board_embed(target, guesses, ctx.author.name, chances)
            )
            if guess == target:
                await ctx.reply(
                    f"Congrats {ctx.author.name.capitalize()}! You guessed the word!"
                )
                await self.wordle_refresh(ctx)
                break

            chances -= 1
            if chances < 0:
                await ctx.reply(
                    f"Sorry {ctx.author.name.capitalize()}! Out of guesses!"
                )
                break
