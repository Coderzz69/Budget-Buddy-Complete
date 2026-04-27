"""Compatibility wrapper for the new stdlib ML bootstrap pipeline."""

from __future__ import annotations

import csv
from pathlib import Path

from bb_ml.pipeline import build_canonical_ledger, parse_raw_rows


OUTPUT_FIELDS = ["datetime", "amount", "merchant", "Receiver"]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    parsed_rows = parse_raw_rows(base_dir / "bhim_transactions.csv")
    canonical_rows = build_canonical_ledger(parsed_rows, source_file="bhim_transactions.csv")

    cleaned_rows = [
        {
            "datetime": row["transaction_ts"],
            "amount": row["amount_inr"],
            "merchant": row["counterparty_normalized"],
            "Receiver": row["counterparty_raw"],
        }
        for row in canonical_rows
        if row["is_expense_candidate"] == "1" and row["is_primary_event"] == "1"
    ]

    output_path = base_dir / "clean_transactions.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"Transactions: {len(cleaned_rows)}")
    print(f"Wrote cleaned expense view to {output_path}")


if __name__ == "__main__":
    main()
