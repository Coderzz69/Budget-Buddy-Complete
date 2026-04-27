import csv
import random
import re
from datetime import datetime, timedelta

# Categories and their representative branded merchants
CATEGORIES = {
    "Food & Dining": [
        ("Zomato", "zomato@upi"),
        ("Swiggy", "swiggy@upi"),
        ("KFC", "kfc@okaxis"),
        ("Starbucks", "starbucks@hdfc"),
        ("Burger King", "bk@upi"),
        ("Dominos", "dominos@okicici"),
        ("Irani Cafe", "irani@okaxis"),
    ],
    "Groceries": [
        ("BigBasket", "bb@upi"),
        ("Blinkit", "blinkit@okaxis"),
        ("Zepto", "zepto@ybl"),
        ("Reliance Fresh", "reliance@hdfc"),
        ("D-Mart", "dmart@upi"),
        ("Milk Basket", "milk@okicici")
    ],
    "Shopping": [
        ("Amazon", "amazon@apl"),
        ("Flipkart", "flipkart@okaxis"),
        ("Myntra", "myntra@upi"),
        ("Zara", "zara@hdfc"),
        ("H&M", "hm@upi"),
        ("Nike", "nike@okicici"),
    ],
    "Travel": [
        ("Uber", "uber@upi"),
        ("Ola", "ola@okaxis"),
        ("IRCTC", "irctc@hdfc"),
        ("MakeMyTrip", "mmt@upi"),
        ("Goibibo", "goibibo@okicici"),
    ],
    "Recharge & Bills": [
        ("Airtel", "airtel@upi"),
        ("Jio Recharge", "jio@okaxis"),
        ("BESCOM", "bescom@hdfc"),
        ("Indane Gas", "gas@upi"),
        ("Rent Payment", "rent@okicici"),
        ("Broadband Bill", "wifi@paytm")
    ],
    "Entertainment": [
        ("Netflix", "netflix@upi"),
        ("Prime Video", "prime@okaxis"),
        ("Disney Hotstar", "hotstar@hdfc"),
        ("BookMyShow", "bms@upi"),
        ("PVR Cinemas", "pvr@okicici"),
        ("Spotify", "spotify@paytm")
    ]
}

# Micro-vendor generators for better token learning
MICRO_VENDORS = {
    "Food & Dining": {
        "prefixes": ["Anuj", "Pandit Ji", "Suresh", "Rahul", "Gupta", "Sharma", "Mishra", "Local", "Laxmi", "Bharat", "Sai", "Ganesh"],
        "suffixes": ["Chai", "Chaiwala", "Tea Stall", "Juice Centre", "Dhaba", "Tea House", "Tiffin", "Snacks", "Bakery", "Fast Food"],
        "handles": ["@upi", "@paytm", "@ybl", "@okaxis"]
    },
    "Groceries": {
        "prefixes": ["Om", "Sri", "Laxmi", "Ganesh", "Balaji", "Daily", "City", "Modern"],
        "suffixes": ["Kirana Store", "General Store", "Provisions", "Mart", "Vegetables", "Fruits", "Sweets"],
        "handles": ["@upi", "@paytm", "@ybl"]
    },
    "Travel": {
        "prefixes": ["Local", "City", "Metro", "Express", "Quick"],
        "suffixes": ["Auto", "Taxi", "Travels", "Transport", "Cabs"],
        "handles": ["@upi", "@paytm"]
    }
}

HEADER = ["Date", "Time", "Bank Name", "Account Number", "Sender", "Receiver", "Payment ID/Reference Number", "Pay/Collect", "Amount (in Rs.)", "DR/CR", "Status"]

def generate_transaction(date_obj):
    category = random.choice(list(CATEGORIES.keys()))
    
    # Selection logic: 60% Branded, 40% Micro-vendor (if available)
    is_micro = random.random() < 0.4 and category in MICRO_VENDORS
    
    if is_micro:
        gen = MICRO_VENDORS[category]
        merchant = f"{random.choice(gen['prefixes'])} {random.choice(gen['suffixes'])}"
        handle = f"{merchant.lower().replace(' ', '')}{random.choice(gen['handles'])}"
    else:
        merchant, handle = random.choice(CATEGORIES[category])
    
    # Amount logic
    if is_micro:
        if category == "Food & Dining":
            amount = round(random.uniform(5, 500), 2)
        elif category == "Groceries":
            amount = round(random.uniform(20, 1000), 2)
        else:
            amount = round(random.uniform(10, 800), 2)
    else:
        if category == "Food & Dining":
            amount = round(random.uniform(100, 2500), 2)
        elif category == "Groceries":
            amount = round(random.uniform(50, 4000), 2)
        elif category == "Shopping":
            amount = round(random.uniform(300, 10000), 2)
        elif category == "Travel":
            amount = round(random.uniform(50, 5000), 2)
        elif category == "Recharge & Bills":
            amount = round(random.uniform(200, 25000), 2)
        elif category == "Entertainment":
            amount = round(random.uniform(150, 2000), 2)
        else:
            amount = round(random.uniform(10, 100), 2)

    # UPI handle randomization
    full_receiver = f"{handle}({merchant.upper()})"
    
    tx_time = f"{random.randint(0,23):02}:{random.randint(0,59):02}:{random.randint(0,59):02}"
    ref_num = f"{random.randint(100000, 999999)}{random.randint(100000, 999999)}"
    
    row = [
        date_obj.strftime("%d/%m/%Y"),
        tx_time,
        "State Bank Of India",
        "XXXXXX7939",
        "xxxxx41450@upi(SANATH KUMAR COONANI)",
        full_receiver,
        ref_num,
        "PAY",
        amount,
        "DR",
        "SUCCESS"
    ]
    return row, merchant.upper(), category

def main(num_rows=2000):
    start_date = datetime(2026, 1, 1)
    transactions = []
    merchant_map = {}
    
    for i in range(num_rows):
        current_date = start_date + timedelta(days=random.randint(0, 100))
        tx, merchant, category = generate_transaction(current_date)
        transactions.append(tx)
        merchant_map[merchant] = category
    
    # Sort by date
    transactions.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))
    
    with open("synthetic_transactions.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(transactions)
    
    # Write merchant map
    with open("synthetic_merchant_map.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["normalized_merchant", "assigned_category", "label_notes"])
        for merchant, category in merchant_map.items():
            writer.writerow([merchant, category, "synthetic"])
    
    print(f"Generated {num_rows} transactions and merchant map")

if __name__ == "__main__":
    main()
