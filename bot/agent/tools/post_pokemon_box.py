import asyncio

from langchain.tools import StructuredTool
from pydantic import BaseModel

from bot.agent import global_interaction
from bot.cogs.pokebox import make_pokemon_boxes


def sync_make_pokemon_boxes(pokemon_names: str):
    loop = asyncio.get_event_loop()
    loop.create_task(
        make_pokemon_boxes(
            global_interaction.get_interaction(), pokemon_names=pokemon_names
        )
    )
    return "Successfully posted pokemon box to channel."


class PokemonBoxSchema(BaseModel):
    pokemon_names: str


create_pokemon_box_tool = StructuredTool(
    name="create_pokemon_box_tool",
    description=(
        "This tool creates a Pokémon storage box image using a list of Pokémon names and posts it to the channel. "
        "Use this tool when you say phrases like 'create a Pokémon box', 'post a Pokémon box', or 'post a box'. "
        "The tool only accepts Pokémon from Generations 1 to 8, with names in lowercase. Pokémon names should use "
        "hyphens for multi-word names, such as 'roaring-moon' or 'iron-leaves'. Pokémon names should be delimited by commas, such as 'pikachu,bulbasaur,charmander'. "
        "If a typo is detected in the Pokémon names, the tool uses its best judgment to correct them. The schema takes a single string, which is parsed into a list internally."
    ),
    args_schema=PokemonBoxSchema,
    func=sync_make_pokemon_boxes,
)
