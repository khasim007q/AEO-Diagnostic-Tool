# app.py
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from llm_engine import query_all_llms
from parser import parse_llm_response
from serp_engine import get_google_results
from scorer import (
    score_brands,
    calculate_consistency,
    cross_validate_with_google,
    get_brand_report,
    calculate_grade,
    generate_insights,
)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="AEO Diagnostic", page_icon="\U0001f50d", layout="wide")

# ─── Custom CSS for Premium Look ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    .hero-header h1 {
        color: white;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }

    /* Grade card */
    .grade-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.05);
    }
    .grade-letter {
        font-size: 96px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    .grade-label {
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
    }

    /* Stat cards */
    .stat-card {
        background: linear-gradient(145deg, #1e1e30, #252545);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stat-card .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #a78bfa;
    }
    .stat-card .stat-label {
        font-size: 13px;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }

    /* Insight items */
    .insight-item {
        background: rgba(255,255,255,0.03);
        border-left: 3px solid #667eea;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(102,126,234,0.3);
        color: #e2e8f0;
    }

    /* Google result cards */
    .google-result {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.06);
        transition: border-color 0.2s ease;
    }
    .google-result:hover {
        border-color: rgba(102,126,234,0.4);
    }
    .google-result .gr-rank {
        color: #667eea;
        font-weight: 700;
        font-size: 14px;
    }
    .google-result .gr-title {
        font-weight: 600;
        font-size: 15px;
        color: #e2e8f0;
        margin-top: 2px;
    }
    .google-result .gr-snippet {
        font-size: 13px;
        color: rgba(255,255,255,0.5);
        margin-top: 4px;
        line-height: 1.4;
    }
    .google-result .gr-url {
        font-size: 12px;
        color: #667eea;
        margin-top: 4px;
        word-break: break-all;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* DataFrame styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ─── Hero Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>\U0001f50d AEO Diagnostic Tool</h1>
    <p>See how your product ranks across GPT, Claude, and Gemini — vs real Google results</p>
</div>
""", unsafe_allow_html=True)

# ─── Input Section ────────────────────────────────────────────────────────────
col_input1, col_input2 = st.columns([2, 1])

with col_input1:
    query = st.text_input(
        "Enter your product query",
        placeholder="e.g. best magnesium supplement for seniors"
    )

with col_input2:
    your_brand = st.text_input(
        "Your brand name (optional)",
        placeholder="e.g. Nature's Best"
    ).strip().lower()

run = st.button("\U0001f680 Run Diagnostic", type="primary", width="stretch")

# ─── Main Execution ──────────────────────────────────────────────────────────
if run and query:
    # --- Query Phase ---
    with st.status("\U0001f504 Running AEO Diagnostic...", expanded=True) as status:
        st.write("\U0001f916 Querying GPT-5-mini, Claude Sonnet 4, and Gemini 2.5 Flash in parallel...")
        llm_raw = query_all_llms(query)

        st.write("\U0001f310 Searching Google via SerpApi...")
        google_results = get_google_results(query)

        st.write("\U0001f9e0 Parsing brand mentions (JSON → regex fallback)...")
        llm_parsed = {}
        for llm_name, result in llm_raw.items():
            llm_parsed[llm_name] = parse_llm_response(
                raw_text=result["raw"],
                json_brands=result["parsed"]
            )

        st.write("\U0001f4ca Scoring and cross-validating...")
        scored = score_brands(llm_parsed)
        scored = cross_validate_with_google(scored, google_results)
        llm_names = list(llm_raw.keys())

        status.update(label="\u2705 Diagnostic complete!", state="complete", expanded=False)

    # --- Build Report ---
    report = get_brand_report(scored, your_brand, llm_names)
    grade, grade_label = calculate_grade(report["your_brand"], llm_names)
    insights = generate_insights(
        report["your_brand"],
        report["competitors"],
        llm_names,
        your_brand
    )

    # ─── Grade Card Section ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f3af Your AEO Score</div>', unsafe_allow_html=True)

    grade_colors = {"A": "#22c55e", "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444", "F": "#dc2626"}
    color = grade_colors.get(grade, "#6b7280")

    col_grade, col_stats, col_insights = st.columns([1, 1.5, 2.5])

    with col_grade:
        st.markdown(f"""
        <div class="grade-card">
            <div class="grade-letter" style="color: {color};">{grade}</div>
            <div class="grade-label" style="color: {color};">{grade_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stats:
        if report["your_brand"]:
            yd = report["your_brand"]
            mentions = sum(1 for llm in llm_names if llm in yd["scores"])
            web_status = "\u2705 Yes" if yd.get("web_validated") else "\u274c No"

            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{yd["total"]}<span style="font-size:16px; opacity:0.5"> / 15</span></div>
                <div class="stat-label">Total AEO Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{mentions}<span style="font-size:16px; opacity:0.5"> / 3</span></div>
                <div class="stat-label">AI Engines Mentioning You</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{web_status}</div>
                <div class="stat-label">Web Validated</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if your_brand:
                st.warning(f"**'{your_brand}'** was not found in any AI response.")
                st.markdown("Try checking the brand name spelling or run with a broader query.")
            else:
                st.info("Enter your brand name above to see your personalized AEO grade.")

    with col_insights:
        st.markdown("**\U0001f4cb Key Insights**")
        for insight in insights:
            st.markdown(f'<div class="insight-item">{insight}</div>', unsafe_allow_html=True)

    # ─── Score Comparison Chart ───────────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f4ca Brand Score Comparison</div>', unsafe_allow_html=True)

    if report["all_brands"]:
        chart_data = []
        for brand in report["all_brands"][:8]:
            for llm in llm_names:
                chart_data.append({
                    "Brand": brand["display_name"][:25],
                    "LLM": llm,
                    "Score": brand["scores"].get(llm, 0)
                })

        chart_df = pd.DataFrame(chart_data)
        pivot_df = chart_df.pivot_table(index="Brand", columns="LLM", values="Score", aggfunc="max").fillna(0)

        # Sort by total score
        pivot_df["_total"] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values("_total", ascending=True)
        pivot_df = pivot_df.drop(columns=["_total"])

        st.bar_chart(pivot_df, horizontal=True, width="stretch")

    # ─── Full Competitive Report Card ─────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f4ca Full Competitive Report Card</div>', unsafe_allow_html=True)

    rows = []
    for brand in report["all_brands"][:8]:
        name = brand["display_name"]
        is_you = your_brand and your_brand in name.lower()
        row = {
            "Brand": f"\u2b50 {name} (YOU)" if is_you else name,
        }
        for llm in llm_names:
            row[f"{llm} Score"] = brand["scores"].get(llm, 0)
        row["Total Score"] = brand["total"]
        row["AI Consensus"] = f"{calculate_consistency(brand, llm_names)}%"
        row["Web Validated"] = "\u2705" if brand.get("web_validated") else "\u274c"
        rows.append(row)

    df = pd.DataFrame(rows)

    def highlight_your_brand(row):
        if "(YOU)" in str(row["Brand"]):
            return ["background-color: rgba(102, 126, 234, 0.15)"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_your_brand, axis=1),
        width="stretch",
        hide_index=True
    )

    # ─── Gap Analysis ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f50d Competitor Gap Analysis</div>', unsafe_allow_html=True)

    if report["your_brand"] and report["competitors"]:
        yd = report["your_brand"]
        gap_rows = []
        for comp in report["competitors"][:5]:
            for llm in llm_names:
                your_score = yd["scores"].get(llm, 0)
                comp_score = comp["scores"].get(llm, 0)
                diff = your_score - comp_score
                gap_rows.append({
                    "Competitor": comp["display_name"],
                    "LLM": llm,
                    "Your Score": your_score,
                    "Their Score": comp_score,
                    "Gap": diff,
                    "Status": "\u2705 Winning" if diff > 0 else ("\U0001f7e1 Tied" if diff == 0 else "\u274c Losing")
                })

        gap_df = pd.DataFrame(gap_rows)
        st.dataframe(gap_df, width="stretch", hide_index=True)
    else:
        st.info("Enter your brand name above to see gap analysis against competitors.")

    # ─── Raw LLM Responses ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f916 Raw LLM Responses</div>', unsafe_allow_html=True)
    tabs = st.tabs(list(llm_raw.keys()))
    for tab, (llm_name, result) in zip(tabs, llm_raw.items()):
        with tab:
            raw_text = result["raw"]
            parsed = result["parsed"]
            st.markdown(raw_text)
            if parsed:
                st.caption(f"✅ JSON parsed successfully — {len(parsed)} brands extracted")
            else:
                st.caption("⚠️ JSON parse failed — used regex fallback")

    # ─── Google Validation ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">\U0001f310 Top Google Results</div>', unsafe_allow_html=True)
    for r in google_results[:5]:
        st.markdown(f"""
        <div class="google-result">
            <div class="gr-rank">#{r['rank']}</div>
            <div class="gr-title">{r['title']}</div>
            <div class="gr-snippet">{r['snippet']}</div>
            <div class="gr-url"><a href="{r['url']}" target="_blank">{r['url']}</a></div>
        </div>
        """, unsafe_allow_html=True)

elif run and not query:
    st.warning("Please enter a product query to run the diagnostic.")
