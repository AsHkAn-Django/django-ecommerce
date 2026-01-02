import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from cart.context_processors import cart_item_count
from cart.models import Cart, CartItem


# --- Fixture to create fake requests ---
@pytest.fixture
def rf():
    return RequestFactory()


# --- ANONYMOUS USER TESTS (Session Based) ---


def test_cp_anonymous_empty_cart(rf):
    """Test that a new guest user sees 0 items."""
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = {}

    context = cart_item_count(request)
    assert context["cart_item_count"] == 0


def test_cp_anonymous_with_items(rf):
    """Test that session items are summed correctly."""
    request = rf.get("/")
    request.user = AnonymousUser()
    # Mocking the session cart structure: {'book_id': quantity}
    # Book 1 (Qty 2) + Book 2 (Qty 3) = 5 Total
    request.session = {"cart": {"1": 2, "2": 3}}

    context = cart_item_count(request)
    assert context["cart_item_count"] == 5


# --- AUTHENTICATED USER TESTS (Database Based) ---


@pytest.mark.django_db
def test_cp_authenticated_empty_cart(rf, create_user):
    """Test logged in user with no cart object."""
    user = create_user(email="empty@test.com", password="pw")

    request = rf.get("/")
    request.user = user

    context = cart_item_count(request)
    assert context["cart_item_count"] == 0


@pytest.mark.django_db
def test_cp_authenticated_empty_items(rf, create_user):
    """Test logged in user has a cart, but no items in it."""
    user = create_user(email="noitems@test.com", password="pw")
    Cart.objects.create(user=user)

    request = rf.get("/")
    request.user = user

    context = cart_item_count(request)
    assert context["cart_item_count"] == 0


@pytest.mark.django_db
def test_cp_authenticated_with_items(rf, create_user, create_book):
    """Test logged in user with actual DB items."""
    user = create_user(email="shopper@test.com", password="pw")
    cart = Cart.objects.create(user=user)

    b1 = create_book()
    b2 = create_book()

    # Add 2 of Book1 and 5 of Book2 = 7 Total
    CartItem.objects.create(cart=cart, book=b1, quantity=2)
    CartItem.objects.create(cart=cart, book=b2, quantity=5)

    request = rf.get("/")
    request.user = user

    context = cart_item_count(request)
    assert context["cart_item_count"] == 7
