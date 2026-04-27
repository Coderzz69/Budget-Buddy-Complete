"""Raw UPI ingestion and feature generation."""

from __future__ import annotations

import csv
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .normalization import (
    extract_display_name,
    extract_upi_handle,
    normalize_counterparty,
    short_hash,
)


RAW_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"


CANONICAL_FIELDNAMES = [
    "row_id",
    "source_file",
    "event_fingerprint",
    "duplicate_group_size",
    "duplicate_rank",
    "is_primary_event",
    "transaction_ts",
    "direction",
    "status",
    "is_success",
    "is_expense_candidate",
    "is_income_candidate",
    "pay_collect",
    "amount_inr",
    "signed_amount_inr",
    "bank_name",
    "account_fingerprint",
    "counterparty_role",
    "counterparty_raw",
    "counterparty_name_raw",
    "counterparty_normalized",
    "upi_handle_hash",
    "reference_hash",
    "hour_of_day",
    "day_of_week",
    "week_of_month",
    "month_key",
]


FEATURE_FIELDNAMES = CANONICAL_FIELDNAMES + [
    "days_since_last_transaction",
    "days_since_last_same_counterparty",
    "counterparty_tx_count_prior",
    "rolling_7d_spend_before_tx_inr",
    "rolling_30d_spend_before_tx_inr",
    "rolling_7d_income_before_tx_inr",
    "rolling_30d_income_before_tx_inr",
    "assigned_category",
    "category_label_source",
]


@dataclass(frozen=True)
class ParsedRow:
    row_id: int
    transaction_ts: datetime
    raw: dict[str, str]


def _parse_datetime(date_value: str, time_value: str) -> datetime:
    return datetime.strptime(f"{date_value} {time_value}", RAW_DATETIME_FORMAT)


def _direction_from_value(value: str) -> str:
    cleaned = (value or "").strip().upper()
    if cleaned == "DR":
        return "debit"
    if cleaned == "CR":
        return "credit"
    return "unknown"


def _counterparty_role(direction: str) -> str:
    if direction == "debit":
        return "receiver"
    if direction == "credit":
        return "sender"
    return "unknown"


def _counterparty_value(row: dict[str, str], direction: str) -> str:
    if direction == "debit":
        return row.get("Receiver", "") or row.get("Sender", "")
    if direction == "credit":
        return row.get("Sender", "") or row.get("Receiver", "")
    return row.get("Receiver", "") or row.get("Sender", "")


def _week_of_month(ts: datetime) -> int:
    return ((ts.day - 1) // 7) + 1


def _event_fingerprint(raw: dict[str, str]) -> str:
    key = "|".join(
        [
            (raw.get("Date", "") or "").strip(),
            (raw.get("Time", "") or "").strip(),
            (raw.get("Amount (in Rs.)", "") or "").strip(),
            (raw.get("DR/CR", "") or "").strip(),
            (raw.get("Status", "") or "").strip(),
            (raw.get("Receiver", "") or "").strip(),
            (raw.get("Sender", "") or "").strip(),
            (raw.get("Payment ID/Reference Number", "") or "").strip(),
        ]
    )
    return short_hash(key)


def parse_raw_rows(input_path: str | Path) -> list[ParsedRow]:
    path = Path(input_path)
    parsed_rows: list[ParsedRow] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            parsed_rows.append(
                ParsedRow(
                    row_id=index,
                    transaction_ts=_parse_datetime(row["Date"], row["Time"]),
                    raw=row,
                )
            )
    return parsed_rows


def build_canonical_ledger(parsed_rows: Iterable[ParsedRow], source_file: str) -> list[dict[str, str]]:
    parsed_rows = sorted(parsed_rows, key=lambda item: item.transaction_ts)
    duplicate_sizes = Counter(_event_fingerprint(parsed.raw) for parsed in parsed_rows)
    duplicate_ranks: Counter[str] = Counter()

    rows: list[dict[str, str]] = []
    for parsed in parsed_rows:
        raw = parsed.raw
        direction = _direction_from_value(raw.get("DR/CR", ""))
        status = (raw.get("Status", "") or "").strip().upper()
        counterparty_raw = _counterparty_value(raw, direction)
        amount = float(raw.get("Amount (in Rs.)", "0") or 0)
        fingerprint = _event_fingerprint(raw)
        duplicate_rank = duplicate_ranks[fingerprint]
        duplicate_ranks[fingerprint] += 1
        is_success = status == "SUCCESS"
        is_expense_candidate = is_success and direction == "debit"
        is_income_candidate = is_success and direction == "credit"
        ts = parsed.transaction_ts
        rows.append(
            {
                "row_id": str(parsed.row_id),
                "source_file": source_file,
                "event_fingerprint": fingerprint,
                "duplicate_group_size": str(duplicate_sizes[fingerprint]),
                "duplicate_rank": str(duplicate_rank),
                "is_primary_event": "1" if duplicate_rank == 0 else "0",
                "transaction_ts": ts.isoformat(sep=" "),
                "direction": direction,
                "status": status,
                "is_success": "1" if is_success else "0",
                "is_expense_candidate": "1" if is_expense_candidate else "0",
                "is_income_candidate": "1" if is_income_candidate else "0",
                "pay_collect": (raw.get("Pay/Collect", "") or "").strip().upper(),
                "amount_inr": f"{amount:.2f}",
                "signed_amount_inr": f"{(-amount if direction == 'debit' else amount):.2f}",
                "bank_name": (raw.get("Bank Name", "") or "").strip(),
                "account_fingerprint": short_hash(raw.get("Account Number", "")),
                "counterparty_role": _counterparty_role(direction),
                "counterparty_raw": counterparty_raw.strip(),
                "counterparty_name_raw": extract_display_name(counterparty_raw),
                "counterparty_normalized": normalize_counterparty(counterparty_raw),
                "upi_handle_hash": short_hash(extract_upi_handle(counterparty_raw)),
                "reference_hash": short_hash(raw.get("Payment ID/Reference Number", "")),
                "hour_of_day": str(ts.hour),
                "day_of_week": str(ts.weekday()),
                "week_of_month": str(_week_of_month(ts)),
                "month_key": ts.strftime("%Y-%m"),
            }
        )
    return rows


def _to_datetime(row: dict[str, str]) -> datetime:
    return datetime.fromisoformat(row["transaction_ts"])


def build_feature_rows(
    canonical_rows: Iterable[dict[str, str]],
    merchant_category_map: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    merchant_category_map = merchant_category_map or {}
    ordered_rows = sorted(canonical_rows, key=_to_datetime)

    last_success_ts: datetime | None = None
    last_by_counterparty: dict[str, datetime] = {}
    prior_counts: Counter[str] = Counter()

    debit_window_7: deque[tuple[datetime, float]] = deque()
    debit_window_30: deque[tuple[datetime, float]] = deque()
    credit_window_7: deque[tuple[datetime, float]] = deque()
    credit_window_30: deque[tuple[datetime, float]] = deque()

    debit_sum_7 = 0.0
    debit_sum_30 = 0.0
    credit_sum_7 = 0.0
    credit_sum_30 = 0.0

    feature_rows: list[dict[str, str]] = []

    for row in ordered_rows:
        tx_ts = _to_datetime(row)
        while debit_window_7 and tx_ts - debit_window_7[0][0] > timedelta(days=7):
            _, value = debit_window_7.popleft()
            debit_sum_7 -= value
        while debit_window_30 and tx_ts - debit_window_30[0][0] > timedelta(days=30):
            _, value = debit_window_30.popleft()
            debit_sum_30 -= value
        while credit_window_7 and tx_ts - credit_window_7[0][0] > timedelta(days=7):
            _, value = credit_window_7.popleft()
            credit_sum_7 -= value
        while credit_window_30 and tx_ts - credit_window_30[0][0] > timedelta(days=30):
            _, value = credit_window_30.popleft()
            credit_sum_30 -= value

        counterparty = row["counterparty_normalized"]
        days_since_last = ""
        if last_success_ts is not None:
            days_since_last = f"{(tx_ts - last_success_ts).total_seconds() / 86400:.4f}"

        days_since_same = ""
        previous_same = last_by_counterparty.get(counterparty)
        if previous_same is not None:
            days_since_same = f"{(tx_ts - previous_same).total_seconds() / 86400:.4f}"

        assigned_category = merchant_category_map.get(counterparty, "")
        labeled_source = "merchant_map" if assigned_category else ""

        feature_row = dict(row)
        feature_row.update(
            {
                "days_since_last_transaction": days_since_last,
                "days_since_last_same_counterparty": days_since_same,
                "counterparty_tx_count_prior": str(prior_counts[counterparty]),
                "rolling_7d_spend_before_tx_inr": f"{debit_sum_7:.2f}",
                "rolling_30d_spend_before_tx_inr": f"{debit_sum_30:.2f}",
                "rolling_7d_income_before_tx_inr": f"{credit_sum_7:.2f}",
                "rolling_30d_income_before_tx_inr": f"{credit_sum_30:.2f}",
                "assigned_category": assigned_category,
                "category_label_source": labeled_source,
            }
        )
        feature_rows.append(feature_row)

        is_success = row["is_success"] == "1"
        is_primary = row["is_primary_event"] == "1"
        amount = float(row["amount_inr"])
        if is_success and is_primary:
            last_success_ts = tx_ts
            last_by_counterparty[counterparty] = tx_ts
            prior_counts[counterparty] += 1

            if row["direction"] == "debit":
                debit_window_7.append((tx_ts, amount))
                debit_window_30.append((tx_ts, amount))
                debit_sum_7 += amount
                debit_sum_30 += amount
            elif row["direction"] == "credit":
                credit_window_7.append((tx_ts, amount))
                credit_window_30.append((tx_ts, amount))
                credit_sum_7 += amount
                credit_sum_30 += amount

    return feature_rows


def load_merchant_category_map(mapping_path: str | Path | None) -> dict[str, str]:
    if not mapping_path:
        return {}

    path = Path(mapping_path)
    if not path.exists():
        return {}

    mapping: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            merchant = (row.get("normalized_merchant", "") or "").strip()
            category = (row.get("assigned_category", "") or row.get("label", "") or "").strip()
            if merchant and category:
                mapping[merchant] = category
    return mapping


def write_csv(path: str | Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    rows = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
