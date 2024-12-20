import logging
from typing import List, Literal

from langchain.tools import StructuredTool, Tool
from pydantic import BaseModel, Field

from bot.api.poketcg import PokemonTCGAPI
from bot.config import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pokemon_tcg_api = PokemonTCGAPI(config.pokemon_tcg_api_key)


# Define the schema for the query input
class QuerySchema(BaseModel):
    select: List[
        Literal[
            "id",
            "name",
            "supertype",
            "subtypes",
            "hp",
            "types",
            "evolvesFrom",
            "abilities",
            "attacks",
            "weaknesses",
            "retreatCost",
            "convertedRetreatCost",
            "set",
            "number",
            "artist",
            "rarity",
            "flavorText",
            "nationalPokedexNumbers",
            "legalities",
            "images",
            "tcgplayer",
            "cardmarket",
        ]
    ]
    names: list[str] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)
    set_names: list[str] = Field(default_factory=list)
    series_names: list[str] = Field(default_factory=list)
    artists: list[str] = Field(default_factory=list)


def _format_query_values(field: str, values: list[str]) -> str:
    if not values:
        return ""

    v = []
    for value in values:
        if len(value.split(" ")) > 1:
            v.append(f'{field}:"{value}"')
        else:
            v.append(f"{field}:{value}")

    if len(v) == 1:
        return v[0]

    return "(" + " AND ".join(v) + ")"


def get_cards(
    select: str,
    names: list[str] = [],
    ids: list[str] = [],
    set_names: list[str] = [],
    series_names: list[str] = [],
    artists: list[str] = [],
):
    query = " ".join(
        [
            _format_query_values("name", names),
            _format_query_values("id", ids),
            _format_query_values("set.name", set_names),
            _format_query_values("set.series", series_names),
            _format_query_values("artist", artists),
        ]
    )

    logger.debug(
        "Running get_cards endpoint with query:%s and select:%s", query, select
    )
    return pokemon_tcg_api.get_cards(query, ",".join(select))


search_cards_tool = StructuredTool(
    name="search_cards_tool",
    description=(
        "This tool retrieves Pokémon card information directly from the API. Use it to query card details efficiently. "
        "The query accepts the following fields: names, ids, set_names, artists, and series_names, all as lists of strings. "
        "The 'select' field must be a list of strings, each one of the following: 'id', 'name', 'supertype', 'subtypes', 'hp', 'types', "
        "'evolvesFrom', 'abilities', 'attacks', 'weaknesses', 'retreatCost', 'convertedRetreatCost', 'set', 'number', 'artist', 'rarity', "
        "'flavorText', 'nationalPokedexNumbers', 'legalities', 'images', 'tcgplayer', 'cardmarket'. For example, provide ['name', 'images'] "
        "to fetch specific fields. Including 'set' in 'select' retrieves set-specific details. This tool is optimized for bandwidth, fetching "
        "data for up to 30 cards per query. Use it to quickly retrieve targeted information instead of downloading unnecessary data."
    ),
    args_schema=QuerySchema,
    func=get_cards,
)


search_sets_tool = Tool(
    name="search_sets_tool",
    description=(
        "This tool provides generic information about Pokémon card sets. Use this tool to find details such as the total number of sets, the number of sets in each series, the latest set, and which set has the most or fewest cards. It contains general set details and cannot verify if a specific Pokémon card belongs to a particular set. If the details needed by the agent are card-specific, use the other tool instead. This tool uses its best judgment to interpret unclear or misspelled set names and provide accurate information. This tool does not require any input parameters."
    ),
    func=lambda *args, **kwargs: pokemon_tcg_api.get_sets(),
)
