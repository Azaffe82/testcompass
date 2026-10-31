"""Test Compass: website A/B testing workflow prototype."""

from __future__ import annotations

import json
import math
from datetime import date
from html import escape
from pathlib import Path
from statistics import NormalDist
from typing import Any

import streamlit as st


DATA_FILE = Path(__file__).with_name("test_compass_backlog.json")
PAGES = ["Test Backlog", "Test Planner", "Test Learnings"]

DEMO_SIGNAL = {
    "dimension": "First User Medium",
    "value": "organic",
    "step": "Sessions to Product View",
    "rate": 0.20953916037804968,
    "peer_rate": 0.21806373354224054,
    "eligible": 122841,
    "progressed": 25740,
    "progressed_is_estimate": False,
    "benchmark_gap": 1047,
    "is_demo": True,
}

st.set_page_config(
    page_title="Test Compass",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink:#203b37;
        --muted:#60736d;
        --line:#dfe8e3;
        --paper:#ffffff;
        --canvas:#f5f7f5;
        --green:#1d5148;
        --mint:#eaf3ee;
        --accent:#7ac7ae;
    }

    .stApp {
        background:var(--canvas);
        color:var(--ink);
    }

    [data-testid="stSidebar"] {
        background:#173f39;
    }

    [data-testid="stSidebar"] * {
        color:#eef7f3 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding:.55rem .65rem;
        border-radius:.55rem;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background:#28584f;
    }

    .block-container {
        max-width:1440px;
        padding:1.5rem 2rem 3rem;
    }

    h1,h2,h3 {
        color:var(--ink);
        letter-spacing:-.02em;
    }

    h1 {
        font-size:1.8rem;
        margin-bottom:.1rem;
    }

    h2 { font-size:1.3rem; }
    h3 { font-size:1.05rem; }

    p, [data-testid="stCaptionContainer"] {
        color:var(--muted);
    }

    .brand {
        font-size:1.3rem;
        font-weight:800;
        letter-spacing:.04em;
        line-height:1.05;
        color:#fff;
    }

    .brand small {
        display:block;
        font-size:.62rem;
        letter-spacing:.14em;
        margin-top:.45rem;
        color:#c9ded6;
    }

    .page-kicker {
        color:#56716c;
        font-size:.72rem;
        font-weight:800;
        letter-spacing:.12em;
        margin-bottom:.2rem;
    }

    .eyebrow {
        color:#6b817b;
        font-size:.68rem;
        font-weight:800;
        letter-spacing:.1em;
    }

    .signal-title {
        font-size:1.35rem;
        font-weight:750;
        color:var(--ink);
        margin:.2rem 0 .15rem;
    }

    .signal-subtitle {
        color:var(--muted);
        font-size:.88rem;
    }

    .prefill-pill {
        display:inline-block;
        background:var(--mint);
        color:#315b51;
        border-radius:99px;
        padding:.45rem .7rem;
        font-size:.67rem;
        font-weight:800;
        letter-spacing:.06em;
    }

    .signal-note {
        background:#edf5f1;
        border-left:4px solid var(--accent);
        border-radius:7px;
        padding:.65rem .8rem;
        color:#46615b;
        font-size:.84rem;
    }

    div[data-testid="stMetric"] {
        background:#f8faf8;
        border:1px solid var(--line);
        border-radius:10px;
        padding:.7rem .8rem;
        min-height:94px;
    }

    div[data-testid="stMetricLabel"] {
        color:#60736d;
        font-size:.72rem;
    }

    div[data-testid="stMetricValue"] {
        color:var(--ink);
        font-size:1.35rem;
    }

    div[data-testid="stForm"] {
        background:transparent;
        border:0;
        padding:0;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        border:1px solid #d5e0da;
        border-radius:8px;
        background:#fff;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background:var(--paper);
        border-color:var(--line) !important;
        border-radius:13px;
        padding:.95rem 1rem;
    }

    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {
        background:var(--green);
        border-color:var(--green);
        border-radius:8px;
        min-height:2.7rem;
        font-weight:700;
    }

    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background:#28675b;
        border-color:#28675b;
    }

    hr { border-color:var(--line); }

    /* Larger sidebar, retaining the original colours and design. */
    [data-testid="stSidebar"] .brand {
        font-size:1.8rem;
    }

    [data-testid="stSidebar"] .brand small {
        font-size:.85rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        font-size:18px !important;
        line-height:1.45;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        font-size:21px !important;
    }

    * Compact adjustments apply only to Test Backlog. */
    .stMain:has(#backlog-page) .block-container {
    max-width:1800px;
    padding:4.5rem 1.8rem 2rem;
    }


    .stMain:has(#backlog-page) [data-testid="stVerticalBlock"] {
    gap:.85rem;
    }

    .stMain:has(#backlog-page) h1 {
        font-size:2.1rem;
        padding:0;
        margin:0;
    }

    .stMain:has(#backlog-page) h2 {
        font-size:1.5rem;
        padding:0;
    }

    .stMain:has(#backlog-page) h3 {
        font-size:1.3rem;
        padding:0;
    }

    .stMain:has(#backlog-page) p,
    .stMain:has(#backlog-page) [data-testid="stWidgetLabel"] p {
        font-size:17px;
        line-height:1.35;
    }

    .stMain:has(#backlog-page) [data-testid="stCaptionContainer"] p {
        font-size:14px;
        line-height:1.3;
    }

    .stMain:has(#backlog-page) input,
    .stMain:has(#backlog-page) textarea {
        font-size:17px !important;
    }

    .stMain:has(#backlog-page) .signal-title {
        font-size:1.5rem;
    }

    .stMain:has(#backlog-page) .signal-subtitle {
        font-size:1rem;
    }

    .stMain:has(#backlog-page) div[data-testid="stMetric"] {
        min-height:68px;
        padding:.35rem .65rem;
    }

    .stMain:has(#backlog-page) .signal-note {
        padding:.35rem .65rem;
    }

    .stMain:has(#backlog-page)
    [data-testid="stVerticalBlockBorderWrapper"] {
        padding:.55rem .7rem;
    }

    /* Visible white text on the original green submit button. */
    .stMain:has(#backlog-page)
    [data-testid="stFormSubmitButton"] button,
    .stMain:has(#backlog-page)
    [data-testid="stFormSubmitButton"] button * {
        color:#ffffff !important;
        -webkit-text-fill-color:#ffffff !important;
        font-size:18px !important;
        font-weight:700 !important;
    }


/* Make the content wider */
.stMain:has(#backlog-page) .block-container {
    max-width: none !important;
    padding: 4.5rem 2rem 2rem !important;
}

/* Make text easier to read */
.stMain:has(#backlog-page) p,
.stMain:has(#backlog-page) [data-testid="stWidgetLabel"] p {
    font-size: 19px !important;
    line-height: 1.45 !important;
}

.stMain:has(#backlog-page) input,
.stMain:has(#backlog-page) textarea {
    font-size: 19px !important;
}

.stMain:has(#backlog-page) [data-testid="stCaptionContainer"] p {
    font-size: 16px !important;
}

.stMain:has(#backlog-page) h1 {
    font-size: 2.5rem !important;
}

.stMain:has(#backlog-page) h3 {
    font-size: 1.6rem !important;
}

.stMain:has(#backlog-page) [data-testid="stMetricValue"] {
    font-size: 2rem !important;
}

/* Larger section labels: investigation signal and test brief */
.stMain:has(#backlog-page) .eyebrow {
    font-size: 18px !important;
    font-weight: 750 !important;
    letter-spacing: .04em !important;
    line-height: 1.4 !important;
    margin-bottom: 8px !important;
}

/* Larger Test Backlog heading below the button */
.stMain:has(#backlog-page) h2 {
    font-size: 2rem !important;
    font-weight: 750 !important;
    margin-top: 12px !important;
    margin-bottom: 6px !important;
}

/* Larger, clearer text — keep the current layout */
.stMain:has(#backlog-page) p,
.stMain:has(#backlog-page) label,
.stMain:has(#backlog-page) [data-testid="stWidgetLabel"] p {
    font-size: 21px !important;
    line-height: 1.45 !important;
    color: #34534a !important;
}

.stMain:has(#backlog-page) input,
.stMain:has(#backlog-page) textarea,
.stMain:has(#backlog-page) [data-baseweb="select"] * {
    font-size: 21px !important;
}

.stMain:has(#backlog-page) [data-testid="stCaptionContainer"] p,
.stMain:has(#backlog-page) .signal-note {
    font-size: 18px !important;
    line-height: 1.45 !important;
    color: #49645b !important;
}

.stMain:has(#backlog-page) .eyebrow {
    font-size: 20px !important;
    color: #426357 !important;
}

.stMain:has(#backlog-page) .signal-subtitle {
    font-size: 21px !important;
}

.stMain:has(#backlog-page) .signal-title,
.stMain:has(#backlog-page) h3 {
    font-size: 1.8rem !important;
}

.stMain:has(#backlog-page) [data-testid="stMetricValue"] {
    font-size: 2.3rem !important;
}

.stMain:has(#backlog-page) h1 {
    font-size: 2.8rem !important;
}

.stMain:has(#backlog-page) h2 {
    font-size: 2.3rem !important;
}

/* Keep button text white */
.stMain:has(#backlog-page) [data-testid="stFormSubmitButton"] button * {
    font-size: 21px !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
}


    </style>
    """,
    unsafe_allow_html=True,
)


def load_ideas() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"Could not read the saved backlog: {exc}")
        st.stop()

    if not isinstance(data, list) or any(
        not isinstance(item, dict) for item in data
    ):
        st.error("The saved backlog must contain a list of idea records.")
        st.stop()

    return data


def save_ideas(ideas: list[dict[str, Any]]) -> bool:
    try:
        DATA_FILE.write_text(
            json.dumps(ideas, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        st.error(f"Could not save the backlog: {exc}")
        return False

    return True


def parse_number(value: Any, label: str) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None

    if not math.isfinite(parsed):
        raise ValueError(f"{label} must be finite.")

    return parsed


def parse_rate(value: Any, label: str) -> float:
    text = str(value).strip()

    if text.endswith("%"):
        parsed = parse_number(text[:-1], label) / 100
    else:
        parsed = parse_number(text, label)
        if parsed > 1:
            parsed /= 100

    if not 0 <= parsed <= 1:
        raise ValueError(f"{label} must be between 0% and 100%.")

    return parsed


def get_signal() -> dict[str, Any]:
    query = st.query_params

    signal_keys = {
        "segment_dimension",
        "segment_value",
        "step_name",
        "step_rate",
        "comparison_rate",
        "eligible_sessions",
        "progressed_sessions",
        "estimated_progression_gap",
        "opportunity_rank",
    }

    if not any(key in query for key in signal_keys):
        return DEMO_SIGNAL.copy()

    required = (
        "segment_dimension",
        "segment_value",
        "step_name",
        "step_rate",
        "comparison_rate",
        "eligible_sessions",
    )

    missing = [
        key for key in required
        if not str(query.get(key, "")).strip()
    ]

    if missing:
        st.error(
            "The selected signal is incomplete. Missing fields: "
            + ", ".join(missing)
            + "."
        )
        st.info(
            "Pass all required fields from Tableau, or open the app "
            "without URL parameters to show the default demo."
        )
        st.stop()

    try:
        eligible_number = parse_number(
            query["eligible_sessions"],
            "Sessions at step",
        )

        if eligible_number <= 0 or not eligible_number.is_integer():
            raise ValueError(
                "Sessions at step must be a positive whole number."
            )

        eligible = int(eligible_number)
        observed_rate = parse_rate(query["step_rate"], "Step rate")
        comparison_rate = parse_rate(
            query["comparison_rate"],
            "Comparison rate",
        )

        progressed_raw = query.get("progressed_sessions")
        progressed_is_estimate = progressed_raw is None

        if progressed_is_estimate:
            progressed = round(eligible * observed_rate)
        else:
            progressed_number = parse_number(
                progressed_raw,
                "Progressed sessions",
            )
            if not progressed_number.is_integer():
                raise ValueError(
                    "Progressed sessions must be a whole number."
                )
            progressed = int(progressed_number)

        if not 0 <= progressed <= eligible:
            raise ValueError(
                "Progressed sessions must be between zero "
                "and sessions at step."
            )

        calculated_gap = max(
            comparison_rate - observed_rate, 0
        ) * eligible

        gap_raw = query.get("estimated_progression_gap")
        benchmark_gap = (
            calculated_gap
            if gap_raw is None
            else parse_number(gap_raw, "Estimated progression gap")
        )

        if benchmark_gap < 0:
            raise ValueError(
                "Estimated progression gap cannot be negative."
            )

        if abs(benchmark_gap - calculated_gap) > max(
            1, eligible * 0.00001
        ):
            raise ValueError(
                "The estimated gap does not match the supplied rates "
                "and session count. Pass the underlying rate values "
                "rather than rounded display values."
            )

        if (
            not progressed_is_estimate
            and abs(progressed / eligible - observed_rate)
            > max(1 / eligible, 0.00001)
        ):
            raise ValueError(
                "The progressed count does not match "
                "the supplied step rate."
            )

    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    return {
        "dimension": str(query["segment_dimension"]),
        "value": str(query["segment_value"]),
        "step": str(query["step_name"]),
        "rate": observed_rate,
        "peer_rate": comparison_rate,
        "eligible": eligible,
        "progressed": progressed,
        "progressed_is_estimate": progressed_is_estimate,
        "benchmark_gap": round(benchmark_gap),
        "is_demo": False,
    }


def signal_finding(signal: dict[str, Any]) -> str:
    difference = (signal["peer_rate"] - signal["rate"]) * 100

    if abs(difference) < 0.000001:
        comparison = "matches the comparison rate"
    else:
        direction = "below" if difference > 0 else "above"
        comparison = (
            f"is {abs(difference):.2f} percentage points "
            f"{direction} the comparison rate"
        )

    return (
        f"{signal['dimension']} '{signal['value']} has a "
        f"{signal['step']} progression rate of {signal['rate']:.2%}, "
        f"which {comparison} ({signal['peer_rate']:.2%}). "
        "The comparison uses other named segments within the same "
        "dimension and funnel step."
    )


def score_idea(impact: int, confidence: int, effort: int) -> float:
    return round((impact * confidence) / max(effort, 1), 1)


def idea_score(idea: dict[str, Any]) -> float:
    if "priority_score" in idea:
        return float(idea["priority_score"])

    return score_idea(
        int(idea.get("impact", 1)),
        int(idea.get("confidence", 1)),
        int(idea.get("effort", 3)),
    )


def status_for(diagnosis_done: bool, confidence: int) -> str:
    if not diagnosis_done:
        return "Needs diagnosis"
    if confidence == 1:
        return "Validate evidence"
    return "Backlog"


def next_idea_id() -> str:
    used = {
        str(idea.get("id", ""))
        for idea in st.session_state.ideas
    }
    number = 1

    while f"TC-{number:03d}" in used:
        number += 1

    return f"TC-{number:03d}"


if "ideas" not in st.session_state:
    st.session_state.ideas = load_ideas()

if st.session_state.get("page") not in PAGES:
    st.session_state.page = PAGES[0]


with st.sidebar:
    st.markdown(
        """
        <div style="
            color: white;
            font-size: 30px;
            font-weight: 800;
            line-height: 1.2;
        ">
            Test Compass
        </div>
        <div style="
            color: #c9ded6;
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 2px;
            margin-top: 8px;
        ">
            AyZee
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.caption("WORKSPACE")

    st.radio(
        "Pages",
        PAGES,
        key="page",
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("From performance signals to website A/B test proposals.")
    st.caption("Backlog records are saved locally in this prototype.")


def render_signal_card(signal: dict[str, Any]) -> None:
    safe_step = escape(str(signal["step"]))
    safe_dimension = escape(str(signal["dimension"]))
    safe_value = escape(str(signal["value"]))
    difference = (signal["peer_rate"] - signal["rate"]) * 100

    with st.container(border=True):
        st.markdown(
            '<div class="eyebrow">'
            "SELECTED INVESTIGATION SIGNAL · GA4 EVIDENCE"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="signal-title">{safe_step}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="signal-subtitle">Selected segment: '
            f"<b>{safe_dimension} · {safe_value}</b></div>",
            unsafe_allow_html=True,
        )

        columns = st.columns(4)

        columns[0].metric(
            "Sessions at step",
            f"{signal['eligible']:,}",
        )
        columns[1].metric(
            "Step progression rate",
            f"{signal['rate']:.2%}",
        )
        columns[2].metric(
            "Rate gap (pp)",
            f"{difference:.2f}",
        )
        columns[3].metric(
            "Estimated gap (sessions)",
            f"{signal['benchmark_gap']:,}",
        )

        progressed_label = (
            "Approximately progressed"
            if signal["progressed_is_estimate"]
            else "Progressed sessions"
        )

        st.caption(
            f"Comparison rate: {signal['peer_rate']:.2%} · "
            f"{progressed_label}: {signal['progressed']:,}. "
            "A positive rate gap means the segment is below the comparison."
        )

        with st.expander("How to interpret this signal"):
            st.write(
                "The comparison combines other named segments within "
                "the same dimension and funnel step."
            )
            st.write(
                "Estimated gap = sessions at step × the positive "
                "difference between the comparison rate and segment rate."
            )
            st.write(
                "Source and medium describe first-user acquisition. "
                "Groups can overlap, and the named-category selection "
                "excludes obscured labels and '(none)'."
            )

        st.markdown(
            '<div class="signal-note">'
            "This signal identifies where to investigate. The estimated "
            "gap is not predicted additional purchases or test uplift. "
            "Review the relevant pages and tracking before choosing a change."
            "</div>",
            unsafe_allow_html=True,
        )


def render_backlog() -> None:
    signal = get_signal()

    st.markdown(
        '<span id="backlog-page"></span>',
        unsafe_allow_html=True,
    )
    st.title("Test Ideas")

    render_signal_card(signal)

    use_example = (
        signal["dimension"] == "First User Medium"
        and signal["value"].lower() == "organic"
        and signal["step"] == "Sessions to Product View"
    )

    example = {
        "title": "Improve product discovery from organic landing pages",
        "change": (
            "Candidate: add a clear 'Shop products' link and relevant "
            "product categories to selected landing pages."
        ),
        "hypothesis": (
            "If visitors see a clearer route to relevant products, "
            "more will view a product because the next shopping "
            "step is easier to find."
        ),
        "audience": (
            "Visitors to selected landing pages; randomise by visitor."
        ),
        "primary_metric": (
            "Share of eligible visitors viewing a product"
        ),
        "guardrail": "Visitor purchase rate; page load time",
    } if use_example else {}

    finding = signal_finding(signal)
    diagnosis = (
        "Page review required; the dashboard does not establish the cause."
    )

    with st.form("idea_form", clear_on_submit=False):
        form_col, review_col = st.columns(
            [1.65, 1],
            gap="large",
        )

        with form_col:
            with st.container(border=True):
                st.markdown(
                    '<div class="eyebrow">TEST BRIEF</div>',
                    unsafe_allow_html=True,
                )
                st.subheader("Turn the signal into a test idea")

                title = st.text_input(
                    "Working test title",
                    value=example.get("title", ""),
                )

                change_col, hypothesis_col = st.columns(2)

                with change_col:
                    change = st.text_area(
                        "Proposed website change",
                        value=example.get("change", ""),
                        height=90,
                    )

                with hypothesis_col:
                    hypothesis = st.text_area(
                        "Hypothesis",
                        value=example.get("hypothesis", ""),
                        height=90,
                    )

                field_a, field_b = st.columns(2)

                with field_a:
                    audience = st.text_input(
                        "Test eligibility",
                        value=example.get("audience", ""),
                    )
                    primary_metric = st.text_input(
                        "Primary metric",
                        value=example.get("primary_metric", ""),
                    )

                with field_b:
                    guardrail = st.text_input(
                        "Guardrail metric",
                        value=example.get("guardrail", ""),
                    )
                    owner = st.text_input(
                        "Owner",
                        placeholder="Assign person or team",
                    )

                st.caption(
                    "Draft product-discovery idea; confirm pages "
                    "and audience during review."
                    if use_example
                    else "Define a candidate change and review "
                    "the relevant pages."
                )

        with review_col:
            with st.container(border=True):
                st.markdown(
                    '<div class="eyebrow">PRIORITY AND READINESS</div>',
                    unsafe_allow_html=True,
                )
                st.subheader("Human review")

                st.caption(
                    "These ratings are separate from the dashboard signal rank."
                )
                st.markdown(
                    "**Manual prioritisation** · impact and evidence "
                    "strength: 1 low–3 high; effort: 1 low–3 high."
                )

                score_a, score_b, score_c = st.columns(3)
                choices = ["Select…", "1", "2", "3"]

                impact = score_a.selectbox(
                    "Impact",
                    choices,
                    key="impact",
                )
                confidence = score_b.selectbox(
                    "Evidence confidence",
                    choices,
                    key="confidence",
                )
                effort = score_c.selectbox(
                    "Effort",
                    choices,
                    key="effort",
                )

                diagnosis_done = st.checkbox(
                    "I reviewed the relevant page or journey"
                )

                st.caption(
                    "Priority score = impact × evidence confidence ÷ effort. "
                    "It is a sorting aid, not predicted lift or revenue."
                )

                st.markdown("**Next step**")
                st.caption(
                    "Save an unreviewed proposal as Needs diagnosis. "
                    "A reviewed proposal with evidence confidence of at "
                    "least 2/3 can move to Test Planner."
                )

        submitted = st.form_submit_button(
            "Add idea to test backlog",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        required = (
            ("Working test title", title),
            ("Proposed website change", change),
            ("Hypothesis", hypothesis),
            ("Test eligibility", audience),
            ("Primary metric", primary_metric),
        )

        missing = [
            label for label, value in required
            if not value.strip()
        ]

        if "Select…" in (impact, confidence, effort):
            missing.append("all three priority ratings")

        if missing:
            st.error(
                "Complete before saving: "
                + ", ".join(missing)
                + "."
            )
        else:
            impact_n = int(impact)
            confidence_n = int(confidence)
            effort_n = int(effort)

            saved = {
                "id": next_idea_id(),
                "title": title.strip(),
                "finding": finding,
                "diagnosis": diagnosis,
                "diagnosis_done": diagnosis_done,
                "change": change.strip(),
                "hypothesis": hypothesis.strip(),
                "audience": audience.strip(),
                "primary_metric": primary_metric.strip(),
                "guardrail": guardrail.strip(),
                "owner": owner.strip(),
                "impact": impact_n,
                "confidence": confidence_n,
                "effort": effort_n,
                "priority_score": score_idea(
                    impact_n,
                    confidence_n,
                    effort_n,
                ),
                "priority": "Needs review",
                "status": status_for(
                    diagnosis_done,
                    confidence_n,
                ),
                "signal": signal.copy(),
                "created": date.today().isoformat(),
            }

            updated_ideas = [
                *st.session_state.ideas,
                saved,
            ]

            if save_ideas(updated_ideas):
                st.session_state.ideas = updated_ideas
                st.success(
                    f"{saved['id']} added to the test backlog."
                )

    st.markdown("## Test backlog")
    st.caption(
        "Sorted by manual priority score, separately "
        "from Tableau's investigation ranking."
    )

    ideas = sorted(
        st.session_state.ideas,
        key=lambda item: (
            -idea_score(item),
            item.get("created", ""),
        ),
    )

    if not ideas:
        st.info("No saved ideas yet. Add your first proposal above.")
        return

    rows = []

    for index, idea in enumerate(ideas, start=1):
        idea_signal = idea.get("signal", {})

        rows.append(
            {
                "Priority order": index,
                "Test idea": (
                    f"{idea.get('title', 'Untitled')} · "
                    f"{idea.get('id', '')}"
                ),
                "Signal": (
                    f"{idea_signal.get('dimension', '')}: "
                    f"{idea_signal.get('value', '')} · "
                    f"{idea_signal.get('step', '')}"
                ),
                "Priority score": idea_score(idea),
                "Status": idea.get("status", "Backlog"),
                "Owner": idea.get("owner", "") or "Unassigned",
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        height=140,
    )

    ready = [
        item for item in ideas
        if item.get("status") == "Backlog"
        and item.get("diagnosis_done")
        and int(item.get("confidence", 0)) >= 2
    ]

    if ready:
        labels = {
            f"{item.get('id')} · {item.get('title')}": item.get("id")
            for item in ready
        }

        selected = st.selectbox(
            "Move a reviewed idea to Test Planner",
            list(labels),
        )

        if st.button(
            "Move selected idea to Test Planner",
            type="primary",
        ):
            selected_id = labels[selected]

            updated_ideas = [
                {**item, "status": "Ready for planning"}
                if item.get("id") == selected_id
                else item.copy()
                for item in st.session_state.ideas
            ]

            if save_ideas(updated_ideas):
                st.session_state.ideas = updated_ideas
                st.rerun()
    else:
        st.caption(
            "Planning requires a reviewed diagnosis and "
            "evidence confidence of at least 2/3."
        )


def render_planner() -> None:
    st.markdown(
        '<div class="page-kicker">TEST PLANNER</div>',
        unsafe_allow_html=True,
    )
    st.title("Plan an experiment")
    st.caption(
        "Review a proposal and estimate sample requirements before launch. "
        "This prototype does not deploy experiments."
    )

    ready = [
        item for item in st.session_state.ideas
        if item.get("status") == "Ready for planning"
    ]

    left, right = st.columns([1.2, 1], gap="large")

    with left, st.container(border=True):
        st.markdown(
            '<div class="eyebrow">PLANNING QUEUE</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Moved from Test Backlog")

        selected_idea = None

        if ready:
            labels = {
                f"{item.get('id')} · {item.get('title')}": item
                for item in ready
            }
            choice = st.selectbox("Select a test", list(labels))
            selected_idea = labels[choice]

            st.markdown(
                f"**Hypothesis**  \n"
                f"{selected_idea.get('hypothesis', '')}"
            )
            st.caption(
                f"Eligibility: {selected_idea.get('audience', '—')} · "
                f"Primary metric: "
                f"{selected_idea.get('primary_metric', selected_idea.get('metric', '—'))}"
            )

            if selected_idea.get("guardrail"):
                st.caption(
                    f"Guardrail: {selected_idea['guardrail']}"
                )
        else:
            st.info(
                "Move a reviewed idea from Test Backlog to start planning."
            )

        st.divider()
        st.markdown("**Schedule and ownership**")
        st.caption(
            "Preview only: schedule fields are not saved in this prototype."
        )

        dates_a, dates_b = st.columns(2)
        idea_key = (
            str(selected_idea.get("id"))
            if selected_idea
            else "empty"
        )

        with dates_a:
            st.date_input(
                "Planned start",
                value=date.today(),
                disabled=not bool(ready),
                key=f"start_{idea_key}",
            )

        with dates_b:
            st.date_input(
                "Planned end",
                value=date.today(),
                disabled=not bool(ready),
                key=f"end_{idea_key}",
            )

        st.text_input(
            "Owner",
            value=(
                str(selected_idea.get("owner", ""))
                if selected_idea
                else ""
            ),
            disabled=not bool(ready),
            key=f"owner_{idea_key}",
        )

    with right, st.container(border=True):
        st.markdown(
            '<div class="eyebrow">POWER AND DURATION</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Sample feasibility")
        st.caption(
            "Illustrative inputs. Approximate two-arm calculation for "
            "a binary conversion metric, with equal allocation "
            "and independent visitors."
        )

        baseline_pct = st.number_input(
            "Baseline conversion rate (%)",
            min_value=0.01,
            max_value=99.0,
            value=2.0,
            step=0.1,
        )
        mde_pp = st.number_input(
            "Minimum detectable effect (percentage points)",
            min_value=0.01,
            max_value=50.0,
            value=0.5,
            step=0.1,
        )
        alpha = st.selectbox(
            "Significance level",
            [0.05, 0.01],
            format_func=lambda value: f"{value:.2f}",
        )
        power = st.selectbox(
            "Target power",
            [0.80, 0.90],
            format_func=lambda value: f"{value:.0%}",
        )
        eligible_per_month = st.number_input(
            "Eligible unique visitors per month",
            min_value=0,
            value=10000,
            step=1000,
        )
        st.caption(
            "Use the audience and metric of the proposed experiment. "
            "Dashboard session counts are not unique visitor counts."
        )

        p0 = baseline_pct / 100
        p1 = p0 + mde_pp / 100

        if p1 >= 1:
            st.error(
                "Baseline plus the minimum detectable effect "
                "must be below 100%."
            )
        else:
            z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
            z_power = NormalDist().inv_cdf(power)
            p_bar = (p0 + p1) / 2

            numerator = (
                z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
                + z_power
                * math.sqrt(
                    p0 * (1 - p0) + p1 * (1 - p1)
                )
            )

            per_arm = math.ceil(
                (numerator / (p1 - p0)) ** 2
            )
            total_sample = 2 * per_arm
            weeks = (
                total_sample / eligible_per_month * 4.345
                if eligible_per_month
                else None
            )

            st.metric(
                "Required sample",
                f"{total_sample:,} visitors",
            )
            st.caption(
                f"{per_arm:,} per arm with a 50/50 allocation."
            )

            if weeks is None:
                st.warning(
                    "Enter monthly eligible traffic to estimate duration."
                )
            else:
                st.metric(
                    "Estimated run time",
                    f"{weeks:.1f} weeks",
                )

            st.caption(
                "Planning approximation, not a launch decision. "
                "Confirm assumptions in a validated experiment calculator, "
                "allow full business cycles and do not stop early "
                "based on interim significance."
            )


def render_learnings() -> None:
    st.markdown(
        '<div class="page-kicker">TEST LEARNINGS</div>',
        unsafe_allow_html=True,
    )
    st.title("Results and learnings")
    st.caption(
        "Document experiment outcomes and make previous decisions reusable."
    )

    result_col, previous_col = st.columns(
        [1, 1.4],
        gap="large",
    )

    with result_col, st.container(border=True):
        st.markdown(
            '<div class="eyebrow">RESULT ENTRY</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Learning to record")
        st.markdown(
            "- Control and treatment conversion rates\n"
            "- Absolute and relative lift\n"
            "- Confidence interval and p-value\n"
            "- Guardrail impact\n"
            "- Decision and follow-up learning"
        )
        st.info(
            "Results entry is a prototype placeholder. "
            "No experiment results are entered or saved here yet."
        )

    with previous_col, st.container(border=True):
        st.markdown(
            '<div class="eyebrow">TEST HISTORY</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Previous tests")
        st.caption(
            "Test · dates · hypothesis · primary metric · result · decision"
        )
        st.info(
            "No completed experiments are recorded in this demo."
        )


if st.session_state.page == "Test Backlog":
    render_backlog()
elif st.session_state.page == "Test Planner":
    render_planner()
else:
    render_learnings()
    