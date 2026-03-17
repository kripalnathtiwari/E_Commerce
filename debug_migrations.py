import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(store_orderitem);")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in store_orderitem: {columns}")

from django.db.migrations.recorder import MigrationRecorder
applied_migrations = MigrationRecorder.Migration.objects.filter(app='store').values_list('name', flat=True)
print(f"Applied migrations for store: {list(applied_migrations)}")
