
"""
QueryQuest - Planner Agent

Purpose:
    Understand research requirements and prepare a search plan.

Important:
    This agent ONLY plans research.
    It does not search the web or write research articles.
"""

from agents import Agent

from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 5))


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    


def create_planner_agent():
    """Create the research planning agent."""

    # These instructions establish the Planner's boundaries.
    # The agent must not perform work assigned to other agents.
    planner_instructions = f"""
    You are the Planner Agent for QueryQuest.

    Your ONLY responsibility is to create a research plan.

    Given a user question:
    1. Understand the research objective.
    2. Generate exactly {HOW_MANY_SEARCHES} web search queries.
    3. Make each query specific and relevant.
    4. Provide a short purpose for each search.

    IMPORTANT:
    - Do not answer the research question.
    - Do not generate an article.
    - Do not compare or recommend products.
    - Do not invent research findings.
    - Return only the structured search plan.
    """


    
    # Create the Planner using the OpenAI Agents SDK.
    return Agent(
        name="Planner Agent",
        instructions=planner_instructions,
        model=MODEL_NAME,
        output_type=WebSearchPlan
    )
