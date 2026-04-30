import os
import django
import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import User, Transaction, Category
from api.ml_services import predict_category

try:
    user = User.objects.get(email='codingwithdrago@gmail.com')
    txs = Transaction.objects.filter(user=user, category__isnull=True)
    categories = {c.name: c for c in Category.objects.all()}

    print(f"Found {txs.count()} uncategorized transactions for {user.email}")

    count = 0
    for tx in txs:
        # Use occurredAt if available, otherwise now
        dt = tx.occurredAt if tx.occurredAt else datetime.datetime.now()
        
        # Try to find a description or note
        note_text = tx.note or getattr(tx, 'description', None) or "Unknown"
        
        pred = predict_category(
            note=note_text,
            amount=tx.amount,
            hour=dt.hour,
            day_of_week=dt.strftime('%A')
        )
        
        if pred and pred['predicted_category'] in categories:
            tx.category = categories[pred['predicted_category']]
            tx.save()
            count += 1

    print(f"Successfully categorized {count} transactions.")
except Exception as e:
    print(f"Error during recategorization: {e}")
