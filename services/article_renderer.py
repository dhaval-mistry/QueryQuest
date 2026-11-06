"""Turn a QueryQuest ResearchArticle into attractive, safe HTML.

Why this service exists:
    The Writer Agent already gives us STRUCTURED content using Pydantic:
    title, summary, sections, paragraphs, source IDs, and conclusion.
    We do not need another LLM to format that content.

    This module renders the same article twice:
      * dark Graphite & Coral HTML for Gradio
      * email-friendly, light HTML for Gmail

Security:
    Every piece of LLM-generated text is HTML-escaped. Source links are
    accepted only when they are absolute HTTP(S) URLs with a hostname.
    Never insert a model's text directly into HTML without escaping it.
"""

from html import escape
from urllib.parse import urlsplit

# Palettes are kept close together so they remain easy to maintain.
# The email version uses light colors because many email readers have white
# backgrounds, and light HTML provides more predictable contrast.
_WEB = {
    "background": "#222630",
    "surface": "#282D39",
    "text": "#F4F5F8",
    "muted": "#B7BECF",
    "accent": "#FF8179",
    "link": "#FFABA4",
    "border": "#424858",
    "highlight": "#352F39",
    "heading": "#FFFFFF",
}

_EMAIL = {
    "background": "#F3F5F9",
    "surface": "#FFFFFF",
    "text": "#202736",
    "muted": "#647084",
    "accent": "#D65B52",
    "link": "#B94A42",
    "border": "#E1E5EC",
    "highlight": "#FFF3F1",
    "heading": "#172033",
}


def _text(value: object) -> str:
    """Escape untrusted content and preserve deliberate line breaks."""
    return escape(str(value if value is not None else ""), quote=True).replace("\n", "<br>")


def _safe_url(raw_url: object) -> str | None:
    """Allow only ordinary HTTP(S) URLs, not javascript: or data: links."""
    url = str(raw_url or "").strip()
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() in {"http", "https"} and parsed.hostname:
            return url
    except ValueError:
        pass
    return None


def _source_index(sources: list[dict]) -> dict[int, dict]:
    """Keep usable source records and their ORIGINAL URLs by source ID."""
    indexed: dict[int, dict] = {}
    for source in sources:
        try:
            number = int(source.get("id"))
        except (TypeError, ValueError):
            continue
        url = _safe_url(source.get("url"))
        if number > 0 and url and number not in indexed:
            indexed[number] = {
                "title": str(source.get("title") or f"Source {number}"),
                "url": url,
                "domain": urlsplit(url).hostname or "Source",
            }
    return indexed


def _citations(source_ids: list[int], known_sources: dict[int, dict], colors: dict) -> str:
    """Make the Writer's numeric source IDs into clickable reference links."""
    badges = []
    for source_id in dict.fromkeys(source_ids):  # avoid repeated citation badges
        source = known_sources.get(source_id)
        if not source:
            continue
        badges.append(
            '<a href="{url}" target="_blank" rel="noopener noreferrer" '
            'style="display:inline-block;margin:0 4px 0 0;color:{link};'
            'font-size:12px;font-weight:700;text-decoration:none;'
            'vertical-align:super;" title="{title}">[{id}]</a>'.format(
                url=escape(source["url"], quote=True),
                link=colors["link"],
                title=escape(source["title"], quote=True),
                id=source_id,
            )
        )
    return "".join(badges)


def render_article_html(
    article,
    sources: list[dict],
    completed: int,
    planned: int,
    *,
    for_email: bool = False,
) -> str:
    """Render the SAME structured article for Gradio or Gmail.

    Parameters:
        article: Your Pydantic ResearchArticle (no model changes required).
        sources: Numbered records from queryquest_workflow.py.
        completed: Number of planned search queries actually executed.
        planned: Total number of queries produced by the Planner.
        for_email: False for the dark Gradio view, True for the light email.

    Returns:
        HTML string. All article text is safely escaped.
    """
    c = _EMAIL if for_email else _WEB
    references = _source_index(sources)
    coverage = f"{completed} of {planned} planned searches completed"
    limited = completed < planned

    # -- Header: strong title, restrained branding, visible research scope.
    pieces = [
        '<div style="background:{surface};color:{text};padding:32px 30px 22px;'
        'border-radius:14px 14px 0 0;border-top:5px solid {accent};">'
        '<div style="color:{accent};font:700 11px Arial,sans-serif;'
        'letter-spacing:2.3px;margin-bottom:15px;">QUERYQUEST · RESEARCH REPORT</div>'
        '<h1 style="margin:0 0 17px;color:{heading};font:700 30px/1.27 '
        'Arial,Helvetica,sans-serif;letter-spacing:-0.6px;">{title}</h1>'
        '<div style="color:{muted};font:13px/1.6 Arial,sans-serif;">'
        '{coverage}</div></div>'.format(
            surface=c["surface"], text=c["text"], accent=c["accent"],
            heading=c["heading"], muted=c["muted"],
            title=_text(article.title), coverage=_text(coverage)
        )
    ]

    # -- Article body: summary, titled sections, conclusion, numbered sources.
    pieces.append(
        '<div style="background:{surface};color:{text};padding:0 30px 28px;'
        'border-radius:0 0 14px 14px;">'.format(**c)
    )

    pieces.append(
        '<div style="background:{highlight};border-left:4px solid {accent};'
        'padding:19px 21px;margin:0 0 28px;border-radius:5px;">'
        '<div style="color:{accent};font:bold 11px Arial,sans-serif;'
        'letter-spacing:1.6px;margin:0 0 10px;">EXECUTIVE SUMMARY</div>'
        '<p style="margin:0;color:{text};font:15px/1.85 Arial,sans-serif;">'
        '{summary}</p></div>'.format(summary=_text(article.summary), **c)
    )

    for index, section in enumerate(article.sections, start=1):
        pieces.append(
            '<section style="margin:0 0 30px;">'
            '<h2 style="border-bottom:1px solid {border};padding:0 0 12px;'
            'margin:0 0 17px;color:{heading};font:700 20px/1.4 Arial,sans-serif;">'
            '<span style="color:{accent};font:700 12px Arial,sans-serif;'
            'margin-right:11px;">{index:02d}</span>{heading_text}</h2>'.format(
                index=index, heading_text=_text(section.heading), **c
            )
        )
        for paragraph in section.paragraphs:
            citations = _citations(paragraph.source_ids, references, c)
            pieces.append(
                '<p style="color:{text};font:15px/1.85 Arial,sans-serif;'
                'margin:0 0 16px;">{content} {citations}</p>'.format(
                    content=_text(paragraph.text), citations=citations, **c
                )
            )
        pieces.append("</section>")

    pieces.append(
        '<section style="padding:19px 21px;margin:12px 0 30px;'
        'background:{highlight};border-radius:7px;">'
        '<h2 style="margin:0 0 10px;color:{heading};'
        'font:700 19px Arial,sans-serif;">Conclusion</h2>'
        '<p style="margin:0;color:{text};font:15px/1.85 Arial,sans-serif;">'
        '{conclusion}</p></section>'.format(
            conclusion=_text(article.conclusion), **c
        )
    )

    pieces.append(
        '<section style="border-top:1px solid {border};padding-top:23px;">'
        '<h2 style="margin:0 0 16px;color:{heading};'
        'font:700 20px Arial,sans-serif;">Sources &amp; references</h2>'.format(**c)
    )
    if references:
        for number, source in sorted(references.items()):
            pieces.append(
                '<div style="margin:0 0 15px;padding:0 0 13px;'
                'border-bottom:1px solid {border};">'
                '<span style="color:{accent};font:700 13px Arial,sans-serif;">'
                '[{number}]</span> '
                '<a href="{url}" target="_blank" rel="noopener noreferrer" '
                'style="color:{link};font:700 14px/1.6 Arial,sans-serif;'
                'text-decoration:underline;">{title}</a>'
                '<div style="padding-left:28px;color:{muted};'
                'font:12px/1.5 Arial,sans-serif;">{domain}</div>'
                '</div>'.format(
                    number=number, url=escape(source["url"], quote=True),
                    title=_text(source["title"]),
                    domain=_text(source["domain"]), **c
                )
            )
    else:
        pieces.append(
            '<p style="color:{muted};font:14px Arial,sans-serif;">'
            'No valid source URLs were provided.</p>'.format(**c)
        )
    pieces.append("</section>")

    if limited:
        pieces.append(
            '<p style="color:{muted};font:12px/1.6 Arial,sans-serif;'
            'margin:17px 0 0;">Research coverage was limited for this run. '
            'The report may not include all relevant perspectives.</p>'.format(**c)
        )

    pieces.append("</div>")

    # Email has a widely compatible table-based outer wrapper and a plain
    # footer. Inner text uses inline CSS because email apps strip CSS rules.
    content = "".join(pieces)
    # Build footer separately to avoid depending on external stylesheets.
    footer = (
        '<p style="margin:24px 0 0;text-align:center;color:{muted};'
        'font:12px/1.7 Arial,sans-serif;">'
        'Powered by Dhaval Mistry | Mahantai<br>'
        'AI-generated research. Verify important claims against the sources.'
        '</p>'
    ).format(**c)

    if for_email:
        return (
            '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>QueryQuest Research Report</title></head>'
            '<body style="margin:0;padding:0;background:{background};">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="border-collapse:collapse;background:{background};">'
            '<tr><td align="center" style="padding:24px 12px 32px;">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="max-width:700px;border-collapse:collapse;">'
            '<tr><td>{content}{footer}</td></tr></table>'
            '</td></tr></table></body></html>'.format(
                content=content, footer=footer, **c
            )
        )

    return (
        '<article class="qq-report" style="max-width:820px;margin:0 auto;'
        'font-family:Arial,Helvetica,sans-serif;">'
        + content + footer + '</article>'
    )


def empty_article_html() -> str:
    """Friendly placeholder shown before research and after New Chat."""
    return (
        '<div class="qq-empty-report" style="text-align:center;'
        'padding:45px 20px;color:#BCC4D5;">'
        '<div style="font-size:28px;margin-bottom:12px;">✦</div>'
        '<div style="font-size:18px;font-weight:bold;margin-bottom:9px;">'
        'Your research report will appear here</div>'
        '<div style="font-size:14px;line-height:1.6;">'
        'Ask a question to generate a structured article with clickable sources.'
        '</div></div>'
    )
