import asyncio
import io
from collections import deque
from typing import NamedTuple

import discord
import matplotlib.image as mpimg
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

from bot.utils import confirm_msg


class Player(NamedTuple):
    player: discord.Member
    color_id: int


BOARD_COLORS = {0: "white", 1: "red", 2: "yellow"}


def _draw_board(board: list[list[int]]) -> bytes:
    img = mpimg.imread("bot/data/connect4_board.jpg")
    fig, ax = plt.subplots()

    ax.imshow(img)
    ax.set_axis_off()

    x = 113
    y = 70
    piece_radius = 37
    for row in board[::-1]:
        x = 113
        for col in row:
            circle = patches.Circle(
                (x, y),
                piece_radius,
                edgecolor=BOARD_COLORS[col],
                facecolor=BOARD_COLORS[col],
                lw=3,
            )
            ax.add_patch(circle)
            x += (piece_radius * 2) + 18
        y += (piece_radius * 2) + 18

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    byte_array = io.BytesIO()
    plt.savefig(byte_array, format="jpg", bbox_inches="tight", pad_inches=0)
    plt.close(fig)

    byte_array.seek(0)
    return byte_array


def _has_win(board):
    lines = []
    lines.extend(board)
    lines.extend([board[:, i] for i in range(len(board[0]))])
    lines.extend([board.diagonal(offset=offset) for offset in range(len(board[0]))])
    lines.extend(
        [board.diagonal(offset=offset) for offset in range(-1, -len(board), -1)]
    )

    for line in lines:
        if len(line) < 4:
            continue

        for i in range(len(line) - 3):
            if len(set(line[i : i + 4])) == 1 and list(set(line[i : i + 4]))[0] != 0:
                return True

    return False


class Connect4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_valid_move(self, ctx, player_id, peeks):
        async def notify_invalid():
            await ctx.send("Not a valid move.")

        def check(message):
            if message.author.id != player_id:
                return False

            response = message.content
            if (
                not response.isnumeric()
                or not (1 <= int(response) <= 7)
                or peeks[int(response) - 1] >= 6
            ):
                asyncio.create_task(notify_invalid())
                return False

            return True

        msg = await self.bot.wait_for("message", check=check, timeout=60)
        return int(msg.content) - 1

    @commands.command()
    async def connect4(self, ctx, opponent: discord.User):
        "Play a game of Connect 4 with your friends."
        challenge_embed = (
            discord.Embed(
                title=f"{opponent.name.capitalize()}, you have been challenged to a Connect 4 game!"
            )
            .add_field(name="Challenger:", value=f"{ctx.author.name}", inline=True)
            .add_field(name="Opponent:", value=f"{opponent.name}", inline=True)
            .set_footer(text="React with 👍 to accept or 👎 to decline the challenge.")
        )
        if not await confirm_msg.request_confirm_message(
            ctx, self.bot, opponent, challenge_embed
        ):
            return

        players = deque([Player(ctx.author, 1), Player(opponent, 2)])

        board = np.zeros((6, 7))
        peeks = np.zeros(7)

        await ctx.send(
            file=discord.File(_draw_board(board), filename="connect4_board.jpg")
        )
        while True:
            await ctx.send(
                f"{players[0].player.name.capitalize()}'s {BOARD_COLORS[players[0].color_id]} move. Input a row number 1-7 to drop a piece."
            )

            try:
                player_move = await self._get_valid_move(ctx, players[0][0].id, peeks)
            except asyncio.TimeoutError:
                await ctx.reply(
                    f"Sorry {players[0].player.name.capitalize()}, out of time! {players[1].player.name.capitalize()} wins!"
                )
                break

            board[int(peeks[player_move])][[player_move]] = players[0].color_id
            peeks[player_move] += 1

            await ctx.send(
                file=discord.File(_draw_board(board), filename="connect4_board.jpg")
            )

            if _has_win(board):
                await ctx.send(f"{players[0].player.name.capitalize()}'s has won!")
                break

            players.rotate()
