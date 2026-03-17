import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from orders.models import PrintOrder
from store.models import OrderItem as StoreOrderItem

def link_orders():
    print_orders = PrintOrder.objects.filter(store_order_item__isnull=True)
    count = 0
    for po in print_orders:
        # Try to find a matching StoreOrderItem
        # Match by user, product, quantity
        potential_matches = StoreOrderItem.objects.filter(
            order__user=po.user,
            product=po.product,
            quantity=po.quantity,
            print_orders__isnull=True # Not already linked (if related_name allows)
        ).order_by('-order__created_at')
        
        if potential_matches.exists():
            match = potential_matches.first()
            po.store_order_item = match
            po.save()
            count += 1
            print(f"Linked PrintOrder {po.id} to StoreOrderItem {match.id}")
        else:
            print(f"No match found for PrintOrder {po.id}")
            
    print(f"Total Linked: {count}")

if __name__ == "__main__":
    link_orders()
