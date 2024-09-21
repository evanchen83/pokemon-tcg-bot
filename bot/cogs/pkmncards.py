import random
from dataclasses import dataclass
from functools import lru_cache

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

from bot.database import PlayerCard, Session
from bot.utils import confirm_msg


@dataclass
class PkmnCard:
    title: str
    url: str


@dataclass
class PlayerPkmnCard(PkmnCard):
    copies: int


PACK_RARITY_COMMON = "common"
PACK_RARITY_UNCOMMON = "uncommon"
PACK_RARITY_RARE = ",".join(
    [
        "rare",
        "rare-holo",
        "promo",
        "ultra-rare",
        "rainbow-rare",
        "rare-secret",
        "shiny-rare",
        "holo-rare-v",
        "rare-holo-ex-↑",
        "rare-holo-gx",
        "rare-holo-ex-↓",
        "illustration-rare",
        "double-rare",
        "holo-rare-vmax",
        "trainer-gallery-holo-rare",
        "special-illustration-rare",
        "rare-holo-lv-x",
        "trainer-gallery-holo-rare-v",
        "rare-shiny-gx",
        "hyper-rare",
        "holo-rare-vstar",
        "trainer-gallery-ultra-rare",
        "rare-prism-star",
        "rare-break",
        "rare-prime",
        "rare-holo-star",
        "legend",
        "shiny-rare-v-or-vmax",
        "rare-shining",
        "radiant-rare",
        "rare-ace",
        "trainer-gallery-secret-rare",
        "shiny-ultra-rare",
        "trainer-gallery-holo-rare-v-or-vmax",
        "amazing-rare",
    ]
)

PACK_RARITY_COUNTS = {
    PACK_RARITY_COMMON: 4,
    PACK_RARITY_UNCOMMON: 3,
    PACK_RARITY_RARE: 3,
}


def _add_player_card_to_db(session, discord_id, card_name, card_image_url):
    player_card = (
        session.query(PlayerCard)
        .filter_by(discord_id=discord_id, card_name=card_name)
        .with_for_update()
        .first()
    )

    if player_card:
        player_card.copies += 1
    else:
        new_card = PlayerCard(
            discord_id=discord_id,
            card_name=card_name,
            card_image_url=card_image_url,
            copies=1,
        )
        session.add(new_card)


def _search_player_cards_from_db(session, discord_id, text_filter):
    query = session.query(PlayerCard).filter_by(discord_id=discord_id)

    if text_filter:
        query = query.filter(PlayerCard.card_name.ilike(text_filter))

    player_cards = query.with_for_update().all()
    return [
        PlayerPkmnCard(
            title=card.card_name, url=card.card_image_url, copies=card.copies
        )
        for card in player_cards
    ]


def _get_player_card_from_db(session, discord_id, card_name):
    return next(
        iter(_search_player_cards_from_db(session, discord_id, card_name)), None
    )


def _remove_player_card_from_db(session, discord_id, card_name):
    player_card = (
        session.query(PlayerCard)
        .filter_by(discord_id=discord_id, card_name=card_name)
        .with_for_update()
        .first()
    )
    removed_card = None

    if player_card:
        removed_card = PkmnCard(
            title=player_card.card_name, url=player_card.card_image_url
        )
        if player_card.copies > 1:
            player_card.copies -= 1
        else:
            session.delete(player_card)

    return removed_card


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
                discord.Embed(title=card_info.title).set_image(url=card_info.url)
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def open_pack(self, ctx, set):
        """Open a booster pack and get new Pokémon game cards."""
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
        card_infos = []

        for rarity, count in PACK_RARITY_COUNTS.items():
            rarity_card_info = self._scrape_card_info(f"set%3A{set}+rarity%3A{rarity}")

            if len(rarity_card_info) < count:
                return await ctx.reply("Unable to generate pack")

            card_infos.extend(random.sample(rarity_card_info, count))

        with Session() as session, session.begin():
            for card_info in card_infos:
                _add_player_card_to_db(
                    session, str(ctx.author.id), card_info.title, card_info.url
                )
                menu.add_page(
                    discord.Embed(title=card_info.title).set_image(url=card_info.url)
                )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def show_player_cards(self, ctx, player: discord.Member, text_filter=None):
        """Show cards held by the player."""
        text_filter = f"%{text_filter}%" if text_filter else None

        with Session() as session, session.begin():
            player_cards = _search_player_cards_from_db(
                session, str(player.id), text_filter
            )

        if not player_cards:
            return await ctx.reply("Player has no cards")

        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
        for card in player_cards:
            menu.add_page(
                discord.Embed(title=card.title)
                .set_image(url=card.url)
                .add_field(name="copies", value=card.copies)
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()

    @commands.command()
    async def gift_player_card(self, ctx, player: discord.Member, card_name):
        """Gift a player one of your cards."""
        with Session() as session, session.begin():
            card = _remove_player_card_from_db(session, str(ctx.author.id), card_name)

            if not card:
                return await ctx.reply(
                    f"{ctx.author.name.capitalize()} has no card {card_name}"
                )

            _add_player_card_to_db(session, str(player.id), card.title, card.url)
            await ctx.reply(
                f"You have successfully gifted the card {card_name} to {player.name.capitalize()}"
            )

    @commands.command()
    async def trade_player_card(
        self, ctx, player: discord.Member, source_card_name, target_card_name
    ):
        """Exchange cards between players."""
        with Session() as session, session.begin():
            source_card = _get_player_card_from_db(
                session, str(ctx.author.id), source_card_name
            )
            target_card = _get_player_card_from_db(
                session, str(player.id), target_card_name
            )

        if not source_card or not target_card:
            return await ctx.reply(
                "Both players must own the specified cards to complete the trade"
            )

        request_embed = (
            discord.Embed(
                title=f"{player.name.capitalize()}, you have a trade proposal:"
            )
            .add_field(name=f"{ctx.author.name}", value=source_card_name, inline=True)
            .add_field(name=f"{player.name}", value=target_card_name, inline=True)
            .set_footer(text="React with 👍 to accept or 👎 to decline.")
        )
        if not await confirm_msg.request_confirm_message(
            ctx, self.bot, player, request_embed
        ):
            return

        with Session() as session, session.begin():
            source_card = _get_player_card_from_db(
                session, str(ctx.author.id), source_card_name
            )
            target_card = _get_player_card_from_db(
                session, str(player.id), target_card_name
            )

            if not source_card or not target_card:
                return await ctx.reply(
                    "Both players must own the specified cards to complete the trade"
                )

            _remove_player_card_from_db(session, str(ctx.author.id), source_card.title)
            _add_player_card_to_db(
                session, str(player.id), source_card.title, source_card.url
            )

            _remove_player_card_from_db(session, str(player.id), target_card.title)
            _add_player_card_to_db(
                session, str(ctx.author.id), target_card.title, target_card.url
            )

            await ctx.reply("Trade completed successfully.")
