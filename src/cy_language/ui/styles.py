"""Custom CSS styles for the Cy Language Editor.

Minimal, tasteful overrides that complement Streamlit's default theme.
Avoid aggressive hacks that break across Streamlit versions.
"""

CUSTOM_CSS = """\
<style>
    /* Tighter top padding for a more app-like feel */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }

    /* Sidebar: subtle section dividers */
    [data-testid="stSidebar"] hr {
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }

    /* Tabs: clear separation between Output and Input */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
    }

    /* ACE editor: remove distracting print margin line */
    .ace_print-margin {
        display: none !important;
    }

    /* ACE editor: make the iframe vertically resizable via drag handle */
    [data-testid="stCustomComponentV1"] > iframe {
        resize: both !important;
        min-height: 150px;
        max-height: 90vh;
    }

    /* Execution time badge */
    .exec-time {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        background-color: #f0f2f6;
        font-size: 0.82rem;
        color: #555;
        font-weight: 500;
    }

    /* Logs tab: compact monospace entries */
    .stTabs [data-baseweb="tab-panel"] [data-testid="stText"] {
        font-family: "Source Code Pro", "Courier New", monospace;
        font-size: 0.85rem;
        line-height: 1.4;
    }
</style>
"""
