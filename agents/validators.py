"""Data quality validation with configurable rules."""

import pandas as pd
from datetime import date, datetime
from models.quality import ValidationIssue, SourceQuality, DataQualityReport


class DataValidator:

    def validate_all(self, sources: dict) -> DataQualityReport:
        """Validate all extracted sources and produce a quality report."""
        reports = []

        for name, extraction in sources.items():
            report = self._validate_source(name, extraction.df)
            reports.append(report)

        # Cross-source referential integrity
        ref_issues = self._check_referential_integrity(sources)
        if ref_issues:
            for r in reports:
                if r.source_name == "orders":
                    r.issues.extend(ref_issues)
                    r.invalid_rows += len(ref_issues)
                    r.valid_rows -= len(ref_issues)
                    r.quality_score = round(r.valid_rows / r.total_rows * 100, 1) if r.total_rows > 0 else 100.0

        total_quarantined = sum(r.invalid_rows for r in reports)
        overall = round(sum(r.quality_score for r in reports) / len(reports), 1) if reports else 100.0

        return DataQualityReport(
            sources=reports,
            overall_score=overall,
            total_quarantined=total_quarantined,
            generated_at=datetime.now().isoformat(),
        )

    def _validate_source(self, name: str, df: pd.DataFrame) -> SourceQuality:
        issues = []

        # Null checks on required columns
        for col in df.columns:
            nulls = df[df[col].isna()]
            for idx in nulls.index:
                issues.append(ValidationIssue(
                    source=name, row_index=int(idx), field=col,
                    value="NULL", rule="not_null", message=f"Missing required field: {col}"
                ))

        # Type/business rule checks per source
        if name == "orders":
            issues.extend(self._validate_orders(df))
        elif name == "customers":
            issues.extend(self._validate_customers(df))
        elif name == "products":
            issues.extend(self._validate_products(df))

        # Deduplicate by row_index (count unique rows with issues)
        invalid_indices = {i.row_index for i in issues}
        invalid_count = len(invalid_indices)
        valid_count = len(df) - invalid_count
        score = round(valid_count / len(df) * 100, 1) if len(df) > 0 else 100.0

        return SourceQuality(
            source_name=name, total_rows=len(df),
            valid_rows=valid_count, invalid_rows=invalid_count,
            quality_score=score, issues=issues,
        )

    def _validate_orders(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues = []
        for idx, row in df.iterrows():
            if pd.notna(row.get("quantity")) and row["quantity"] <= 0:
                issues.append(ValidationIssue(
                    source="orders", row_index=int(idx), field="quantity",
                    value=str(row["quantity"]), rule="positive_value",
                    message="Quantity must be positive"
                ))
            if pd.notna(row.get("unit_price")) and row["unit_price"] <= 0:
                issues.append(ValidationIssue(
                    source="orders", row_index=int(idx), field="unit_price",
                    value=str(row["unit_price"]), rule="positive_value",
                    message="Unit price must be positive"
                ))
            if pd.notna(row.get("discount_pct")) and (row["discount_pct"] < 0 or row["discount_pct"] > 100):
                issues.append(ValidationIssue(
                    source="orders", row_index=int(idx), field="discount_pct",
                    value=str(row["discount_pct"]), rule="range_check",
                    message="Discount must be between 0 and 100"
                ))
        return issues

    def _validate_customers(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues = []
        seen_ids = set()
        for idx, row in df.iterrows():
            cid = row.get("customer_id")
            if pd.notna(cid) and cid in seen_ids:
                issues.append(ValidationIssue(
                    source="customers", row_index=int(idx), field="customer_id",
                    value=str(cid), rule="unique", message="Duplicate customer_id"
                ))
            if pd.notna(cid):
                seen_ids.add(cid)
        return issues

    def _validate_products(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues = []
        for idx, row in df.iterrows():
            cost = row.get("cost_price")
            retail = row.get("retail_price")
            if pd.notna(cost) and pd.notna(retail) and cost > retail:
                issues.append(ValidationIssue(
                    source="products", row_index=int(idx), field="retail_price",
                    value=f"cost={cost}, retail={retail}", rule="business_rule",
                    message="Cost price exceeds retail price"
                ))
        return issues

    def _check_referential_integrity(self, sources: dict) -> list[ValidationIssue]:
        issues = []
        if "orders" not in sources or "customers" not in sources:
            return issues

        customer_ids = set(sources["customers"].df["customer_id"].dropna())
        product_ids = set(sources["products"].df["product_id"].dropna()) if "products" in sources else set()

        orders_df = sources["orders"].df
        for idx, row in orders_df.iterrows():
            if pd.notna(row.get("customer_id")) and row["customer_id"] not in customer_ids:
                issues.append(ValidationIssue(
                    source="orders", row_index=int(idx), field="customer_id",
                    value=str(row["customer_id"]), rule="referential_integrity",
                    message="Customer ID not found in customers table"
                ))
            if product_ids and pd.notna(row.get("product_id")) and row["product_id"] not in product_ids:
                issues.append(ValidationIssue(
                    source="orders", row_index=int(idx), field="product_id",
                    value=str(row["product_id"]), rule="referential_integrity",
                    message="Product ID not found in products table"
                ))
        return issues
