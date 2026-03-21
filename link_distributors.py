import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from store.models import OrderItem as StoreOrderItem

def repair_missing_distributors():
    print("Finding OrderItems with missing distributors...")
    items = StoreOrderItem.objects.filter(distributor__isnull=True)
    count = items.count()
    print(f"Found {count} items to fix.")
    
    fixed = 0
    for item in items:
        if item.product and item.product.distributor:
            item.distributor = item.product.distributor
            item.save()
            fixed += 1
            print(f"Fixed Item {item.id}: Assigned to {item.distributor.user.username}")

    print(f"Successfully fixed {fixed} items!")

if __name__ == "__main__":
    repair_missing_distributors()
