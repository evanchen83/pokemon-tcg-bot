from langchain.agents import Tool
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


def conversational_fallback(input_text: str) -> str:
    return llm(input_text).content


conversational_tool = Tool(
    name="ConversationalFallback",
    func=conversational_fallback,
    description=(
        "This is a generic conversational tool. Use it to handle general queries that don't match "
        "specific tools. For example, if a user asks casual questions like 'How's your day?' or "
        "'Who's the president?', respond using your LLM's domain knowledge to provide an appropriate answer."
    ),
)
