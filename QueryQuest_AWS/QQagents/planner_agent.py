
"""
QueryQuest - Planner Agent

Purpose:
    Understand research requirements and prepare a search plan.

Important:
    This agent ONLY plans research.
    It does not search the web or write research articles.
"""

from pydantic import BaseModel, Field
from config import bedrock_model, positive_int
from services.bedrock_agent import BedrockAgent


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(min_length=1, max_length=200, description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")



def create_planner_agent():
    """Create the research planning agent."""

    # These instructions establish the Planner's boundaries.
    # The agent must not perform work assigned to other agents.
    search_count = positive_int("HOW_MANY_SEARCHES", 5)
    planner_instructions = f"""
    You are the Planner Agent for QueryQuest.

    Your ONLY responsibility is to create a research plan.

    Given a user question:
    1. Understand the research objective.
    2. Generate exactly {search_count} web search queries.
    3. Make each query specific, relevant, and no more than 200 characters.
    4. Provide a short purpose for each search.

    IMPORTANT:
    - Do not answer the research question.
    - Do not generate an article.
    - Do not compare or recommend products.
    - Do not invent research findings.
    - Return only the structured search plan.
    """



    # Create the Planner using AWS Bedrock Converse.
    return BedrockAgent(
        name="Planner Agent",
        instructions=planner_instructions,
        model=bedrock_model("planner"),
        output_type=WebSearchPlan
    )
