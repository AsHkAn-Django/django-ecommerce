from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views import generic
from django.contrib import messages

from cart.models import Cart, CartItem
from myApp.models import Book
from .forms import CartAddForm


@require_POST
@login_required
def cart_add(request, pk):
    """Add book to cart"""
    book = get_object_or_404(Book, pk=pk)
    user = request.user
    form = CartAddForm(request.POST or None)
    if form.is_valid():
        cd = form.cleaned_data
        cart, _ = Cart.objects.get_or_create(user=user)

        # This checks if the user has this item in his cart so doesn't duplicate it and just update the quantity
        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        if not created:
            cart_item.quantity += cd['quantity']
        else:
            cart_item.quantity = cd['quantity']
        cart_item.save()
        messages.success(request, 'Item added to the cart.')
        return redirect('cart:cart_list')

    messages.warning(request, 'There was a problem in adding the item.')
    return redirect('myApp:shopping')


@login_required
def cart_list(request):
    cart = get_object_or_404(Cart.objects.prefetch_related('items__book'), user=request.user)
    return render(request, 'cart/cart_list.html', {'cart': cart})


class SessionCartView(generic.ListView):
    model = CartItem
    template_name = 'cart/session_cart.html'

    def get_context_data(self, **kwargs):
        cart = self.request.session.get("cart", [])
        cart_items = [(get_object_or_404(Book, pk=int(item['pk'])), item['quantity']) for item in cart]
        total = sum(item[0].price * int(item[1]) for item in cart_items)
        return {'items':cart_items, 'total':total}


def purchase(request, pk):
    cart = request.session.get('cart', {})
    form = CartAddForm(request.POST or None)

    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        new_cart_item = {'pk':pk, 'quantity':quantity}
        cart.append(new_cart_item)
        request.session['cart'] = cart

    cart_items = [(get_object_or_404(Book, pk=int(item['pk'])), item['quantity']) for item in cart]

    total = sum(item[0].price * int(item[1]) for item in cart_items)

    messages.success(request, "Item added to cart!")
    return render(request, 'cart/session_cart.html', {'items': cart_items, 'total': total})


def delete_item(request, pk):
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=pk)
        book = get_object_or_404(Book, title=item)
        book.stock += 1
        book.save()
        item.delete()
        return redirect('cart:cart_list')
    cart = request.session.get("cart", [])
    for item in cart:
        if int(item['pk']) == int(pk):
            cart.remove(item)
            messages.success(request, 'Item was deleted successfully.')
    request.session["cart"] = cart

    return redirect('cart:session_cart')