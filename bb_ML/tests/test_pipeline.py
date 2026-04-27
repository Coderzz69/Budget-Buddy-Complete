import unittest
from datetime import datetime

from bb_ml.pipeline import ParsedRow, build_canonical_ledger, build_feature_rows


class PipelineTests(unittest.TestCase):
    def make_raw(
        self,
        ts: datetime,
        *,
        amount: str,
        direction: str = "DR",
        status: str = "SUCCESS",
        receiver: str = "alpha@ybl(Alpha)",
        sender: str = "me@oksbi(Me)",
        reference: str = "ref-1",
    ) -> dict[str, str]:
        return {
            "Date": ts.strftime("%d/%m/%Y"),
            "Time": ts.strftime("%H:%M:%S"),
            "Amount (in Rs.)": amount,
            "DR/CR": direction,
            "Status": status,
            "Receiver": receiver,
            "Sender": sender,
            "Payment ID/Reference Number": reference,
            "Pay/Collect": "PAY",
            "Bank Name": "State Bank Of India",
            "Account Number": "1234567890",
        }

    def make_parsed(self, row_id: int, ts: datetime, raw: dict[str, str]) -> ParsedRow:
        return ParsedRow(row_id=row_id, transaction_ts=ts, raw=raw)

    def test_build_canonical_ledger_marks_duplicate_primary_events(self) -> None:
        ts_one = datetime(2026, 1, 1, 10, 0, 0)
        ts_two = datetime(2026, 1, 2, 9, 0, 0)
        duplicate_raw = self.make_raw(ts_one, amount="100.00", reference="dup-ref")
        unique_raw = self.make_raw(ts_two, amount="250.00", reference="unique-ref")
        parsed_rows = [
            self.make_parsed(1, ts_one, duplicate_raw),
            self.make_parsed(2, ts_one, duplicate_raw.copy()),
            self.make_parsed(3, ts_two, unique_raw),
        ]

        canonical_rows = build_canonical_ledger(parsed_rows, source_file="sample.csv")

        self.assertEqual(canonical_rows[0]["duplicate_group_size"], "2")
        self.assertEqual(canonical_rows[0]["duplicate_rank"], "0")
        self.assertEqual(canonical_rows[0]["is_primary_event"], "1")
        self.assertEqual(canonical_rows[1]["duplicate_group_size"], "2")
        self.assertEqual(canonical_rows[1]["duplicate_rank"], "1")
        self.assertEqual(canonical_rows[1]["is_primary_event"], "0")
        self.assertEqual(canonical_rows[2]["duplicate_group_size"], "1")
        self.assertEqual(canonical_rows[2]["is_primary_event"], "1")

    def test_build_feature_rows_only_counts_primary_success_history(self) -> None:
        first_success_ts = datetime(2026, 1, 1, 10, 0, 0)
        failed_ts = datetime(2026, 1, 2, 10, 0, 0)
        second_success_ts = datetime(2026, 1, 3, 12, 0, 0)
        first_raw = self.make_raw(first_success_ts, amount="100.00", reference="dup-ref")
        failed_raw = self.make_raw(failed_ts, amount="40.00", status="FAILED", reference="fail-ref")
        second_raw = self.make_raw(second_success_ts, amount="60.00", reference="success-ref")
        parsed_rows = [
            self.make_parsed(1, first_success_ts, first_raw),
            self.make_parsed(2, first_success_ts, first_raw.copy()),
            self.make_parsed(3, failed_ts, failed_raw),
            self.make_parsed(4, second_success_ts, second_raw),
        ]

        canonical_rows = build_canonical_ledger(parsed_rows, source_file="sample.csv")
        feature_rows = build_feature_rows(canonical_rows, merchant_category_map={"ALPHA": "Groceries"})
        latest_row = next(row for row in feature_rows if row["row_id"] == "4")

        self.assertEqual(latest_row["assigned_category"], "Groceries")
        self.assertEqual(latest_row["counterparty_tx_count_prior"], "1")
        self.assertEqual(latest_row["rolling_7d_spend_before_tx_inr"], "100.00")
        self.assertAlmostEqual(float(latest_row["days_since_last_transaction"]), 2.0833, places=4)
        self.assertAlmostEqual(float(latest_row["days_since_last_same_counterparty"]), 2.0833, places=4)


if __name__ == "__main__":
    unittest.main()
