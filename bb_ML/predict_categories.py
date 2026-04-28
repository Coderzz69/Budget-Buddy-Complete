#!/usr/bin/env python3
import json
import csv
import argparse
from pathlib import Path
from bb_ml.classifier import NaiveBayesCategoryClassifier, load_expense_rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs/behavior_event_view.csv")
    parser.add_argument("--model", default="outputs/category_classifier_model.json")
    parser.add_argument("--output", default="outputs/behavior_event_view_predicted.csv")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    input_path = (base_dir / args.input).resolve()
    model_path = (base_dir / args.model).resolve()
    output_path = (base_dir / args.output).resolve()

    if not model_path.exists():
        print(f"Model not found at {model_path}. Train the model first.")
        return

    with model_path.open("r", encoding="utf-8") as f:
        model_dict = json.load(f)
        model = NaiveBayesCategoryClassifier.from_dict(model_dict)

    rows = load_expense_rows(input_path)
    
    # We only predict for debits that don't have an assigned_category or if we want to override
    predicted_count = 0
    for row in rows:
        if row["direction"] == "debit":
            # If it doesn't have an assigned category, or it was assigned from the small merchant map,
            # we let the model decide (which uses the merchant map first anyway, then NB).
            prediction, confidence = model.predict(row)
            row["assigned_category"] = prediction
            row["category_label_source"] = "model_prediction"
            predicted_count += 1

    fieldnames = list(rows[0].keys()) if rows else []
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Applied predictions to {predicted_count} debit transactions.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
