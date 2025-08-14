from cart.models import Cart
from django.db.models import Sum


def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            total_items = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            total_items = 0
        return {'cart_item_count': total_items}

    cart = request.session.get('cart', {})
    total_items = sum(cart.values())
    return {'cart_item_count': total_items}
