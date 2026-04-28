from celery import shared_task
from django.contrib.auth import get_user_model
from api.services.behavior_engine import BehaviorEngine
from api.models import Alert
from django.utils import timezone

User = get_user_model()

@shared_task
def recompute_after_upload(user_id):
    """
    Triggered after a user uploads a new bank statement CSV.
    """
    try:
        user = User.objects.get(id=user_id)
        engine = BehaviorEngine(user)
        engine.run_full_analysis()
        generate_alerts.delay(user_id)
    except User.DoesNotExist:
        pass


@shared_task
def nightly_forecast():
    """
    Run every night to update trajectories for all active users.
    """
    users = User.objects.all() # In production, filter active users
    for user in users:
        engine = BehaviorEngine(user)
        engine.run_full_analysis()


@shared_task
def generate_alerts(user_id):
    """
    Evaluates the UserBehaviorProfile and PredictionCache to generate alerts.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Weekend overspend alert
        if hasattr(user, 'behavior_profile'):
            profile = user.behavior_profile
            if profile.weekend_overspend_ratio > 1.5:
                Alert.objects.create(
                    user=user,
                    alert_type='weekend_warning',
                    message=f"You spend {int(profile.weekend_overspend_ratio * 100)}% more on weekends than weekdays. Watch your Saturday spending!"
                )
                
        # Run-out prediction alert
        predictions = user.predictions.order_by('-created_at')
        if predictions.exists():
            latest_pred = predictions.first()
            if latest_pred.predicted_runout_date:
                days_left = (latest_pred.predicted_runout_date - timezone.now().date()).days
                if 0 <= days_left <= 7:
                    Alert.objects.create(
                        user=user,
                        alert_type='low_balance',
                        message=f"At your current burn rate, your balance may run out in {days_left} days."
                    )
                    
    except User.DoesNotExist:
        pass
