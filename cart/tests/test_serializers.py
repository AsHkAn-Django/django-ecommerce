import pytest
from rest_framework.exceptions import ValidationError
from django.http import Http404
from cart.models import Cart, CartItem
from cart.api.serializers import CreateCartSerializer, CreateCartItemSerializer
from rest_framework.test import APIRequestFactory


# --- Helper to Mock Request ---
def get_context(user):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user
    return {"request": request}


# --- 1. CREATE CART SERIALIZER TESTS ---


@pytest.mark.django_db
def test_create_cart_serializer_success(create_user):
    """Test creating a cart for a user who doesn't have one."""
    user = create_user(email="new@test.com", password="pw")
    context = get_context(user)

    serializer = CreateCartSerializer(data={}, context=context)
    assert serializer.is_valid() is True
    cart = serializer.save()

    assert cart.user == user


@pytest.mark.django_db
def test_create_cart_serializer_already_exists(create_user):
    """Test that creating a duplicate cart raises ValidationError."""
    user = create_user(email="dup@test.com", password="pw")
    Cart.objects.create(user=user)  # Cart already exists

    context = get_context(user)
    serializer = CreateCartSerializer(data={}, context=context)

    with pytest.raises(ValidationError) as e:
        serializer.is_valid(raise_exception=True)

    assert "User already has a cart" in str(e.value)


# --- 2. CREATE CART ITEM SERIALIZER TESTS ---


@pytest.mark.django_db
def test_add_item_serializer_new_item(create_user, create_book):
    """Test adding a fresh book to the cart."""
    user = create_user(email="add@test.com", password="pw")
    Cart.objects.create(user=user)
    book = create_book(title="New Book", stock=10)

    context = get_context(user)
    data = {"book": book.id, "quantity": 2}

    serializer = CreateCartItemSerializer(data=data, context=context)
    assert serializer.is_valid() is True
    item = serializer.save()

    assert item.quantity == 2
    assert item.book == book


@pytest.mark.django_db
def test_add_item_serializer_accumulates(create_user, create_book):
    """Test adding existing book sums the quantity (1 + 2 = 3)."""
    user = create_user(email="sum@test.com", password="pw")
    cart = Cart.objects.create(user=user)
    book = create_book(stock=10)

    # Already have 1
    CartItem.objects.create(cart=cart, book=book, quantity=1)

    context = get_context(user)
    data = {"book": book.id, "quantity": 2}

    serializer = CreateCartItemSerializer(data=data, context=context)
    assert serializer.is_valid() is True
    item = serializer.save()

    assert item.quantity == 3  # 1 + 2


@pytest.mark.django_db
def test_add_item_serializer_exceeds_stock(create_user, create_book):
    """Test validation error if adding more than stock."""
    user = create_user(email="stock@test.com", password="pw")
    Cart.objects.create(user=user)
    book = create_book(stock=5)

    context = get_context(user)
    # Try to add 6
    data = {"book": book.id, "quantity": 6}

    serializer = CreateCartItemSerializer(data=data, context=context)

    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_add_item_serializer_no_cart_fails(create_user, create_book):
    """
    Test that adding item fails if user has no cart.
    Note: Your code uses get_object_or_404 inside validate(),
    which raises Http404, NOT ValidationError.
    """
    user = create_user(email="nocart@test.com", password="pw")
    # NO Cart created for this user
    book = create_book()

    context = get_context(user)
    data = {"book": book.id, "quantity": 1}

    serializer = CreateCartItemSerializer(data=data, context=context)

    # Because you used get_object_or_404 in validate(), it raises Http404
    with pytest.raises(Http404):
        serializer.is_valid(raise_exception=True)
