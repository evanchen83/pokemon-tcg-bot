from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI

from bot.agent.tools import (
    generic_conversation,
    pokemon_tcg,
    post_images,
    post_pokemon_box,
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

agent = initialize_agent(
    tools=[
        generic_conversation.conversational_tool,
        pokemon_tcg.search_cards_tool,
        pokemon_tcg.search_sets_tool,
        post_images.post_images_tool,
        post_pokemon_box.create_pokemon_box_tool,
    ],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)
