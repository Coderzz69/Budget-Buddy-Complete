#!/usr/bin/env python3
import csv
import random
from datetime import datetime, timedelta

def generate_student_statement():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    merchants = {
        "Food & Dining": ["College Canteen", "Zomato", "Swiggy", "Starbucks", "Chai Point", "Burger King", "Domino's", "Maggie Point"],
        "Travel": ["Uber", "Ola", "Metro Rail", "Auto Rickshaw", "IRCTC", "BluSmart"],
        "Shopping": ["Amazon", "Flipkart", "Myntra", "College Bookstore", "Decathlon", "Uniqlo"],
        "Entertainment": ["Netflix", "Spotify", "PVR Cinemas", "BookMyShow", "Steam Games", "Nintendo eShop"],
        "Recharge & Bills": ["Airtel Prepaid", "Jio Recharge", "Hostel Electricity", "Wanderlust Wifi"],
        "Groceries": ["Blinkit", "Zepto", "BigBasket", "Local Kirana Store"]
    }
    
    rows = []
    current_date = start_date
    
    # Static Bank Info
    bank_name = "HDFC BANK"
    account_number = "XXXXXX1234"
    
    while current_date <= end_date:
        # 1. Monthly Income (Pocket Money from Parents) on the 2nd
        if current_date.day == 2:
            rows.append({
                "Date": current_date.strftime("%d/%m/%Y"),
                "Time": "10:30:00",
                "Amount (in Rs.)": "15000.00",
                "DR/CR": "CR",
                "Status": "SUCCESS",
                "Sender": "Dad (UPI: parent@okhdfc)",
                "Receiver": "STUDENT NAME",
                "Payment ID/Reference Number": f"REF{random.randint(100000, 999999)}",
                "Pay/Collect": "COLLECT",
                "Bank Name": bank_name,
                "Account Number": account_number
            })
            
        # 2. Monthly Rent on the 1st
        if current_date.day == 1:
            rows.append({
                "Date": current_date.strftime("%d/%m/%Y"),
                "Time": "09:00:00",
                "Amount (in Rs.)": "8000.00",
                "DR/CR": "DR",
                "Status": "SUCCESS",
                "Sender": "STUDENT NAME",
                "Receiver": "Hostel/PG Rent",
                "Payment ID/Reference Number": f"REF{random.randint(100000, 999999)}",
                "Pay/Collect": "PAY",
                "Bank Name": bank_name,
                "Account Number": account_number
            })
            
        # 3. Daily Expenses
        num_expenses = random.randint(1, 4)
        for _ in range(num_expenses):
            # Select weighted category
            category = random.choices(
                list(merchants.keys()),
                weights=[30, 25, 10, 10, 10, 15]
            )[0]
            
            merchant = random.choice(merchants[category])
            
            # Amount based on category
            if category == "Food & Dining":
                amount = random.uniform(50, 600)
            elif category == "Travel":
                amount = random.uniform(40, 400)
            elif category == "Shopping":
                amount = random.uniform(200, 2500)
            elif category == "Entertainment":
                amount = random.uniform(149, 800)
            elif category == "Recharge & Bills":
                amount = random.uniform(199, 499)
            else: # Groceries
                amount = random.uniform(100, 1200)
                
            time = f"{random.randint(8, 22):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            
            rows.append({
                "Date": current_date.strftime("%d/%m/%Y"),
                "Time": time,
                "Amount (in Rs.)": f"{amount:.2f}",
                "DR/CR": "DR",
                "Status": "SUCCESS",
                "Sender": "STUDENT NAME",
                "Receiver": f"{merchant} (UPI: shopping@upi)",
                "Payment ID/Reference Number": f"REF{random.randint(100000, 999999)}",
                "Pay/Collect": "PAY",
                "Bank Name": bank_name,
                "Account Number": account_number
            })
            
        current_date += timedelta(days=1)
        
    # Sort by date and time
    rows.sort(key=lambda x: datetime.strptime(f"{x['Date']} {x['Time']}", "%d/%m/%Y %H:%M:%S"))
    
    # Write to CSV
    output_path = "student_bank_statement.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Generated {len(rows)} transactions in {output_path}")

if __name__ == "__main__":
    generate_student_statement()
