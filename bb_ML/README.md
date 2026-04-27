# Budget Buddy ML Bootstrap

This directory now contains the first working slice of the ML pipeline described in [Budget-Buddy/plan.md](/home/sanathcoonani/Desktop/Budget_Buddy_app/Budget-Buddy/plan.md).

The implementation is stdlib-first so it works even when notebook dependencies such as `pandas` are not installed.

## What it builds

Starting from `bhim_transactions.csv`, the pipeline produces:

- `outputs/canonical_ledger.csv`
- `outputs/transaction_features.csv`
- `outputs/behavior_event_view.csv`
- `outputs/expense_training_view.csv`
- `outputs/merchant_label_candidates.csv`
- `outputs/merchant_category_map_template.csv`
- `outputs/recurring_patterns.csv`
- `outputs/anomaly_scores.csv`
- `outputs/behavior_summary.json`
- `ml_io_spec.md` (Interface specification)

## Usage

From `bb_ML/`:

```bash
python3 build_ml_assets.py
```

Optional:

```bash
python3 build_ml_assets.py --label-map merchant_category_map.csv
```

## Current scope

Implemented now:

- raw UPI ingestion into a canonical ledger
- debit and credit preservation
- duplicate-event detection with a primary-event behavior view
- counterparty normalization with hashed identifiers
- rolling spend and income features
- recurring-pattern baseline detection
- anomaly baseline scoring
- merchant labeling candidate generation
- first bootstrap category classifier training

Not implemented yet:

- supervised category training
- backend model serving
- frontend insight integration

## Category classifier

Train the first classifier after labeling merchants:

```bash
python3 train_category_classifier.py
```

Outputs:

- `outputs/category_classifier_model.json`
- `outputs/category_classifier_metrics.json`
- `outputs/category_predictions.csv`
- `outputs/category_classifier_accuracy_report.md`

The current classifier is intentionally simple:

- exact merchant-match fallback from the merchant map
- Naive Bayes over merchant tokens, UPI provider tokens, amount buckets, and time buckets for unseen merchants

The accuracy report now includes:

- time-split and merchant-holdout evaluation
- macro and weighted F1
- per-label precision, recall, and F1
- top confusion pairs
- representative high-confidence mistakes

## Tests

Run the ML unit tests from `bb_ML/`:

```bash
python3 -m unittest discover -s tests -v
```

The current suite covers:

- feature extraction tokens and bucketing
- label split behavior
- merchant-holdout split behavior
- merchant-map fallback predictions
- duplicate-event handling in the ledger
- rolling feature generation from primary successful events only

## Merchant labeling workflow

1. Run `python3 build_ml_assets.py`.
2. Open `outputs/merchant_category_map_template.csv`.
3. Copy it to `merchant_category_map.csv`.
4. Fill `assigned_category` for the merchants you trust.
5. Re-run the build command to propagate labels into `transaction_features.csv` and `expense_training_view.csv`.
6. Run `python3 train_category_classifier.py` to regenerate the model and accuracy report.
