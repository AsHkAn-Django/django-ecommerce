from django.views import generic
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Exists, OuterRef
from django.contrib.auth.decorators import login_required

from .models import Book, CartItem, Favorite, Rating
from .forms import RatingForm
from .recommned import get_top_n_recommendations




class ShoppingListView(generic.ListView):
    context_object_name = 'books'
    template_name = "myApp/shopping.html"

    def get_queryset(self):
        self.request.session['prevent_double_purchase'] = False
        qs = Book.objects.all()
        if self.request.user.is_authenticated:
            qs = qs.annotate(is_favorite=Exists(
                Favorite.objects.filter(user=self.request.user, book=OuterRef('pk')))
            )
        return qs



class IndexView(generic.TemplateView):
    template_name = "myApp/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            recommended_ids = get_top_n_recommendations(self.request.user.id)
            recommended_books = Book.objects.filter(id__in=recommended_ids)
            context['recommended_books'] = recommended_books
        else:
            context['recommended_books'] = []

        return context



class CartView(generic.ListView):
    model = CartItem
    template_name = 'myApp/cart.html'

    def get_context_data(self, **kwargs):
        items = get_cart_context(self.request.user)
        return items



class SessionCartView(generic.ListView):
    model = CartItem
    template_name = 'myApp/session_cart.html'

    def get_context_data(self, **kwargs):
        cart_ids = self.request.session.get("cart", [])
        cart_items = [Book.objects.get(id=book_id) for book_id in cart_ids]
        total = sum(item.price for item in cart_items)
        return {'items':cart_items, 'total':total}



class BookUpdateView(UserPassesTestMixin, LoginRequiredMixin, generic.UpdateView):
    model = Book
    fields = ('stock',)
    template_name = "myApp/update_book.html"

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Books added to the stock successfully!')
        return super().form_valid(form)



def purchase(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Check if the last action was a duplicate purchase due to refresh
    last_purchase = request.session.get('last_purchase')
    current_purchase = f"{request.user.id}-{book.id}"

    if last_purchase == current_purchase and request.session.get('prevent_double_purchase', False):
        messages.warning(request, "You've already added this item!")
        return redirect('myApp:cart')

    # Store purchase in session to prevent accidental duplicates
    request.session['last_purchase'] = current_purchase
    request.session['prevent_double_purchase'] = True  # Mark this as a recent purchase

    messages.success(request, "Item added to cart!")

    if request.user.is_authenticated:
        book.stock -= 1
        book.save()
        CartItem.objects.create(book=book, buyer=request.user)
        return render(request, 'myApp/cart.html', get_cart_context(request.user))

    cart_ids = request.session.get('cart', [])
    cart_ids.append(pk)
    request.session['cart'] = cart_ids
    cart_items = [Book.objects.get(id=book_id) for book_id in cart_ids]
    total = sum(item.price for item in cart_items)
    return render(request, 'myApp/session_cart.html', {'items': cart_items, 'total': total})



def get_cart_context(user):
    items = CartItem.objects.filter(buyer=user)
    total = sum(item.book.price for item in items)
    return {'items': items, 'total': total}


def delete_item(request, pk):
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=pk)
        book = get_object_or_404(Book, title=item)
        book.stock += 1
        book.save()
        item.delete()
        return redirect('myApp:cart')
    cart_ids = request.session.get("cart", [])
    cart_ids.remove(pk)
    request.session["cart"] = cart_ids
    return redirect('myApp:session_cart')


@login_required
def add_to_favorite_toggle(request, pk):
    book = get_object_or_404(Book, pk=pk)
    favorite = Favorite.objects.filter(user=request.user, book=book)
    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(user=request.user, book=book)
    return redirect('myApp:shopping')



class FavoriteListView(LoginRequiredMixin, generic.ListView):
    template_name = "myApp/favorite_list.html"
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)




class RatingFormView(generic.FormView):
    model = Rating
    template_name = "myApp/rating.html"
    form_class = RatingForm
    success_url = reverse_lazy('myApp:shopping')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        context['book'] = get_object_or_404(Book, pk=pk)
        return context

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        book = get_object_or_404(Book, pk=pk)
        rating, created = Rating.objects.update_or_create(book=book,
        user=self.request.user, defaults={'rate': form.cleaned_data['rate']})
        if created:
            messages.success(self.request, 'Rating added successfully.')
        else:
            messages.success(self.request, "Rating updated successfully.")
        return redirect('myApp:shopping')



class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'myApp/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        if self.request.user.is_authenticated:
            context['is_favorite'] = book.book_favorites.filter(user=self.request.user).exists()
        else:
            context['is_favorite'] = False
        return context
