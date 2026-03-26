import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from accounts.models import Account
from django.db.models.functions import Lower
from django.db.models import Count

duplicates = Account.objects.annotate(email_lower=Lower('email')).values('email_lower').annotate(count=Count('id')).filter(count__gt=1)

for d in duplicates:
    email_lower = d['email_lower']
    users = Account.objects.filter(email__iexact=email_lower).order_by('id')
    first_user = users.first()
    if first_user:
        print(f"Keeping {first_user.email} (id={first_user.id})")
        to_delete = users.exclude(id=first_user.id)
        count = to_delete.count()
        to_delete.delete()
        print(f"Deleted {count} duplicate(s) for {email_lower}")
