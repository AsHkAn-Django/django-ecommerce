import pytest
from django.urls import reverse
from rest_framework import status
from cart.models import Cart, CartItem


# --- FIXTURE FOR URLS ---


@pytest.fixture
def cart_url():
    return reverse("cart_api:cart_list_api")


@pytest.fixture
def add_item_url():
    return reverse("cart_api:add_item_api")


# --- CART API VIEW (GET/POST) ---


@pytest.mark.django_db
def test_create_cart_api(api_client, create_user, cart_url):
    """Test POST /api/v1/cart/ creates a cart."""
    user = create_user(email="api@test.com", password="pw")
    api_client.force_authenticate(user=user)

    response = api_client.post(cart_url, {})

    assert response.status_code == status.HTTP_201_CREATED
    assert Cart.objects.filter(user=user).exists() is True


@pytest.mark.django_db
def test_get_cart_api_success(api_client, create_user, create_book, cart_url):
    """Test GET /api/v1/cart/ returns items."""
    user = create_user(email="get@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(title="API Book")
    CartItem.objects.create(cart=cart, book=book, quantity=2)

    api_client.force_authenticate(user=user)
    response = api_client.get(cart_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["book"]["title"] == "API Book"


@pytest.mark.django_db
def test_get_cart_api_404_if_no_cart(api_client, create_user, cart_url):
    """Test GET /api/v1/cart/ returns 404 if cart doesn't exist."""
    user = create_user(email="404@test.com", password="pw")
    api_client.force_authenticate(user=user)

    response = api_client.get(cart_url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cart_api_anonymous_forbidden(api_client, cart_url):
    """Test Unauthenticated user cannot access."""
    response = api_client.get(cart_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- ADD ITEM API VIEW (POST) ---


@pytest.mark.django_db
def test_add_item_api_success(api_client, create_user, create_book, add_item_url):
    """Test POST /api/v1/cart/add-item/ works."""
    user = create_user(email="adder@test.com", password="pw")
    Cart.objects.create(user=user)
    book = create_book(stock=10)

    api_client.force_authenticate(user=user)
    payload = {"book": book.id, "quantity": 5}

    response = api_client.post(add_item_url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert "has been added" in response.data["success"]

    # Verify DB
    cart = Cart.objects.get(user=user)
    assert cart.items.first().quantity == 5


@pytest.mark.django_db
def test_add_item_api_stock_error(api_client, create_user, create_book, add_item_url):
    """Test that API returns 400 Bad Request if stock exceeded."""
    user = create_user(email="fail@test.com", password="pw")
    Cart.objects.create(user=user)
    book = create_book(stock=1)  # Only 1 available

    api_client.force_authenticate(user=user)
    payload = {"book": book.id, "quantity": 5}

    response = api_client.post(add_item_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Serializer errors usually come in a dict
    assert len(response.data) > 0  # Should contain error message
