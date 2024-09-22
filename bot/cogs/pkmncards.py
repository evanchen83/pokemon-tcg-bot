import random
from dataclasses import dataclass
from functools import lru_cache

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.database import PlayerCards, Session
from bot.utils import confirm_msg


@dataclass
class PkmnCard:
    name: str
    image_url: str


PACK_COUNT_BY_RARITY = {
    "rarity%3Acommon": 4,
    "rarity%3Auncommon": 3,
    "-rarity%3Acommon,uncommon": 3,
}


def _add_or_increment_player_card(session, user_id, card_name, card_image_url):
    stmt = pg_insert(PlayerCards).values(
        discord_id=user_id, card_name=card_name, card_image_url=card_image_url, count=1
    )
    stmt = stmt.on_conflict_do_update(
        constraint="player_cards_pkey", set_={"count": PlayerCards.count + 1}
    )

    session.execute(stmt)


class PkmnCards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def list_sets(self, ctx):
        """Display all available Pokémon card sets."""
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbedDynamic, rows_requested=10)

        page = requests.get("https://pkmncards.com/sets/")
        soup = BeautifulSoup(page.content, "html.parser")

        for a in soup.find_all("a")[32:-27]:
            if a.has_attr("class"):
                menu.add_row(f"**{a.text}**")
            else:
                a["href"] = a["href"][:-1]
                set_name = a["href"][a["href"].rfind("/") + 1 :]
                menu.add_row(set_name)

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @lru_cache(maxsize=500)
    def _scrape_card_info(self, query_str):
        """Scrape pkmncards website for card information."""
        page = requests.get(f"https://pkmncards.com/?s={query_str}")

        soup = BeautifulSoup(page.content, "html.parser")
        cards = soup.find_all("div", {"class": "entry-content"})

        if not cards:
            return []

        card_infos = []
        if len(cards) == 1:  # single card gallery
            card_infos.append(
                PkmnCard(
                    cards[0].find("h2", {"class": "card-title"}).text,
                    cards[0].find("img")["src"],
                )
            )
        else:
            for card in cards:
                card_infos.append(PkmnCard(card.a["title"], card.a.img["src"]))

        return card_infos

    @commands.command()
    async def search_cards(self, ctx, *args):
        """Search for specific Pokémon cards by name or other criteria."""
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        query_str = "+".join([a.replace(":", "%3A") for a in args])
        card_infos = self._scrape_card_info(query_str)

        if not card_infos:
            return await ctx.reply("No cards found for query")

        for card_info in card_infos:
            menu.add_page(
                discord.Embed(title=card_info.name).set_image(url=card_info.image_url)
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def open_booster(self, ctx, set):
        """Open a booster pack and get new Pokémon game cards."""
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
        card_infos = []

        for rarity, count in PACK_COUNT_BY_RARITY.items():
            rarity_card_info = self._scrape_card_info(f"set%3A{set}+{rarity}")

            if len(rarity_card_info) < count:
                return await ctx.reply("Unable to generate pack")

            card_infos.extend(random.sample(rarity_card_info, count))

        with Session() as session, session.begin():
            for card_info in card_infos:
                _add_or_increment_player_card(
                    session,
                    str(ctx.author.id),
                    card_info.name,
                    card_info.image_url,
                )
                menu.add_page(
                    discord.Embed(title=card_info.name).set_image(
                        url=card_info.image_url
                    )
                )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def show_cards(self, ctx, user: discord.Member, text_filter=None):
        """Show cards held by the player."""
        text_filter = f"%{text_filter}%" if text_filter else None

        with Session() as session, session.begin():
            query = session.query(PlayerCards).filter_by(discord_id=str(user.id))

            if text_filter:
                query = query.filter(PlayerCards.card_name.ilike(text_filter))

            player_cards = query.all()

            if not player_cards:
                return await ctx.reply("Player has no cards")

            menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
            for card in player_cards:
                menu.add_page(
                    discord.Embed(title=card.card_name)
                    .set_image(url=card.card_image_url)
                    .add_field(name="count", value=card.count)
                )

            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def gift_card(self, ctx, user: discord.Member, card_name):
        """Gift a player one of your cards."""
        with Session() as session, session.begin():
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(ctx.author.id), card_name=card_name)
                .with_for_update()
                .one_or_none()
            )

            if not source_card:
                return await ctx.reply(
                    f"{ctx.author.name.capitalize()} has no card {card_name}"
                )

            if source_card.count > 1:
                source_card.count -= 1
            else:
                session.delete(source_card)

            _add_or_increment_player_card(
                session,
                str(user.id),
                source_card.card_name,
                card_image_url=source_card.card_image_url,
            )

            await ctx.reply(
                f"You have successfully gifted the card {card_name} to {user.name.capitalize()}"
            )

    @commands.command()
    async def trade_card(
        self, ctx, user: discord.Member, source_card_name, target_card_name
    ):
        """Exchange cards between players."""
        with Session() as session, session.begin():
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(ctx.author.id), card_name=source_card_name)
                .one_or_none()
            )
            target_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(user.id), card_name=target_card_name)
                .one_or_none()
            )

        if not source_card or not target_card:
            return await ctx.reply(
                "Both players must own the specified cards to complete the trade"
            )

        request_embed = (
            discord.Embed(title=f"{user.name.capitalize()}, you have a trade proposal:")
            .add_field(name=f"{ctx.author.name}", value=source_card_name, inline=True)
            .add_field(name=f"{user.name}", value=target_card_name, inline=True)
            .set_footer(text="React with 👍 to accept or 👎 to decline.")
        )
        if not await confirm_msg.request_confirm_message(
            ctx, self.bot, user, request_embed
        ):
            return

        with Session() as session, session.begin():
            source_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(ctx.author.id), card_name=source_card_name)
                .with_for_update()
                .one_or_none()
            )
            target_card = (
                session.query(PlayerCards)
                .filter_by(discord_id=str(user.id), card_name=target_card_name)
                .with_for_update()
                .one_or_none()
            )

            if not source_card or not target_card:
                return await ctx.reply(
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

            _add_or_increment_player_card(
                session,
                str(ctx.author.id),
                target_card.card_name,
                target_card.card_image_url,
            )
            _add_or_increment_player_card(
                session, str(user.id), source_card.card_name, source_card.card_image_url
            )

            await ctx.reply("Trade completed successfully.")
