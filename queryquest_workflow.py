
"""
QueryQuest - Main Research Workflow

Purpose:
    Connect our three agents and send the article by email.

Workflow:
    1. Planner creates search queries.
    2. Search Agent researches each query.
    3. Python combines the search results.
    4. Writer generates the final article.
    5. User approves sending the article by email.

Run:
    uv run python queryquest_workflow.py
"""

import json
import os

from dotenv import load_dotenv
from agents import Runner, trace

from QQagents.planner_agent import create_planner_agent
from QQagents.search_agent import create_search_agent
from QQagents.writer_agent import create_writer_agent
from services.email_sender import send_email


# Load configuration from the project .env file.
load_dotenv(override=True)


def format_article(article, sources, completed, planned):
    """
    Convert the Writer's Pydantic article into readable text.

    We use this same text for:
        - Terminal output
        - Email delivery

    Source IDs are checked before sending.
    """

    # Collect the actual source IDs passed to the Writer.
    valid_ids = {source["id"] for source in sources}

    # Start the email with the article title.
    lines = [
        article.title,
        "=" * len(article.title),
        "",
        f"Research coverage: {completed}/{planned} planned searches",
        "",
        "EXECUTIVE SUMMARY",
        article.summary,
        "",
    ]

    # Add every article section and its paragraphs.
    for section in article.sections:

        lines.append(section.heading.upper())
        lines.append("-" * len(section.heading))

        for paragraph in section.paragraphs:

            # Reject citations that reference unknown sources.
            if not paragraph.source_ids:
                raise ValueError(
                    "Writer returned a paragraph without citations."
                )

            if not set(paragraph.source_ids).issubset(valid_ids):
                raise ValueError(
                    "Writer referenced an unknown source ID."
                )

            # Example citation format: [1] [3]
            citations = " ".join(
                f"[{source_id}]"
                for source_id in paragraph.source_ids
            )

            lines.append(f"{paragraph.text} {citations}")
            lines.append("")

    # Add the Writer's conclusion.
    lines.extend([
        "CONCLUSION",
        article.conclusion,
        "",
        "SOURCES",
    ])

    # Preserve source URLs from the Search Agent.
    # The Writer never needs to invent these URLs.
    for source in sources:
        lines.append(
            f"[{source['id']}] "
            f"{source['title']}\n"
            f"{source['url']}"
        )

    lines.extend([
        "",
        "Powered by Dhaval Mistry | Mahantai",
    ])

    return "\n".join(lines)


def run_research(question):
    """
    Execute the QueryQuest research pipeline.

    Returns:
        article: Structured article from the Writer.
        sources: Numbered source records.
        completed: Number of search queries executed.
        planned: Total number of planned queries.
    """

    # Limit queries during development to control cost.
    max_searches = int(
        os.getenv("MAX_SEARCHES_PER_RUN", "2")
    )

    if max_searches < 1:
        raise ValueError("MAX_SEARCHES_PER_RUN must be at least 1")

    # Group our agent runs in one OpenAI trace.
    # This makes the entire workflow easier to inspect.
    with trace("QueryQuest - Research Workflow"):

        # ---------------------------------------
        # STEP 1: PLANNER AGENT
        # ---------------------------------------
        print("\n[1] Planning research...", flush=True)

        planner = create_planner_agent()

        planner_result = Runner.run_sync(
            planner,
            question,
        )

        # The Planner returns a Pydantic WebSearchPlan.
        plan = planner_result.final_output

        # Execute only the allowed number of queries.
        selected_searches = plan.searches[:max_searches]

        if not selected_searches:
            raise ValueError(
                "Planner returned no search queries."
            )

        print(
            f"Planner generated {len(plan.searches)} queries."
        )
        print(
            f"Executing {len(selected_searches)} queries."
        )

        # ---------------------------------------
        # STEP 2: SEARCH AGENT
        # ---------------------------------------
        print("\n[2] Searching the web...", flush=True)

        search_agent = create_search_agent()

        # Store findings and source records in memory.
        all_findings = []
        all_sources = []

        # Used to avoid adding the same URL twice.
        seen_urls = set()

        for index, search in enumerate(
            selected_searches,
            start=1
        ):

            print(
                f"\nSearch {index}: {search.query}",
                flush=True
            )

            # Give the Search Agent one query and
            # explain why the Planner selected it.
            search_input = (
                f"Research this query: {search.query}\n"
                f"Research purpose: {search.reason}"
            )

            # The Search Agent returns SearchResult.
            search_run = Runner.run_sync(
                search_agent,
                search_input,
            )

            result = search_run.final_output

            # Collect important findings.
            all_findings.extend(result.findings)

            # Collect the source records from this search.
            for source in result.sources:

                url = source.url.strip()

                # Ignore empty or invalid-looking URLs.
                if not url.startswith(("https://", "http://")):
                    continue

                # Do not add duplicate URLs.
                if url in seen_urls:
                    continue

                seen_urls.add(url)

                # Assign a unique source number.
                # The Writer uses this ID for citations.
                source_id = len(all_sources) + 1

                all_sources.append({
                    "id": source_id,
                    "title": source.title,
                    "url": url,
                    "finding": source.finding,
                })

        # Don't write an article without sources.
        if not all_sources:
            raise ValueError(
                "Search Agent returned no usable sources."
            )

        print(
            f"\nCollected {len(all_sources)} unique sources."
        )

        # ---------------------------------------
        # STEP 3: WRITER AGENT
        # ---------------------------------------
        print("\n[3] Writing research article...", flush=True)

        writer = create_writer_agent()

        # Combine the original question and evidence.
        # The Writer receives numbered source IDs.
        writer_input = {
            "research_question": question,
            "findings": all_findings,
            "sources": all_sources,
            "research_scope_note": (
                f"Only {len(selected_searches)} of "
                f"{len(plan.searches)} planned queries "
                "were executed. Acknowledge limited "
                "coverage if relevant."
            ),
        }

        # Pass the research evidence to the Writer.
        writer_result = Runner.run_sync(
            writer,
            json.dumps(writer_input, indent=2),
        )

        # The Writer returns a Pydantic ResearchArticle.
        article = writer_result.final_output

    return (
        article,
        all_sources,
        len(selected_searches),
        len(plan.searches),
    )


def main():
    """Run QueryQuest from the terminal."""

    print("\nWelcome to QueryQuest!")
    print("AI Research Assistant\n")

    question = input("Enter your research question: ").strip()

    if not question:
        print("Please enter a research question.")
        return

    # Execute all three agents.
    article, sources, completed, planned = run_research(
        question
    )

    # Format the article for display and email.
    article_text = format_article(
        article,
        sources,
        completed,
        planned,
    )

    print("\n" + "=" * 60)
    print(article_text)
    print("=" * 60)

    # For safety, require confirmation before emailing.
    recipient = os.getenv("EMAIL_TO") or os.getenv(
        "EMAIL_ADDRESS"
    )

    answer = input(
        f"\nSend this article to {recipient}? (y/n): "
    ).strip().lower()

    if answer != "y":
        print("Email skipped. Research completed!")
        return

    # Clearly label partial research during testing.
    prefix = "[TEST] " if completed < planned else ""

    subject = f"{prefix}QueryQuest: {article.title}"

    try:
        # Gmail SMTP sends the completed article.
        # This is a normal Python function, not an LLM.
        send_email(
            subject=subject,
            body=article_text,
        )

        print("\nQueryQuest completed successfully!")

    except Exception as error:
        # Keep the generated article visible even
        # if SMTP delivery fails.
        print(f"\nEmail delivery failed: {error}")


if __name__ == "__main__":
    main()
