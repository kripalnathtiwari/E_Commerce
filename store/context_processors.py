from .models import CartItem

def count_items_in_cart(request):
    count = 0

    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__user=request.user).count()

    return {
        'count_items_in_cart': count
    }