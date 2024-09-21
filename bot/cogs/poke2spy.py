import time
from io import BytesIO
from typing import Dict

import discord
import imagehash
import pandas as pd
import requests
from discord.ext import commands
from PIL import Image
from rembg import new_session, remove


def _get_pokemon_hashes() -> Dict[imagehash.ImageMultiHash, str]:
    df = pd.read_csv("bot/data/pokemon_hashes.csv")
    pokemon_names = df["pokemon_names"].to_list()
    img_front_hashes = (
        df["img_front_large_crop_hashes"].apply(imagehash.hex_to_multihash).to_list()
    )
    img_back_hashes = (
        df["img_back_large_crop_hashes"].apply(imagehash.hex_to_multihash).to_list()
    )

    pokemon_hashes = {}
    pokemon_hashes.update({k: v for k, v in zip(img_front_hashes, pokemon_names)})
    pokemon_hashes.update({k: v for k, v in zip(img_back_hashes, pokemon_names)})
    return pokemon_hashes


def _is_encounter_msg(msg: discord.Message) -> bool:
    return (
        "pokémon has appeared!" in msg.embeds[0].title.lower()
        if msg.embeds and msg.embeds[0].title
        else False
    )


def _predict_encounter_pokemon(image_bytes: BytesIO) -> str:
    encounter_img = Image.open(image_bytes)
    encounter_img = remove(encounter_img, session=session)
    encounter_img = encounter_img.crop(encounter_img.getbbox()).resize((500, 500))

    encounter_hash = imagehash.crop_resistant_hash(
        encounter_img, min_segment_size=500, segmentation_image_size=1000
    )
    closest_match_hash = min(POKEMON_HASHES.keys(), key=lambda x: encounter_hash - x)

    return POKEMON_HASHES[closest_match_hash]


POKEMON_HASHES = _get_pokemon_hashes()
session = new_session()


class Poke2Spy(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, msg):
        if _is_encounter_msg(msg):
            st = time.perf_counter()
            prediction = _predict_encounter_pokemon(
                BytesIO(requests.get(msg.embeds[0].image.url).content)
            )
            et = time.perf_counter()
            await msg.reply(f"{prediction.capitalize()} - {et-st:.4} seconds.")

    @commands.command()
    async def spy(self, ctx):
        """Predict the Pokémon name from a PokéTwo encounter."""
        if not ctx.message.reference or not _is_encounter_msg(
            msg := await ctx.channel.fetch_message(ctx.message.reference.message_id)
        ):
            return await ctx.reply("Msg is not a PokeTwo encounter!")
        st = time.perf_counter()
        prediction = _predict_encounter_pokemon(
            BytesIO(requests.get(msg.embeds[0].image.url).content)
        )
        et = time.perf_counter()
        await ctx.reply(f"{prediction.capitalize()} - {et-st:.4} seconds.")
