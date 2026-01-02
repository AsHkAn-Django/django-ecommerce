import pytest
from decimal import Decimal
from cart.models import Cart, CartItem
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_cart_creation(create_user):
    """Test that a cart is linked to a user correctly."""
    user = create_user(email="buyer@test.com", password="pw")
    cart = Cart.objects.create(user=user)

    assert cart.user == user
    assert str(cart) == "buyer@test.com"


@pytest.mark.django_db
def test_cart_item_creation(create_user, create_book):
    """Test creating a cart item linked to a book."""
    user = create_user(email="item@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(title="Python 101", price=10.00)
    item = CartItem.objects.create(cart=cart, book=book, quantity=2)

    assert item.cart == cart
    assert item.book == book
    assert item.quantity == 2
    assert str(item) == "Python 101"


@pytest.mark.django_db
def test_cart_item_get_cost(create_user, create_book):
    """Test individual item cost calculation (Price * Qty)."""
    user = create_user(email="math@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(price=15.00)

    # Buy 3 items at $15.00
    item = CartItem.objects.create(cart=cart, book=book, quantity=3)

    # Should be 45.00
    expected_cost = Decimal("45.00")
    assert item.get_cost() == expected_cost


@pytest.mark.django_db
def test_cart_get_total_cost(create_user, create_book):
    """Test total cart cost (Sum of all items)."""
    user = create_user(email="sum@test.com", password="pw")
    cart = Cart.objects.create(user=user)

    b1 = create_book(price=10.00)
    b2 = create_book(price=20.00)

    # 2 of Book1 ($20) + 1 of Book2 ($20) = $40 Total
    CartItem.objects.create(cart=cart, book=b1, quantity=2)
    CartItem.objects.create(cart=cart, book=b2, quantity=1)

    expected_total = Decimal("40.00")
    assert cart.get_total_cost() == expected_total


@pytest.mark.django_db
def test_cart_total_cost_empty(create_user):
    """Test that an empty cart returns 0."""
    user = create_user(email="empty@test.com", password="pw")
    cart = Cart.objects.create(user=user)

    assert cart.get_total_cost() == 0


@pytest.mark.django_db
def test_cart_cascade_on_user_delete(create_user):
    """Test that deleting a user automatically deletes their cart."""
    user = create_user(email="delete_me@test.com", password="pw")
    Cart.objects.create(user=user)

    assert Cart.objects.count() == 1

    # Delete the user
    user.delete()

    # Cart should be gone (CASCADE)
    assert Cart.objects.count() == 0


@pytest.mark.django_db
def test_cart_item_cascade_on_cart_delete(create_user, create_book):
    """Test that deleting a cart deletes all its items."""
    user = create_user(email="cart_del@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book()
    CartItem.objects.create(cart=cart, book=book, quantity=1)

    assert CartItem.objects.count() == 1

    # Delete the cart
    cart.delete()

    # Item should be gone
    assert CartItem.objects.count() == 0


@pytest.mark.django_db
def test_cart_item_cascade_on_book_delete(create_user, create_book):
    """Test that deleting a book removes it from all carts."""
    user = create_user(email="book_del@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book()
    CartItem.objects.create(cart=cart, book=book, quantity=1)

    assert CartItem.objects.count() == 1

    # Delete the book
    book.delete()

    # Item should be gone
    assert CartItem.objects.count() == 0


@pytest.mark.django_db
def test_cart_item_related_name_access(create_user, create_book):
    """Test accessing items via the 'items' related_name on Cart."""
    user = create_user(email="rel@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    b1 = create_book(title="B1")
    b2 = create_book(title="B2")

    CartItem.objects.create(cart=cart, book=b1, quantity=1)
    CartItem.objects.create(cart=cart, book=b2, quantity=1)

    # Your model has related_name="items" in CartItem
    assert cart.items.count() == 2
    assert cart.items.first().book.title in ["B1", "B2"]


@pytest.mark.django_db
def test_cart_item_timestamps(create_user, create_book):
    """Test that timestamps are automatically generated."""
    user = create_user(email="time@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book()

    item = CartItem.objects.create(cart=cart, book=book, quantity=1)

    assert item.created_at is not None
    assert item.updated_at is not None


@pytest.mark.django_db
def test_cart_item_negative_quantity_validation(create_user, create_book):
    """
    Test that model validation rejects negative quantities.
    Note: Standard .save() often bypasses this in SQLite.
    We must use .full_clean() to test model validation explicitly.
    """
    user = create_user(email="neg@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book()

    # Create item with invalid negative quantity
    item = CartItem(cart=cart, book=book, quantity=-1)

    with pytest.raises(ValidationError):
        item.full_clean()
