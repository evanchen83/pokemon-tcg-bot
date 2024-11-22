import logging
import random

import discord
import pokemontcgsdk
from cachetools import TTLCache, cached
from discord import app_commands
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.config import config
from bot.database import Session, player_cards

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@cached(cache=TTLCache(maxsize=100, ttl=600))
def _query_cards(query: str) -> list[pokemontcgsdk.Card]:
    return pokemontcgsdk.Card.where(q=query)


@cached(cache=TTLCache(maxsize=1, ttl=600))
def _query_set_names() -> list[pokemontcgsdk.Set]:
    return pokemontcgsdk.Set.all()


async def _set_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice]:
    filtered = [
        app_commands.Choice(name=s.name, value=s.id)
        for s in _query_set_names()
        if current.lower() in s.name.lower()
    ]
    return filtered[:25]


def _upsert_player_cards(user_id: str, card_ids: list[str]):
    with Session.begin() as session:
        for card_id in card_ids:
            stmt = (
                pg_insert(player_cards)
                .values(discord_id=user_id, card_id=card_id, count=1)
                .on_conflict_do_update(
                    index_elements=["discord_id", "card_id"],
                    set_={"count": player_cards.c.count + 1},
                )
            )
            session.execute(stmt)


def _get_player_cards(user_id: str) -> tuple[str, int]:
    with Session.begin() as session:
        stmt = select(player_cards.c.card_id, player_cards.c.count).where(
            player_cards.c.discord_id == user_id
        )
        result = session.execute(stmt)
        return result.fetchall()


class PokemonTCG(commands.Cog):
    def __init__(self, bot):
        pokemontcgsdk.RestClient.configure(config.pokemon_tcg_api_key)
        self.bot = bot

    @app_commands.command(name="open_pack", description="Open a Pokémon booster pack.")
    @app_commands.autocomplete(set_id=_set_name_autocomplete)
    async def open_pack(self, interaction: discord.Interaction, set_id: str):
        await interaction.response.defer()
        set_cards = _query_cards(f"set.id:{set_id}")

        common_cards = [c for c in set_cards if c.rarity == "Common"]
        uncommon_cards = [c for c in set_cards if c.rarity == "Uncommon"]
        rare_cards = [
            c for c in set_cards if c.rarity != "Common" and c.rarity != "Uncommon"
        ]

        pack_cards = (
            random.choices(common_cards, k=4)
            + random.choices(uncommon_cards, k=3)
            + random.choices(rare_cards, k=3)
        )
        _upsert_player_cards(str(interaction.user.id), [p.id for p in pack_cards])

        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        for pack_card in pack_cards:
            menu.add_page(
                discord.Embed(
                    title=f"{pack_card.name}",
                    description=f"**Set**: {pack_card.set.name}\n"
                    f"**Rarity**: {pack_card.rarity}\n"
                    f"**Type**: {', '.join(pack_card.types) if pack_card.types else 'N/A'}",
                    color=discord.Color.blue(),
                )
                .set_image(url=pack_card.images.small)
                .set_footer(
                    text=f"Collector's Number: {pack_card.number} | Released: {pack_card.set.releaseDate}"
                )
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @app_commands.command(
        name="my_cards", description="Show cards for yourself or another user."
    )
    async def my_cards(
        self,
        interaction: discord.Interaction,
        user: discord.User = None,
        search_name: str = None,
    ):
        user = user or interaction.user
        user_card_ids = _get_player_cards(str(user.id))

        count_by_id = {c[0]: c[1] for c in user_card_ids}

        search_query = "(" + " OR ".join([f"id:{id[0]}" for id in user_card_ids]) + ")"
        if search_name:
            search_query += f" name:*{search_name}*"

        user_cards = _query_cards(search_query)

        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        for user_card in user_cards:
            menu.add_page(
                discord.Embed(
                    title=f"{user_card.name}",
                    description=f"**Count**: {count_by_id[user_card.id]}\n"
                    f"**Set**: {user_card.set.name}\n"
                    f"**Rarity**: {user_card.rarity}\n"
                    f"**Type**: {', '.join(user_card.types) if user_card.types else 'N/A'}",
                    color=discord.Color.blue(),
                )
                .set_image(url=user_card.images.small)
                .set_footer(
                    text=f"Collector's Number: {user_card.number} | Released: {user_card.set.releaseDate}"
                )
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()
