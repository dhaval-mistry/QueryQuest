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
"""
