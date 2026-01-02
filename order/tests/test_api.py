import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from cart.models import Cart, CartItem
from order.models import Order


# --- FIXTURES ---
@pytest.fixture
def order_list_url():
    return reverse("order_api:order_api")


@pytest.fixture
def order_create_url():
    return reverse("order_api:order_create_api")


# --- GET ORDERS LIST ---


@pytest.mark.django_db
def test_get_order_list_api(api_client, create_user, order_list_url):
    """Test retrieving past orders."""
    user = create_user(email="list@test.com", password="pw")
    Order.objects.create(user=user, first_name="Old Order")

    api_client.force_authenticate(user=user)
    response = api_client.get(order_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["first_name"] == "Old Order"


# --- 2. CREATE ORDER (WITH STRIPE MOCK) ---


@pytest.mark.django_db
def test_create_order_api_success(
    api_client, create_user, create_book, order_create_url
):
    """
    Test the full flow: Cart -> Order -> Stripe Session.
    We MOCK Stripe so we don't need real API keys.
    """
    # 1. Setup User & Cart
    user = create_user(email="pay@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(price=50.00)
    CartItem.objects.create(cart=cart, book=book, quantity=1)

    api_client.force_authenticate(user=user)

    payload = {"first_name": "Jane", "last_name": "Doe", "email": "jane@test.com"}

    # 2. MOCK STRIPE
    # We patch 'stripe.checkout.Session.create' inside the view
    # The string path must match where it is IMPORTED or USED
    with patch("order.api.views.stripe.checkout.Session.create") as mock_stripe:

        # Configure the mock to return a fake object with a .url attribute
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/fake-url"
        mock_stripe.return_value = mock_session

        # 3. Call API
        response = api_client.post(order_create_url, payload)

        # 4. Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["stripe_url"] == "https://checkout.stripe.com/fake-url"
        assert Order.objects.count() == 1

        # Verify Stripe was actually called with correct data
        mock_stripe.assert_called_once()
        # You can even check arguments if you want:
        # args, kwargs = mock_stripe.call_args
        # assert kwargs['client_reference_id'] == Order.objects.first().id


@pytest.mark.django_db
def test_create_order_api_empty_cart(api_client, create_user, order_create_url):
    """Test that API returns 400 if cart is empty."""
    user = create_user(email="empty@test.com", password="pw")
    # No cart items

    api_client.force_authenticate(user=user)
    payload = {"first_name": "A", "last_name": "B", "email": "a@b.com"}

    response = api_client.post(order_create_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Check for the specific error message from serializer
    # DRF returns {'non_field_errors': ['Your cart is empty!']} or similar
    assert "Your cart is empty!" in str(response.data)
