import pytest
from myApp.api.serializers import BookSerializer
from myApp.models import Favorite, Rating
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory


# --- Helper to Mock Request Context ---
def get_serializer_context(user):
    """
    Serializers need a 'request' in their context to check
    if a user is authenticated (for is_favorite).
    """
    factory = APIRequestFactory()
    request = factory.get('/')
    request.user = user or AnonymousUser()
    return {'request': request}


@pytest.mark.django_db
def test_book_serializer_contains_expected_fields(create_book):
    """Test that the serialized data has exactly the keys we expect."""
    book = create_book(title="Test Book")
    serializer = BookSerializer(book, context=get_serializer_context(None))
    data = serializer.data

    expected_keys = {
        'id', 'title', 'author', 'stock', 'price',
        'image', 'description', 'average_rate',
        'rate_numbers', 'is_favorite'
    }
    assert set(data.keys()) == expected_keys


@pytest.mark.django_db
def test_serializer_average_rate_calculation(create_user, create_book):
    """Test that average_rate is calculated and included in JSON."""
    book = create_book()
    u1 = create_user(email="u1@test.com", password="pw")
    u2 = create_user(email="u2@test.com", password="pw")

    Rating.objects.create(user=u1, book=book, rate=5.0)
    Rating.objects.create(user=u2, book=book, rate=3.0)

    context = get_serializer_context(u1)
    serializer = BookSerializer(book, context=context)

    # 5 + 3 / 2 = 4.0
    assert serializer.data['average_rate'] == 4.0
    assert serializer.data['rate_numbers'] == 2


@pytest.mark.django_db
def test_serializer_is_favorite_true(create_user, create_book):
    """Test is_favorite returns True if the context user liked the book."""
    user = create_user(email="fan@test.com", password="pw")
    book = create_book()
    Favorite.objects.create(user=user, book=book)

    context = get_serializer_context(user)
    serializer = BookSerializer(book, context=context)

    assert serializer.data['is_favorite'] is True


@pytest.mark.django_db
def test_serializer_is_favorite_false(create_user, create_book):
    """Test is_favorite returns False if not in favorites."""
    user = create_user(email="hater@test.com", password="pw")
    book = create_book()

    context = get_serializer_context(user)
    serializer = BookSerializer(book, context=context)

    assert serializer.data['is_favorite'] is False


@pytest.mark.django_db
def test_serializer_validation_negative_price():
    """Test serializer rejects negative prices."""
    data = {'title': 'Bad Price', 'price': -5.00, 'author': 'Me', 'stock': 1}
    serializer = BookSerializer(data=data, context=get_serializer_context(None))
    assert serializer.is_valid() is False
    assert 'price' in serializer.errors


@pytest.mark.django_db
def test_serializer_ignores_read_only_input():
    """Test that sending 'stock' in payload is ignored (because it's read-only)."""
    data = {'title': 'Stock Hack', 'price': 10.00, 'author': 'Me', 'stock': 100}
    serializer = BookSerializer(data=data, context=get_serializer_context(None))
    assert serializer.is_valid() is True
    book = serializer.save()
    assert book.stock != 100