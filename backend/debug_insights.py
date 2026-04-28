
import os
import django
import json
import datetime
from django.test import RequestFactory
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.views import InsightsSummaryView
from api.models import User

def serialize(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)

user = User.objects.first()
factory = RequestFactory()
request = factory.get('/api/insights/summary/?period=month')
request.user = type('Obj', (object,), {'db_user': user, 'is_authenticated': True})
view = InsightsSummaryView.as_view()
response = view(request)

print(json.dumps(response.data, indent=2, default=serialize))
