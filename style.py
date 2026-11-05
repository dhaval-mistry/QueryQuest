"""Visual style for the QueryQuest Gradio interface.

Keep the appearance separate from the research and email logic.
"""

import gradio as gr


# Gradio handles the controls. CSS handles our custom branding and layout.
THEME = gr.themes.Base(primary_hue="red", neutral_hue="slate").set(
    body_background_fill="#191b22",
    body_text_color="#f7f7fb",
    block_background_fill="#252833",
    block_label_text_color="#e5e6eb",
    input_background_fill="#252833",
    input_border_color="#4b5060",
    button_primary_background_fill="#ff746c",
    button_primary_background_fill_hover="#f65e55",
    button_primary_text_color="#191b22",
)

CUSTOM_CSS = """
.gradio-container {
    max-width: 1000px !important;
    margin: 0 auto !important;
}

#qq-heading {
    text-align: center;
    padding: 20px 0 12px;
}
#qq-heading h1 {
    font-size: clamp(2rem, 5vw, 3.2rem);
    letter-spacing: -1.4px;
    margin-bottom: 2px;
}
#qq-heading h1 strong { color: #ff746c; }
#qq-heading p { color: #c8cbd4; }

#qq-article {
    border: 1px solid #444958;
    border-radius: 16px;
    padding: 20px;
    min-height: 180px;
}
#qq-article a { color: #ffa09a !important; }

#qq-footer {
    text-align: center;
    color: #a5a9b5;
    padding: 20px 0 8px;
    font-size: 0.85rem;
}
"""
