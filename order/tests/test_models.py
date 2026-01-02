import pytest
from decimal import Decimal
from order.models import Order, OrderItem


@pytest.mark.django_db
def test_order_total_cost_calculation(create_user, create_book):
    """Test that order total is the sum of all line items."""
    user = create_user(email="order@test.com", password="pw")
    order = Order.objects.create(
        user=user, first_name="John", last_name="Doe", email="john@test.com"
    )

    b1 = create_book(price=10.00)
    b2 = create_book(price=20.00)

    # Add items to order
    OrderItem.objects.create(order=order, book=b1, price=10.00, quantity=2)  # 20
    OrderItem.objects.create(order=order, book=b2, price=20.00, quantity=1)  # 20

    # Expect 40.00
    assert order.get_total_cost() == Decimal("40.00")


@pytest.mark.django_db
def test_order_stripe_url_logic(create_user, settings):
    """Test the Stripe dashboard URL generation."""
    user = create_user(email="stripe@test.com", password="pw")
    order = Order.objects.create(user=user, stripe_id="pi_12345")

    # Case 1: Live Mode
    settings.STRIPE_SECRET_KEY = "sk_live_xyz"
    assert order.get_stripe_url() == "https://dashboard.stripe.com/payments/pi_12345"

    # Case 2: Test Mode
    settings.STRIPE_SECRET_KEY = "sk_test_xyz"
    assert (
        order.get_stripe_url() == "https://dashboard.stripe.com/test/payments/pi_12345"
    )

    # Case 3: No ID
    order.stripe_id = ""
    order.save()
    assert order.get_stripe_url() == ""


@pytest.mark.django_db
def test_order_str_representation(create_user):
    user = create_user(email="str@test.com", password="pw")
    order = Order.objects.create(user=user, id=99)
    assert str(order) == "Order 99"


@pytest.mark.django_db
def test_order_delete_cascades_to_items(create_user, create_book):
    """Test that deleting an Order removes its OrderItems (Cleanup)."""
    user = create_user(email="clean@test.com", password="pw")
    order = Order.objects.create(user=user, first_name="Delete", last_name="Me")

    # Add an item
    OrderItem.objects.create(order=order, book=create_book(), price=10, quantity=1)

    assert OrderItem.objects.count() == 1

    # Delete the Order
    order.delete()

    # Item should be gone
    assert OrderItem.objects.count() == 0


@pytest.mark.django_db
def test_order_item_cost_calculation(create_user, create_book):
    """Test the get_cost() method on a single line item."""
    user = create_user(email="math@test.com", password="pw")
    order = Order.objects.create(user=user)
    book = create_book(price=10.00)

    # 3 items at $10 = $30
    item = OrderItem.objects.create(order=order, book=book, price=10.00, quantity=3)

    assert item.get_cost() == 30.00
