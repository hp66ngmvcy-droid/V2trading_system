"""Visual layout helpers for the Streamlit dashboard."""

from __future__ import annotations

from html import escape
from typing import Any


def apply_theme(st: object) -> None:
    st.markdown(
        """
        <style>
        :root {
          --tar-bg: #f6f8fb;
          --tar-panel: #ffffff;
          --tar-panel-soft: #f9fbfd;
          --tar-border: #d9e2ec;
          --tar-text: #142033;
          --tar-muted: #65758b;
          --tar-green: #178a5b;
          --tar-red: #b42318;
          --tar-amber: #b76e00;
          --tar-blue: #1d4ed8;
        }
        .stApp {
          background: var(--tar-bg);
          color: var(--tar-text);
        }
        [data-testid="stSidebar"] {
          background: #101827;
          border-right: 1px solid #1f2a3d;
        }
        [data-testid="stSidebar"] * {
          color: #e6edf7;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
          border-radius: 6px;
          padding: 4px 8px;
          margin: 2px 0;
        }
        h1, h2, h3 {
          letter-spacing: 0;
          color: var(--tar-text);
        }
        h1 {
          font-size: 1.8rem;
          line-height: 1.16;
        }
        h2 {
          font-size: 1.35rem;
        }
        h3 {
          font-size: 1.05rem;
        }
        p, li, label, .stMarkdown, .stText, .stCaption, .stJson, .stAlert {
          font-size: 0.88rem;
          line-height: 1.35;
        }
        div[data-testid="stMetric"] {
          background: var(--tar-panel);
          border: 1px solid var(--tar-border);
          border-radius: 8px;
          padding: 10px 12px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
          min-width: 0;
          overflow-wrap: anywhere;
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
          font-size: 0.72rem;
          line-height: 1.15;
          color: var(--tar-muted);
          white-space: normal;
          overflow-wrap: anywhere;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
          font-size: clamp(0.9rem, 1.8vw, 1.35rem);
          line-height: 1.12;
          white-space: normal;
          overflow-wrap: anywhere;
        }
        .tar-hero {
          background: linear-gradient(135deg, #102033 0%, #1a365d 55%, #0f766e 100%);
          border-radius: 8px;
          color: white;
          padding: 16px 18px;
          margin: 4px 0 14px 0;
          border: 1px solid rgba(255,255,255,0.14);
        }
        .tar-hero h1 {
          color: white;
          margin: 0 0 6px 0;
          font-size: clamp(1.35rem, 2.4vw, 2rem);
          line-height: 1.12;
        }
        .tar-hero p {
          margin: 0;
          color: #dbeafe;
          font-size: 0.9rem;
          line-height: 1.32;
        }
        .tar-card {
          background: var(--tar-panel);
          border: 1px solid var(--tar-border);
          border-radius: 8px;
          padding: 12px;
          margin: 6px 0 10px 0;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
          overflow-wrap: anywhere;
        }
        .tar-card h3 {
          margin: 0 0 8px 0;
          font-size: 0.98rem;
        }
        .tar-muted {
          color: var(--tar-muted);
          font-size: 0.78rem;
          line-height: 1.32;
          overflow-wrap: anywhere;
        }
        .tar-pill {
          display: inline-flex;
          align-items: center;
          padding: 3px 7px;
          border-radius: 999px;
          font-size: 0.72rem;
          font-weight: 650;
          border: 1px solid transparent;
          white-space: normal;
          overflow-wrap: anywhere;
        }
        .tar-pill.good {
          color: var(--tar-green);
          background: #e9f8f1;
          border-color: #bbefd7;
        }
        .tar-pill.warn {
          color: var(--tar-amber);
          background: #fff7e6;
          border-color: #f4d08c;
        }
        .tar-pill.bad {
          color: var(--tar-red);
          background: #fff0ee;
          border-color: #ffc9c2;
        }
        .tar-pill.info {
          color: var(--tar-blue);
          background: #edf4ff;
          border-color: #c7dcff;
        }
        .stButton button {
          border-radius: 6px;
          border: 1px solid var(--tar-border);
          font-weight: 650;
          font-size: 0.84rem;
          min-height: 2.15rem;
          white-space: normal;
          line-height: 1.15;
        }
        .stDataFrame {
          border: 1px solid var(--tar-border);
          border-radius: 8px;
          overflow: hidden;
        }
        div[data-testid="stCodeBlock"] pre,
        code,
        pre {
          font-size: 0.76rem !important;
          line-height: 1.28 !important;
          white-space: pre-wrap !important;
          overflow-wrap: anywhere !important;
        }
        div[data-testid="stVerticalBlock"] {
          gap: 0.55rem;
        }
        div[data-testid="column"] {
          min-width: 0;
        }
        @media (max-width: 1100px) {
          .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
          }
          h1 { font-size: 1.35rem; }
          h2 { font-size: 1.12rem; }
          h3 { font-size: 0.98rem; }
          p, li, label, .stMarkdown, .stText, .stCaption, .stJson, .stAlert {
            font-size: 0.8rem;
          }
          div[data-testid="stMetric"] {
            padding: 8px 9px;
          }
          div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 0.95rem;
          }
          .tar-hero {
            padding: 12px 14px;
          }
          .tar-card {
            padding: 10px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(st: object, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="tar-hero">
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(st: object, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="tar-card">
          <h3>{escape(title)}</h3>
          <div class="tar-muted">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(st: object, label: str, state: str) -> None:
    klass = _state_class(state)
    st.markdown(f'<span class="tar-pill {klass}">{escape(label)}: {escape(state)}</span>', unsafe_allow_html=True)


def metric_row(st: object, metrics: list[tuple[str, Any, str | None]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)


def _state_class(state: str) -> str:
    upper = state.upper()
    if upper in {"SAFE_TO_TEST", "GO", "KEEP", "ONLINE", "TRUE", "PASSED"}:
        return "good"
    if upper in {"CAUTION", "REVIEW", "RETEST", "REDUCE_RISK", "REVIEW_ONLY", "UNSCORED"}:
        return "warn"
    if upper in {"BLOCK_TRADING", "HOLD_TRADING", "KILL", "NO_GO", "PAUSE", "FALSE", "FAILED"}:
        return "bad"
    return "info"
