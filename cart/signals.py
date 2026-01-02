from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem


@receiver(user_logged_in)
def merge_carts_on_login(sender, user, request, **kwargs):
    """
    Merge session cart into authenticated user's cart after login.
    """
    session_cart = request.session.get("cart", {})

    if not session_cart:
        return  # No guest cart to merge

    # Get or create user's cart
    user_cart, _ = Cart.objects.get_or_create(user=user)

    for book_id, quantity in session_cart.items():
        # Get or create cart item
        item, created = CartItem.objects.get_or_create(cart=user_cart, book_id=book_id)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

    # Clear session cart
    request.session["cart"] = {}
