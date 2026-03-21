from orders.models import Distributor, Return
from store.models import OrderItem
from django.db.models import Q

for d in Distributor.objects.all():
    print('--- distributor', d.user.username, d.user.email)
    distributor_order_items = OrderItem.objects.filter(Q(distributor=d) | Q(product__distributor=d))
    orders = set(item.order for item in distributor_order_items)
    print('orders count', len(orders))
    rets = Return.objects.filter(order__in=orders).order_by('-created_at')
    print('returns count', rets.count())
    for r in rets:
        items = r.order.items.filter(distributor=d)
        if not items.exists():
            items = r.order.items.filter(product__distributor=d)
        print(' return', r.id, 'order', r.order.id, 'items', items.count())
