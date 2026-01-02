import pytest
from rest_framework.exceptions import ValidationError
from cart.models import Cart, CartItem
from order.models import OrderItem
from order.api.serializers import CreateOrderSerializer
from rest_framework.test import APIRequestFactory


# --- Helper to Mock Request ---
def get_context(user):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user
    return {"request": request}


@pytest.mark.django_db
def test_create_order_serializer_fails_empty_cart(create_user):
    """Test validation fails if user has no cart."""
    user = create_user(email="nocart@test.com", password="pw")
    # No cart created

    context = get_context(user)
    serializer = CreateOrderSerializer(
        data={"first_name": "A", "last_name": "B", "email": "a@b.com"}, context=context
    )

    with pytest.raises(ValidationError) as e:
        serializer.is_valid(raise_exception=True)
    assert "Your cart is empty!" in str(e.value)


@pytest.mark.django_db
def test_create_order_serializer_fails_stock_check(create_user, create_book):
    """Test validation fails if cart item exceeds stock."""
    user = create_user(email="stock@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(stock=5)

    # User tries to buy 10
    CartItem.objects.create(cart=cart, book=book, quantity=10)

    context = get_context(user)
    serializer = CreateOrderSerializer(
        data={"first_name": "A", "last_name": "B", "email": "a@b.com"}, context=context
    )

    with pytest.raises(ValidationError) as e:
        serializer.is_valid(raise_exception=True)
    assert "Not enough stock" in str(e.value)


@pytest.mark.django_db
def test_create_order_serializer_success(create_user, create_book):
    """Test that a valid cart creates an Order and moves items."""
    user = create_user(email="buyer@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(title="Test Book", price=100.00, stock=10)
    CartItem.objects.create(cart=cart, book=book, quantity=2)

    context = get_context(user)
    data = {"first_name": "John", "last_name": "Doe", "email": "john@test.com"}

    serializer = CreateOrderSerializer(data=data, context=context)
    assert serializer.is_valid()
    order = serializer.save()

    # Check Order Created
    assert order.user == user
    assert order.first_name == "John"

    # Check Items Moved
    assert OrderItem.objects.count() == 1
    item = OrderItem.objects.first()
    assert item.order == order
    assert item.book == book
    assert item.quantity == 2
    assert item.price == 100.00
