# bb_ML Model Input/Output Specification

This document details the interface for the Budget Buddy Machine Learning (bb_ML) pipeline, including the features used for prediction and the resulting output artifacts.

## 1. Prediction Inputs (Features)

The model consumes transaction data and transforms it into the following feature set:

| Feature | Source Field | Description | Example / Transformation |
| :--- | :--- | :--- | :--- |
| **Merchant** | `counterparty_normalized` | The cleaned name of the merchant/person. | `MERCHANT=AMAZON` |
| **Merchant Tokens** | `counterparty_normalized` | Individual words from the cleaned merchant name. | `MERCHANT_TOKEN=AMAZON` |
| **Raw Tokens** | `counterparty_raw` | Words from the raw transaction note (min length 3). | `RAW_TOKEN=ORDER` |
| **Amount Bucket** | `amount_inr` | Categorical range of the transaction amount. | `AMOUNT_LT_20`, `AMOUNT_GE_1000` |
| **Time Bucket** | `hour_of_day` | Time of day classification. | `HOUR_MORNING`, `HOUR_NIGHT` |
| **Weekday** | `day_of_week` | The day the transaction occurred. | `WEEKDAY=Monday` |
| **Week of Month** | `week_of_month` | The week number within the month. | `WEEK_OF_MONTH=2` |
| **Provider Token** | `counterparty_raw` | Detected UPI provider (if applicable). | `UPI_PHONEPE`, `UPI_GPAY` |

## 2. Model Outputs (Inference)

When the backend calls `predict_category()`, the model returns a structured JSON response:

- **`predicted_category`**: The most likely category label (e.g., `Shopping`, `Food`).
- **`confidence`**: A value between 0 and 1 representing the model's certainty.
- **`alternatives`**: A list of the next most likely categories with their respective confidence scores.

## 3. Training Artifacts

The training pipeline generates the following files in the `outputs/` directory:

| Filename | Type | Description |
| :--- | :--- | :--- |
| `category_classifier_model.json` | **Model** | Serialized Naive Bayes probabilities and feature mapping. |
| `category_classifier_metrics.json` | **Metrics** | Performance scores (Accuracy, Precision, Recall). |
| `behavior_summary.json` | **Summary** | Behavioral analysis results (Anomaly counts, recurring patterns). |
| `category_predictions.csv` | **Data** | Full list of validation rows with model-assigned labels. |

## 4. Source Data Requirements

For training, the pipeline expects:
- `bhim_transactions.csv`: Raw transaction history.
- `merchant_category_map.csv`: Seed labels for merchant-to-category associations.

## 5. Testing with Curl

Since the endpoints require authentication, you'll need a valid JWT token. Replace `<TOKEN>` with your actual bearer token.

### 1. Get Behavioral Summary
```bash
curl -X GET http://localhost:8000/api/ml/summary/ \
     -H "Authorization: Bearer <TOKEN>"
```

### 2. Predict Category
```bash
curl -X POST http://localhost:8000/api/ml/categorize/ \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"note": "Zomato Dinner", "amount": 450.0}'
```

Alternative field name support (`description`):
```bash
curl -X POST http://localhost:8000/api/ml/categorize/ \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"description": "Petrol filling", "amount": 2000}'
```
