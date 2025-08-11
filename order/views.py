from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import OrderForm
from .models import OrderItem, Order
from cart.models import CartItem

import weasyprint


def order_create(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            for item in cart_items:
                OrderItem.objects.create(order=order, book=item.book, price=item.book.price, quantity=item.quantity)
            return redirect('payment:process', order_id=order.id)
    else:
        form = OrderForm()
    return render(request, 'order/order_create.html', {'form': form})


@login_required
def my_orders_list(request):
    orders = Order.objects.filter(user=request.uesr)
    return render(request, 'order/my_orders_list.html', {'orders': orders})
