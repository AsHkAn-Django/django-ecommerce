from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from cart.models import Cart, CartItem
from myApp.models import Book


@require_POST
def cart_add(request, pk):
    """Add a book to the cart for authenticated or session-based users."""
    book = get_object_or_404(Book, pk=pk)

    # Get quantity from POST, default to 1, ensure it's a positive integer
    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity <= 0:
            raise ValueError
    except ValueError:
        messages.warning(request, "Invalid quantity.")
        return redirect("myApp:shopping")

    # Determine current quantity in cart
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        existing_item = CartItem.objects.filter(cart=cart, book=book).first()
        current_quantity = existing_item.quantity if existing_item else 0
    else:
        cart = request.session.get("cart", {})
        pk_str = str(pk)
        current_quantity = int(cart.get(pk_str, 0))

    # Total quantity after adding
    total_quantity = current_quantity + quantity

    # Stock check
    try:
        book.quantity_stock_check(total_quantity)
    except ValueError as e:
        messages.warning(request, str(e))
        return redirect("myApp:shopping")

    # Update cart
    if request.user.is_authenticated:
        cart_item, _ = CartItem.objects.get_or_create(cart=cart, book=book)
        cart_item.quantity = total_quantity
        cart_item.save()
        messages.success(request, "Item added to the cart.")
        return redirect("cart:cart_list")
    else:
        cart[pk_str] = total_quantity
        request.session["cart"] = cart
        messages.success(request, "Item added to cart!")
        return redirect("cart:session_cart")


@login_required
def cart_list(request):
    """Display the cart for authenticated users."""
    cart = get_object_or_404(
        Cart.objects.prefetch_related("items__book"), user=request.user
    )
    return render(request, "cart/cart_list.html", {"cart": cart})


def session_cart_view(request):
    """Display the cart for session-based users."""
    cart = request.session.get("cart", {})
    cart_items = [
        (get_object_or_404(Book, pk=int(pk)), qty) for pk, qty in cart.items()
    ]
    total = sum(book.price * qty for book, qty in cart_items)
    return render(
        request, "cart/session_cart.html", {"items": cart_items, "total": total}
    )


def delete_item(request, pk):
    """Delete an item from the cart (auth or session-based)."""
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=pk)
        item.delete()
        messages.success(request, "Item was deleted successfully.")
        return redirect("cart:cart_list")

    cart = request.session.get("cart", {})
    pk_str = str(pk)
    if pk_str in cart:
        del cart[pk_str]
        request.session["cart"] = cart
        messages.success(request, "Item was deleted successfully.")
    return redirect("cart:session_cart")
