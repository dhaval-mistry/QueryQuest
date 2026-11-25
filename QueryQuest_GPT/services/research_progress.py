"""Events from the actual research workflow and accessible progress markup."""
from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class ResearchUpdate:
    stage: str
    detail: str
    result: tuple | None = None


def progress_html(stage="idle", detail="Ready when you are.", *, failed=False):
    names = [("planner", "Planner"), ("search", "Search"), ("writer", "Writer")]
    active = next((i for i, (key, _) in enumerate(names) if key == stage), -1)
    cards = []
    for i, (key, name) in enumerate(names):
        state = "done" if stage == "complete" or (active >= 0 and i < active) else "waiting"
        if i == active:
            state = "failed" if failed else "active"
        symbol = "&#10003;" if state == "done" else ("!" if state == "failed" else str(i + 1))
        label = {"done": "Complete", "waiting": "Waiting", "active": "Running", "failed": "Stopped"}[state]
        cards.append(f'<div class="qq-step qq-{state}"><span class="qq-step-icon" aria-hidden="true">{symbol}</span>'
                     f'<span><strong>{name}</strong><small>{label}</small></span></div>')
    tone = " qq-progress-error" if failed else ""
    return ('<div class="qq-progress' + tone + '"><div class="qq-steps">' + ''.join(cards) +
            '</div><p role="status" aria-live="polite" aria-atomic="true">' + escape(detail) + '</p></div>')
