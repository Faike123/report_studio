from __future__ import annotations

import streamlit as st


def apply_igne_theme():
    st.markdown(
        """
<style>
/* ============================= */
/* REPORT STUDIO DEMO THEME      */
/* ============================= */

:root {
    --rs-green: #004631;
    --rs-green-2: #006447;
    --rs-green-soft: #e8f3ee;
    --rs-yellow: #f2c94c;
    --rs-yellow-soft: #fff8da;
    --rs-border: #d9e1dd;
    --rs-text: #17231d;
    --rs-muted: #64746d;
    --rs-bg: #f8faf9;
    --rs-card: #ffffff;
}

/* App background */
.stApp {
    background: linear-gradient(180deg, #f8faf9 0%, #ffffff 42%);
    color: var(--rs-text);
}

/* Main content */
.block-container {
    padding-top: 1.15rem;
    padding-bottom: 3rem;
    max-width: 1480px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #004631 0%, #073529 100%);
    border-right: 1px solid #003524;
}

section[data-testid="stSidebar"] * {
    color: #ffffff;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #edf6f2 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 0.35rem 0.55rem;
    margin-bottom: 0.22rem;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(242,201,76,0.16);
    border-color: rgba(242,201,76,0.55);
}

/* Headings */
h1, h2, h3 {
    color: var(--rs-green);
    letter-spacing: -0.025em;
}

h1 {
    font-weight: 800;
    border-bottom: 4px solid var(--rs-yellow);
    padding-bottom: 0.35rem;
    margin-bottom: 0.75rem;
}

h2 {
    font-weight: 760;
}

h3 {
    font-weight: 720;
}

/* Captions and muted text */
[data-testid="stCaptionContainer"] {
    color: var(--rs-muted);
}

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--rs-card);
    border: 1px solid var(--rs-border);
    border-left: 5px solid var(--rs-green);
    border-radius: 14px;
    padding: 0.72rem 0.88rem;
    box-shadow: 0 2px 10px rgba(0, 70, 49, 0.05);
}

[data-testid="stMetricLabel"] {
    color: var(--rs-muted);
    font-weight: 700;
}

[data-testid="stMetricValue"] {
    color: var(--rs-green);
    font-weight: 850;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid var(--rs-green);
    color: var(--rs-green);
    background: #ffffff;
    font-weight: 750;
    transition: all 0.12s ease-in-out;
}

.stButton > button:hover {
    border-color: var(--rs-yellow);
    color: var(--rs-green);
    background: var(--rs-yellow-soft);
    transform: translateY(-1px);
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--rs-green) !important;
    color: #ffffff !important;
    border-color: var(--rs-green) !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    background: var(--rs-green-2) !important;
    border-color: var(--rs-yellow) !important;
}

/* File uploader: lighter, less dark */
[data-testid="stFileUploader"] section {
    background: #ffffff !important;
    border: 1px dashed var(--rs-border) !important;
    border-radius: 14px !important;
    color: var(--rs-text) !important;
}

[data-testid="stFileUploader"] section * {
    color: var(--rs-text) !important;
}

[data-testid="stFileUploader"] small {
    color: var(--rs-muted) !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
}

/* Dataframe / table containers: lighter */
[data-testid="stDataFrame"] {
    border: 1px solid var(--rs-border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 70, 49, 0.035);
    background: #ffffff !important;
}

/* Try to force dataframe visual lightness where Streamlit allows it */
[data-testid="stDataFrame"] div {
    border-color: #e3e8e5 !important;
}

/* Data editor container */
[data-testid="stDataEditor"] {
    border: 1px solid var(--rs-border);
    border-radius: 12px;
    overflow: hidden;
    background: #ffffff !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--rs-green-soft);
    border-radius: 10px;
    font-weight: 750;
    color: var(--rs-green) !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid var(--rs-border);
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 750;
    color: var(--rs-green);
}

button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid var(--rs-yellow);
}

/* Inputs/selects: lighter */
[data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea {
    border-radius: 10px !important;
    background: #ffffff !important;
    color: var(--rs-text) !important;
    border-color: var(--rs-border) !important;
}

[data-baseweb="select"] * {
    color: var(--rs-text) !important;
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 10px;
    background: var(--rs-yellow-soft);
    border: 1px solid var(--rs-yellow);
    color: var(--rs-green);
    font-weight: 800;
}

.stDownloadButton > button:hover {
    background: var(--rs-yellow);
    color: var(--rs-green);
}

/* Custom hero */
.rs-hero {
    background: linear-gradient(135deg, #004631 0%, #006447 72%);
    color: #ffffff;
    padding: 1.05rem 1.25rem;
    border-radius: 18px;
    border: 1px solid #003524;
    box-shadow: 0 8px 24px rgba(0, 70, 49, 0.14);
    margin-bottom: 1rem;
}

.rs-hero h1,
.rs-hero h2,
.rs-hero h3 {
    color: #ffffff;
    border: 0;
    padding: 0;
    margin: 0;
}

.rs-hero p {
    color: #e8f3ef;
    margin-top: 0.35rem;
    margin-bottom: 0;
}

.rs-badge {
    display: inline-block;
    background: var(--rs-yellow);
    color: #10251d;
    font-size: 0.74rem;
    font-weight: 850;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    padding: 0.22rem 0.5rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
}

.rs-card {
    background: #ffffff;
    border: 1px solid var(--rs-border);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 3px 14px rgba(0, 70, 49, 0.05);
    margin-bottom: 1rem;
}

.rs-card-title {
    color: var(--rs-green);
    font-weight: 850;
    font-size: 1rem;
    margin-bottom: 0.35rem;
}

.rs-card-subtle {
    color: var(--rs-muted);
    font-size: 0.88rem;
}

.rs-stepbar {
    display: flex;
    gap: 0.45rem;
    flex-wrap: wrap;
    margin: 0.75rem 0 1rem 0;
}

.rs-step {
    background: #ffffff;
    border: 1px solid var(--rs-border);
    border-radius: 999px;
    padding: 0.35rem 0.7rem;
    color: var(--rs-green);
    font-weight: 800;
    font-size: 0.82rem;
}

.rs-step.active {
    background: var(--rs-green);
    color: #ffffff;
    border-color: var(--rs-green);
}

.rs-step.done {
    background: var(--rs-yellow-soft);
    border-color: var(--rs-yellow);
}

/* Keep old class aliases working */
.igne-hero { 
    background: linear-gradient(135deg, #004631 0%, #006447 72%);
    color: #ffffff;
    padding: 1.05rem 1.25rem;
    border-radius: 18px;
    border: 1px solid #003524;
    box-shadow: 0 8px 24px rgba(0, 70, 49, 0.14);
    margin-bottom: 1rem;
}
.igne-hero h1, .igne-hero h2, .igne-hero h3 {
    color: #ffffff;
    border: 0;
    padding: 0;
    margin: 0;
}
.igne-hero p {
    color: #e8f3ef;
    margin-top: 0.35rem;
    margin-bottom: 0;
}
.igne-badge {
    display: inline-block;
    background: var(--rs-yellow);
    color: #10251d;
    font-size: 0.74rem;
    font-weight: 850;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    padding: 0.22rem 0.5rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
}

hr {
    border: none;
    border-top: 1px solid var(--rs-border);
    margin: 1.25rem 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str = "", badge: str = "Report Studio"):
    st.markdown(
        f"""
<div class="rs-hero">
  <div class="rs-badge">{badge}</div>
  <h2>{title}</h2>
  <p>{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def stepbar(active: str):
    steps = [
        ("import", "Import"),
        ("detect", "Detect"),
        ("select", "Select"),
        ("review", "Review"),
        ("export", "Export"),
    ]

    order = [s[0] for s in steps]
    active_index = order.index(active) if active in order else 0

    html = ['<div class="rs-stepbar">']

    for i, (key, label) in enumerate(steps):
        cls = "rs-step"
        if key == active:
            cls += " active"
        elif i < active_index:
            cls += " done"
        html.append(f'<div class="{cls}">{i+1}. {label}</div>')

    html.append("</div>")

    st.markdown("\n".join(html), unsafe_allow_html=True)
