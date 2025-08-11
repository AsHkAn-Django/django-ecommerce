from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from cart.models import Cart, CartItem
from myApp.models import Book
from .forms import CartAddForm


@require_POST
def cart_add(request, pk):
    """Add a book to the cart for authenticated or session-based users."""
    book = get_object_or_404(Book, pk=pk)
    form = CartAddForm(request.POST or None)

    if not form.is_valid():
        messages.warning(request, 'There was a problem adding the item.')
        return redirect('myApp:shopping')

    cd = form.cleaned_data

    # Authenticated user cart handling
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)

        if not created:
            cart_item.quantity += cd['quantity']
        else:
            cart_item.quantity = cd['quantity']

        cart_item.save()
        messages.success(request, 'Item added to the cart.')
        return redirect('cart:cart_list')

    # Session-based cart handling (dict pk_str -> quantity)
    cart = request.session.get('cart', {})
    pk_str = str(pk)
    cart[pk_str] = cart.get(pk_str, 0) + cd['quantity']
    request.session['cart'] = cart

    messages.success(request, "Item added to cart!")
    return redirect('cart:session_cart')


@login_required
def cart_list(request):
    """Display the cart for authenticated users."""
    cart = get_object_or_404(
        Cart.objects.prefetch_related('items__book'),
        user=request.user
    )
    return render(request, 'cart/cart_list.html', {'cart': cart})


def session_cart_view(request):
    """Display the cart for session-based users."""
    cart = request.session.get("cart", {})
    cart_items = [(get_object_or_404(Book, pk=int(pk)), qty) for pk, qty in cart.items()]
    total = sum(book.price * qty for book, qty in cart_items)
    return render(request, 'cart/session_cart.html', {'items': cart_items, 'total': total})


def delete_item(request, pk):
    """Delete an item from the cart (auth or session-based)."""
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=pk)
        book = item.book
        book.stock += 1
        book.save()
        item.delete()
        return redirect('cart:cart_list')

    cart = request.session.get("cart", {})
    pk_str = str(pk)
    if pk_str in cart:
        del cart[pk_str]
        request.session["cart"] = cart
        messages.success(request, 'Item was deleted successfully.')

    return redirect('cart:session_cart')
