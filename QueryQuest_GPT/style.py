"""QueryQuest visual theme, intentionally separate from the agent logic.

The report itself uses safe, inline CSS in services/article_renderer.py.
This stylesheet only styles the surrounding Gradio user interface.
"""

import gradio as gr


THEME = gr.themes.Base(primary_hue="red", neutral_hue="slate").set(
    body_background_fill="#191B23",
    body_text_color="#F7F7FB",
    block_background_fill="#242834",
    block_label_text_color="#E5E8EE",
    input_background_fill="#242834",
    input_border_color="#454B59",
    button_primary_background_fill="#FF8179",
    button_primary_background_fill_hover="#F46B63",
    button_primary_text_color="#181B23",
)

CUSTOM_CSS = """
/* Center the application and give it comfortable breathing room. */
.gradio-container {
    max-width: 1040px !important;
    margin: 0 auto !important;
    padding: 22px 18px !important;
}

/* Brand heading: quiet and professional, with the coral accent. */
#qq-header {
    text-align: center;
    padding: 27px 10px 26px;
}
#qq-header .qq-eyebrow {
    color: #FF8179;
    font-size: 11px;
    letter-spacing: 3px;
    font-weight: 700;
}
#qq-header h1 {
    color: #F8F9FB;
    font-size: clamp(38px, 6vw, 62px);
    letter-spacing: -2px;
    line-height: 1.15;
    margin: 10px 0 9px;
    font-weight: 750;
}
#qq-header h1 span { color: #FF8179; }
#qq-header p {
    color: #B6BECE;
    font-size: 15px;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto;
}

/* A distinct, comfortable reading surface for a long research article. */
#qq-article {
    background: #222630;
    border: 1px solid #414758;
    border-radius: 18px;
    padding: 24px 14px;
    min-height: 190px;
    overflow-wrap: anywhere;
}
#qq-article a:hover { text-decoration: underline !important; }
#qq-article .qq-report { width: 100%; }

#qq-footer {
    text-align: center;
    color: #949EAE;
    padding: 29px 0 8px;
    font-size: 12px;
}

@media (max-width: 640px) {
    .gradio-container { padding: 12px 10px !important; }
    #qq-header { padding: 16px 6px 20px; }
    #qq-article { padding: 10px 1px; }
    #qq-article .qq-report > div { border-radius: 0 !important; }
}

/* The shell has the same width for empty, loading, completed and error states. */
html { scrollbar-gutter: stable; }
.gradio-container {
    width: 100% !important;
    max-width: 940px !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}
.gradio-container > .main, .gradio-container .contain,
.gradio-container .form, .gradio-container .block {
    min-width: 0 !important;
    box-sizing: border-box;
}
.gradio-container > .main { width: 100% !important; }
#qq-article, #qq-progress { width: 100%; min-width: 0; box-sizing: border-box; }
#qq-article { padding: 18px; }
#qq-article .qq-report { width: 100%; max-width: 100% !important; min-width: 0; }
#qq-article .qq-report * { box-sizing: border-box; overflow-wrap: anywhere; }
.qq-report-header { padding: 28px 28px 20px !important; }
.qq-report-body { padding: 0 28px 26px !important; }
.qq-report-title { font-size: clamp(23px, 3.5vw, 30px) !important; }

/* Stage indicators follow workflow events; only the active step animates. */
#qq-progress { background: transparent; border: 0; padding: 0; }
.qq-progress { padding: 12px 0 2px; }
.qq-steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.qq-step { display: flex; align-items: center; gap: 10px; padding: 13px 14px;
    border: 1px solid #414758; border-radius: 12px; background: #222630; min-width: 0; }
.qq-step-icon { display: grid; place-items: center; width: 30px; height: 30px;
    border: 2px solid #636b7c; border-radius: 50%; flex: 0 0 30px;
    font-size: 12px; color: #b7becf; position: relative; }
.qq-step strong { display: block; color: #e5e8ee; font-size: 13px; line-height: 1.4; }
.qq-step small { display: block; color: #b7becf; font-size: 11px; line-height: 1.5; }
.qq-active { border-color: #ff8179; background: #302a33; }
.qq-active .qq-step-icon { color: #ffaba4; border-color: #ff817944; }
.qq-active .qq-step-icon::after { content: ""; position: absolute; inset: -2px;
    border: 2px solid transparent; border-top-color: #ff8179; border-radius: 50%;
    animation: qq-spin 1s linear infinite; }
.qq-done .qq-step-icon { border-color: #6dccab; color: #6dccab; }
.qq-failed { border-color: #ff8179; }
.qq-failed .qq-step-icon { border-color: #ff8179; color: #ffaba4; }
.qq-progress p { color: #b7becf; font-size: 13px; line-height: 1.6; margin: 10px 2px 0;
    min-height: 22px; overflow-wrap: anywhere; }
.qq-progress-error p { color: #ffaba4; }
@keyframes qq-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .qq-active .qq-step-icon::after { animation: none; } }
@media (max-width: 640px) {
    #qq-actions, #qq-samples { flex-direction: column !important; gap: 8px !important; }
    #qq-actions > *, #qq-samples > * { width: 100% !important; min-width: 0 !important; }
    #qq-article { padding: 10px; }
    .qq-report-header { padding: 20px 15px 16px !important; }
    .qq-report-body { padding: 0 15px 20px !important; }
    .qq-report-summary { padding: 14px !important; }
    .qq-step { padding: 10px 6px; gap: 6px; justify-content: center; }
    .qq-step-icon { width: 24px; height: 24px; flex-basis: 24px; }
    .qq-steps { gap: 6px; }
    .qq-step strong { font-size: 12px; }
}
@media (max-width: 360px) {
    .qq-step { flex-direction: column; text-align: center; }
}
"""
