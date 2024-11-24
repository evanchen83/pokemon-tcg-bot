import logging
import random

import discord
from discord import app_commands
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.api.poketcg import PokemonTCGAPI
from bot.config import config
from bot.database import Session, player_cards

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pokeapi = PokemonTCGAPI(config.pokemon_tcg_api_key)


async def _set_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice]:
    filtered = [
        app_commands.Choice(name=s["name"], value=s["id"])
        for s in pokeapi.get_sets()
        if current.lower() in s["name"].lower()
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


class PokemonTCGBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="open_pack", description="Open a Pokémon booster pack.")
    @app_commands.autocomplete(set_id=_set_name_autocomplete)
    async def open_pack(self, interaction: discord.Interaction, set_id: str):
        await interaction.response.defer()

        # Fetch set cards, now including set details in the payload
        set_cards = pokeapi.get_cards_by_set_id(set_id)

        if not set_cards:
            await interaction.followup.send("Invalid set ID or no cards found.")
            return

        # Categorize cards by rarity
        common_cards = [c for c in set_cards if c.get("rarity") == "Common"]
        uncommon_cards = [c for c in set_cards if c.get("rarity") == "Uncommon"]
        rare_cards = [
            c for c in set_cards if c.get("rarity") not in {"Common", "Uncommon"}
        ]

        # Randomly select cards for the pack
        pack_cards = (
            (random.choices(common_cards, k=4) if common_cards else [])
            + (random.choices(uncommon_cards, k=3) if uncommon_cards else [])
            + (random.choices(rare_cards, k=3) if rare_cards else [])
        )
        _upsert_player_cards(str(interaction.user.id), [p["id"] for p in pack_cards])

        # Create a menu to display the pack's cards
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        for pack_card in pack_cards:
            menu.add_page(
                discord.Embed(
                    title=f"{pack_card['name']}",
                    description=f"**Set**: {pack_card['set']['name']}\n"
                    f"**Rarity**: {pack_card.get('rarity', 'N/A')}\n"
                    f"**Type**: {', '.join(pack_card.get('types', [])) if pack_card.get('types') else 'N/A'}",
                    color=discord.Color.blue(),
                )
                .set_image(url=pack_card["images"]["small"])
                .set_footer(
                    text=f"Collector's Number: {pack_card['number']} | Released: {pack_card['set'].get('releaseDate', 'Unknown')}"
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
        filter_name: str = None,
    ):
        await interaction.response.defer()

        # Default to the interaction user if no user is specified
        user = user or interaction.user
        user_card_ids = _get_player_cards(str(user.id))

        if not user_card_ids:
            await interaction.followup.send(f"{user.display_name} has no cards.")
            return

        # Fetch cards in a single query
        card_ids = [card_id[0] for card_id in user_card_ids]
        user_cards = pokeapi.get_cards_by_ids(card_ids, filter_name)

        if not user_cards:
            await interaction.followup.send("No cards found with the given filters.")
            return

        # Map card counts by ID
        count_by_id = {card_id[0]: card_id[1] for card_id in user_card_ids}

        # Create a menu to display user cards
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        for user_card in user_cards:
            menu.add_page(
                discord.Embed(
                    title=f"{user_card['name']}",
                    description=f"**Count**: {count_by_id[user_card['id']]}\n"
                    f"**Set**: {user_card['set']['name']}\n"
                    f"**Rarity**: {user_card.get('rarity', 'N/A')}\n"
                    f"**Type**: {', '.join(user_card.get('types', [])) if user_card.get('types') else 'N/A'}",
                    color=discord.Color.blue(),
                )
                .set_image(url=user_card["images"]["small"])
                .set_footer(
                    text=f"Collector's Number: {user_card['number']} | Released: {user_card['set'].get('releaseDate', 'Unknown')}"
                )
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        await menu.start()
