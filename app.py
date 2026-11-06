"""QueryQuest: Gradio interface for your existing three-agent research workflow.

What changed in the HTML upgrade:
    1. gr.HTML replaces the plain Markdown article output.
    2. One renderer formats the article for both the website and Gmail.
    3. Email now sends HTML plus a plain-text fallback.

What did NOT change:
    * Planner Agent, Search Agent, Writer Agent
    * OpenAI Agents SDK / Pydantic structured outputs
    * queryquest_workflow.py

Run from the QueryQuest project root:
    uv run python app.py
"""

import logging

import gradio as gr
from dotenv import load_dotenv

# Reuse the Planner -> Search -> Writer workflow that already works.
from queryquest_workflow import run_research, format_article
from services.article_renderer import render_article_html, empty_article_html
from services.email_sender import send_email, normalize_email
from style import THEME, CUSTOM_CSS

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def research(question):
    """Generate research once, then prepare both HTML and text versions.

    The three AI agents still produce a Pydantic ResearchArticle.
    Formatting is regular Python, so it costs zero additional LLM tokens.
    """
    question = (question or "").strip()
    if not question:
        raise gr.Error("Enter a research question first.")

    try:
        article, sources, completed, planned = run_research(question)

        # Dark HTML for the Gradio research report.
        preview_html = render_article_html(
            article, sources, completed, planned
        )

        # Light HTML for Gmail. Inline CSS helps email-client compatibility.
        email_html = render_article_html(
            article, sources, completed, planned, for_email=True
        )

        # Keep a plain text version for email clients that disable HTML.
        email_text = format_article(article, sources, completed, planned)

        # gr.State keeps this report separate for each browser session.
        article_state = {
            "title": article.title,
            "email_body": email_text,
            "email_html": email_html,
        }
        return preview_html, article_state, "Research completed. Your report is ready."

    except Exception as error:
        logger.exception("QueryQuest research failed")
        raise gr.Error("Research failed. Check the terminal for details.") from error


def email_article(address, article_state):
    """Email the existing article only after the user clicks Send."""
    if not article_state or not article_state.get("email_body"):
        return "Generate your research report first."

    try:
        recipient = normalize_email(address)
    except ValueError as error:
        return str(error)

    try:
        # Only this service talks to Gmail SMTP. It is NOT an AI agent.
        send_email(
            subject=f"QueryQuest: {article_state['title']}",
            body=article_state["email_body"],
            html_body=article_state.get("email_html"),
            recipient=recipient,
        )
        return f"HTML report submitted to Gmail for delivery to {recipient}."
    except Exception:
        logger.exception("QueryQuest email delivery failed")
        return "Email failed. Check your Gmail configuration and terminal logs."


def clear_chat():
    """Clear the visible report and the per-session email payload."""
    return "", empty_article_html(), {}, "", "", ""


def build_app():
    """Build the Gradio UI without launching it on import."""
    with gr.Blocks(title="QueryQuest | AI Research") as demo:
        gr.HTML(
            '<div id="qq-header">'
            '<div class="qq-eyebrow">RESEARCH ASSISTANT</div>'
            '<h1>Query<span>Quest</span></h1>'
            '<p>Ask a question. Explore the evidence. Read a beautifully formatted report.</p>'
            '</div>'
        )

        question = gr.Textbox(
            label="What would you like to research?",
            placeholder="Enter a research question...",
            lines=3,
            elem_id="qq-question",
        )

        with gr.Row():
            search_btn = gr.Button("Generate research report", variant="primary")
            new_chat_btn = gr.Button("+ New Chat")

        with gr.Row():
            sample_btn1 = gr.Button("AI agent security", size="sm")
            sample_btn2 = gr.Button("AI engineering careers", size="sm")
            sample_btn3 = gr.Button("Future of digital banking", size="sm")

        status = gr.Markdown("")
        gr.Markdown("### Research report")
        article_output = gr.HTML(
            value=empty_article_html(),
            elem_id="qq-article",
        )
        article_state = gr.State({})

        with gr.Accordion("Email this report (optional)", open=False):
            email = gr.Textbox(
                label="Recipient email address",
                placeholder="you@example.com",
            )
            email_btn = gr.Button("Send formatted report", variant="primary")
            email_status = gr.Markdown("")

        gr.HTML(
            '<div id="qq-footer">Powered by Dhaval Mistry | Mahantai</div>'
        )

        # Gradio invokes existing Python functions; no new agent is created.
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
            outputs=[question, article_output, article_state, status, email, email_status],
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
    # Keep the application local during development. Public email needs
    # recipient verification, rate limiting, and protection against abuse.
    build_app().queue(default_concurrency_limit=1, max_size=10).launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=THEME,
        css=CUSTOM_CSS,
    )
