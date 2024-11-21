import logging
import random
from dataclasses import dataclass
from functools import lru_cache

import discord
import requests
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.database import PlayerCards, Session
from bot.utils import confirm_msg

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set logging level to INFO or DEBUG as needed


@dataclass
class PkmnCard:
    name: str
    image_url: str


def _scrape_set_names():
    page = requests.get("https://pkmncards.com/sets/")
    soup = BeautifulSoup(page.content, "html.parser")
    set_names = []

    for a in soup.find_all("a")[32:-27]:
        if not a.has_attr("class"):
            a["href"] = a["href"][:-1]
            set_name = a["href"][a["href"].rfind("/") + 1 :]
            set_names.append(set_name)

    logger.info(f"Scraped set names: {set_names}")
    return set_names


async def _set_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice]:
    filtered = [
        app_commands.Choice(name=name, value=name)
        for name in SET_NAMES
        if current.lower() in name.lower()
    ]
    return filtered[:25]


async def _source_card_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice]:
    with Session.begin() as session:
        query = session.query(PlayerCards).filter_by(
            discord_id=str(interaction.user.id)
        )
        card_names = [c.card_name for c in query.all()]

    filtered = [
        app_commands.Choice(name=name, value=name)
        for name in card_names
        if current.lower() in name.lower()
    ]
    return filtered[:25]


async def _target_card_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice]:
    with Session.begin() as session:
        query = session.query(PlayerCards).filter_by(
            discord_id=str(interaction.namespace.user.id)
        )
        card_names = [c.card_name for c in query.all()]

    filtered = [
        app_commands.Choice(name=name, value=name)
        for name in card_names
        if current.lower() in name.lower()
    ]
    return filtered[:25]


def _upsert_player_card(session, user_id, card_name, card_image_url):
    stmt = pg_insert(PlayerCards).values(
        discord_id=user_id, card_name=card_name, card_image_url=card_image_url, count=1
    )
    stmt = stmt.on_conflict_do_update(
        constraint="player_cards_pkey", set_={"count": PlayerCards.count + 1}
    )

    session.execute(stmt)
    logger.info(f"Upserted card '{card_name}' for user {user_id}")


@lru_cache()
def _scrape_card_info(query_str):
    page = requests.get(f"https://pkmncards.com/?s={query_str}")
    soup = BeautifulSoup(page.content, "html.parser")
    cards = soup.find_all("div", {"class": "entry-content"})

    if not cards:
        logger.info(f"No cards found for query: {query_str}")
        return []

    card_infos = []
    if len(cards) == 1:
        card_infos.append(
            PkmnCard(
                cards[0].find("h2", {"class": "card-title"}).text,
                cards[0].find("img")["src"],
            )
        )
    else:
        for card in cards:
            card_infos.append(PkmnCard(card.a["title"], card.a.img["src"]))

    logger.info(
        f"Scraped card info for query '{query_str}': {[c.name for c in card_infos]}"
    )
    return card_infos


SET_NAMES = _scrape_set_names()
PACK_COUNT_BY_RARITY = {
    "rarity%3Acommon": 4,
    "rarity%3Auncommon": 3,
    "-rarity%3Acommon,uncommon": 3,
}


class PokemonTCG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="open_pack", description="Open a Pokémon booster pack.")
    @app_commands.autocomplete(set=_set_name_autocomplete)
    async def open_pack(self, interaction: discord.Interaction, set: str):
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        card_infos = []

        logger.info(f"User {interaction.user} is opening a pack from set: {set}")

        for rarity, count in PACK_COUNT_BY_RARITY.items():
            rarity_card_info = _scrape_card_info(f"set%3A{set}+{rarity}")
            if len(rarity_card_info) < count:
                continue

            sampled_cards = random.sample(rarity_card_info, count)
            card_infos.extend(sampled_cards)
            logger.info(
                f"Selected cards for rarity {rarity}: {[c.name for c in sampled_cards]}"
            )

        with Session.begin() as session:
            for card_info in card_infos:
                _upsert_player_card(
                    session,
                    str(interaction.user.id),
                    card_info.name,
                    card_info.image_url,
                )
                menu.add_page(
                    discord.Embed(title=card_info.name).set_image(
                        url=card_info.image_url
                    )
                )

        logger.info(
            f"User {interaction.user} received cards: {[c.name for c in card_infos]}"
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
        filter: str = None,
    ):
        target_user = user or interaction.user
        logger.info(f"User {interaction.user} requested cards for {target_user}")

        with Session.begin() as session:
            query = session.query(PlayerCards).filter_by(discord_id=str(target_user.id))

            if filter:
                query = query.filter(PlayerCards.card_name.ilike(f"%{filter}%"))

            player_cards = query.all()

            if not player_cards:
                logger.info(
                    f"User {target_user} has no cards matching the filter '{filter}'"
                )
                return await interaction.response.send_message("Player has no cards")

            menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
            for card in player_cards:
                menu.add_page(
                    discord.Embed(title=card.card_name)
                    .set_image(url=card.card_image_url)
                    .add_field(name="count", value=card.count)
                )

            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())

            logger.info(
                f"Displayed cards for user {target_user}: {[c.card_name for c in player_cards]}"
            )
            await menu.start()

    @app_commands.command(
        name="gift_card", description="Gifting a card to someone else."
    )
    @app_commands.autocomplete(card=_source_card_autocomplete)
    async def gift_card(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        card: str,
    ):
        logger.info(f"User {interaction.user} is gifting card {card} to {user}")
        with Session.begin() as session:
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(interaction.user.id), card_name=card)
                .with_for_update()
                .one_or_none()
            )

            if not source_card:
                logger.warning(
                    f"{interaction.user} tried to gift card {card}, but they do not own it."
                )
                return await interaction.response.send_message(
                    f"{interaction.user.name.capitalize()} has no card {card}"
                )

            if source_card.count > 1:
                source_card.count -= 1
            else:
                session.delete(source_card)

            _upsert_player_card(
                session,
                str(user.id),
                source_card.card_name,
                card_image_url=source_card.card_image_url,
            )

            logger.info(f"Gifted card {card} from {interaction.user} to {user}")
            await interaction.response.send_message(
                f"You have successfully gifted the card {card} to {user.name.capitalize()}"
            )

    @app_commands.command(
        name="trade_card", description="Trading a card with someone else."
    )
    @app_commands.autocomplete(my_card=_source_card_autocomplete)
    @app_commands.autocomplete(for_card=_target_card_autocomplete)
    async def trade_card(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        my_card: str,
        for_card: str,
    ):
        logger.info(
            f"User {interaction.user} is proposing a trade with {user}: {my_card} for {for_card}"
        )

        with Session.begin() as session:
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(interaction.user.id), card_name=my_card)
                .one_or_none()
            )
            target_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(user.id), card_name=for_card)
                .one_or_none()
            )

        if not source_card or not target_card:
            logger.warning(
                "Trade failed: one or both users do not own the specified cards."
            )
            return await interaction.response.send_message(
                "Both players must own the specified cards to complete the trade"
            )

        request_embed = (
            discord.Embed(title=f"{user.name.capitalize()}, you have a trade proposal:")
            .add_field(name=f"{interaction.user.name}", value=my_card, inline=True)
            .add_field(name=f"{user.name}", value=for_card, inline=True)
            .set_footer(text="React with 👍 to accept or 👎 to decline.")
        )
        await interaction.response.defer()
        if not await confirm_msg.request_confirm_message(
            interaction, self.bot, user, request_embed
        ):
            logger.info("Trade declined by the other user.")
            return

        with Session.begin() as session:
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(interaction.user.id), card_name=my_card)
                .with_for_update()
                .one_or_none()
            )
            target_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(user.id), card_name=for_card)
                .with_for_update()
                .one_or_none()
            )

            if not source_card or not target_card:
                logger.warning(
                    "Trade failed during recheck: one or both users do not own the specified cards."
                )
                return await interaction.followup.send(
                    "Both players must own the specified cards to complete the trade"
                )

            if source_card.count > 1:
                source_card.count -= 1
            else:
                session.delete(source_card)

            if target_card.count > 1:
                target_card.count -= 1
            else:
                session.delete(target_card)

            _upsert_player_card(
                session,
                str(interaction.user.id),
                target_card.card_name,
                target_card.card_image_url,
            )
            _upsert_player_card(
                session, str(user.id), source_card.card_name, source_card.card_image_url
            )

            logger.info(
                f"Trade completed: {interaction.user} traded {my_card} for {for_card} with {user}"
            )
            await interaction.followup.send("Trade completed successfully.")
