"""Streamlit dashboard for ShopFlow analytics."""

import os
import re
import subprocess
import sys
import uuid

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns
import streamlit as st

from agents import run_recorder
from agents.analytics_engine import AnalyticsEngine
from db.database import execute_sql, get_engine

DB_PATH = "output/shopflow.db"
# Bump when the sample data content changes, so a hosted deploy that still
# has an old database on disk rebuilds it instead of serving stale data.
DATA_VERSION = "2"
VERSION_PATH = DB_PATH + ".version"
COLORS = ["#1f77b4", "#2ca02c", "#17becf", "#ff7f0e", "#9467bd", "#d62728"]

sns.set_style("whitegrid")
st.set_page_config(page_title="ShopFlow Analytics", layout="wide")


def build_demo_db():
    """Generate sample data and run the ETL pipeline to create the demo DB.

    Used by hosted deploys (e.g. Streamlit Cloud) where the database is not
    pre-built. Locally, prefer `python main.py --generate`.

    The pipeline writes to a unique temporary file that is then atomically
    moved into place, so the live database file is never left half-built.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    generator = os.path.join(repo_dir, "data", "generate_sample_data.py")

    subprocess.run([sys.executable, generator], check=True, cwd=repo_dir)

    from agents.orchestrator import PipelineOrchestrator

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tmp_path = f"{DB_PATH}.{uuid.uuid4().hex}.tmp"
    PipelineOrchestrator(
        data_dir=os.path.join(repo_dir, "data"),
        db_path=tmp_path,
        mode="full",
    ).run()
    os.replace(tmp_path, DB_PATH)
    with open(VERSION_PATH, "w") as f:
        f.write(DATA_VERSION)


def _demo_db_is_current():
    """True only if a database built for the current DATA_VERSION exists."""
    if not os.path.exists(DB_PATH) or not os.path.exists(VERSION_PATH):
        return False
    with open(VERSION_PATH) as f:
        return f.read().strip() == DATA_VERSION


@st.cache_resource(
    show_spinner=(
        "First-time setup: generating sample data and running the ETL "
        "pipeline. This takes ~30 seconds and only happens once per deploy."
    )
)
def ensure_demo_db():
    """Build the demo database exactly once per process.

    st.cache_resource runs this a single time and makes concurrent sessions
    wait for the first build to finish, which prevents two builds from racing
    on the same SQLite file (the cause of duplicate-key errors on cold start).
    Rebuilds when the on-disk database predates the current DATA_VERSION.
    """
    if not _demo_db_is_current():
        build_demo_db()
    return DB_PATH


def check_db():
    try:
        ensure_demo_db()
    except Exception as exc:
        import traceback

        st.error(f"Failed to build demo database: {exc}")
        st.code(traceback.format_exc(), language="text")
        st.stop()


@st.cache_data(ttl=300)
def load_query(query_name: str) -> pd.DataFrame:
    engine = AnalyticsEngine(DB_PATH)
    return engine.execute_query(query_name)


@st.cache_data(ttl=300)
def load_kpis() -> dict:
    engine = AnalyticsEngine(DB_PATH)
    return engine.get_kpis()


@st.cache_data(ttl=300)
def run_raw_sql(sql: str) -> pd.DataFrame:
    engine = AnalyticsEngine(DB_PATH)
    return engine.execute_raw(sql)


def show_fig(fig):
    """Render a matplotlib figure and close it.

    Streamlit reruns the whole script on every interaction, so figures that
    are not closed accumulate in matplotlib's global registry and leak
    memory (the "More than 20 figures have been opened" warning).
    """
    st.pyplot(fig)
    plt.close(fig)


FORBIDDEN_SQL_KEYWORDS = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "PRAGMA",
        "VACUUM",
    }
)


def validate_readonly_sql(sql: str) -> str | None:
    """Return an error message if the SQL is not a single read-only SELECT.

    Uses an allowlist (must start with SELECT/WITH), rejects multiple
    statements, and blocks writing keywords anywhere as defense in depth,
    so leading whitespace or a trailing statement cannot slip a write past.
    """
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        return None
    if ";" in stripped:
        return "Please run a single SELECT statement."
    upper = stripped.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return "Only SELECT queries are allowed."
    tokens = set(re.findall(r"[A-Za-z_]+", upper))
    if FORBIDDEN_SQL_KEYWORDS & tokens:
        return "Only read-only SELECT queries are allowed."
    return None


def page_overview():
    st.header("Executive Overview")

    kpis = load_kpis()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", f"{kpis['total_revenue'] / 1e6:.2f}M")
    c2.metric("Total Orders", f"{int(kpis['total_orders']):,}")
    c3.metric("Avg Order Value", f"{kpis['avg_order_value']:,.2f}")
    c4.metric("Unique Customers", f"{int(kpis['unique_customers']):,}")
    c5.metric("Return Rate", f"{kpis['return_rate']:.1f}%")

    st.subheader("Monthly Revenue Trend")
    df = load_query("revenue_trends")
    fig, ax = plt.subplots(figsize=(12, 4))
    labels = [f"{row['month_name'][:3]} {row['year']}" for _, row in df.iterrows()]
    ax.plot(range(len(df)), df["revenue"], color=COLORS[0], linewidth=2)
    ax.fill_between(range(len(df)), df["revenue"], alpha=0.15, color=COLORS[0])
    ax.set_xticks(range(0, len(df), max(1, len(df) // 12)))
    ax.set_xticklabels([labels[i] for i in range(0, len(df), max(1, len(df) // 12))], rotation=45)
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax.set_ylabel("Revenue")
    plt.tight_layout()
    show_fig(fig)

    st.subheader("Revenue by Category")
    cat_df = run_raw_sql("""
        SELECT p.category, ROUND(SUM(f.total_amount), 2) AS revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY revenue DESC
    """)
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.barh(cat_df["category"], cat_df["revenue"], color=COLORS[: len(cat_df)])
    ax2.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax2.set_xlabel("Revenue")
    plt.tight_layout()
    show_fig(fig2)


def page_customers():
    st.header("Customer Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("RFM Segments")
        rfm = load_query("rfm_segmentation")
        seg_counts = rfm["segment"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(
            seg_counts.values,
            labels=seg_counts.index,
            autopct="%1.1f%%",
            colors=COLORS[: len(seg_counts)],
        )
        plt.tight_layout()
        show_fig(fig)

    with col2:
        st.subheader("Cohort Retention")
        cohort = load_query("cohort_retention")
        if (
            not cohort.empty
            and "cohort_month" in cohort.columns
            and "months_since_first" in cohort.columns
        ):
            pivot = cohort.pivot_table(
                index="cohort_month",
                columns="months_since_first",
                values="active_customers",
                aggfunc="sum",
            )
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax2)
            ax2.set_title("Active Customers by Cohort")
            plt.tight_layout()
            show_fig(fig2)
        else:
            st.info("Cohort data not available.")

    st.subheader("Top 20 Customers by Lifetime Value")
    ltv = load_query("customer_ltv")
    top20 = ltv.head(20)
    if "customer_id" in top20.columns and "total_spent" in top20.columns:
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        ax3.bar(range(len(top20)), top20["total_spent"], color=COLORS[0])
        ax3.set_xticks(range(len(top20)))
        ax3.set_xticklabels(top20["customer_id"], rotation=45, ha="right")
        ax3.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        ax3.set_ylabel("Lifetime Value")
        plt.tight_layout()
        show_fig(fig3)


def page_products():
    st.header("Product & Supply Chain")

    st.subheader("Top Products by Category")
    top_prod = load_query("top_products_by_category")
    st.dataframe(top_prod, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ABC Analysis")
        abc = load_query("abc_analysis")
        if "abc_class" in abc.columns:
            abc_counts = abc["abc_class"].value_counts().reindex(["A", "B", "C"])
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar(abc_counts.index, abc_counts.values, color=[COLORS[0], COLORS[1], COLORS[2]])
            ax.set_ylabel("Number of Products")
            ax.set_xlabel("ABC Class")
            plt.tight_layout()
            show_fig(fig)

    with col2:
        st.subheader("Return Rate by Category")
        ret = load_query("return_rate_analysis")
        if not ret.empty and "category" in ret.columns:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.barh(ret["category"], ret["return_rate_pct"], color=COLORS[3])
            ax2.set_xlabel("Return Rate (%)")
            plt.tight_layout()
            show_fig(fig2)

    st.subheader("Supplier Scorecard")
    supp = load_query("supplier_scorecard")
    st.dataframe(supp, use_container_width=True)


def page_quality():
    st.header("Data Quality")

    eng = get_engine(DB_PATH)

    try:
        sources = execute_sql(
            "SELECT source, COUNT(*) as issues FROM data_quality_issues GROUP BY source",
            engine=eng,
        )
    except Exception:
        st.info("No quality data available. Run the pipeline first.")
        return

    total_issues = sum(r["issues"] for r in sources) if sources else 0
    total_rows = execute_sql("SELECT COUNT(*) as cnt FROM fact_sales", engine=eng)
    total = total_rows[0]["cnt"] if total_rows else 0

    score = round((1 - total_issues / max(total + total_issues, 1)) * 100, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Quality Score", f"{score}%")
    c2.metric("Total Issues", f"{total_issues:,}")
    c3.metric("Rows Loaded", f"{total:,}")

    if sources:
        st.subheader("Issues by Source")
        src_df = pd.DataFrame(sources)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(src_df["source"], src_df["issues"], color=COLORS[0])
        ax.set_ylabel("Issues")
        plt.tight_layout()
        show_fig(fig)

    st.subheader("Recent Issues")
    issues = execute_sql(
        "SELECT source, field, rule, message, value FROM data_quality_issues LIMIT 50",
        engine=eng,
    )
    if issues:
        st.dataframe(pd.DataFrame(issues), use_container_width=True)
    else:
        st.success("No data quality issues found.")


def page_sql_explorer():
    st.header("SQL Explorer")

    engine = AnalyticsEngine(DB_PATH)
    queries = engine.get_available_queries()

    st.subheader("Pre-built Queries")
    selected = st.selectbox("Select a query", [""] + queries)
    if selected:
        filepath = os.path.join(engine.sql_dir, f"{selected}.sql")
        with open(filepath) as f:
            sql_text = f.read()
        with st.expander("View SQL", expanded=False):
            st.code(sql_text, language="sql")
        if st.button("Execute Query"):
            df = engine.execute_query(selected)
            st.dataframe(df, use_container_width=True)

    st.subheader("Custom SQL")
    custom_sql = st.text_area(
        "Enter SQL query (read-only)", height=150, placeholder="SELECT * FROM fact_sales LIMIT 10"
    )
    if st.button("Run Custom SQL"):
        error = validate_readonly_sql(custom_sql)
        if error:
            st.error(error)
        elif custom_sql.strip():
            try:
                df = engine.execute_raw(custom_sql.strip().rstrip(";").strip())
                st.dataframe(df, use_container_width=True)
            except (ValueError, TypeError) as exc:
                st.error(f"Invalid query: {exc}")
            except Exception as exc:
                st.error(f"Query failed: {exc}")


def page_pipeline_runs():
    st.header("Pipeline Runs")
    st.caption("Observability for the orchestrator — each run is logged to the etl_runs table.")

    runs = run_recorder.list_runs(DB_PATH, limit=50)
    if not runs:
        st.info(
            "No runs recorded yet. Trigger a pipeline run via `python main.py` "
            "(or the auto-build on first start) and refresh this page."
        )
        return

    df = pd.DataFrame(runs)
    df["started_at"] = pd.to_datetime(df["started_at"])
    df["finished_at"] = pd.to_datetime(df["finished_at"])

    # KPI strip
    total_runs = len(df)
    success_runs = int((df["status"] == "success").sum())
    failed_runs = int((df["status"] == "failed").sum())
    success_rate = (success_runs / total_runs * 100) if total_runs else 0.0
    avg_duration = df["duration_seconds"].dropna().mean() if not df.empty else 0.0

    cols = st.columns(4)
    cols[0].metric("Total runs", total_runs)
    cols[1].metric("Success rate", f"{success_rate:.0f}%")
    cols[2].metric("Failures", failed_runs)
    cols[3].metric("Avg duration", f"{avg_duration:.2f}s" if avg_duration else "-")

    # Trend
    if df["duration_seconds"].notna().sum() >= 2:
        st.subheader("Duration over time")
        trend_df = df.sort_values("started_at").set_index("started_at")[["duration_seconds"]]
        st.line_chart(trend_df)

    # Table
    st.subheader("Recent runs")
    display_cols = [
        "run_id",
        "started_at",
        "duration_seconds",
        "mode",
        "status",
        "quality_score",
        "error_message",
    ]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    # Latest-run drill-down
    latest = df.iloc[0]
    st.subheader(f"Run #{latest['run_id']} — phase breakdown")
    timings = latest.get("phase_timings") or {}
    if timings:
        timings_df = pd.DataFrame(
            {"phase": list(timings.keys()), "seconds": list(timings.values())}
        )
        st.bar_chart(timings_df.set_index("phase"))
    else:
        st.caption("No per-phase timings recorded for the latest run.")


def render_footer():
    st.divider()
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:0.85rem;'>"
        "Built by Eugen Goebel &middot; "
        "<a href='https://github.com/eugen-goebel' target='_blank'>GitHub</a> &middot; "
        "<a href='https://www.linkedin.com/in/eugen-goebel/' target='_blank'>LinkedIn</a>"
        "</div>",
        unsafe_allow_html=True,
    )


def main():
    check_db()

    st.sidebar.title("ShopFlow Analytics")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Overview",
            "Customer Analytics",
            "Product & Supply Chain",
            "Data Quality",
            "Pipeline Runs",
            "SQL Explorer",
        ],
    )

    pages = {
        "Executive Overview": page_overview,
        "Customer Analytics": page_customers,
        "Product & Supply Chain": page_products,
        "Data Quality": page_quality,
        "Pipeline Runs": page_pipeline_runs,
        "SQL Explorer": page_sql_explorer,
    }
    pages[page]()
    render_footer()


if __name__ == "__main__":
    main()
