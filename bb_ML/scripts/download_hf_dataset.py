import os
import random
import pandas as pd
from datasets import load_dataset
from datetime import datetime, timedelta

# Configuration
DATASET_NAME = "mitulshah/transaction-categorization"
OUTPUT_FILE = "bb_ML/outputs/hf_expense_training_view.csv"
SAMPLE_SIZE = 100000

# Mapping: HuggingFace -> Budget Buddy
CATEGORY_MAP = {
    "Food & Dining": "Food & Dining",
    "Shopping & Retail": "Shopping",
    "Entertainment & Recreation": "Entertainment",
    "Transportation": "Travel",
    "Healthcare & Medical": "Recharge & Bills",
    "Utilities & Services": "Recharge & Bills",
    "Financial Services": "Recharge & Bills",
    "Government & Legal": "Recharge & Bills",
    "Charity & Donations": "Shopping"
}

# Categories to skip (Income is not an expense)
SKIP_CATEGORIES = ["Income"]

def generate_synthetic_metadata():
    """Generate realistic metadata for training rows."""
    # Last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    random_days = random.randint(0, 180)
    random_seconds = random.randint(0, 86400)
    ts = start_date + timedelta(days=random_days, seconds=random_seconds)
    
    # Amount based on category (roughly)
    amount = round(random.uniform(10.0, 5000.0), 2)
    
    return {
        "transaction_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "amount_inr": f"{amount:.2f}",
        "hour_of_day": str(ts.hour),
        "day_of_week": str(ts.weekday()),
        "week_of_month": str(((ts.day - 1) // 7) + 1)
    }

def main():
    print(f"Loading dataset: {DATASET_NAME}...")
    try:
        # Load only the train split
        dataset = load_dataset(DATASET_NAME, split="train")
        df = dataset.to_pandas()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Falling back to local if already exists or reporting failure.")
        return

    print(f"Total records found: {len(df):,}")

    # 1. Filter out Income
    df = df[~df['category'].isin(SKIP_CATEGORIES)]
    
    # 2. Map Categories
    df['assigned_category'] = df['category'].map(CATEGORY_MAP)
    
    # 3. Drop rows that didn't map (though based on the dataset card they should all map)
    df = df.dropna(subset=['assigned_category'])
    
    print(f"Records after mapping: {len(df):,}")

    # 4. Sample
    if len(df) > SAMPLE_SIZE:
        print(f"Sampling {SAMPLE_SIZE:,} stratified rows using sklearn...")
        from sklearn.model_selection import train_test_split
        # Stratify keeps category distribution perfectly
        _, sampled_df = train_test_split(
            df, 
            test_size=SAMPLE_SIZE / len(df), 
            stratify=df['assigned_category'],
            random_state=42
        )
        df = sampled_df.reset_index(drop=True)
    
    # 5. Normalize Counterparty
    # The dataset uses 'transaction_description'
    df['counterparty_raw'] = df['transaction_description']
    df['counterparty_normalized'] = df['transaction_description'].str.upper().str.strip()
    
    print(f"Columns after sampling: {df.columns.tolist()}")

    # 6. Add synthetic temporal metadata
    print("Generating synthetic metadata (timestamps, amounts)...")
    metadata_list = [generate_synthetic_metadata() for _ in range(len(df))]
    metadata_df = pd.DataFrame(metadata_list)
    
    # Reset indices to merge securely
    df = df.reset_index(drop=True)
    metadata_df = metadata_df.reset_index(drop=True)
    df = pd.concat([df, metadata_df], axis=1)
    
    # 7. Select final columns
    final_cols = [
        "transaction_ts", "amount_inr", "counterparty_raw", 
        "counterparty_normalized", "assigned_category",
        "hour_of_day", "day_of_week", "week_of_month", "country"
    ]
    
    # Debug missing columns
    missing = [c for c in final_cols if c not in df.columns]
    if missing:
        print(f"Critical Error: Missing columns {missing}")
        print(f"Available columns: {df.columns.tolist()}")
        return
        
    df = df[final_cols]

    # Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved {len(df):,}-row training set to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
