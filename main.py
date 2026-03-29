"""CLI entry point for the ShopFlow ETL pipeline."""

import argparse
import subprocess
import sys
import os

from agents.orchestrator import PipelineOrchestrator
from agents.analytics_engine import AnalyticsEngine


def generate_sample_data():
    """Run the sample data generator as a subprocess."""
    script = os.path.join(os.path.dirname(__file__), "data", "generate_sample_data.py")
    subprocess.run([sys.executable, script], check=True)


def list_queries(db_path: str):
    """Print all available SQL query names."""
    engine = AnalyticsEngine(db_path)
    queries = engine.get_available_queries()
    if not queries:
        print("No queries found in sql/queries/")
        return
    print("Available queries:")
    for name in queries:
        print(f"  - {name}")


def run_query(db_path: str, query_name: str):
    """Execute a named query and print results."""
    engine = AnalyticsEngine(db_path)
    try:
        df = engine.execute_query(query_name)
        print(f"\nQuery: {query_name}")
        print("-" * 60)
        print(df.to_string(index=False))
    except FileNotFoundError:
        print(f"Query '{query_name}' not found. Use --list-queries to see options.")
        sys.exit(1)


def print_summary(result):
    """Print a formatted pipeline summary."""
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Duration:       {result.duration_seconds:.2f}s")
    print(f"Quality Score:  {result.quality_report.overall_score}%")
    print(f"Quarantined:    {result.quality_report.total_quarantined} rows")

    print("\nRows loaded:")
    for key in ("dim_date", "dim_customer", "dim_product", "dim_supplier", "fact_sales"):
        if key in result.row_counts:
            print(f"  {key:20s} {result.row_counts[key]:>8,}")

    print("\nKPIs:")
    for key, value in result.kpis.items():
        label = key.replace("_", " ").title()
        if isinstance(value, float):
            print(f"  {label:20s} {value:>12,.2f}")
        else:
            print(f"  {label:20s} {value:>12,}")

    print("\nPhase timings:")
    for phase in result.phases:
        print(f"  {phase.name:20s} {phase.duration:>8.2f}s")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="ShopFlow ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to the raw data directory (default: data)",
    )
    parser.add_argument(
        "--db-path",
        default="output/shopflow.db",
        help="Path to the SQLite database (default: output/shopflow.db)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate sample data before running the pipeline",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run a specific SQL query after the pipeline",
    )
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="List available SQL queries and exit",
    )
    args = parser.parse_args()

    if args.list_queries:
        list_queries(args.db_path)
        return

    if args.generate:
        print("Generating sample data...\n")
        generate_sample_data()
        print()

    orchestrator = PipelineOrchestrator(
        data_dir=args.data_dir,
        db_path=args.db_path,
    )
    result = orchestrator.run()
    print_summary(result)

    if args.query:
        run_query(args.db_path, args.query)


if __name__ == "__main__":
    main()
