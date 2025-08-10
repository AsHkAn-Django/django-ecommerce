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
    template_name = 'myApp/session_cart.html'

    def get_context_data(self, **kwargs):
        cart_ids = self.request.session.get("cart", [])
        cart_items = [Book.objects.get(id=book_id) for book_id in cart_ids]
        total = sum(item.price for item in cart_items)
        return {'items':cart_items, 'total':total}



def purchase(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Check if the last action was a duplicate purchase due to refresh
    last_purchase = request.session.get('last_purchase')
    current_purchase = f"{request.user.id}-{book.id}"

    if last_purchase == current_purchase and request.session.get('prevent_double_purchase', False):
        messages.warning(request, "You've already added this item!")
        return redirect('cart:cart_list')

    # Store purchase in session to prevent accidental duplicates
    request.session['last_purchase'] = current_purchase
    request.session['prevent_double_purchase'] = True  # Mark this as a recent purchase

    messages.success(request, "Item added to cart!")

    if request.user.is_authenticated:
        pass
        # book = get_object_or_404(Book, pk=pk)
        # user = request.user
        # form = CartAddForm(request.POST or None)
        # if form.is_valid():
        #     cd = form.cleaned_data
        #     cart, _ = Cart.objects.get_or_create(user=user)

        #     # This checks if the user has this item in his cart so doesn't duplicate it and just update the quantity
        #     cart_item, created = CartItem.objects.get_or_create(cart=cart, product=book)
        #     if not created:
        #         cart_item.quantity += cd['quantity']
        #     else:
        #         cart_item.quantity = cd['quantity']
        #     cart_item.save()
        # return redirect('cart:cart_list')

    cart_ids = request.session.get('cart', [])
    cart_ids.append(pk)
    request.session['cart'] = cart_ids
    cart_items = [Book.objects.get(id=book_id) for book_id in cart_ids]
    total = sum(item.price for item in cart_items)
    return render(request, 'myApp/session_cart.html', {'items': cart_items, 'total': total})



def delete_item(request, pk):
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=pk)
        book = get_object_or_404(Book, title=item)
        book.stock += 1
        book.save()
        item.delete()
        return redirect('cart:cart_list')
    cart_ids = request.session.get("cart", [])
    cart_ids.remove(pk)
    request.session["cart"] = cart_ids
    return redirect('myApp:session_cart')