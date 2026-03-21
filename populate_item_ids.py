import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from store.models import OrderItem as StoreOrderItem
from orders.models import OrderItem as DistributorOrderItem, PrintOrder

print("Populating StoreOrderItem...")
for item in StoreOrderItem.objects.filter(item_id__isnull=True):
    item.item_id = 'ITM-' + str(uuid.uuid4()).replace('-', '').upper()[:8]
    item.save()
    print(f"Updated StoreOrderItem {item.id} with {item.item_id}")

print("Populating DistributorOrderItem...")
for item in DistributorOrderItem.objects.filter(item_id__isnull=True):
    item.item_id = 'ITM-' + str(uuid.uuid4()).replace('-', '').upper()[:8]
    item.save()
    print(f"Updated DistributorOrderItem {item.id} with {item.item_id}")

print("Populating PrintOrder...")
for item in PrintOrder.objects.filter(item_id__isnull=True):
    item.item_id = 'PRN-' + str(uuid.uuid4()).replace('-', '').upper()[:8]
    item.save()
    print(f"Updated PrintOrder {item.id} with {item.item_id}")
