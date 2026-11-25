"""Gradio interface for AWS research and optional Amazon SES delivery.

Run: uv run python app.py
"""

import logging
import os

import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

# Reuse the Planner -> Search -> Writer workflow that already works.
from queryquest_workflow import research_steps, format_article
from config import AWSConfigurationError
from services.article_renderer import render_article_html, empty_article_html
from services.email_sender import send_email, normalize_email
from style import THEME, CUSTOM_CSS
from services.research_progress import progress_html
from pydantic import ValidationError

load_dotenv(Path(__file__).resolve().parent / ".env")
logger = logging.getLogger(__name__)


def research(question):
    """Stream actual agent stages; expose only validated reports for email."""
    question = (question or "").strip()
    if not question:
        raise gr.Error("Enter a research question first.")
    stage = "checking"
    yield (empty_article_html(), {}, progress_html(stage, "Checking your research setup?"),
           gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False))
    try:
        for update in research_steps(question):
            stage = update.stage
            if update.result is None:
                yield (gr.skip(), gr.skip(), progress_html(stage, update.detail),
                       gr.skip(), gr.skip(), gr.skip())
                continue
            article, sources, completed, planned = update.result
            email_text = format_article(article, sources, completed, planned)
            preview = render_article_html(article, sources, completed, planned)
            email_html = render_article_html(article, sources, completed, planned, for_email=True)
            state = {"title": article.title, "email_body": email_text, "email_html": email_html}
            yield (preview, state, progress_html("complete", update.detail),
                   gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True))
    except AWSConfigurationError as error:
        logger.warning("AWS configuration incomplete: %s", error)
        yield (gr.skip(), {}, progress_html(stage, str(error), failed=True),
               gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=False))
    except Exception as error:
        logger.exception("QueryQuest research failed during %s", stage)
        if isinstance(error, ValidationError):
            message = "The writer returned an invalid article format. Please try again."
        else:
            label = {"planner": "planning", "search": "web search", "writer": "writing"}.get(stage, "setup")
            message = f"Research stopped during {label}. Please try again; details are in the terminal."
        yield (gr.skip(), {}, progress_html(stage, message, failed=True),
               gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=False))


def email_article(address, article_state):
    """Email the existing article only after the user clicks Send."""
    if not article_state or not article_state.get("email_body"):
        return "Generate your research report first."

    try:
        recipient = normalize_email(address)
    except ValueError as error:
        return str(error)

    try:
        # Only this service talks to Amazon SES. It is NOT an AI agent.
        send_email(
            subject=f"QueryQuest: {article_state['title']}",
            body=article_state["email_body"],
            html_body=article_state.get("email_html"),
            recipient=recipient,
        )
        return f"HTML report submitted to Amazon SES for delivery to {recipient}."
    except Exception:
        logger.exception("QueryQuest email delivery failed")
        return "Email failed. Check your Amazon SES configuration and terminal logs."


def clear_chat():
    """Clear the visible report and the per-session email payload."""
    return "", empty_article_html(), {}, progress_html(), "", "", gr.update(interactive=False)


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

        with gr.Row(elem_id="qq-actions"):
            search_btn = gr.Button("Generate research report", variant="primary")
            new_chat_btn = gr.Button("+ New Chat")

        with gr.Row(elem_id="qq-samples"):
            sample_btn1 = gr.Button("AI agent security", size="sm")
            sample_btn2 = gr.Button("AI engineering careers", size="sm")
            sample_btn3 = gr.Button("Future of digital banking", size="sm")

        status = gr.HTML(progress_html(), elem_id="qq-progress")
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
            email_btn = gr.Button("Send formatted report", variant="primary", interactive=False)
            email_status = gr.HTML(progress_html(), elem_id="qq-progress")

        gr.HTML(
            '<div id="qq-footer">Powered by Dhaval Mistry | Mahantai</div>'
        )

        # Gradio invokes existing Python functions; no new agent is created.
        search_btn.click(
            research,
            inputs=question,
            outputs=[article_output, article_state, status, search_btn, new_chat_btn, email_btn],
            concurrency_limit=1,
            trigger_mode="once",
            show_progress="hidden",
        )
        email_btn.click(
            email_article,
            inputs=[email, article_state],
            outputs=email_status,
        )
        new_chat_btn.click(
            clear_chat,
            outputs=[question, article_output, article_state, status, email, email_status, email_btn],
        )
        sample_btn1.click(
            lambda: "What are best practices for securing AI agents?",
            outputs=question,
        )
        sample_btn2.click(
            lambda: "How are AI engineering careers changing in 2027?",
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
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("PORT") or os.getenv("GRADIO_SERVER_PORT", "7860")),
        theme=THEME,
        css=CUSTOM_CSS,
    )
