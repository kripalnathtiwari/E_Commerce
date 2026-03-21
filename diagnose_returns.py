import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from orders.models import Return as OrdersReturn
from store.models import OrderItem as StoreOrderItem
from orders.models import Distributor

def diagnose_returns():
    print(f"Total Returns in DB: {OrdersReturn.objects.count()}")
    for ret in OrdersReturn.objects.select_related('order', 'user').all():
        print(f"Return ID {ret.id}: Order #{ret.order.id}, User {ret.user.username}, Status {ret.return_status}")
        # Find which distributors own items in this order
        items = StoreOrderItem.objects.filter(order=ret.order)
        print(f"  Items in order {ret.order.id}: {items.count()}")
        for itm in items:
            print(f"    Item {itm.id}: Distributor {itm.distributor}")

    print("\nAll Distributors:")
    for dist in Distributor.objects.all():
        print(f"  Distributor ID {dist.id}: {dist.user.username}")

if __name__ == "__main__":
    diagnose_returns()
