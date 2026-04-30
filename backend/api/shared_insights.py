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
    currency: str = 'INR'
) -> List[Dict[str, Any]]:
    cards = []
    period_label = _period_label(period)
    delta_amount = summary.get('deltaAmount', 0)
    delta_pct = summary.get('deltaPct', 0)
    total_spend = summary.get('totalSpend', 0)

    # 1. Spotlight Summary
    if total_spend > 0:
        raw_limit = summary.get('budgetLimit', 0)
        has_budget = raw_limit > 0
        budget_limit = raw_limit if has_budget else 10000.0
        
        status = "On Track"
        if not has_budget:
            status = "No budget set"
        elif total_spend > budget_limit:
            status = "Over Budget"
        elif total_spend < budget_limit * 0.8:
            status = "Under Budget (Excellent)"
            
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

    # 2. Reduction Suggestion
    discretionary_cats = ['food', 'dining', 'shopping', 'entertainment', 'lifestyle', 'travel']
    reduction_candidates = [
        item for item in breakdown 
        if any(cat in (item.get('categoryName') or item.get('category', '')).lower() for cat in discretionary_cats) 
        and item.get('percentage', 0) > 20
    ]
    if reduction_candidates:
        worst = max(reduction_candidates, key=lambda x: x['percentage'])
        cards.append({
            'id': 'reduction-tip',
            'kind': 'reduction',
            'title': 'Trimming Opportunity',
            'message': f"You're spending {worst['percentage']:.0f}% on {worst.get('categoryName') or worst.get('category')}. Small adjustments here could save you {currency} {worst['amount']*0.15:,.0f} next month.",
            'tone': 'warning',
            'amount': worst['amount'] * 0.15, 
            'footer': "Target: 15% reduction",
        })

    # 3. Potential to spend more (Opportunity)
    budget_limit = summary.get('budgetLimit', 10000)
    if 0 < total_spend < budget_limit * 0.7:
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

    # 4. Spending Change Insight
    if delta_pct != 0 and summary.get('previousSpend', 0) > 0:
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

    # 5. Top Category Detail
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

    return cards[:6]
