"""Streamlit dashboard for ShopFlow analytics."""

import os
import subprocess
import sys
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

from agents.analytics_engine import AnalyticsEngine
from db.database import get_engine, execute_sql

DB_PATH = "output/shopflow.db"
COLORS = ["#1f77b4", "#2ca02c", "#17becf", "#ff7f0e", "#9467bd", "#d62728"]

sns.set_style("whitegrid")
st.set_page_config(page_title="ShopFlow Analytics", layout="wide")


def build_demo_db():
    """Generate sample data and run the ETL pipeline to create the demo DB.

    Used by hosted deploys (e.g. Streamlit Cloud) where the database is not
    pre-built. Locally, prefer `python main.py --generate`.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    generator = os.path.join(repo_dir, "data", "generate_sample_data.py")

    subprocess.run([sys.executable, generator], check=True, cwd=repo_dir)

    from agents.orchestrator import PipelineOrchestrator

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    orchestrator = PipelineOrchestrator(
        data_dir=os.path.join(repo_dir, "data"),
        db_path=DB_PATH,
        mode="full",
    )
    orchestrator.run()


def check_db():
    if os.path.exists(DB_PATH):
        return

    with st.spinner(
        "First-time setup: generating sample data and running the ETL "
        "pipeline. This takes ~30 seconds and only happens once per deploy."
    ):
        try:
            build_demo_db()
        except Exception as exc:
            import traceback
            st.error(f"Failed to build demo database: {exc}")
            st.code(traceback.format_exc(), language="text")
            st.stop()
    st.rerun()


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


def page_overview():
    st.header("Executive Overview")

    kpis = load_kpis()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", f"{kpis['total_revenue']:,.2f}")
    c2.metric("Total Orders", f"{kpis['total_orders']:,}")
    c3.metric("Avg Order Value", f"{kpis['avg_order_value']:,.2f}")
    c4.metric("Unique Customers", f"{kpis['unique_customers']:,}")
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
    st.pyplot(fig)

    st.subheader("Revenue by Category")
    cat_df = run_raw_sql("""
        SELECT p.category, ROUND(SUM(f.total_amount), 2) AS revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY revenue DESC
    """)
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.barh(cat_df["category"], cat_df["revenue"], color=COLORS[:len(cat_df)])
    ax2.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax2.set_xlabel("Revenue")
    plt.tight_layout()
    st.pyplot(fig2)


def page_customers():
    st.header("Customer Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("RFM Segments")
        rfm = load_query("rfm_segmentation")
        seg_counts = rfm["segment"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(seg_counts.values, labels=seg_counts.index, autopct="%1.1f%%",
               colors=COLORS[:len(seg_counts)])
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("Cohort Retention")
        cohort = load_query("cohort_retention")
        if not cohort.empty and "cohort_month" in cohort.columns and "months_since_first" in cohort.columns:
            pivot = cohort.pivot_table(
                index="cohort_month", columns="months_since_first",
                values="active_customers", aggfunc="sum"
            )
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax2)
            ax2.set_title("Active Customers by Cohort")
            plt.tight_layout()
            st.pyplot(fig2)
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
        st.pyplot(fig3)


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
            st.pyplot(fig)

    with col2:
        st.subheader("Return Rate by Category")
        ret = load_query("return_rate_analysis")
        if not ret.empty and "category" in ret.columns:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.barh(ret["category"], ret["return_rate_pct"], color=COLORS[3])
            ax2.set_xlabel("Return Rate (%)")
            plt.tight_layout()
            st.pyplot(fig2)

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
        st.pyplot(fig)

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
    custom_sql = st.text_area("Enter SQL query (read-only)", height=150, placeholder="SELECT * FROM fact_sales LIMIT 10")
    if st.button("Run Custom SQL"):
        sql_stripped = custom_sql.strip().upper()
        forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "DETACH", "PRAGMA")
        if any(sql_stripped.startswith(kw) for kw in forbidden):
            st.error("Only SELECT queries are allowed.")
        elif custom_sql.strip():
            try:
                df = engine.execute_raw(custom_sql)
                st.dataframe(df, use_container_width=True)
            except (ValueError, TypeError) as exc:
                st.error(f"Invalid query: {exc}")
            except Exception as exc:
                st.error(f"Query failed: {exc}")


def main():
    check_db()

    st.sidebar.title("ShopFlow Analytics")
    page = st.sidebar.radio(
        "Navigation",
        ["Executive Overview", "Customer Analytics", "Product & Supply Chain",
         "Data Quality", "SQL Explorer"],
    )

    pages = {
        "Executive Overview": page_overview,
        "Customer Analytics": page_customers,
        "Product & Supply Chain": page_products,
        "Data Quality": page_quality,
        "SQL Explorer": page_sql_explorer,
    }
    pages[page]()


if __name__ == "__main__":
    main()
