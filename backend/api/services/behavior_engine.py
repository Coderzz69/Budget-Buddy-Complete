from datetime import timedelta
from collections import defaultdict
from django.utils import timezone
from django.db.models import Sum, Q, Avg
from api.models import UserBehaviorProfile, Transaction, Account, PredictionCache

class BehaviorEngine:
    """
    Core engine for computing user behavioral heuristics and generating predictions.
    This class is designed to run asynchronously via Celery.
    """

    def __init__(self, user):
        self.user = user

    def run_full_analysis(self):
        """
        Orchestrates the full behavioral analysis pipeline.
        Must be called from a Celery task.
        """
        self._compute_salary_expectation()
        self._compute_weekend_overspend_ratio()
        self._compute_monthly_burn_rate()
        
        self._generate_trajectory_forecast()

    def _compute_salary_expectation(self):
        """
        Heuristic: Look at high-value recurring income transactions to 
        determine likely salary credit days.
        """
        # Get income transactions over the last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        incomes = Transaction.objects.filter(
            user=self.user,
            type='income',
            occurredAt__gte=six_months_ago
        )
        
        # Group by day of month
        day_counts = defaultdict(int)
        day_amounts = defaultdict(float)
        
        for tx in incomes:
            day = tx.occurredAt.day
            day_counts[day] += 1
            day_amounts[day] += tx.amount

        if not day_counts:
            return

        # Find the day with the highest frequency and volume
        best_day = max(day_counts.keys(), key=lambda d: (day_counts[d], day_amounts[d]))
        
        # Save to profile
        profile, _ = UserBehaviorProfile.objects.get_or_create(user=self.user)
        profile.salary_credit_date_expected = best_day
        profile.save()

    def _compute_weekend_overspend_ratio(self):
        """
        Compares average daily spend on weekends vs weekdays.
        """
        three_months_ago = timezone.now() - timedelta(days=90)
        expenses = Transaction.objects.filter(
            user=self.user,
            type='expense',
            occurredAt__gte=three_months_ago
        )

        weekday_spend = 0.0
        weekend_spend = 0.0
        weekday_count = 0
        weekend_count = 0

        # Group transactions by date to get daily totals
        daily_totals = defaultdict(float)
        for tx in expenses:
            date_key = tx.occurredAt.date()
            daily_totals[date_key] += tx.amount

        for date_obj, total in daily_totals.items():
            # ISO weekday: 1 = Monday, 7 = Sunday
            if date_obj.isoweekday() >= 6: 
                weekend_spend += total
                weekend_count += 1
            else:
                weekday_spend += total
                weekday_count += 1

        avg_weekday = weekday_spend / weekday_count if weekday_count else 0.0
        avg_weekend = weekend_spend / weekend_count if weekend_count else 0.0

        # Ratio > 1 implies weekend overspend
        ratio = 1.0
        if avg_weekday > 0:
            ratio = avg_weekend / avg_weekday
        elif avg_weekend > 0:
            ratio = 2.0 # Arbitrary cap if no weekday spend but weekend spend exists

        profile, _ = UserBehaviorProfile.objects.get_or_create(user=self.user)
        profile.weekend_overspend_ratio = round(ratio, 2)
        profile.save()

    def _compute_monthly_burn_rate(self):
        """
        Calculates average daily burn rate based on trailing 30, 60, and 90 days.
        """
        ninety_days_ago = timezone.now() - timedelta(days=90)
        expenses = Transaction.objects.filter(
            user=self.user,
            type='expense',
            occurredAt__gte=ninety_days_ago
        )
        
        total_spend = sum(tx.amount for tx in expenses)
        days_active = 90 # Simplified; could be dynamic based on first transaction
        
        daily_burn = total_spend / days_active if days_active else 0.0
        monthly_burn = daily_burn * 30

        profile, _ = UserBehaviorProfile.objects.get_or_create(user=self.user)
        profile.average_monthly_burn = round(monthly_burn, 2)
        profile.save()

    def _generate_trajectory_forecast(self):
        """
        Projects account balances into the future.
        """
        profile, _ = UserBehaviorProfile.objects.get_or_create(user=self.user)
        daily_burn = float(profile.average_monthly_burn or 0.0) / 30.0

        target_date = timezone.now()
        balances = Account.objects.filter(user=self.user).aggregate(total=Sum('balance'))
        current_balance = float(balances['total'] or 0.0)

        trajectory_data = []
        runout_date = None

        # Forecast next 30 days
        for day_offset in range(31):
            forecast_date = target_date + timedelta(days=day_offset)
            projected_balance = current_balance - (daily_burn * day_offset)
            
            # Simple simulation: add salary if expected
            if profile.salary_credit_date_expected and forecast_date.day == profile.salary_credit_date_expected:
                # Add a synthetic jump based on previous incomes... omitted for brevity, let's keep it simple
                pass
                
            trajectory_data.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'predicted_balance': round(projected_balance, 2)
            })

            if projected_balance <= 0 and runout_date is None:
                runout_date = forecast_date.date()

        # Save to PredictionCache
        PredictionCache.objects.create(
            user=self.user,
            model_version='v1_heuristic',
            trajectory_data=trajectory_data,
            predicted_runout_date=runout_date
        )
