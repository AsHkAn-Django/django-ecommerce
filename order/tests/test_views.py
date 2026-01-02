import pytest
from django.urls import reverse
from cart.models import Cart, CartItem
from order.models import Order


@pytest.mark.django_db
def test_order_create_view_converts_cart_to_order(client, create_user, create_book):
    """
    The main integration test:
    1. User adds items to Cart.
    2. User POSTs to create_order.
    3. System should create Order + OrderItems.
    4. System should redirect to Payment.
    """
    # 1. Setup User & Cart
    user = create_user(email="buyer@test.com", password="pw")
    client.force_login(user)

    cart = Cart.objects.create(user=user)
    book = create_book(title="Expensive Book", price=50.00)

    # Add 2 items to cart
    CartItem.objects.create(cart=cart, book=book, quantity=2)

    # 2. Post to Order Create
    url = reverse("order:order_create")
    payload = {"first_name": "Alice", "last_name": "Smith", "email": "alice@test.com"}
    response = client.post(url, payload)

    # 3. Assert Order Created
    assert Order.objects.count() == 1
    order = Order.objects.first()

    assert order.user == user
    assert order.first_name == "Alice"

    # 4. Assert Order Items Copied Correctly
    assert order.items.count() == 1
    order_item = order.items.first()

    assert order_item.book == book
    assert order_item.price == 50.00  # Price was locked in
    assert order_item.quantity == 2

    # 5. Assert Redirect to Payment
    # The URL pattern requires an order_id to be valid.
    expected_url = reverse("payment:process", kwargs={"order_id": order.id})

    assert response.status_code == 302
    # Now we compare the actual redirect URL with the one we expect
    assert response.url == expected_url


@pytest.mark.django_db
def test_my_orders_list_view(client, create_user):
    """Test that users can see their own orders."""
    user = create_user(email="me@test.com", password="pw")
    client.force_login(user)

    Order.objects.create(user=user, first_name="My Order")

    url = reverse("order:my_orders_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "My Order" in str(response.content)


# --- SECURITY & ERROR HANDLING ---


@pytest.mark.django_db
def test_order_create_requires_login(client):
    """Test that guests are redirected to login page."""
    url = reverse("order:order_create")
    response = client.get(url)

    # Should redirect to /accounts/login/?next=/order/create/
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_order_create_invalid_form_does_not_create_order(
    client, create_user, create_book
):
    """Test that submitting a bad form (missing email) fails safely."""
    user = create_user(email="badform@test.com", password="pw")
    client.force_login(user)

    # Give the user a cart item so they pass the "Empty Cart Check"
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, book=create_book(), quantity=1)

    url = reverse("order:order_create")

    # Missing 'email' and 'last_name'
    payload = {"first_name": "JustName"}

    response = client.post(url, payload)

    # 1. NOW it should stay on the same page (200 OK)
    assert response.status_code == 200

    # 2. Template should show form errors
    assert response.context["form"].errors

    # 3. Database should still be empty (of orders)
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_order_create_preserves_cart_on_failure(client, create_user, create_book):
    """
    If the order fails (e.g. invalid form),
    ensure the user's cart items are NOT deleted.
    """
    user = create_user(email="savecart@test.com", password="pw")
    client.force_login(user)

    # Setup Cart
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, book=create_book(), quantity=1)

    url = reverse("order:order_create")

    # Submit INVALID data
    client.post(url, {"first_name": "Fail"})

    # Cart item should still exist
    assert CartItem.objects.filter(cart=cart).exists() is True


@pytest.mark.django_db
def test_order_create_redirects_if_cart_empty(client, create_user):
    """Test that you cannot create an order with an empty cart."""
    user = create_user(email="empty@test.com", password="pw")
    client.force_login(user)
    # Ensure no cart items exist

    url = reverse("order:order_create")
    response = client.get(url)

    # Should redirect to shopping
    assert response.status_code == 302
    assert response.url == reverse("myApp:shopping")
