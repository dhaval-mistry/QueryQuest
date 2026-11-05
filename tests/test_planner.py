
"""
Manual test for the QueryQuest Planner Agent.

Run from the project root:
    uv run python -m tests.test_planner
"""

from dotenv import load_dotenv
from agents import Runner, set_tracing_disabled
from QQagents.planner_agent import create_planner_agent

load_dotenv(override=True)


def main():

    # Temporarily disable OpenAI trace export.
    # This isolates the Bedrock model test from
    # the separate OpenAI tracing 401 issue.
    set_tracing_disabled(False)
    

    # Create the Planner Agent.
    planner = create_planner_agent()

    question = "Compare OpenAI Agents SDK, LangGraph, and CrewAI for production applications."

    # Print this before invoking AWS.
    # If execution stops here, the problem occurs
    # during the model call or output processing.
    print("Calling Planner Agent...", flush=True)

    # Execute the agent and wait for the final result.
    result = Runner.run_sync(
        planner,
        question
    )

    print("Planner completed successfully!")

    # final_output should be a WebSearchPlan object.
    plan = result.final_output

    # Convert the Pydantic object to formatted JSON.
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
