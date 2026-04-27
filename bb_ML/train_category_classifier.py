#!/usr/bin/env python3
"""Train the first bootstrap category classifier from labeled expense rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from bb_ml.classifier import (
    NaiveBayesCategoryClassifier,
    evaluate_classifier,
    load_expense_rows,
    split_labeled_rows,
    split_labeled_rows_by_merchant,
    write_accuracy_report,
    write_model,
    write_predictions,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="outputs/expense_training_view.csv",
        help="Expense training view with propagated merchant labels.",
    )
    parser.add_argument(
        "--model-out",
        default="outputs/category_classifier_model.json",
        help="Path to store the trained model artifact.",
    )
    parser.add_argument(
        "--metrics-out",
        default="outputs/category_classifier_metrics.json",
        help="Path to store the evaluation metrics.",
    )
    parser.add_argument(
        "--predictions-out",
        default="outputs/category_predictions.csv",
        help="Path to store row-level predictions.",
    )
    parser.add_argument(
        "--report-out",
        default="outputs/category_classifier_accuracy_report.md",
        help="Path to store the markdown accuracy report.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    input_path = (base_dir / args.input).resolve()
    model_out = (base_dir / args.model_out).resolve()
    metrics_out = (base_dir / args.metrics_out).resolve()
    predictions_out = (base_dir / args.predictions_out).resolve()
    report_out = (base_dir / args.report_out).resolve()

    rows = load_expense_rows(input_path)
    labeled_rows = [row for row in rows if row.get("assigned_category")]
    unlabeled_rows = [row for row in rows if not row.get("assigned_category")]

    if not labeled_rows:
        raise SystemExit("No labeled rows found. Build merchant labels first.")

    train_rows, validation_rows = split_labeled_rows(labeled_rows)
    model = NaiveBayesCategoryClassifier.train(train_rows)
    time_split_metrics = evaluate_classifier(model, validation_rows)

    merchant_train_rows, merchant_validation_rows = split_labeled_rows_by_merchant(labeled_rows)
    merchant_holdout_metrics = None
    if merchant_validation_rows:
        merchant_holdout_model = NaiveBayesCategoryClassifier.train(merchant_train_rows)
        merchant_holdout_metrics = evaluate_classifier(merchant_holdout_model, merchant_validation_rows)

    dataset_metrics = {
        "input_path": str(input_path),
        "total_rows": len(rows),
        "labeled_rows": len(labeled_rows),
        "unlabeled_rows": len(unlabeled_rows),
        "merchant_map_size": len(model.merchant_map),
        "unique_labeled_merchants": len({row["counterparty_normalized"] for row in labeled_rows if row["counterparty_normalized"]}),
        "label_distribution": dict(Counter(row["assigned_category"] for row in labeled_rows)),
        "train_label_distribution": dict(Counter(row["assigned_category"] for row in train_rows)),
        "validation_label_distribution": dict(Counter(row["assigned_category"] for row in validation_rows)),
        "merchant_holdout_validation_label_distribution": (
            dict(Counter(row["assigned_category"] for row in merchant_validation_rows))
            if merchant_validation_rows
            else {}
        ),
    }

    metrics = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "dataset": dataset_metrics,
        "top_1_accuracy": time_split_metrics["top_1_accuracy"],
        "top_3_accuracy": time_split_metrics["top_3_accuracy"],
        "macro_precision": time_split_metrics["macro_precision"],
        "macro_recall": time_split_metrics["macro_recall"],
        "macro_f1": time_split_metrics["macro_f1"],
        "weighted_f1": time_split_metrics["weighted_f1"],
        "per_label_accuracy": time_split_metrics["per_label_accuracy"],
        "per_label_metrics": time_split_metrics["per_label_metrics"],
        "train_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "unlabeled_rows": len(unlabeled_rows),
        "merchant_map_size": len(model.merchant_map),
        "train_label_distribution": dataset_metrics["train_label_distribution"],
        "validation_label_distribution": dataset_metrics["validation_label_distribution"],
        "time_split": time_split_metrics,
        "merchant_holdout": merchant_holdout_metrics,
    }

    write_model(model_out, model)
    write_predictions(predictions_out, rows, model)
    write_accuracy_report(report_out, metrics)

    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    with metrics_out.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Trained classifier with {len(train_rows)} training rows and {len(validation_rows)} validation rows")
    print(f"Wrote model to {model_out}")
    print(f"Wrote metrics to {metrics_out}")
    print(f"Wrote predictions to {predictions_out}")
    print(f"Wrote accuracy report to {report_out}")


if __name__ == "__main__":
    main()
