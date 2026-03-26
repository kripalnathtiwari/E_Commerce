import os
import sys
import django

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
app = SocialApp.objects.first()
if app:
    print(f"Secret length: {len(app.secret)}")
else:
    print("No app found")
