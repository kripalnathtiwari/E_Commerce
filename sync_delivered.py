import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Commerce.settings')
django.setup()

from orders.models import Order, PrintOrder
from store.models import OrderItem as StoreOrderItem

def sync_all_delivered():
    print("Syncing Standard Orders...")
    for order in Order.objects.filter(delivery_status='delivered'):
        items = StoreOrderItem.objects.filter(
            order__user=order.user
        ).exclude(status='Delivered')
        
        for item in items:
            item.status = 'Delivered'
            item.save()
            print(f"Synced Standard Order Item {item.id} for user {order.user.username}")

    print("Syncing Print Orders...")
    for po in PrintOrder.objects.filter(delivery_status='delivered'):
        if po.store_order_item:
            po.store_order_item.status = 'Delivered'
            po.store_order_item.save()
            print(f"Synced Print Order Item {po.store_order_item.id} for PrintOrder {po.id}")
        else:
            store_item = StoreOrderItem.objects.filter(
                order__user=po.user,
                product=po.product,
                quantity=po.quantity
            ).last()
            if store_item:
                store_item.status = 'Delivered'
                store_item.save()
                po.store_order_item = store_item
                po.save()
                print(f"Linked and Synced Print Order {po.id} to Store Item {store_item.id}")

if __name__ == "__main__":
    try:
        sync_all_delivered()
        print("Done!")
    except Exception as e:
        import traceback
        traceback.print_exc()
