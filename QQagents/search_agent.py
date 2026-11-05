
"""
QueryQuest - Search Agent

Purpose:
    Execute web searches and collect useful information.

Responsibilities:
    1. Search the web using OpenAI WebSearchTool.
    2. Identify relevant information.
    3. Return key findings and source URLs.

This agent does NOT write the final research article.
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from agents import Agent, WebSearchTool, ModelSettings


# Load environment variables from the .env file.
load_dotenv(override=True)

# Use the same OpenAI model as our Planner Agent.
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")


# --------------------------------------------------
# Pydantic: Represent one source found by web search.
# --------------------------------------------------
class SearchSource(BaseModel):

    title: str = Field(
        description="Title of the source webpage."
    )

    url: str = Field(
        description="Actual URL of the webpage found."
    )

    finding: str = Field(
        description="Important information found in this source."
    )


# --------------------------------------------------
# Pydantic: Define the complete search result.
# --------------------------------------------------
class SearchResult(BaseModel):

    query: str = Field(
        description="Original query being researched."
    )

    findings: list[str] = Field(
        description="Important findings from the research."
    )

    sources: list[SearchSource] = Field(
        description="Web sources supporting the findings."
    )


# --------------------------------------------------
# Create the Search Agent.
# --------------------------------------------------
def create_search_agent():
    """Create an agent that searches the web."""

    # Instructions establish the Search Agent's role.
    instructions = """
    You are the Search Agent for QueryQuest.

    Your responsibility is to research one search query.

    Follow these steps:

    1. Use the web search tool to find relevant sources.
    2. Prefer official documentation and credible websites.
    3. Extract the most useful information.
    4. Provide 3 to 5 concise findings when possible.
    5. Include source titles and real source URLs.

    IMPORTANT RULES:

    - Always perform a web search before answering.
    - Do not invent information or source URLs.
    - Only include findings supported by retrieved sources.
    - If evidence is insufficient, say so.
    - Do not write a full research article.
    - Do not make final recommendations.
    - Return the structured SearchResult.
    """

    # Create our second agent.
    return Agent(
        name="Search Agent",

        # Define what the agent is responsible for.
        instructions=instructions,

        # OpenAI model from our existing configuration.
        model=MODEL_NAME,

        # Give the agent access to live web search.
        tools=[
            WebSearchTool()
        ],

        # Require a web-search tool call.
        # The SDK resets the tool choice afterward,
        # allowing the model to produce its final output.
        model_settings=ModelSettings(
            tool_choice="web_search"
        ),

        # The SDK validates the final result
        # using our Pydantic SearchResult schema.
        output_type=SearchResult,
    )
