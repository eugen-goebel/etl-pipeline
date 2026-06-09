"""Six-phase ETL pipeline coordinator for the ShopFlow star schema."""

import time

import pandas as pd

from agents import run_recorder
from agents.analytics_engine import AnalyticsEngine
from agents.dimension_builder import DimensionBuilder, FactBuilder
from agents.extractors import extract_all
from agents.loader import DatabaseLoader
from agents.transformers import DataCleaner, DataEnricher
from agents.validators import DataValidator
from models.quality import DataQualityReport


class PhaseResult:
    """Timing result for a single pipeline phase."""

    def __init__(self, name: str, duration: float):
        self.name = name
        self.duration = duration

    def __repr__(self):
        return f"PhaseResult(name={self.name!r}, duration={self.duration:.2f}s)"


class PipelineResult:
    """Final output of a complete pipeline run."""

    def __init__(
        self,
        quality_report: DataQualityReport,
        kpis: dict,
        row_counts: dict[str, int],
        duration_seconds: float,
        phases: list[PhaseResult],
    ):
        self.quality_report = quality_report
        self.kpis = kpis
        self.row_counts = row_counts
        self.duration_seconds = duration_seconds
        self.phases = phases


class PipelineOrchestrator:
    """Coordinates the full ETL pipeline across six phases."""

    def __init__(
        self, data_dir: str = "data", db_path: str = "output/shopflow.db", mode: str = "full"
    ):
        self.data_dir = data_dir
        self.db_path = db_path
        self.mode = mode

    def run(self) -> PipelineResult:
        """Execute the complete ETL pipeline and return consolidated results."""
        pipeline_start = time.time()
        phases: list[PhaseResult] = []
        row_counts: dict[str, int] = {}

        run_id = None
        try:
            run_id = run_recorder.start_run(self.db_path, mode=self.mode)
        except Exception as exc:  # noqa: BLE001 — observability must not block ETL
            print(f"      [run-recorder] could not start run record: {exc}")

        try:
            result = self._execute(pipeline_start, phases, row_counts)
        except Exception as exc:
            if run_id is not None:
                try:
                    run_recorder.finish_run(
                        self.db_path,
                        run_id,
                        status="failed",
                        error_message=str(exc),
                        phase_timings={p.name: p.duration for p in phases},
                        row_counts=row_counts,
                    )
                except Exception as inner:  # noqa: BLE001
                    print(f"      [run-recorder] could not finalize failed run: {inner}")
            raise

        if run_id is not None:
            try:
                run_recorder.finish_run(
                    self.db_path,
                    run_id,
                    status="success",
                    quality_score=result.quality_report.overall_score,
                    phase_timings={p.name: p.duration for p in result.phases},
                    row_counts=result.row_counts,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"      [run-recorder] could not finalize successful run: {exc}")

        return result

    def _execute(
        self,
        pipeline_start: float,
        phases: list[PhaseResult],
        row_counts: dict[str, int],
    ) -> PipelineResult:
        """Inner pipeline body — split out so the recorder can wrap it."""
        # ── Phase 1: Extract ────────────────────────────────────────────
        print("[1/6] Extract -- loading raw sources")
        t0 = time.time()
        sources = extract_all(self.data_dir)
        phase_dur = time.time() - t0
        phases.append(PhaseResult("extract", phase_dur))

        for name, result in sources.items():
            row_counts[f"raw_{name}"] = result.row_count
            print(f"      {name}: {result.row_count} rows")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Phase 2: Validate ───────────────────────────────────────────
        print("[2/6] Validate -- checking data quality")
        t0 = time.time()
        validator = DataValidator()
        quality_report = validator.validate_all(sources)
        phase_dur = time.time() - t0
        phases.append(PhaseResult("validate", phase_dur))

        print(f"      overall quality score: {quality_report.overall_score}%")
        print(f"      quarantined rows: {quality_report.total_quarantined}")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Phase 3: Transform ──────────────────────────────────────────
        print("[3/6] Transform -- cleaning and enriching data")
        t0 = time.time()

        cleaner = DataCleaner()
        clean = {
            "orders": cleaner.clean_orders(sources["orders"].df),
            "customers": cleaner.clean_customers(sources["customers"].df),
            "products": cleaner.clean_products(sources["products"].df),
            "suppliers": cleaner.clean_suppliers(sources["suppliers"].df),
            "returns": cleaner.clean_returns(sources["returns"].df),
            "shipping": cleaner.clean_shipping(sources["shipping"].df),
        }

        enricher = DataEnricher()
        clean["orders"] = enricher.enrich_orders(
            clean["orders"], clean["returns"], clean["shipping"]
        )
        clean["products"] = enricher.enrich_products(clean["products"])

        phase_dur = time.time() - t0
        phases.append(PhaseResult("transform", phase_dur))

        for name, df in clean.items():
            row_counts[f"clean_{name}"] = len(df)
        print(f"      cleaned orders: {len(clean['orders'])} rows")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Phase 4: Build Dimensions ───────────────────────────────────
        print("[4/6] Build Dimensions -- constructing star schema")
        t0 = time.time()

        dim_builder = DimensionBuilder()
        dim_date = dim_builder.build_dim_date()
        dim_customer = dim_builder.build_dim_customer(clean["customers"])
        dim_supplier = dim_builder.build_dim_supplier(clean["suppliers"])
        dim_product = dim_builder.build_dim_product(clean["products"], dim_supplier)

        fact_builder = FactBuilder()
        fact_sales = fact_builder.build_fact_sales(
            clean["orders"], dim_customer, dim_product, dim_supplier
        )

        phase_dur = time.time() - t0
        phases.append(PhaseResult("build_dimensions", phase_dur))

        row_counts["dim_date"] = len(dim_date)
        row_counts["dim_customer"] = len(dim_customer)
        row_counts["dim_supplier"] = len(dim_supplier)
        row_counts["dim_product"] = len(dim_product)
        row_counts["fact_sales"] = len(fact_sales)

        print(f"      dim_date: {len(dim_date)}, dim_customer: {len(dim_customer)}")
        print(f"      dim_product: {len(dim_product)}, dim_supplier: {len(dim_supplier)}")
        print(f"      fact_sales: {len(fact_sales)}")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Phase 5: Load ───────────────────────────────────────────────
        print(f"[5/6] Load -- writing to database ({self.mode} mode)")
        t0 = time.time()

        # Build quality issues DataFrame for persistence
        quality_rows = []
        for src in quality_report.sources:
            for issue in src.issues:
                quality_rows.append(issue.model_dump())
        quality_issues_df = pd.DataFrame(quality_rows) if quality_rows else None

        loader = DatabaseLoader(self.db_path)
        if self.mode == "incremental":
            new_count = loader.load_incremental(
                dim_date=dim_date,
                dim_customer=dim_customer,
                dim_product=dim_product,
                dim_supplier=dim_supplier,
                fact_sales=fact_sales,
                quality_issues=quality_issues_df,
            )
            if new_count is not None:
                print(f"      new fact rows: {new_count}")
        else:
            loader.load(
                dim_date=dim_date,
                dim_customer=dim_customer,
                dim_product=dim_product,
                dim_supplier=dim_supplier,
                fact_sales=fact_sales,
                quality_issues=quality_issues_df,
            )

        phase_dur = time.time() - t0
        phases.append(PhaseResult("load", phase_dur))
        print(f"      database: {self.db_path}")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Phase 6: Analyze ────────────────────────────────────────────
        print("[6/6] Analyze -- computing KPIs and running queries")
        t0 = time.time()

        engine = AnalyticsEngine(self.db_path)
        kpis = engine.get_kpis()

        available = engine.get_available_queries()
        query_results = {}
        for query_name in available:
            try:
                query_results[query_name] = engine.execute_query(query_name)
            except Exception as exc:
                print(f"      query '{query_name}' failed: {exc}")

        phase_dur = time.time() - t0
        phases.append(PhaseResult("analyze", phase_dur))

        print(f"      KPIs: {kpis}")
        print(f"      executed {len(query_results)}/{len(available)} queries")
        print(f"      completed in {phase_dur:.2f}s")

        # ── Summary ─────────────────────────────────────────────────────
        total_duration = time.time() - pipeline_start
        print(f"\nPipeline finished in {total_duration:.2f}s")

        return PipelineResult(
            quality_report=quality_report,
            kpis=kpis,
            row_counts=row_counts,
            duration_seconds=total_duration,
            phases=phases,
        )
