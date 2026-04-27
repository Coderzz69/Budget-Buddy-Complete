"""Bootstrap expense category classifier for Budget Buddy."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[A-Z0-9]+")
PREDICTION_FIELDNAMES = [
    "row_id",
    "transaction_ts",
    "counterparty_normalized",
    "amount_inr",
    "existing_category",
    "predicted_category",
    "predicted_confidence",
    "prediction_source",
    "top_1_match",
    "top_3_match",
    "top_2_category",
    "top_2_confidence",
    "top_3_category",
    "top_3_confidence",
]


def _to_datetime(row: dict[str, str]) -> datetime:
    return datetime.fromisoformat(row["transaction_ts"])



def _amount_bucket(amount: float) -> str:
    if amount < 20:
        return "AMOUNT_LT_20"
    if amount < 50:
        return "AMOUNT_20_49"
    if amount < 100:
        return "AMOUNT_50_99"
    if amount < 250:
        return "AMOUNT_100_249"
    if amount < 500:
        return "AMOUNT_250_499"
    if amount < 1000:
        return "AMOUNT_500_999"
    return "AMOUNT_GE_1000"



def _hour_bucket(hour: int) -> str:
    if 5 <= hour < 11:
        return "HOUR_MORNING"
    if 11 <= hour < 16:
        return "HOUR_AFTERNOON"
    if 16 <= hour < 21:
        return "HOUR_EVENING"
    return "HOUR_NIGHT"



def _provider_token(raw_value: str) -> str:
    raw = (raw_value or "").strip().lower()
    if "@" not in raw:
        return "UPI_UNKNOWN"
    provider = raw.split("@", 1)[1]
    provider = provider.split("(", 1)[0]
    provider = re.sub(r"[^a-z0-9]+", "_", provider).strip("_")
    return f"UPI_{provider.upper()}" if provider else "UPI_UNKNOWN"



def _safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator



def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)



def _format_metric(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.4f}"



def extract_features(row: dict[str, str]) -> list[str]:
    features: list[str] = []
    merchant = (row.get("counterparty_normalized", "") or "").strip().upper()
    raw = (row.get("counterparty_raw", "") or "").strip().upper()
    amount = float(row.get("amount_inr", "0") or 0)
    hour = int(row.get("hour_of_day", "0") or 0)
    weekday = row.get("day_of_week", "")
    week_of_month = row.get("week_of_month", "")

    if merchant:
        features.append(f"MERCHANT={merchant}")
        for token in TOKEN_RE.findall(merchant):
            if token:
                features.append(f"MERCHANT_TOKEN={token}")

    for token in TOKEN_RE.findall(raw):
        if len(token) >= 3:
            features.append(f"RAW_TOKEN={token}")

    features.append(_amount_bucket(amount))
    features.append(_hour_bucket(hour))
    if weekday:
        features.append(f"WEEKDAY={weekday}")
    if week_of_month:
        features.append(f"WEEK_OF_MONTH={week_of_month}")
    features.append(_provider_token(row.get("counterparty_raw", "")))
    return features



def load_expense_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))



def split_labeled_rows(rows: Iterable[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        label = (row.get("assigned_category", "") or "").strip()
        if label:
            grouped[label].append(row)

    train_rows: list[dict[str, str]] = []
    validation_rows: list[dict[str, str]] = []

    for label_rows in grouped.values():
        ordered = sorted(label_rows, key=_to_datetime)
        if len(ordered) < 4:
            train_rows.extend(ordered)
            continue

        split_index = max(1, int(len(ordered) * 0.8))
        if split_index >= len(ordered):
            split_index = len(ordered) - 1
        train_rows.extend(ordered[:split_index])
        validation_rows.extend(ordered[split_index:])

    train_rows.sort(key=_to_datetime)
    validation_rows.sort(key=_to_datetime)
    return train_rows, validation_rows



def split_labeled_rows_by_merchant(
    rows: Iterable[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        label = (row.get("assigned_category", "") or "").strip()
        merchant = (row.get("counterparty_normalized", "") or "").strip()
        if label and merchant:
            grouped[label][merchant].append(row)

    train_rows: list[dict[str, str]] = []
    validation_rows: list[dict[str, str]] = []

    for merchant_groups in grouped.values():
        merchants = sorted(merchant_groups)
        if len(merchants) < 2:
            for merchant in merchants:
                train_rows.extend(merchant_groups[merchant])
            continue

        holdout_count = max(1, int(len(merchants) * 0.2))
        if holdout_count >= len(merchants):
            holdout_count = len(merchants) - 1

        holdout_merchants = set(merchants[-holdout_count:])
        for merchant, merchant_rows in merchant_groups.items():
            target = validation_rows if merchant in holdout_merchants else train_rows
            target.extend(sorted(merchant_rows, key=_to_datetime))

    train_rows.sort(key=_to_datetime)
    validation_rows.sort(key=_to_datetime)
    return train_rows, validation_rows


@dataclass
class NaiveBayesCategoryClassifier:
    labels: list[str]
    priors: dict[str, float]
    feature_totals: dict[str, int]
    feature_counts: dict[str, dict[str, int]]
    vocabulary: list[str]
    merchant_map: dict[str, str]

    @classmethod
    def train(cls, rows: Iterable[dict[str, str]]) -> "NaiveBayesCategoryClassifier":
        label_counts: Counter[str] = Counter()
        feature_totals: dict[str, int] = defaultdict(int)
        feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
        vocabulary: set[str] = set()
        merchant_label_votes: dict[str, Counter[str]] = defaultdict(Counter)

        training_rows = [row for row in rows if row.get("assigned_category")]
        for row in training_rows:
            label = row["assigned_category"]
            label_counts[label] += 1
            merchant = row["counterparty_normalized"]
            if merchant:
                merchant_label_votes[merchant][label] += 1

            for feature in extract_features(row):
                vocabulary.add(feature)
                feature_counts[label][feature] += 1
                feature_totals[label] += 1

        labels = sorted(label_counts)
        if not labels:
            raise ValueError("No labeled rows available to train the classifier.")

        softened = {label: math.sqrt(count) for label, count in label_counts.items()}
        total_softened = sum(softened.values())
        priors = {label: softened[label] / total_softened for label in labels}

        merchant_map = {
            merchant: votes.most_common(1)[0][0]
            for merchant, votes in merchant_label_votes.items()
            if votes
        }

        return cls(
            labels=labels,
            priors=priors,
            feature_totals=dict(feature_totals),
            feature_counts={label: dict(counts) for label, counts in feature_counts.items()},
            vocabulary=sorted(vocabulary),
            merchant_map=merchant_map,
        )

    def predict_proba(self, row: dict[str, str], top_k: int = 3) -> list[tuple[str, float]]:
        merchant = row.get("counterparty_normalized", "")
        if merchant in self.merchant_map:
            label = self.merchant_map[merchant]
            baseline = [(candidate, 0.0) for candidate in self.labels if candidate != label]
            scored = [(label, 0.995)]
            remaining_mass = 0.005
            if baseline:
                share = remaining_mass / len(baseline)
                scored.extend((candidate, share) for candidate, _ in baseline)
            return scored[:top_k]

        vocab_size = max(1, len(self.vocabulary))
        features = extract_features(row)
        scores: list[tuple[str, float]] = []
        for label in self.labels:
            log_prob = math.log(self.priors[label])
            total = self.feature_totals.get(label, 0)
            counts = self.feature_counts.get(label, {})
            for feature in features:
                count = counts.get(feature, 0)
                log_prob += math.log((count + 1) / (total + vocab_size))
            scores.append((label, log_prob))

        max_log = max(score for _, score in scores)
        exp_scores = [(label, math.exp(score - max_log)) for label, score in scores]
        total_exp = sum(score for _, score in exp_scores) or 1.0
        probabilities = [(label, score / total_exp) for label, score in exp_scores]
        probabilities.sort(key=lambda item: (-item[1], item[0]))
        return probabilities[:top_k]

    def predict(self, row: dict[str, str]) -> tuple[str, float]:
        predictions = self.predict_proba(row, top_k=1)
        return predictions[0]

    def to_dict(self) -> dict[str, object]:
        return {
            "labels": self.labels,
            "priors": self.priors,
            "feature_totals": self.feature_totals,
            "feature_counts": self.feature_counts,
            "vocabulary": self.vocabulary,
            "merchant_map": self.merchant_map,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "NaiveBayesCategoryClassifier":
        return cls(
            labels=list(payload["labels"]),
            priors=dict(payload["priors"]),
            feature_totals={key: int(value) for key, value in dict(payload["feature_totals"]).items()},
            feature_counts={
                label: {feature: int(count) for feature, count in dict(features).items()}
                for label, features in dict(payload["feature_counts"]).items()
            },
            vocabulary=list(payload["vocabulary"]),
            merchant_map=dict(payload["merchant_map"]),
        )



def build_prediction_rows(
    rows: Iterable[dict[str, str]],
    model: NaiveBayesCategoryClassifier,
    top_k: int = 3,
) -> list[dict[str, object]]:
    prediction_rows: list[dict[str, object]] = []
    requested_top_k = max(3, top_k)

    for row in rows:
        predictions = model.predict_proba(row, top_k=requested_top_k)
        padded = predictions + [("", 0.0)] * (requested_top_k - len(predictions))
        predicted_labels = [label for label, _ in predictions]
        actual_category = (row.get("assigned_category", "") or "").strip()
        prediction_rows.append(
            {
                "row_id": row.get("row_id", ""),
                "transaction_ts": row.get("transaction_ts", ""),
                "counterparty_normalized": row.get("counterparty_normalized", ""),
                "amount_inr": row.get("amount_inr", ""),
                "existing_category": actual_category,
                "predicted_category": padded[0][0],
                "predicted_confidence": padded[0][1],
                "prediction_source": (
                    "merchant_map"
                    if row.get("counterparty_normalized", "") in model.merchant_map
                    else "naive_bayes"
                ),
                "top_1_match": bool(actual_category and padded[0][0] == actual_category),
                "top_3_match": bool(actual_category and actual_category in predicted_labels[:3]),
                "top_2_category": padded[1][0],
                "top_2_confidence": padded[1][1],
                "top_3_category": padded[2][0],
                "top_3_confidence": padded[2][1],
            }
        )

    return prediction_rows



def evaluate_classifier(
    model: NaiveBayesCategoryClassifier,
    validation_rows: Iterable[dict[str, str]],
) -> dict[str, object]:
    rows = list(validation_rows)
    prediction_rows = build_prediction_rows(rows, model, top_k=3)
    if not prediction_rows:
        return {
            "validation_rows": 0,
            "top_1_accuracy": None,
            "top_3_accuracy": None,
            "macro_precision": None,
            "macro_recall": None,
            "macro_f1": None,
            "weighted_f1": None,
            "merchant_map_hit_rate": None,
            "known_merchant_rows": 0,
            "known_merchant_top_1_accuracy": None,
            "unseen_merchant_rows": 0,
            "unseen_merchant_top_1_accuracy": None,
            "per_label_accuracy": {},
            "per_label_metrics": {},
            "confusion_matrix": {},
            "confusion_highlights": [],
            "error_examples": [],
        }

    correct_top1 = 0
    correct_top3 = 0
    per_label_total: Counter[str] = Counter()
    per_label_correct: Counter[str] = Counter()
    per_label_top3: Counter[str] = Counter()
    predicted_total: Counter[str] = Counter()
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    known_rows = 0
    known_correct = 0
    unseen_rows = 0
    unseen_correct = 0

    for prediction in prediction_rows:
        true_label = str(prediction["existing_category"])
        predicted_label = str(prediction["predicted_category"])
        per_label_total[true_label] += 1
        predicted_total[predicted_label] += 1
        confusion[true_label][predicted_label] += 1

        if prediction["top_1_match"]:
            correct_top1 += 1
            per_label_correct[true_label] += 1
        if prediction["top_3_match"]:
            correct_top3 += 1
            per_label_top3[true_label] += 1

        if prediction["prediction_source"] == "merchant_map":
            known_rows += 1
            if prediction["top_1_match"]:
                known_correct += 1
        else:
            unseen_rows += 1
            if prediction["top_1_match"]:
                unseen_correct += 1

    labels = sorted({*model.labels, *per_label_total.keys(), *predicted_total.keys()})
    supported_labels = [label for label in labels if per_label_total[label] > 0]

    per_label_metrics: dict[str, dict[str, object]] = {}
    for label in labels:
        support = per_label_total[label]
        predicted_count = predicted_total[label]
        true_positive = confusion[label][label]
        precision = _safe_div(true_positive, predicted_count)
        recall = _safe_div(true_positive, support)
        f1 = _safe_div(2 * precision * recall, precision + recall) if precision or recall else 0.0
        top3_recall = _safe_div(per_label_top3[label], support)
        per_label_metrics[label] = {
            "support": support,
            "predicted_count": predicted_count,
            "accuracy": _round_metric(recall if support else None),
            "precision": _round_metric(precision),
            "recall": _round_metric(recall),
            "f1": _round_metric(f1),
            "top_3_recall": _round_metric(top3_recall if support else None),
        }

    macro_precision = None
    macro_recall = None
    macro_f1 = None
    weighted_f1 = None
    if supported_labels:
        macro_precision = sum(float(per_label_metrics[label]["precision"] or 0.0) for label in supported_labels) / len(
            supported_labels
        )
        macro_recall = sum(float(per_label_metrics[label]["recall"] or 0.0) for label in supported_labels) / len(
            supported_labels
        )
        macro_f1 = sum(float(per_label_metrics[label]["f1"] or 0.0) for label in supported_labels) / len(
            supported_labels
        )
        total_support = sum(per_label_total[label] for label in supported_labels)
        weighted_f1 = _safe_div(
            sum(float(per_label_metrics[label]["f1"] or 0.0) * per_label_total[label] for label in supported_labels),
            total_support,
        )

    confusion_matrix = {
        actual: {
            predicted: confusion[actual][predicted]
            for predicted in labels
            if confusion[actual][predicted]
        }
        for actual in labels
        if per_label_total[actual]
    }

    confusion_highlights = []
    for actual in labels:
        for predicted in labels:
            if actual == predicted:
                continue
            count = confusion[actual][predicted]
            if count:
                confusion_highlights.append(
                    {
                        "actual_category": actual,
                        "predicted_category": predicted,
                        "count": count,
                    }
                )
    confusion_highlights.sort(
        key=lambda item: (-int(item["count"]), str(item["actual_category"]), str(item["predicted_category"]))
    )

    error_examples = [
        {
            "row_id": prediction["row_id"],
            "transaction_ts": prediction["transaction_ts"],
            "counterparty_normalized": prediction["counterparty_normalized"],
            "amount_inr": prediction["amount_inr"],
            "actual_category": prediction["existing_category"],
            "predicted_category": prediction["predicted_category"],
            "predicted_confidence": _round_metric(float(prediction["predicted_confidence"])),
            "prediction_source": prediction["prediction_source"],
            "top_alternatives": [
                {
                    "label": str(prediction["top_2_category"]),
                    "confidence": _round_metric(float(prediction["top_2_confidence"])),
                },
                {
                    "label": str(prediction["top_3_category"]),
                    "confidence": _round_metric(float(prediction["top_3_confidence"])),
                },
            ],
        }
        for prediction in prediction_rows
        if not prediction["top_1_match"]
    ]
    error_examples.sort(
        key=lambda item: (
            -float(item["predicted_confidence"] or 0.0),
            str(item["transaction_ts"]),
            str(item["counterparty_normalized"]),
        )
    )

    return {
        "validation_rows": len(prediction_rows),
        "top_1_accuracy": _round_metric(correct_top1 / len(prediction_rows)),
        "top_3_accuracy": _round_metric(correct_top3 / len(prediction_rows)),
        "macro_precision": _round_metric(macro_precision),
        "macro_recall": _round_metric(macro_recall),
        "macro_f1": _round_metric(macro_f1),
        "weighted_f1": _round_metric(weighted_f1),
        "merchant_map_hit_rate": _round_metric(known_rows / len(prediction_rows)),
        "known_merchant_rows": known_rows,
        "known_merchant_top_1_accuracy": _round_metric(known_correct / known_rows) if known_rows else None,
        "unseen_merchant_rows": unseen_rows,
        "unseen_merchant_top_1_accuracy": _round_metric(unseen_correct / unseen_rows) if unseen_rows else None,
        "per_label_accuracy": {
            label: _round_metric(per_label_correct[label] / total)
            for label, total in sorted(per_label_total.items())
        },
        "per_label_metrics": {label: per_label_metrics[label] for label in labels if per_label_total[label]},
        "confusion_matrix": confusion_matrix,
        "confusion_highlights": confusion_highlights[:10],
        "error_examples": error_examples[:15],
    }



def build_accuracy_report_markdown(metrics: dict[str, object]) -> str:
    dataset = dict(metrics.get("dataset", {}))
    time_split = dict(metrics.get("time_split", {}))
    merchant_holdout = dict(metrics.get("merchant_holdout", {})) if metrics.get("merchant_holdout") else {}

    lines = ["# Category Classifier Accuracy Report", ""]
    generated_at = metrics.get("generated_at")
    if generated_at:
        lines.append(f"Generated at: `{generated_at}`")
        lines.append("")

    lines.extend(
        [
            "## Dataset",
            "",
            f"- Total expense rows: `{dataset.get('total_rows', 0)}`",
            f"- Labeled expense rows: `{dataset.get('labeled_rows', 0)}`",
            f"- Unlabeled expense rows: `{dataset.get('unlabeled_rows', 0)}`",
            f"- Unique labeled merchants: `{dataset.get('unique_labeled_merchants', 0)}`",
            f"- Merchant map size: `{dataset.get('merchant_map_size', 0)}`",
            "",
        ]
    )

    label_distribution = dict(dataset.get("label_distribution", {}))
    if label_distribution:
        lines.extend([
            "### Labeled Distribution",
            "",
            "| Label | Rows | Share |",
            "| --- | ---: | ---: |",
        ])
        total_labeled = int(dataset.get("labeled_rows", 0)) or 1
        for label, count in sorted(label_distribution.items(), key=lambda item: (-int(item[1]), item[0])):
            share = count / total_labeled
            lines.append(f"| {label} | {count} | {share:.2%} |")
        lines.append("")

    dominant_label = None
    dominant_ratio = 0.0
    if label_distribution:
        dominant_label, dominant_count = max(label_distribution.items(), key=lambda item: item[1])
        dominant_ratio = dominant_count / (int(dataset.get("labeled_rows", 0)) or 1)

    if dominant_label:
        lines.extend(
            [
                "## Readout",
                "",
                f"- The labeled set is dominated by `{dominant_label}` at `{dominant_ratio:.2%}` of labeled rows.",
            ]
        )
        if time_split.get("top_1_accuracy") is not None and merchant_holdout.get("top_1_accuracy") is not None:
            gap = float(time_split["top_1_accuracy"]) - float(merchant_holdout["top_1_accuracy"])
            lines.append(
                f"- The gap between time-split and merchant-holdout top-1 accuracy is `{gap:.4f}`, which indicates how much performance depends on known merchants."
            )
        lines.append("")

    lines.extend(_render_evaluation_section("Time-Split Validation", time_split))
    if merchant_holdout:
        lines.extend(_render_evaluation_section("Merchant-Holdout Validation", merchant_holdout))

    return "\n".join(lines).rstrip() + "\n"



def _render_evaluation_section(title: str, evaluation: dict[str, object]) -> list[str]:
    lines = [f"## {title}", ""]
    if not evaluation or not evaluation.get("validation_rows"):
        lines.extend(["No validation rows were available for this slice.", ""])
        return lines

    lines.extend(
        [
            f"- Validation rows: `{evaluation.get('validation_rows', 0)}`",
            f"- Top-1 accuracy: `{_format_metric(evaluation.get('top_1_accuracy'))}`",
            f"- Top-3 accuracy: `{_format_metric(evaluation.get('top_3_accuracy'))}`",
            f"- Macro precision: `{_format_metric(evaluation.get('macro_precision'))}`",
            f"- Macro recall: `{_format_metric(evaluation.get('macro_recall'))}`",
            f"- Macro F1: `{_format_metric(evaluation.get('macro_f1'))}`",
            f"- Weighted F1: `{_format_metric(evaluation.get('weighted_f1'))}`",
            f"- Merchant-map hit rate: `{_format_metric(evaluation.get('merchant_map_hit_rate'))}`",
            f"- Known-merchant top-1 accuracy: `{_format_metric(evaluation.get('known_merchant_top_1_accuracy'))}` over `{evaluation.get('known_merchant_rows', 0)}` rows",
            f"- Unseen-merchant top-1 accuracy: `{_format_metric(evaluation.get('unseen_merchant_top_1_accuracy'))}` over `{evaluation.get('unseen_merchant_rows', 0)}` rows",
            "",
        ]
    )

    per_label_metrics = dict(evaluation.get("per_label_metrics", {}))
    if per_label_metrics:
        lines.extend([
            "### Per-Label Metrics",
            "",
            "| Label | Support | Predicted | Precision | Recall | F1 | Top-3 Recall |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for label, values in sorted(
            per_label_metrics.items(),
            key=lambda item: (-int(dict(item[1]).get("support", 0)), item[0]),
        ):
            values = dict(values)
            lines.append(
                "| {label} | {support} | {predicted} | {precision} | {recall} | {f1} | {top3} |".format(
                    label=label,
                    support=values.get("support", 0),
                    predicted=values.get("predicted_count", 0),
                    precision=_format_metric(values.get("precision")),
                    recall=_format_metric(values.get("recall")),
                    f1=_format_metric(values.get("f1")),
                    top3=_format_metric(values.get("top_3_recall")),
                )
            )
        lines.append("")

    confusion_highlights = list(evaluation.get("confusion_highlights", []))
    if confusion_highlights:
        lines.extend([
            "### Top Confusions",
            "",
            "| Actual | Predicted | Count |",
            "| --- | --- | ---: |",
        ])
        for item in confusion_highlights:
            lines.append(
                f"| {item['actual_category']} | {item['predicted_category']} | {item['count']} |"
            )
        lines.append("")

    error_examples = list(evaluation.get("error_examples", []))
    if error_examples:
        lines.extend([
            "### Representative Errors",
            "",
            "| Timestamp | Merchant | Amount | Actual | Predicted | Source | Confidence | Alternatives |",
            "| --- | --- | ---: | --- | --- | --- | ---: | --- |",
        ])
        for item in error_examples[:10]:
            alternatives = ", ".join(
                f"{alt['label']} ({_format_metric(alt['confidence'])})"
                for alt in item.get("top_alternatives", [])
                if alt.get("label")
            )
            lines.append(
                "| {timestamp} | {merchant} | {amount} | {actual} | {predicted} | {source} | {confidence} | {alternatives} |".format(
                    timestamp=item.get("transaction_ts", ""),
                    merchant=item.get("counterparty_normalized", ""),
                    amount=item.get("amount_inr", ""),
                    actual=item.get("actual_category", ""),
                    predicted=item.get("predicted_category", ""),
                    source=item.get("prediction_source", ""),
                    confidence=_format_metric(item.get("predicted_confidence")),
                    alternatives=alternatives or "-",
                )
            )
        lines.append("")

    return lines



def write_accuracy_report(path: str | Path, metrics: dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_accuracy_report_markdown(metrics), encoding="utf-8")



def write_model(path: str | Path, model: NaiveBayesCategoryClassifier) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(model.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")



def write_predictions(
    path: str | Path,
    rows: Iterable[dict[str, str]],
    model: NaiveBayesCategoryClassifier,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_rows = build_prediction_rows(rows, model, top_k=3)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDNAMES)
        writer.writeheader()
        for row in prediction_rows:
            writer.writerow(
                {
                    "row_id": row["row_id"],
                    "transaction_ts": row["transaction_ts"],
                    "counterparty_normalized": row["counterparty_normalized"],
                    "amount_inr": row["amount_inr"],
                    "existing_category": row["existing_category"],
                    "predicted_category": row["predicted_category"],
                    "predicted_confidence": f"{float(row['predicted_confidence']):.4f}",
                    "prediction_source": row["prediction_source"],
                    "top_1_match": "1" if row["top_1_match"] else "0",
                    "top_3_match": "1" if row["top_3_match"] else "0",
                    "top_2_category": row["top_2_category"],
                    "top_2_confidence": f"{float(row['top_2_confidence']):.4f}",
                    "top_3_category": row["top_3_category"],
                    "top_3_confidence": f"{float(row['top_3_confidence']):.4f}",
                }
            )
