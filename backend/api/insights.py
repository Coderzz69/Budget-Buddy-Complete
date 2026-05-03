import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import calendar

from django.utils import timezone
from django.db.models import Sum, Q
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
        from django.utils import timezone as django_timezone
        from dateutil.relativedelta import relativedelta

        month_param = request.query_params.get('month')
        try:
            if month_param:
                target_date = datetime.datetime.strptime(month_param, '%Y-%m')
            else:
                target_date = datetime.datetime.now()
        except Exception:
            target_date = datetime.datetime.now()

        # Make target_date aware
        target_date = django_timezone.make_aware(target_date) if django_timezone.is_naive(target_date) else target_date
        # Normalize to start of month
        target_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Check Cache
        month_str = target_date.strftime('%Y-%m')
        cache_key = f"insights_{user.id}_{month_str}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 2. Extract Date Ranges
        current_start = target_date
        days_in_month = calendar.monthrange(target_date.year, target_date.month)[1]
        current_end = current_start + datetime.timedelta(days=days_in_month)
        prev_start = current_start - relativedelta(months=1)
        prev_end = current_start
        
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
            
        # 7. Aggregate Budgets (Persistent: Use latest if not set for this month)
        all_user_budgets = Budget.objects.filter(
            user=user
        ).order_by('category_id', '-month', '-createdAt').distinct('category_id').select_related('category')
        
        budget_map = {b.category.name: b.limit for b in all_user_budgets}
        actual_budget_limit = sum(budget_map.values())
        has_budget = actual_budget_limit > 0

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
        # 6. Build Breakdown List (Including categories with budgets but no spend)
        top_categories = []
        all_cat_names = set(tx_groups.keys()) | set(budget_map.keys())
        
        # Pre-fetch category styling for categories that might not have transactions
        category_styling = {
            c.name: {'icon': c.icon, 'color': c.color} 
            for c in Category.objects.filter(name__in=all_cat_names)
            .filter(Q(user=user) | Q(user__isnull=True))
        }
        
        for cat_name in all_cat_names:
            group = tx_groups.get(cat_name, {})
            amount = group.get('total', 0)
            styling = category_styling.get(cat_name, {})
            
            top_categories.append({
                'category': cat_name if cat_name else "Uncategorized",
                'amount': float(amount),
                'percentage': (float(amount) / current_total) * 100 if current_total > 0 else 0,
                'budget': float(budget_map.get(cat_name, 0)),
                'icon': group.get('category__icon') or styling.get('icon') or 'ellipsis.circle.fill',
                'color': group.get('category__color') or styling.get('color') or '#94A3B8',
            })
            
        top_categories.sort(key=lambda x: (x['amount'], x['budget']), reverse=True)
        top_categories = top_categories[:10]

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

        # 7.5. Aggregate Goals
        from .models import Goal
        user_goals = Goal.objects.filter(user=user)
        total_goal_contribution = sum(g.monthly_contribution for g in user_goals)

        insight_cards = build_insight_cards(
            period='month',
            summary=summary_data,
            top_category=target_top_category,
            highest_expense=None,
            budget_alert=None,
            peak_day=None,
            breakdown=top_categories,
            currency=user.currency,
            target_date=target_date,
            total_goal_contribution=total_goal_contribution
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
