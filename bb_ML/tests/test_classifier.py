import unittest

from bb_ml.classifier import (
    NaiveBayesCategoryClassifier,
    build_accuracy_report_markdown,
    evaluate_classifier,
    extract_features,
    split_labeled_rows,
    split_labeled_rows_by_merchant,
)


class ClassifierTests(unittest.TestCase):
    def make_row(
        self,
        *,
        ts: str,
        merchant: str,
        raw: str,
        label: str,
        amount: str = "120.00",
        hour: str = "10",
        weekday: str = "1",
        week_of_month: str = "1",
    ) -> dict[str, str]:
        return {
            "row_id": ts,
            "transaction_ts": ts,
            "counterparty_normalized": merchant,
            "counterparty_raw": raw,
            "amount_inr": amount,
            "hour_of_day": hour,
            "day_of_week": weekday,
            "week_of_month": week_of_month,
            "assigned_category": label,
        }

    def test_extract_features_includes_expected_tokens_and_buckets(self) -> None:
        row = self.make_row(
            ts="2026-01-05 19:15:00",
            merchant="BIG BAZAAR",
            raw="bigbazaar@oksbi(Big Bazaar)",
            label="Groceries",
            amount="349.00",
            hour="19",
            weekday="2",
            week_of_month="3",
        )

        features = set(extract_features(row))

        self.assertIn("MERCHANT=BIG BAZAAR", features)
        self.assertIn("MERCHANT_TOKEN=BIG", features)
        self.assertIn("MERCHANT_TOKEN=BAZAAR", features)
        self.assertIn("RAW_TOKEN=BIGBAZAAR", features)
        self.assertIn("AMOUNT_250_499", features)
        self.assertIn("HOUR_EVENING", features)
        self.assertIn("WEEKDAY=2", features)
        self.assertIn("WEEK_OF_MONTH=3", features)
        self.assertIn("UPI_OKSBI", features)

    def test_split_labeled_rows_keeps_small_classes_in_train(self) -> None:
        groceries = [
            self.make_row(
                ts=f"2026-01-0{day} 09:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            )
            for day in range(1, 6)
        ]
        travel = [
            self.make_row(
                ts=f"2026-01-0{day} 11:00:00",
                merchant="CITY CABS",
                raw="cabs@ybl(City Cabs)",
                label="Travel",
            )
            for day in range(6, 9)
        ]

        train_rows, validation_rows = split_labeled_rows(groceries + travel)

        self.assertEqual(len(validation_rows), 1)
        self.assertEqual(validation_rows[0]["transaction_ts"], "2026-01-05 09:00:00")
        self.assertEqual(sum(1 for row in train_rows if row["assigned_category"] == "Travel"), 3)

    def test_split_labeled_rows_by_merchant_holds_out_last_sorted_merchant(self) -> None:
        rows = [
            self.make_row(
                ts=f"2026-02-0{idx} 10:00:00",
                merchant=merchant,
                raw=f"{merchant.lower().replace(' ', '')}@ybl({merchant})",
                label="Groceries",
            )
            for idx, merchant in enumerate(["ALPHA STORE", "BETA STORE", "ZETA STORE"], start=1)
        ]
        rows.append(
            self.make_row(
                ts="2026-02-04 12:00:00",
                merchant="PERSON ONE",
                raw="person@oksbi(Person One)",
                label="Transfers",
            )
        )

        train_rows, validation_rows = split_labeled_rows_by_merchant(rows)

        self.assertEqual({row["counterparty_normalized"] for row in validation_rows}, {"ZETA STORE"})
        self.assertIn("PERSON ONE", {row["counterparty_normalized"] for row in train_rows})

    def test_merchant_map_fallback_predicts_exact_label(self) -> None:
        train_rows = [
            self.make_row(
                ts="2026-01-01 09:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            ),
            self.make_row(
                ts="2026-01-02 09:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            ),
            self.make_row(
                ts="2026-01-01 12:00:00",
                merchant="TASTY BITE",
                raw="tasty@ybl(Tasty Bite)",
                label="Food & Dining",
            ),
            self.make_row(
                ts="2026-01-02 12:00:00",
                merchant="TASTY BITE",
                raw="tasty@ybl(Tasty Bite)",
                label="Food & Dining",
            ),
        ]
        model = NaiveBayesCategoryClassifier.train(train_rows)

        predicted_label, confidence = model.predict(
            self.make_row(
                ts="2026-02-01 18:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
                amount="999.00",
                hour="18",
            )
        )

        self.assertEqual(predicted_label, "Groceries")
        self.assertAlmostEqual(confidence, 0.995, places=3)

    def test_evaluate_classifier_reports_confusions_and_errors(self) -> None:
        train_rows = [
            self.make_row(
                ts="2026-01-01 09:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            ),
            self.make_row(
                ts="2026-01-02 09:30:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            ),
            self.make_row(
                ts="2026-01-01 12:00:00",
                merchant="TASTY BITE",
                raw="tasty@ybl(Tasty Bite)",
                label="Food & Dining",
            ),
            self.make_row(
                ts="2026-01-02 12:30:00",
                merchant="TASTY BITE",
                raw="tasty@ybl(Tasty Bite)",
                label="Food & Dining",
            ),
            self.make_row(
                ts="2026-01-01 15:00:00",
                merchant="PERSON ONE",
                raw="person@oksbi(Person One)",
                label="Transfers",
            ),
            self.make_row(
                ts="2026-01-02 15:30:00",
                merchant="PERSON ONE",
                raw="person@oksbi(Person One)",
                label="Transfers",
            ),
        ]
        model = NaiveBayesCategoryClassifier.train(train_rows)
        validation_rows = [
            self.make_row(
                ts="2026-02-01 09:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Groceries",
            ),
            self.make_row(
                ts="2026-02-02 12:00:00",
                merchant="TASTY BITE",
                raw="tasty@ybl(Tasty Bite)",
                label="Food & Dining",
            ),
            self.make_row(
                ts="2026-02-03 18:00:00",
                merchant="FRESH MART",
                raw="fresh@oksbi(Fresh Mart)",
                label="Food & Dining",
            ),
        ]

        metrics = evaluate_classifier(model, validation_rows)
        report = build_accuracy_report_markdown(
            {
                "generated_at": "2026-04-21T12:00:00+00:00",
                "dataset": {
                    "total_rows": 3,
                    "labeled_rows": 3,
                    "unlabeled_rows": 0,
                    "unique_labeled_merchants": 2,
                    "merchant_map_size": 3,
                    "label_distribution": {"Groceries": 1, "Food & Dining": 2},
                },
                "time_split": metrics,
            }
        )

        self.assertEqual(metrics["top_1_accuracy"], 0.6667)
        self.assertEqual(metrics["top_3_accuracy"], 1.0)
        self.assertEqual(metrics["merchant_map_hit_rate"], 1.0)
        self.assertEqual(metrics["confusion_matrix"]["Food & Dining"]["Groceries"], 1)
        self.assertEqual(len(metrics["error_examples"]), 1)
        self.assertEqual(metrics["error_examples"][0]["predicted_category"], "Groceries")
        self.assertIn("## Time-Split Validation", report)
        self.assertIn("| Food & Dining | Groceries | 1 |", report)


if __name__ == "__main__":
    unittest.main()
