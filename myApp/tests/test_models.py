import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from decimal import Decimal
from myApp.models import Book, Rating, Favorite, book_image_upload_path
import os


@pytest.fixture
def create_book():
    """Favtory to create a book quickly."""

    def make_book(title="Test Book", price=10.00, stock=5):
        return Book.objects.create(
            title=title,
            author="Test Author",
            price=Decimal(price),
            stock=stock,
            description="Test Description",
        )

    return make_book


# ----- Book basic tests -----


@pytest.mark.django_db
def test_book_string_representation(create_book):
    """Test the __str__ method of the book model.l"""
    book = create_book(title="Harry Potter")
    assert str(book) == "Harry Potter"


@pytest.mark.django_db
def test_book_absolute_url(create_book):
    """Test get_absolute_url returns the correct home path."""
    book = create_book()
    assert book.get_absolute_url() == "/"


@pytest.mark.django_db
def test_book_image_upload_path():
    """Test that the image path slugifies the title correctly."""

    class MockInstance:
        title = "My Cool Book"

    filename = "cover.jpg"
    path = book_image_upload_path(MockInstance(), filename)

    # Use os.path.join so it expects backslashes on Windows
    expected_path = os.path.join("uploads", "my-cool-book", "cover.jpg")

    assert path == expected_path


# ----- Book Stock Logic Tests -----


@pytest.mark.django_db
def test_stock_lower_than_10_returns_true(create_book):
    """Test logic returns True when stock is single digit."""
    book = create_book(stock=9)
    assert book.stock_lower_than10() is True


@pytest.mark.django_db
def test_stock_lower_than_10_returns_false(create_book):
    """Test logic returns False when stock is 10 or more."""
    book = create_book(stock=10)
    assert book.stock_lower_than10() is False


@pytest.mark.django_db
def test_quantity_stock_check_success(create_book):
    """Test check passes when request quantity is available."""
    book = create_book(stock=5)
    # Should return True, not raise error
    assert book.quantity_stock_check(5) is True


@pytest.mark.django_db
def test_quantity_stock_check_failure(create_book):
    """Test check raises ValueError when request quantity exceeds stock."""
    book = create_book(stock=5)
    with pytest.raises(ValueError) as exc:
        book.quantity_stock_check(6)

    assert str(exc.value) == "Only 5 items available."


# ----- RATING LOGIC TESTS -----


@pytest.mark.django_db
def test_rating_string_representation(create_user, create_book):
    """Test __str__ for Rating."""
    user = create_user(email="r@test.com", password="pw")
    book = create_book(title="Book A")
    rating = Rating.objects.create(user=user, book=book, rate=5.0)

    assert str(rating) == f"{user.email} rated 5.0 to Book A"


@pytest.mark.django_db
def test_rating_max_value_validation(create_user, create_book):
    """Test rating cannot be higher than 5.0."""
    user = create_user(email="max@test.com", password="pw")
    book = create_book()
    rating = Rating(user=user, book=book, rate=6.0)

    with pytest.raises(ValidationError):
        rating.full_clean()


@pytest.mark.django_db
def test_rating_min_value_validation(create_user, create_book):
    """Test rating cannot be lower than 1.0."""
    user = create_user(email="min@test.com", password="pw")
    book = create_book()
    rating = Rating(user=user, book=book, rate=0.0)

    with pytest.raises(ValidationError):
        rating.full_clean()


@pytest.mark.django_db
def test_rating_unique_constraint(create_user, create_book):
    """Test that a user cannot rate the same book twice."""
    user = create_user(email="unique@test.com", password="pw")
    book = create_book()

    # First rating
    Rating.objects.create(user=user, book=book, rate=4.0)

    # Second rating for same book + user -> Should crash DB
    with pytest.raises(IntegrityError):
        Rating.objects.create(user=user, book=book, rate=3.0)


# ----- FAVORITE MODEL TESTS -----


@pytest.mark.django_db
def test_favorite_creation(create_user, create_book):
    """Test creating a favorite."""
    user = create_user(email="fav@test.com", password="pw")
    book = create_book()
    fav = Favorite.objects.create(user=user, book=book)

    assert fav.user == user
    assert fav.book == book


@pytest.mark.django_db
def test_favorite_string_representation(create_user, create_book):
    """Test __str__ for Favorite."""
    user = create_user(email="favstr@test.com", password="pw")
    book = create_book(title="My Fav")
    fav = Favorite.objects.create(user=user, book=book)

    assert str(fav) == "favstr@test.com added My Fav"


@pytest.mark.django_db
def test_book_price_cannot_be_negative(create_book):
    """Test that negative price raises ValidationError."""
    book = create_book(price=-10.00)
    with pytest.raises(ValidationError):
        book.full_clean()  # Must call full_clean to trigger validators


@pytest.mark.django_db
def test_book_stock_cannot_be_negative(create_book):
    """Test that negative stock raises ValidationError."""
    book = create_book(stock=-1)
    with pytest.raises(ValidationError):
        book.full_clean()


@pytest.mark.django_db
def test_get_average_rating_calculation(create_user, create_book):
    """Test average rating is calculated correctly."""
    book = create_book()
    u1 = create_user(email="u1@test.com", password="pw")
    u2 = create_user(email="u2@test.com", password="pw")

    Rating.objects.create(user=u1, book=book, rate=5.0)
    Rating.objects.create(user=u2, book=book, rate=3.0)

    # (5 + 3) / 2 = 4.0
    assert book.get_average_rating() == Decimal("4.0")
    assert book.get_rates_number() == 2


@pytest.mark.django_db
def test_get_average_rating_empty(create_book):
    """Test average rating returns 0.0 if no ratings exist."""
    book = create_book()
    assert book.get_average_rating() == Decimal("0.0")
    assert book.get_rates_number() == 0
