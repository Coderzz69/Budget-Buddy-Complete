import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Transaction, Budget, Category
from .shared_insights import build_insight_cards

class InsightsEngineView(APIView):
    """
    API View capable of generating comprehensive financial insights from the
    machine learning annotated MLTrainingRow table.
    """
    permission_classes = [IsAuthenticated]

    def get_month_range(self, date_obj):
        start_date = date_obj.replace(day=1)
        next_month_date = start_date + relativedelta(months=1)
        
        tz = timezone.get_current_timezone()
        start_datetime = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min), tz)
        end_datetime = timezone.make_aware(datetime.datetime.combine(next_month_date, datetime.time.min), tz)
        
        return start_datetime, end_datetime

    def get(self, request):
        user = request.user.db_user
        month_str = request.query_params.get('month')
        
        # 1. Parse constraints and default to current month if None
        if month_str:
            try:
                target_date = datetime.datetime.strptime(month_str, '%Y-%m').date()
            except ValueError:
                return Response(
                    {"error": "Invalid month format. Expected YYYY-MM."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.localtime(timezone.now()).date()
            
        # Check Cache
        cache_key = f"insights_{user.id}_{target_date.strftime('%Y-%m')}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 2. Extract Date Ranges
        tz = timezone.get_current_timezone()
        current_start, current_end = self.get_month_range(target_date)
        prev_start, prev_end = self.get_month_range(target_date - relativedelta(months=1))
        
        # 3. Query base sets
        current_txs = Transaction.objects.filter(
            user=user, 
            occurredAt__gte=current_start, 
            occurredAt__lt=current_end,
            type='expense'
        )
        prev_txs = Transaction.objects.filter(
            user=user, 
            occurredAt__gte=prev_start, 
            occurredAt__lt=prev_end,
            type='expense'
        )
        
        # 4. Compute Totals 
        current_total = current_txs.aggregate(total=Sum('amount'))['total'] or 0.0
        prev_total = prev_txs.aggregate(total=Sum('amount'))['total'] or 0.0
        
        if prev_total > 0:
            percent_change = ((current_total - prev_total) / prev_total) * 100
        else:
            percent_change = 100.0 if current_total > 0 else 0.0
            
        # 7. Aggregate Budgets (Robust against TZ shifting)
        # We fetch budgets within 24 hours of the month start to handle UTC/IST shifts correctly.
        all_user_budgets = Budget.objects.filter(
            user=user,
            month__gte=current_start - timedelta(hours=24),
            month__lt=current_start + timedelta(hours=24)
        ).select_related('category')
        
        budget_map = {b.category.name: b.limit for b in all_user_budgets}
        actual_budget_limit = sum(budget_map.values())

        # 5. Group top categories (Merged with budgets)
        tx_groups = { 
            group['category__name']: group 
            for group in current_txs.values('category__name', 'category__icon', 'category__color')\
                                    .annotate(total=Sum('amount'))
        }
        
        # Create a combined set of category names from both transactions and budgets
        # We explicitly handle None (Uncategorized) later
        all_relevant_cats = set(tx_groups.keys()) | set(budget_map.keys())

        combined_categories = []
        for cat_name in all_relevant_cats:
            tx_data = tx_groups.get(cat_name, {})
            cat_total = tx_data.get('total', 0.0)
            cat_budget = budget_map.get(cat_name, 0.0)
            
            if cat_name is None:
                # Handle Uncategorized
                combined_categories.append({
                    "category": "Uncategorized",
                    "icon": "help-circle",
                    "color": "#94A3B8",
                    "amount": round(cat_total, 2),
                    "budget": 0.0,
                    "percentage": round((cat_total / current_total) * 100, 2) if current_total > 0 else 0
                })
                continue

            # Attempt to find icon/color from category model if not in tx_data
            icon = tx_data.get('category__icon')
            color = tx_data.get('category__color')
            if not icon or not color:
                cat_obj = Category.objects.filter(name=cat_name).first()
                if cat_obj:
                    icon = icon or cat_obj.icon
                    color = color or cat_obj.color

            combined_categories.append({
                "category": cat_name,
                "icon": icon,
                "color": color,
                "amount": round(cat_total, 2),
                "budget": round(cat_budget, 2),
                "percentage": round((cat_total / current_total) * 100, 2) if current_total > 0 else 0
            })

        # Sort by spend primarily, then by budget
        combined_categories.sort(key=lambda x: (x['amount'], x['budget']), reverse=True)
        top_categories = combined_categories[:10]

        # 6. Spikes detection
        prev_categories = {
            group['category__name']: group['total'] 
            for group in prev_txs.values('category__name')\
                                .annotate(total=Sum('amount'))
        }
        
        spikes = []
        for item in combined_categories:
            cat_name = item['category']
            curr_cat_total = item['amount']
            prev_cat_total = prev_categories.get(cat_name, 0.0)
            
            if curr_cat_total > 1.5 * prev_cat_total and (curr_cat_total - prev_cat_total) > 1000:
                spikes.append({
                    "category": cat_name,
                    "increase": round(curr_cat_total - prev_cat_total, 2)
                })
        
        top_cat_name = top_categories[0]['category'] if top_categories else None

        summary_data = {
            'totalSpend': float(current_total),
            'previousSpend': float(prev_total),
            'deltaAmount': float(current_total - prev_total),
            'deltaPct': float(percent_change),
            'transactionCount': current_txs.count(),
            'budgetLimit': float(actual_budget_limit)
        }
        
        target_top_category = None
        if top_categories:
            target_top_category = {
                'categoryName': top_categories[0]['category'],
                'amount': top_categories[0]['amount'],
                'percentage': top_categories[0]['percentage'],
                'transactionCount': current_txs.filter(category__name=top_categories[0]['category']).count()
            }

        insight_cards = build_insight_cards(
            period='month',
            summary=summary_data,
            top_category=target_top_category,
            highest_expense=None,
            budget_alert=None,
            peak_day=None,
            breakdown=top_categories,
            currency=user.currency
        )
        
        # 8. Aggregate Response
        response_data = {
            "total_spent": round(current_total, 2),
            "previous_total": round(prev_total, 2),
            "percent_change": round(percent_change, 2),
            "top_categories": top_categories,
            "spikes": spikes,
            "insight_cards": insight_cards,
            "top_category": top_cat_name,
            "savings_hint": f"You spent {round(top_categories[0]['percentage'])}% on {top_cat_name}." if top_cat_name else None
        }
        
        cache.set(cache_key, response_data, 60 * 15)
        return Response(response_data)
