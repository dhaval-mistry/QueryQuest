
"""
Manual test for the QueryQuest Planner Agent.

Run from the project root:
    uv run python -m tests.test_planner
"""

from pathlib import Path
from dotenv import load_dotenv
from QQagents.planner_agent import create_planner_agent

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main():

    # Create the Planner Agent.
    planner = create_planner_agent()

    question = "Compare OpenAI Agents SDK, LangGraph, and CrewAI for production applications."

    # Print this before invoking AWS.
    # If execution stops here, the problem occurs
    # during the model call or output processing.
    print("Calling Planner Agent...", flush=True)

    # Execute the agent and wait for the final result.
    plan = planner.run(question)

    print("Planner completed successfully!")

    # The result is a validated WebSearchPlan object.

    # Convert the Pydantic object to formatted JSON.
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
