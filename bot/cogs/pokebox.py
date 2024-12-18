import logging
import pathlib
import random
from io import BytesIO

import cv2
import discord
import pydash
import rapidfuzz
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _load_pokemon_names() -> set[str]:
    return {p.stem for p in pathlib.Path("data/pokemon-sprites/regular").rglob("*.png")}


POKEMON_NAMES = _load_pokemon_names()
MAX_BOX_SIZE = 30
MAX_BOX_LIMIT = 10


def _overlay_transparent(background, overlay, x, y):
    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, ol_channels = overlay.shape

    if ol_channels < 4:
        raise ValueError("Overlay image must have an alpha channel")

    x1, x2 = max(0, x), min(bg_w, x + ol_w)
    y1, y2 = max(0, y), min(bg_h, y + ol_h)

    ol_x1, ol_x2 = max(0, -x), min(ol_w, bg_w - x)
    ol_y1, ol_y2 = max(0, -y), min(ol_h, bg_h - y)

    alpha = overlay[ol_y1:ol_y2, ol_x1:ol_x2, 3] / 255.0

    for c in range(3):
        background[y1:y2, x1:x2, c] = (
            alpha * overlay[ol_y1:ol_y2, ol_x1:ol_x2, c]
            + (1 - alpha) * background[y1:y2, x1:x2, c]
        )

    return background


def _overlay_box_name(box_index: str, box: cv2.typing.MatLike) -> cv2.typing.MatLike:
    position = (90, 20)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    color = (255, 255, 255)
    thickness = 1

    cv2.putText(
        box, box_index, position, font, font_scale, color, thickness, cv2.LINE_AA
    )
    return box


def _make_pokemon_box(pokemon_names: list[str], box_name: str) -> BytesIO:
    logger.debug("Creating box: %s with pokemon: %s", box_name, pokemon_names)
    box = cv2.imread("data/storage-bg.png", cv2.IMREAD_UNCHANGED)
    box = _overlay_box_name(box_name, box)

    sprite_width = 36
    x, y = int(-sprite_width * 0.25), sprite_width // 2
    i = 0
    for pokemon_name in pokemon_names:
        overlay = cv2.imread(
            f"data/pokemon-sprites/regular/{pokemon_name}.png",
            cv2.IMREAD_UNCHANGED,
        )

        box = _overlay_transparent(box, overlay, x, y)
        x += sprite_width
        if x >= sprite_width * 5:
            x = int(-sprite_width * 0.25)
            y += int(sprite_width * 0.9)
            i += 1

    _, buffer = cv2.imencode(".png", box)
    return BytesIO(buffer)


def _fuzzy_match_pokemon(pokemon_names: list[str]) -> list[str]:
    matched_pokemon = []

    for pokemon_name in pokemon_names:
        if pokemon_name in POKEMON_NAMES:
            matched_pokemon.append(pokemon_name)
            continue

        top_match, score, _ = rapidfuzz.process.extractOne(pokemon_name, POKEMON_NAMES)
        logger.debug(
            "Matched invalid pokemon name: %s with %s. Similarity: %s",
            pokemon_name,
            top_match,
            score,
        )

        matched_pokemon.append(top_match)

    return matched_pokemon


async def make_pokemon_boxes(
    interaction: discord.Interaction,
    random_size: int | None,
    pokemon_names: str | None,
    search_name: str | None,
):
    if not interaction.response.is_done():
        await interaction.response.defer()

    if search_name:
        pokemon_names = [p for p in POKEMON_NAMES if search_name.strip().lower() in p]
    elif pokemon_names:
        pokemon_names = _fuzzy_match_pokemon(
            [p.strip().lower() for p in pokemon_names.split(",")]
        )
    elif random_size:
        pokemon_names = random.choices(list(POKEMON_NAMES), k=int(random_size))

    if len(pokemon_names) > MAX_BOX_LIMIT * MAX_BOX_SIZE:
        return await interaction.followup.send(
            "Cannot generate more than 10 boxes of pokemon."
        )

    if invalid_pokemon_names := [p for p in pokemon_names if p not in POKEMON_NAMES]:
        return await interaction.followup.send(
            f"Invalid pokemon names: {invalid_pokemon_names}"
        )

    boxes = [
        _make_pokemon_box(n, f"Box: {i}")
        for i, n in enumerate(pydash.chunk(pokemon_names, MAX_BOX_SIZE))
    ]

    for i, box in enumerate(boxes):
        file = discord.File(fp=box, filename=f"image_{i}.png")

        embed = discord.Embed()
        embed.set_image(url=f"attachment://image_{i}.png")

        await interaction.followup.send(embed=embed, file=file)


class PokeBox(commands.Cog):
    @app_commands.command(name="box", description="Create a pokemon storage box")
    async def box(
        self,
        interaction: discord.Interaction,
        random_size: int | None,
        pokemon_names: str | None,
        search_name: str | None,
    ):
        await make_pokemon_boxes(interaction, random_size, pokemon_names, search_name)
