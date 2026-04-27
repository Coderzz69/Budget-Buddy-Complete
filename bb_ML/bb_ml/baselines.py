"""Baseline behavior signals for recurring patterns, anomalies, and labeling."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Iterable


def _to_datetime(row: dict[str, str]) -> datetime:
    return datetime.fromisoformat(row["transaction_ts"])


def _safe_median(values: list[float]) -> float:
    return median(values) if values else 0.0


def _median_absolute_deviation(values: list[float], center: float | None = None) -> float:
    if not values:
        return 0.0
    center = _safe_median(values) if center is None else center
    deviations = [abs(value - center) for value in values]
    return _safe_median(deviations)


def _clock_distance(hour_a: int, hour_b: int) -> int:
    diff = abs(hour_a - hour_b)
    return min(diff, 24 - diff)


def build_merchant_label_candidates(feature_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in feature_rows:
        if row["is_primary_event"] != "1":
            continue
        if row["is_expense_candidate"] != "1":
            continue
        grouped[row["counterparty_normalized"]].append(row)

    candidates: list[dict[str, str]] = []
    for merchant, rows in grouped.items():
        rows = sorted(rows, key=_to_datetime)
        amounts = [float(row["amount_inr"]) for row in rows]
        raw_examples = Counter(row["counterparty_raw"] for row in rows)
        assigned = rows[0].get("assigned_category", "")
        candidates.append(
            {
                "normalized_merchant": merchant,
                "example_counterparty_raw": raw_examples.most_common(1)[0][0],
                "tx_count": str(len(rows)),
                "total_spend_inr": f"{sum(amounts):.2f}",
                "avg_amount_inr": f"{(sum(amounts) / len(amounts)):.2f}",
                "median_amount_inr": f"{_safe_median(amounts):.2f}",
                "first_seen": rows[0]["transaction_ts"],
                "last_seen": rows[-1]["transaction_ts"],
                "assigned_category": assigned,
                "label_status": "prelabeled" if assigned else "needs_review",
                "label_notes": "",
            }
        )

    candidates.sort(key=lambda row: (-float(row["total_spend_inr"]), -int(row["tx_count"]), row["normalized_merchant"]))
    return candidates


def detect_recurring_patterns(feature_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in feature_rows:
        if row["is_primary_event"] != "1":
            continue
        if row["is_success"] != "1":
            continue
        grouped[(row["counterparty_normalized"], row["direction"])].append(row)

    patterns: list[dict[str, str]] = []
    for (counterparty, direction), rows in grouped.items():
        rows = sorted(rows, key=_to_datetime)
        if len(rows) < 3:
            continue

        timestamps = [_to_datetime(row) for row in rows]
        amounts = [float(row["amount_inr"]) for row in rows]
        intervals = [
            (timestamps[index] - timestamps[index - 1]).total_seconds() / 86400
            for index in range(1, len(timestamps))
        ]
        if not intervals:
            continue

        median_interval = _safe_median(intervals)
        interval_mad = _median_absolute_deviation(intervals, median_interval)
        mean_amount = sum(amounts) / len(amounts)
        amount_mad = _median_absolute_deviation(amounts, _safe_median(amounts))
        amount_cv = 0.0 if mean_amount == 0 else min(amount_mad / mean_amount, 5.0)

        frequency = "irregular"
        if 6 <= median_interval <= 8:
            frequency = "weekly"
        elif 13 <= median_interval <= 16:
            frequency = "biweekly"
        elif 27 <= median_interval <= 32:
            frequency = "monthly"

        if frequency == "irregular":
            continue

        interval_consistency = 1.0 - min(interval_mad / max(median_interval, 1.0), 1.0)
        amount_stability = 1.0 - min(amount_cv, 1.0)
        density_score = min(len(rows) / 6.0, 1.0)
        confidence = min(
            1.0,
            (0.45 * interval_consistency) + (0.35 * amount_stability) + (0.20 * density_score) + 0.2,
        )

        if confidence < 0.6:
            continue

        last_seen = timestamps[-1]
        next_expected = last_seen + timedelta(days=round(median_interval))
        patterns.append(
            {
                "counterparty_normalized": counterparty,
                "direction": direction,
                "tx_count": str(len(rows)),
                "recurring_frequency": frequency,
                "median_interval_days": f"{median_interval:.2f}",
                "interval_mad_days": f"{interval_mad:.2f}",
                "expected_amount_min_inr": f"{max(min(amounts), _safe_median(amounts) - amount_mad):.2f}",
                "expected_amount_max_inr": f"{max(amounts):.2f}",
                "next_expected_date": next_expected.date().isoformat(),
                "confidence": f"{confidence:.3f}",
                "first_seen": timestamps[0].isoformat(sep=" "),
                "last_seen": last_seen.isoformat(sep=" "),
            }
        )

    patterns.sort(key=lambda row: (-float(row["confidence"]), -int(row["tx_count"]), row["counterparty_normalized"]))
    return patterns


def detect_anomalies(feature_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    ordered_rows = sorted(
        (row for row in feature_rows if row["is_success"] == "1" and row["is_primary_event"] == "1"),
        key=_to_datetime,
    )

    history_amounts: dict[tuple[str, str], list[float]] = defaultdict(list)
    history_hours: dict[tuple[str, str], list[int]] = defaultdict(list)

    anomalies: list[dict[str, str]] = []
    for row in ordered_rows:
        key = (row["counterparty_normalized"], row["direction"])
        prior_amounts = history_amounts[key]
        prior_hours = history_hours[key]

        amount = float(row["amount_inr"])
        hour = int(row["hour_of_day"])
        amount_score = 0.0
        amount_flag = False
        if len(prior_amounts) >= 3:
            med = _safe_median(prior_amounts)
            mad = _median_absolute_deviation(prior_amounts, med)
            if mad > 0:
                robust_z = abs(0.6745 * (amount - med) / mad)
                amount_score = min(robust_z / 6.0, 1.0)
                amount_flag = robust_z >= 3.5
            else:
                amount_flag = amount > med * 1.8 if med > 0 else False
                amount_score = 1.0 if amount_flag else 0.0

        hour_flag = False
        hour_score = 0.0
        if len(prior_hours) >= 3:
            median_hour = int(round(_safe_median([float(value) for value in prior_hours])))
            distance = _clock_distance(hour, median_hour)
            hour_flag = distance >= 6
            hour_score = min(distance / 12.0, 1.0)

        new_counterparty_flag = len(prior_amounts) == 0

        score = (0.55 * amount_score) + (0.25 * (1.0 if new_counterparty_flag else 0.0)) + (0.20 * hour_score)
        reasons: list[str] = []
        if amount_flag:
            reasons.append("unusually_large_amount")
        if new_counterparty_flag:
            reasons.append("first_time_counterparty")
        if hour_flag:
            reasons.append("unusual_transaction_hour")

        anomalies.append(
            {
                "row_id": row["row_id"],
                "transaction_ts": row["transaction_ts"],
                "counterparty_normalized": row["counterparty_normalized"],
                "direction": row["direction"],
                "amount_inr": row["amount_inr"],
                "anomaly_score": f"{min(score, 1.0):.3f}",
                "amount_flag": "1" if amount_flag else "0",
                "new_counterparty_flag": "1" if new_counterparty_flag else "0",
                "unusual_hour_flag": "1" if hour_flag else "0",
                "explanations": "|".join(reasons),
            }
        )

        prior_amounts.append(amount)
        prior_hours.append(hour)

    anomalies.sort(key=lambda row: (-float(row["anomaly_score"]), row["transaction_ts"]))
    return anomalies


def build_behavior_summary(
    canonical_rows: Iterable[dict[str, str]],
    recurring_patterns: Iterable[dict[str, str]],
    anomalies: Iterable[dict[str, str]],
) -> dict[str, object]:
    rows = sorted(canonical_rows, key=_to_datetime)
    primary_rows = [row for row in rows if row["is_primary_event"] == "1"]
    successful = [row for row in primary_rows if row["is_success"] == "1"]
    debit_success = [row for row in successful if row["direction"] == "debit"]
    credit_success = [row for row in successful if row["direction"] == "credit"]

    merchant_counts = Counter(row["counterparty_normalized"] for row in debit_success)
    merchant_spend: dict[str, float] = defaultdict(float)
    weekday_spend: dict[str, float] = defaultdict(float)
    hour_counts: dict[str, int] = defaultdict(int)
    for row in debit_success:
        merchant_spend[row["counterparty_normalized"]] += float(row["amount_inr"])
        weekday_spend[row["day_of_week"]] += float(row["amount_inr"])
        hour_counts[row["hour_of_day"]] += 1

    summary = {
        "dataset": {
            "total_rows": len(rows),
            "primary_event_rows": len(primary_rows),
            "successful_rows": len(successful),
            "successful_debit_rows": len(debit_success),
            "successful_credit_rows": len(credit_success),
            "start_ts": rows[0]["transaction_ts"] if rows else "",
            "end_ts": rows[-1]["transaction_ts"] if rows else "",
        },
        "cash_flow": {
            "successful_debit_volume_inr": round(sum(float(row["amount_inr"]) for row in debit_success), 2),
            "successful_credit_volume_inr": round(sum(float(row["amount_inr"]) for row in credit_success), 2),
            "net_successful_cash_flow_inr": round(
                sum(float(row["signed_amount_inr"]) for row in successful),
                2,
            ),
        },
        "behavior": {
            "top_merchants_by_count": merchant_counts.most_common(10),
            "top_merchants_by_spend": sorted(
                ((merchant, round(value, 2)) for merchant, value in merchant_spend.items()),
                key=lambda item: (-item[1], item[0]),
            )[:10],
            "weekday_spend_inr": dict(sorted(weekday_spend.items(), key=lambda item: item[0])),
            "hour_activity_count": dict(sorted(hour_counts.items(), key=lambda item: int(item[0]))),
        },
        "signals": {
            "recurring_pattern_count": len(list(recurring_patterns)),
            "high_anomaly_count": sum(1 for row in anomalies if float(row["anomaly_score"]) >= 0.7),
        },
    }
    return summary


def write_json(path: str | Path, payload: dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
