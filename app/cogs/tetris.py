import asyncio
import copy
import dataclasses
import random
from collections import defaultdict, deque

import discord
import numpy as np
from discord.ext import commands


@dataclasses.dataclass
class Piece:
    color_id: int
    rotation_masks: deque[list[list[int]]]
    anchor_row: int = 0
    anchor_col: int = 4

    def overlay_cells(self):
        cells = []
        current_rotation_mask = self.rotation_masks[0]
        for r in range(len(current_rotation_mask)):
            for c in range(len(current_rotation_mask[0])):
                if current_rotation_mask[r][c]:
                    cells.append((self.anchor_row + r, self.anchor_col + c))
        return cells


PIECE_J_ROT_1 = [[0, 0, 0], [1, 1, 1], [0, 0, 1]]
PIECE_J_ROT_2 = [[0, 1, 0], [0, 1, 0], [1, 1, 0]]
PIECE_J_ROT_3 = [[0, 0, 0], [1, 0, 0], [1, 1, 1]]
PIECE_J_ROT_4 = [[0, 1, 0], [0, 1, 0], [0, 1, 1]]
PIECE_J = Piece(
    color_id="🟩",
    rotation_masks=deque([PIECE_J_ROT_1, PIECE_J_ROT_2, PIECE_J_ROT_3, PIECE_J_ROT_4]),
)

PIECE_L_ROT_1 = [[0, 0, 0], [1, 1, 1], [1, 0, 0]]
PIECE_L_ROT_2 = [[1, 1, 0], [0, 1, 0], [0, 1, 0]]
PIECE_L_ROT_3 = [[0, 0, 0], [0, 0, 1], [1, 1, 1]]
PIECE_L_ROT_4 = [[0, 1, 0], [0, 1, 0], [0, 1, 1]]
PIECE_L = Piece(
    color_id="🟧",
    rotation_masks=deque([PIECE_L_ROT_1, PIECE_L_ROT_2, PIECE_L_ROT_3, PIECE_L_ROT_4]),
)

PIECE_T_ROT_1 = [[0, 0, 0], [1, 1, 1], [0, 1, 0]]
PIECE_T_ROT_2 = [[0, 1, 0], [1, 1, 0], [0, 1, 0]]
PIECE_T_ROT_3 = [[0, 0, 0], [0, 1, 0], [1, 1, 1]]
PIECE_T_ROT_4 = [[0, 1, 0], [0, 1, 1], [0, 1, 0]]
PIECE_T = Piece(
    color_id="🟦",
    rotation_masks=deque([PIECE_T_ROT_1, PIECE_T_ROT_2, PIECE_T_ROT_3, PIECE_T_ROT_4]),
)

PIECE_Z_ROT_1 = [[0, 0, 0], [0, 1, 1], [1, 1, 0]]
PIECE_Z_ROT_2 = [[1, 0, 0], [1, 1, 0], [0, 1, 0]]
PIECE_Z_ROT_3 = [[0, 0, 0], [0, 1, 1], [1, 1, 0]]
PIECE_Z_ROT_4 = [[1, 0, 0], [1, 1, 0], [0, 1, 0]]
PIECE_Z = Piece(
    color_id="🟪",
    rotation_masks=deque([PIECE_Z_ROT_1, PIECE_Z_ROT_2, PIECE_Z_ROT_3, PIECE_Z_ROT_4]),
)

PIECE_S_ROT_1 = [[0, 0, 0], [1, 1, 0], [0, 1, 1]]
PIECE_S_ROT_2 = [[0, 0, 1], [0, 1, 1], [0, 1, 0]]
PIECE_S_ROT_3 = [[0, 0, 0], [1, 1, 0], [0, 1, 1]]
PIECE_S_ROT_4 = [[0, 0, 1], [0, 1, 1], [0, 1, 0]]
PIECE_S = Piece(
    color_id="🟨",
    rotation_masks=deque([PIECE_S_ROT_1, PIECE_S_ROT_2, PIECE_S_ROT_3, PIECE_S_ROT_4]),
)


PIECE_I_ROT_1 = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]]
PIECE_I_ROT_2 = [[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]]
PIECE_I = Piece(color_id="🟥", rotation_masks=deque([PIECE_I_ROT_1, PIECE_I_ROT_2]))

PIECE_D_ROT_1 = [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
PIECE_D = Piece(color_id="🟫", rotation_masks=deque([PIECE_D_ROT_1]))

PIECES = [PIECE_L, PIECE_J, PIECE_T, PIECE_Z, PIECE_S, PIECE_I, PIECE_D]


def is_valid_cells(cells, grid):
    for r, c in cells:
        if not (0 < r < len(grid)) or not (-1 < c < len(grid[0])) or grid[r][c] != "⬛":
            return False
    return True


def clear_rows(grid):
    full_row_indexes = np.any(grid == "⬛", axis=1)
    num_removed_rows = np.sum(~full_row_indexes)
    return np.vstack(
        (np.full((num_removed_rows, grid.shape[1]), "⬛"), grid[full_row_indexes])
    ), num_removed_rows


def move_player(player_move, piece, grid):
    if player_move == "⬅️":
        cells_move_left = [(r, c - 1) for r, c in piece.overlay_cells()]
        if is_valid_cells(cells_move_left, grid):
            piece.anchor_col -= 1
    elif player_move == "➡️":
        cells_move_left = [(r, c + 1) for r, c in piece.overlay_cells()]
        if is_valid_cells(cells_move_left, grid):
            piece.anchor_col += 1
    elif player_move == "⬆️":
        piece.rotation_masks.rotate(1)
        if not is_valid_cells(piece.overlay_cells(), grid):
            piece.rotation_masks.rotate(-1)
    elif player_move == "⬇️":
        while True:
            cells_move_left = [(r + 1, c) for r, c in piece.overlay_cells()]
            if is_valid_cells(cells_move_left, grid):
                piece.anchor_row += 1
            else:
                break


def make_grid_embed(grid, piece, score):
    overlay_grid = copy.deepcopy(grid)
    for r, c in piece.overlay_cells():
        overlay_grid[r][c] = piece.color_id

    grid_str = ""
    for r in overlay_grid[3:]:
        grid_str += "".join(r) + "\n"

    return discord.Embed(title=f"TETRIS. Score: {score}", description=grid_str)


player_moves_by_game = defaultdict(deque)


class Tetris(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        player_moves_by_game[reaction.message.id].append(reaction.emoji)
        await reaction.message.remove_reaction(reaction.emoji, user)

    @commands.command()
    async def tetris_play(self, ctx):
        """Play a classic game of Tetris."""
        current_piece = copy.deepcopy(random.choice(PIECES))
        grid = np.full((22, 10), "⬛")
        score = 0

        game_msg = await ctx.send(embed=make_grid_embed(grid, current_piece, score))
        await game_msg.add_reaction("⬆️")
        await game_msg.add_reaction("⬇️")
        await game_msg.add_reaction("⬅️")
        await game_msg.add_reaction("➡️")
        await game_msg.add_reaction("❌")

        while True:
            if player_moves_by_game[game_msg.id]:
                player_move = player_moves_by_game[game_msg.id].pop()
                if player_move == "❌":
                    await ctx.send("GAME OVER")
                    break
                else:
                    move_player(player_move, current_piece, grid)

            cells_move_down = [(r + 1, c) for r, c in current_piece.overlay_cells()]
            if is_valid_cells(cells_move_down, grid):
                current_piece.anchor_row += 1
            else:
                for r, c in current_piece.overlay_cells():
                    grid[r][c] = current_piece.color_id

                current_piece = copy.deepcopy(random.choice(PIECES))
                if not is_valid_cells(current_piece.overlay_cells(), grid):
                    await ctx.send("GAME OVER")
                    break

            grid, num_removed_rows = clear_rows(grid)
            score += num_removed_rows * 10

            await game_msg.edit(embed=make_grid_embed(grid, current_piece, score))
            await asyncio.sleep(1)
