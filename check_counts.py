import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from orders.models import Order, PrintOrder, Return
from store.models import OrderItem as StoreOrderItem

def check_counts():
    print(f"Total Standard (orders): {Order.objects.count()}")
    print(f"Total Print (orders): {PrintOrder.objects.count()}")
    print(f"Total Store items: {StoreOrderItem.objects.count()}")
    print(f"Total Returns: {Return.objects.count()}")
    
    # Check returns for specific distributor (if any)
    for ret in Return.objects.all():
        print(f"Return {ret.id}: Order #{ret.order.id}, Status {ret.return_status}")
    
    # Check if returns are linked to any distributor
    for item in StoreOrderItem.objects.all():
        print(f"Item {item.id} Distributor: {item.distributor}")

if __name__ == "__main__":
    check_counts()
