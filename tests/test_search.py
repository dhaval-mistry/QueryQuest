
"""
QueryQuest - Search Agent Test

Purpose:
    Test whether our Search Agent can:
    1. Search the live web.
    2. Extract key findings.
    3. Return Pydantic structured output.

Run:
    uv run python -m tests.test_search
"""

from agents import Runner
from dotenv import load_dotenv

from QQagents.search_agent import create_search_agent


def main():
    """Run a simple Search Agent test."""

    # Create our Search Agent.
    search_agent = create_search_agent()

    # This is one example query from our Planner.
    # Later, these queries will come directly
    # from the Planner's WebSearchPlan object.
    query = (
        "OpenAI Agents SDK official documentation "
        "production features architecture limitations"
    )

    print("Calling Search Agent...", flush=True)

    # Execute the Search Agent.
    # The agent will use WebSearchTool and return
    # a validated SearchResult Pydantic object.
    result = Runner.run_sync(
        search_agent,
        query,
    )

    # The SDK returns a SearchResult object
    # because we supplied output_type=SearchResult.
    search_result = result.final_output

    print("\nSearch Agent completed successfully!")

    # Convert the Pydantic object to readable JSON.
    print(search_result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
