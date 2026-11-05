"""QueryQuest Version 1: simple Gradio UI for your existing research workflow.

Run from the project root:
    uv run python app.py

No new agent framework or AWS integration is required.
"""

import logging
from urllib.parse import urlsplit

import gradio as gr
from dotenv import load_dotenv

# Reuse the three-agent workflow that already works in the terminal.
from queryquest_workflow import run_research, format_article
from services.email_sender import send_email, normalize_email
from style import THEME, CUSTOM_CSS

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def article_as_markdown(article, sources, completed, planned):
    """Display the existing Pydantic ResearchArticle in a readable format.

    Use real URLs from the Search Agent, not URLs invented by the Writer.
    """
    known_sources = {source["id"]: source for source in sources}
    lines = [
        f"# {article.title}",
        "",
        "## Executive summary",
        article.summary,
        "",
    ]

    # Every section contains paragraphs with source IDs.
    for section in article.sections:
        lines.extend([f"## {section.heading}", ""])
        for paragraph in section.paragraphs:
            citations = []
            for source_id in paragraph.source_ids:
                source = known_sources.get(source_id)
                if source:
                    url = source.get("url", "")
                    if urlsplit(url).scheme in {"http", "https"}:
                        citations.append(f"[{source_id}](<{url}>)")
            lines.extend([paragraph.text + " " + " ".join(citations), ""])

    lines.extend(["## Conclusion", article.conclusion, "", "## Sources", ""])
    for source in sources:
        url = source.get("url", "")
        if urlsplit(url).scheme in {"http", "https"}:
            title = source.get("title", "Source").replace("[", "").replace("]", "")
            lines.append(f"- [{source['id']}] [{title}](<{url}>)")

    # Distinguish a test-limited report from all planned searches.
    if completed < planned:
        lines.append(
            f"\n*Research coverage: {completed} of {planned} planned searches.*"
        )
    return "\n".join(lines)


def research(question):
    """Run the existing Planner -> Search -> Writer pipeline once."""
    question = (question or "").strip()
    if not question:
        raise gr.Error("Enter a research question first.")

    try:
        # This function already runs your three working OpenAI agents.
        article, sources, completed, planned = run_research(question)

        # Markdown is for the webpage; text is for the email.
        markdown = article_as_markdown(article, sources, completed, planned)
        email_body = format_article(article, sources, completed, planned)

        # gr.State keeps each browser session's completed article separate.
        state = {"title": article.title, "email_body": email_body}
        return markdown, state, "Research completed. You can email the article below."
    except Exception as error:
        logger.exception("Research failed")
        raise gr.Error("Research failed. Check the terminal for details.") from error


def email_article(address, article_state):
    """Send only after the user explicitly clicks the Email button."""
    if not article_state or not article_state.get("email_body"):
        return "Please generate a research article first."

    try:
        recipient = normalize_email(address)
    except ValueError as error:
        return str(error)

    try:
        send_email(
            subject=f"QueryQuest: {article_state['title']}",
            body=article_state["email_body"],
            recipient=recipient,
        )
        return f"Article submitted to Gmail for delivery to {recipient}."
    except Exception:
        logger.exception("Email delivery failed")
        return "Email failed. Check Gmail settings and terminal logs."


def clear_chat():
    """Reset all user-visible fields and the saved article for this session."""
    return "", "*Your research article will appear here.*", {}, "", "", ""


def build_app():
    """Create the web UI without starting the server during import."""
    with gr.Blocks(title="QueryQuest") as demo:
        gr.Markdown(
            "# Query**Quest**\nAI-powered deep research, made simple.",
            elem_id="qq-heading",
        )

        with gr.Row():
            question = gr.Textbox(
                label="Research question",
                placeholder="What would you like to research?",
                lines=3,
                scale=5,
            )

        with gr.Row():
            search_btn = gr.Button("Research", variant="primary")
            new_chat_btn = gr.Button("+ New Chat")

        with gr.Row():
            sample_btn1 = gr.Button("AI agent security", size="sm")
            sample_btn2 = gr.Button("AI engineering careers", size="sm")
            sample_btn3 = gr.Button("Future of digital banking", size="sm")

        status = gr.Markdown("")
        article_output = gr.Markdown(
            "*Your research article will appear here.*",
            elem_id="qq-article",
        )
        article_state = gr.State({})

        with gr.Accordion("Email this article (optional)", open=False):
            email = gr.Textbox(
                label="Recipient email address",
                placeholder="you@example.com",
            )
            email_btn = gr.Button("Send article to this email", variant="primary")
            email_status = gr.Markdown("")

        gr.HTML('<div id="qq-footer">Powered by Dhaval Mistry | Mahantai</div>')

        # Gradio runs the Python callbacks when users click UI buttons.
        search_btn.click(
            research,
            inputs=question,
            outputs=[article_output, article_state, status],
            concurrency_limit=1,
        )
        email_btn.click(
            email_article,
            inputs=[email, article_state],
            outputs=email_status,
        )
        new_chat_btn.click(
            clear_chat,
            outputs=[question, article_output, article_state,
                     status, email, email_status],
        )
        sample_btn1.click(
            lambda: "What are best practices for securing AI agents?",
            outputs=question,
        )
        sample_btn2.click(
            lambda: "How are AI engineering careers changing in 2026?",
            outputs=question,
        )
        sample_btn3.click(
            lambda: "How will AI change digital banking in the next five years?",
            outputs=question,
        )
    return demo


if __name__ == "__main__":
    # Bind to localhost: safe for testing, not a public email-sending service.
    build_app().queue(default_concurrency_limit=1, max_size=10).launch(
        server_name="127.0.0.1", server_port=7860,
        theme=THEME, css=CUSTOM_CSS
    )
