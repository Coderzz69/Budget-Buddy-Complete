import datetime
from typing import Any, Dict, List, Optional

def _period_label(period: str) -> str:
    return "month" if period == 'month' else "period"

def _tone_for_delta(delta: float) -> str:
    if delta > 0:
        return 'warning'
    return 'success'

def build_insight_cards(
    *,
    period: str,
    summary: Dict[str, Any],
    top_category: Optional[Dict[str, Any]],
    highest_expense: Optional[Dict[str, Any]],
    budget_alert: Optional[Dict[str, Any]],
    peak_day: Optional[Dict[str, Any]],
    breakdown: List[Dict[str, Any]],
    currency: str = 'INR',
    target_date: Optional[datetime.date] = None,
    total_goal_contribution: float = 0.0
) -> List[Dict[str, Any]]:
    cards = []
    period_label = _period_label(period)
    delta_amount = summary.get('deltaAmount', 0)
    delta_pct = summary.get('deltaPct', 0)
    total_spend = summary.get('totalSpend', 0)
    raw_limit = summary.get('budgetLimit', 0)
    has_budget = raw_limit > 0
    budget_limit = raw_limit if has_budget else 10000.0

    # Time-aware calculations
    now = datetime.date.today()
    is_current_month = target_date and target_date.year == now.year and target_date.month == now.month
    day_of_month = now.day
    import calendar
    _, days_in_month = calendar.monthrange(now.year, now.month)
    pro_rated_budget = (budget_limit * day_of_month) / days_in_month if is_current_month else budget_limit

    # 1. Top Category Detail
    if top_category:
        name = top_category.get('categoryName') or top_category.get('category')
        cards.append({
            'id': 'top-category',
            'kind': 'top_category',
            'title': 'Top Category',
            'message': f"{name} drove {top_category['percentage']:.0f}% of spending.",
            'tone': 'warning' if top_category['percentage'] >= 40 else 'positive',
            'amount': top_category['amount'],
            'footer': f"{top_category.get('transactionCount', '')} transactions",
        })

    # 2. Spotlight Summary
    if total_spend > 0:
        status = "On Track"
        if not has_budget:
            status = "No budget set"
        elif total_spend > budget_limit:
            status = "Over Budget"
        else:
            if is_current_month:
                if total_spend > pro_rated_budget * 1.1:
                    status = "Spending Fast"
                elif total_spend < pro_rated_budget * 0.7:
                    status = "Under Budget (Excellent)"
                else:
                    status = "On Track"
            else:
                # For past months
                if total_spend < budget_limit * 0.8:
                    status = "Under Budget (Excellent)"
                else:
                    status = "On Track"
            
        message = f"You've spent {currency} {total_spend:,.2f} this month."
        if not has_budget:
            message += f" Status: {status}. Set a budget to track your progress effectively."
        else:
            message += f" Status: {status}."

        cards.append({
            'id': 'spotlight',
            'kind': 'spotlight',
            'title': 'Overall Summary',
            'message': message,
            'tone': 'info' if status in ["On Track", "No budget set"] else ('success' if "Excellent" in status else 'warning'),
            'amount': total_spend,
            'footer': f"Current monthly budget limit: {currency} {budget_limit:,.0f}" if has_budget else f"Recommended monthly limit: {currency} {budget_limit:,.0f}",
        })

    # 3. Reduction Suggestion
    discretionary_cats = ['food', 'dining', 'shopping', 'entertainment', 'lifestyle', 'travel']
    reduction_candidates = [
        item for item in breakdown 
        if any(cat in (item.get('categoryName') or item.get('category', '')).lower() for cat in discretionary_cats) 
        and item.get('percentage', 0) > 20
    ]
    if reduction_candidates:
        worst = max(reduction_candidates, key=lambda x: x['percentage'])
        spent = worst['amount']
        cat_budget = worst.get('budget', 0)
        
        if cat_budget > 0 and spent > cat_budget:
            over_amount = spent - cat_budget
            cards.append({
                'id': 'reduction-tip',
                'kind': 'reduction',
                'title': 'Budget Alert',
                'message': f"You're over budget on {worst.get('categoryName') or worst.get('category')} by {currency} {over_amount:,.0f}. Bringing this back to your limit would save you the most.",
                'tone': 'warning',
                'amount': over_amount,
                'footer': f"Current budget: {currency} {cat_budget:,.0f}",
            })
        else:
            saving = spent * 0.15
            cards.append({
                'id': 'reduction-tip',
                'kind': 'reduction',
                'title': 'Trimming Opportunity',
                'message': f"You're spending {worst['percentage']:.0f}% on {worst.get('categoryName') or worst.get('category')}. Small adjustments here could save you {currency} {saving:,.0f} next month.",
                'tone': 'warning',
                'amount': saving, 
                'footer': "Target: 15% reduction",
            })

    # 4. Potential to spend more (Opportunity)
    if 0 < total_spend < budget_limit * 0.7:
        # Only suggest a "treat" if they are also under their pro-rated budget for the day
        if not is_current_month or total_spend < pro_rated_budget:
            buffer = budget_limit - total_spend
            cards.append({
                'id': 'spending-buffer',
                'kind': 'opportunity',
                'title': 'Spending Buffer',
                'message': f"You have a {currency} {buffer:,.0f} buffer remaining this month. Perfect for a well-deserved treat.",
                'tone': 'success',
                'amount': buffer,
                'footer': "Safe to spend more",
            })
        elif is_current_month:
            # If they are under total but spending fast, give a more cautious message
            buffer = budget_limit - total_spend
            cards.append({
                'id': 'spending-buffer',
                'kind': 'opportunity',
                'title': 'Remaining Funds',
                'message': f"You have {currency} {buffer:,.0f} left in your budget, but you're spending faster than usual today. Tread carefully!",
                'tone': 'info',
                'amount': buffer,
                'footer': "Watch your daily pace",
            })

    # 5. Monthly Progress & Recovery Advice
    overspent_list = [c for c in breakdown if c.get('budget', 0) > 0 and c['amount'] > c['budget']]
    if overspent_list:
        total_over = sum(c['amount'] - c['budget'] for c in overspent_list)
        others = [c for c in breakdown if c.get('budget', 0) > 0 and c['amount'] < c['budget']]
        other_remaining_budget = sum(c['budget'] - c['amount'] for c in others)

        if len(overspent_list) > 1:
            names = [c.get('categoryName') or c.get('category') for c in overspent_list]
            cat_str = f"{', '.join(names[:-1])} and {names[-1]}"
            if other_remaining_budget > 0:
                reduction_pct = min((total_over / other_remaining_budget) * 100, 100)
                message = f"You've overspent on {cat_str}. Reduce spending on other categories by {reduction_pct:.0f}% to recover."
            else:
                message = f"You've overspent on {cat_str}. No budget remaining in other categories. Stop all non-essential spending."
        else:
            worst_over = overspent_list[0]
            cat_name = worst_over.get('categoryName') or worst_over.get('category')
            if other_remaining_budget > 0:
                reduction_pct = min((total_over / other_remaining_budget) * 100, 100)
                message = f"You've overspent on {cat_name}. Reduce spending on other categories by {reduction_pct:.0f}% to stay in your safe space."
            else:
                message = f"You're over budget on {cat_name}. Stop non-essential spending immediately to recover."
            
        cards.append({
            'id': 'spend-change',
            'kind': 'spend_change',
            'title': 'Monthly Progress',
            'message': message,
            'tone': 'warning',
            'amount': total_over,
            'footer': f"Overspent by {currency} {total_over:,.0f} so far",
        })
    elif delta_pct != 0 and summary.get('previousSpend', 0) > 0:
        direction = 'more' if delta_amount > 0 else 'less'
        tone = _tone_for_delta(delta_amount)
        
        message = f"Spent {abs(delta_pct):.0f}% {direction} than last {period_label}."
        if delta_amount < 0:
            message = f"Great work! You spent {abs(delta_pct):.0f}% less than last {period_label}."
            
        cards.append({
            'id': 'spend-change',
            'kind': 'spend_change',
            'title': 'Monthly Progress',
            'message': message,
            'tone': tone,
            'amount': abs(delta_amount),
            'footer': f"{summary.get('transactionCount', 0)} expenses this {period_label}",
        })

    # 6. Goal-Oriented Savings
    if total_goal_contribution > 0 and has_budget:
        # Check if they are on track to save enough for their goals
        projected_total = total_spend + total_goal_contribution
        if projected_total > budget_limit:
            extra_needed = projected_total - budget_limit
            # How much % they need to cut from their current budget to fit the goals
            reduction_needed_pct = (extra_needed / budget_limit) * 100
            
            warning_prefix = ""
            if delta_pct > 15:
                warning_prefix = "Your spending has shot up this month! "
            
            cards.append({
                'id': 'goal-insight',
                'kind': 'goal_tracking',
                'title': 'Savings Goal Insight',
                'message': f"{warning_prefix}To hit your monthly goals, you need to save an additional {reduction_needed_pct:.0f}% off every category.",
                'tone': 'warning' if delta_pct > 15 else 'info',
                'amount': extra_needed,
                'footer': f"Target Monthly Savings: {currency} {total_goal_contribution:,.0f}",
            })
        else:
            cards.append({
                'id': 'goal-insight',
                'kind': 'goal_tracking',
                'title': 'Savings Goal Insight',
                'message': "You're perfectly on track to meet your savings goals this month! Keep it up.",
                'tone': 'success',
                'amount': total_goal_contribution,
                'footer': "Goals are fully funded",
            })

    return cards[:7] # Allow 7 cards now
