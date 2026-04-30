import os
import django
import datetime
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import User, Transaction, Budget, Category
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from datetime import timedelta

user = User.objects.get(email='codingwithdrago@gmail.com')
target_date = datetime.date(2026, 4, 1)

# Logic from InsightsEngineView
start_date = target_date.replace(day=1)
next_month_date = start_date + relativedelta(months=1)
tz = timezone.get_current_timezone()
current_start = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min), tz)
current_end = timezone.make_aware(datetime.datetime.combine(next_month_date, datetime.time.min), tz)

print(f"Current Start: {current_start}")
print(f"Current Start (UTC): {current_start.astimezone(datetime.timezone.utc)}")

budgets = Budget.objects.filter(
    user=user,
    month__gte=current_start - timedelta(hours=24), 
    month__lt=current_end
)

print(f"Budgets found: {budgets.count()}")
for b in budgets:
    print(f" - {b.category.name}: {b.limit} (Month: {b.month})")

budget_map = { b.category.name: b.limit for b in budgets }
print(f"Budget Map: {budget_map}")

current_txs = Transaction.objects.filter(
    user=user,
    occurredAt__gte=current_start,
    occurredAt__lt=current_end
)
print(f"Transactions count: {current_txs.count()}")

tx_groups = { 
    group['category__name']: group 
    for group in current_txs.values('category__name', 'category__icon', 'category__color')\
                            .annotate(total=Sum('amount'))
}
print(f"TX groups keys: {list(tx_groups.keys())}")

all_relevant_cats = set(tx_groups.keys()) | set(budget_map.keys())
print(f"All relevant categories: {all_relevant_cats}")
