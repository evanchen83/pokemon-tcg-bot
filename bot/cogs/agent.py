import logging

import discord
import pydash
from discord import app_commands
from discord.ext import commands
from langchain_openai import ChatOpenAI

from bot.agent import global_interaction
from bot.agent.llm_agent import agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


class Agent(commands.Cog):
    @app_commands.command(name="agent", description="Ask the AI Agent for something.")
    async def agent(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        global_interaction.set_interaction(interaction)

        result = agent.invoke({"input": query})
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"**Input:**\n\n{result['input']}\n\n**Output:**\n\n{pydash.truncate(result['output'], length=1000)}"
            )
        )
