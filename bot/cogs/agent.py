import asyncio
import json
import logging

import discord
from discord import app_commands
from discord.ext import commands
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from bot.cogs import pokebox

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

CURRENT_INTERACTION = None


def sync_box_wrapper(
    pokemon_names: str | None = None,
) -> str:
    global CURRENT_INTERACTION
    if not CURRENT_INTERACTION:
        return "No active interaction context found."

    logger.debug("Running box command with pokemon_names=%s")

    loop = asyncio.get_event_loop()
    loop.create_task(
        pokebox.make_pokemon_boxes(
            interaction=CURRENT_INTERACTION,
            random_size=None,
            pokemon_names=pokemon_names,
            search_name=None,
        )
    )

    return "Box command executed successfully."


class BoxCommandSchema(BaseModel):
    pokemon_names: str | None = Field(
        None, description="A comma-separated list of Pokémon names."
    )


box_tool = StructuredTool(
    name="BoxCommand",
    func=sync_box_wrapper,
    description=(
        "Generates a Pokémon PC storage box with specific Pokémon. "
        "Provide a comma-separated list of Pokémon names for the `pokemon_names` parameter.\n\n"
        "**Usage:**\n"
        "- Input: A comma-separated list of valid Pokémon names, e.g., `Charmander, Pikachu, Bulbasaur`.\n"
        "- Use this when the user specifies particular Pokémon names or categories.\n\n"
        "**Examples:**\n"
        "1. Query: 'Create a box with Charmander, Pikachu, and Bulbasaur'\n"
        "   Input: `pokemon_names='Charmander, Pikachu, Bulbasaur'`\n\n"
        "2. Query: 'Generate a box with Fire-type Pokémon'\n"
        "   Input: `pokemon_names='Charmander, Vulpix, Growlithe, Ponyta'`\n\n"
        "3. Query: 'Create a box with legendary Pokémon'\n"
        "   Input: `pokemon_names='Mewtwo, Lugia, Ho-Oh, Rayquaza'`."
    ),
    args_schema=BoxCommandSchema,
)


def conversational_fallback(input_text: str) -> str:
    return llm(input_text)


conversational_tool = Tool(
    name="ConversationalFallback",
    func=conversational_fallback,
    description="Fallback to handle queries that don't match specific tools.",
)

agent = initialize_agent(
    tools=[box_tool, conversational_tool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)


class Agent(commands.Cog):
    @app_commands.command(name="agent", description="Ask the AI Agent for something.")
    async def agent(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        global CURRENT_INTERACTION
        CURRENT_INTERACTION = interaction

        result = agent.invoke({"input": query})
        embed = discord.Embed(
            title="AI Agent Response",
            description=f"```json\n{json.dumps(result, indent=4, ensure_ascii=False)}\n```",
            color=discord.Color.blue(),
        ).set_footer(text="Powered by LangChain • AI Agent")

        await interaction.followup.send(embed=embed)
