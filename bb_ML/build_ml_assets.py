#!/usr/bin/env python3
"""Build baseline ML artifacts from the raw six-month UPI export."""

from __future__ import annotations

import argparse
from pathlib import Path

from bb_ml.baselines import (
    build_behavior_summary,
    build_merchant_label_candidates,
    detect_anomalies,
    detect_recurring_patterns,
    write_json,
)
from bb_ml.pipeline import (
    CANONICAL_FIELDNAMES,
    FEATURE_FIELDNAMES,
    build_canonical_ledger,
    build_feature_rows,
    load_merchant_category_map,
    parse_raw_rows,
    write_csv,
)


MERCHANT_LABEL_FIELDNAMES = [
    "normalized_merchant",
    "example_counterparty_raw",
    "tx_count",
    "total_spend_inr",
    "avg_amount_inr",
    "median_amount_inr",
    "first_seen",
    "last_seen",
    "assigned_category",
    "label_status",
    "label_notes",
]


MERCHANT_MAP_TEMPLATE_FIELDS = [
    "normalized_merchant",
    "assigned_category",
    "label_notes",
]


RECURRING_FIELDNAMES = [
    "counterparty_normalized",
    "direction",
    "tx_count",
    "recurring_frequency",
    "median_interval_days",
    "interval_mad_days",
    "expected_amount_min_inr",
    "expected_amount_max_inr",
    "next_expected_date",
    "confidence",
    "first_seen",
    "last_seen",
]


ANOMALY_FIELDNAMES = [
    "row_id",
    "transaction_ts",
    "counterparty_normalized",
    "direction",
    "amount_inr",
    "anomaly_score",
    "amount_flag",
    "new_counterparty_flag",
    "unusual_hour_flag",
    "explanations",
]


def build_assets(input_csv: Path, output_dir: Path, label_map_csv: Path | None) -> None:
    parsed_rows = parse_raw_rows(input_csv)
    canonical_rows = build_canonical_ledger(parsed_rows, source_file=input_csv.name)

    merchant_map = load_merchant_category_map(label_map_csv)
    feature_rows = build_feature_rows(canonical_rows, merchant_category_map=merchant_map)
    primary_event_rows = [row for row in feature_rows if row["is_primary_event"] == "1"]
    expense_rows = [
        row for row in primary_event_rows if row["is_expense_candidate"] == "1"
    ]

    recurring_patterns = detect_recurring_patterns(feature_rows)
    anomaly_rows = detect_anomalies(feature_rows)
    merchant_candidates = build_merchant_label_candidates(feature_rows)
    merchant_map_template = [
        {
            "normalized_merchant": row["normalized_merchant"],
            "assigned_category": row["assigned_category"],
            "label_notes": row["label_notes"],
        }
        for row in merchant_candidates
    ]
    behavior_summary = build_behavior_summary(canonical_rows, recurring_patterns, anomaly_rows)

    write_csv(output_dir / "canonical_ledger.csv", canonical_rows, CANONICAL_FIELDNAMES)
    write_csv(output_dir / "transaction_features.csv", feature_rows, FEATURE_FIELDNAMES)
    write_csv(output_dir / "behavior_event_view.csv", primary_event_rows, FEATURE_FIELDNAMES)
    write_csv(output_dir / "expense_training_view.csv", expense_rows, FEATURE_FIELDNAMES)
    write_csv(output_dir / "merchant_label_candidates.csv", merchant_candidates, MERCHANT_LABEL_FIELDNAMES)
    write_csv(output_dir / "merchant_category_map_template.csv", merchant_map_template, MERCHANT_MAP_TEMPLATE_FIELDS)
    write_csv(output_dir / "recurring_patterns.csv", recurring_patterns, RECURRING_FIELDNAMES)
    write_csv(output_dir / "anomaly_scores.csv", anomaly_rows, ANOMALY_FIELDNAMES)
    write_json(output_dir / "behavior_summary.json", behavior_summary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="bhim_transactions.csv",
        help="Raw UPI CSV export to ingest.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where derived artifacts will be written.",
    )
    parser.add_argument(
        "--label-map",
        default="merchant_category_map.csv",
        help="Optional merchant-to-category mapping file.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    input_csv = (base_dir / args.input).resolve()
    output_dir = (base_dir / args.output_dir).resolve()
    label_map = (base_dir / args.label_map).resolve()

    build_assets(
        input_csv=input_csv,
        output_dir=output_dir,
        label_map_csv=label_map if label_map.exists() else None,
    )

    print(f"Built ML artifacts in {output_dir}")


if __name__ == "__main__":
    main()
