
"""
QueryQuest - Writer Agent Test

Purpose:
    Test whether the Writer can turn research
    findings into a structured article.

Run:
    uv run python -m tests.test_writer

This test uses sample source information.
It does not call the Search Agent.
"""

import json

from agents import Runner

from QQagents.search_agent import SearchResult, SearchSource
from QQagents.writer_agent import create_writer_agent


def main():
    """Test the Writer Agent independently."""

    # Create sample data using the same Pydantic
    # SearchResult class returned by our Search Agent.
    #
    # These are simplified descriptions for testing,
    # not the results of a new live web search.
    search_result = SearchResult(
        query="AI agent frameworks for production",
        findings=[
            "OpenAI Agents SDK supports agents, tools, "
            "handoffs, and tracing.",

            "LangGraph supports stateful agent "
            "orchestration and durable execution.",

            "CrewAI provides agents, crews, and flows."
        ],
        sources=[
            SearchSource(
                title="OpenAI Agents SDK Documentation",
                url="https://openai.github.io/openai-agents-python/",
                finding="Describes agents, tools, "
                        "handoffs, and tracing."
            ),
            SearchSource(
                title="LangGraph Documentation",
                url="https://docs.langchain.com/oss/python/langgraph/overview",
                finding="Describes stateful orchestration "
                        "and durable execution."
            ),
            SearchSource(
                title="CrewAI Documentation",
                url="https://docs.crewai.com/",
                finding="Describes agents, crews, "
                        "and flows."
            )
        ]
    )

    # Assign each source a numeric reference ID.
    # The Writer uses these IDs for citations.
    sources = []

    for index, source in enumerate(
        search_result.sources,
        start=1
    ):
        sources.append({
            "id": index,
            "title": source.title,
            "url": source.url,
            "finding": source.finding
        })

    # Build the input sent to the Writer Agent.
    writer_input = {
        "research_question": (
            "Compare OpenAI Agents SDK, LangGraph "
            "and CrewAI for production applications."
        ),
        "findings": search_result.findings,
        "sources": sources
    }

    # Create the Writer Agent.
    writer = create_writer_agent()

    print("Calling Writer Agent...", flush=True)

    # Execute the Writer using our prepared evidence.
    # The SDK returns a structured ResearchArticle.
    result = Runner.run_sync(
        writer,
        json.dumps(writer_input, indent=2)
    )

    article = result.final_output

    # Verify that every citation refers to a source
    # provided in the input.
    valid_source_ids = set(range(1, len(sources) + 1))

    for section in article.sections:
        for paragraph in section.paragraphs:
            if not set(paragraph.source_ids).issubset(
                valid_source_ids
            ):
                raise ValueError(
                    "Writer returned an unknown source ID."
                )

    # Display the article in a readable format.
    print("\n" + "=" * 50)
    print(article.title)
    print("=" * 50)

    print("\nSUMMARY\n")
    print(article.summary)

    for section in article.sections:
        print(f"\n## {section.heading}\n")

        for paragraph in section.paragraphs:
            # Format IDs as citations such as [1] [2].
            citations = " ".join(
                f"[{source_id}]"
                for source_id in paragraph.source_ids
            )

            print(f"{paragraph.text} {citations}\n")

    print("\nCONCLUSION\n")
    print(article.conclusion)

    # Display original source URLs.
    # We do not allow the Writer to invent them.
    print("\nSOURCES\n")

    for source in sources:
        print(
            f"[{source['id']}] "
            f"{source['title']}: {source['url']}"
        )

    # Confirm that Pydantic structured output worked.
    print("\nStructured output type:")
    print(type(article).__name__)


if __name__ == "__main__":
    main()
