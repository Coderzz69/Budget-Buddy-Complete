import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import User
from api.services.behavior_engine import BehaviorEngine
from api.tasks.behavior_tasks import generate_alerts

def run_training():
    users = User.objects.all()
    print(f"Starting behavioral training for {users.count()} users...")
    
    for user in users:
        print(f"Analyzing behavior for {user.email}...")
        engine = BehaviorEngine(user)
        try:
            engine.run_full_analysis()
            generate_alerts(user.id)
            print(f"Successfully generated profile and alerts for {user.email}")
        except Exception as e:
            print(f"Failed analysis for {user.email}: {e}")

if __name__ == "__main__":
    run_training()
