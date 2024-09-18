import random
from collections import namedtuple
from functools import lru_cache

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

PkmnCard = namedtuple("CardInfo", ["title", "url"])

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


class PkmnCards(commands.Cog):
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
    def _query_card_info(self, query_str):
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
        card_infos = self._query_card_info(query_str)

        if not card_infos:
            return await ctx.reply("No cards found for query.")

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
            rarity_card_info = self._query_card_info(f"set%3A{set}+rarity%3A{rarity}")

            if len(rarity_card_info) < count:
                return await ctx.reply("Unable to generate pack.")

            card_infos.extend(random.sample(rarity_card_info, count))

        for card_info in card_infos:
            menu.add_page(
                discord.Embed(title=card_info.title).set_image(url=card_info.url)
            )

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()
