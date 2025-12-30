import pytest
from django.urls import reverse
from myApp.models import Book, Favorite, Rating


# ----- Helper Fixture -----
@pytest.fixture
def book_factory():
    def create_book(title="Test Book", stock=10):
        return Book.objects.create(
            title=title, author="Author", price=10.00, stock=stock
        )

    return create_book


# ----- SHOPPING LIST & HOME -----


@pytest.mark.django_db
def test_shopping_list_view_loads(client, book_factory):
    """Test that the shopping list loads and shows books."""
    book_factory(title="Book One")
    book_factory(title="Book Two")

    url = reverse("myApp:shopping")
    response = client.get(url)

    assert response.status_code == 200
    assert "Book One" in str(response.content)
    assert "Book Two" in str(response.content)


@pytest.mark.django_db
def test_home_page_loads(client):
    """Test the index page loads."""
    url = reverse("myApp:home")
    response = client.get(url)
    assert response.status_code == 200
    assert "myApp/index.html" in [t.name for t in response.templates]


# ----- DETAIL VIEW -----


@pytest.mark.django_db
def test_book_detail_view(client, book_factory):
    """Test that the detail page shows the correct book info."""
    book = book_factory(title="Unique Title")
    url = reverse("myApp:book_detail", args=[book.id])

    response = client.get(url)

    assert response.status_code == 200
    assert "Unique Title" in str(response.content)


# ----- SECURITY TESTS (CRITICAL) -----


@pytest.mark.django_db
def test_update_book_view_allowed_for_staff(client, create_superuser, book_factory):
    """Test that a staff member (superuser) CAN access the update page."""
    admin = create_superuser(email="admin@test.com", password="pw")
    client.force_login(admin)

    book = book_factory()
    url = reverse("myApp:update_book", args=[book.id])

    response = client.get(url)
    assert response.status_code == 200  # Access Granted


@pytest.mark.django_db
def test_update_book_view_forbidden_for_normal_user(client, create_user, book_factory):
    """Test that a normal user CANNOT access the update page."""
    user = create_user(email="normal@test.com", password="pw")
    client.force_login(user)

    book = book_factory()
    url = reverse("myApp:update_book", args=[book.id])

    response = client.get(url)
    # UserPassesTestMixin typically raises 403 Forbidden
    assert response.status_code == 403  # Access Denied


# ----- LOGIC TESTS (Favorites) -----


@pytest.mark.django_db
def test_add_to_favorite_toggle(client, create_user, book_factory):
    """Test adding and removing a favorite."""
    user = create_user(email="fav@test.com", password="pw")
    client.force_login(user)
    book = book_factory()

    url = reverse("myApp:add_to_favorite", args=[book.id])

    # 1.Should ADD to favorites
    response = client.get(url)
    assert response.status_code == 302  # Redirects back to shopping
    assert Favorite.objects.filter(user=user, book=book).exists() is True

    # 2.Should REMOVE from favorites (Toggle)
    response = client.get(url)
    assert response.status_code == 302
    assert Favorite.objects.filter(user=user, book=book).exists() is False


@pytest.mark.django_db
def test_add_to_favorite_requires_login(client, book_factory):
    """Test that anonymous users cannot add favorites."""
    book = book_factory()
    url = reverse("myApp:add_to_favorite", args=[book.id])

    response = client.get(url)
    # Should redirect to login page
    assert response.status_code == 302
    assert "login" in response.url


# ----- RATING SUBMISSION -----


@pytest.mark.django_db
def test_submit_rating(client, create_user, book_factory):
    """Test submitting a valid rating."""
    user = create_user(email="rater@test.com", password="pw")
    client.force_login(user)
    book = book_factory()

    url = reverse("myApp:rating", args=[book.id])
    data = {"rate": 5}

    response = client.post(url, data)

    assert response.status_code == 302  # Redirect
    assert Rating.objects.filter(user=user, book=book, rate=5.0).exists() is True


@pytest.mark.django_db
def test_favorite_list_view(client, create_user, book_factory):
    """Test that the favorite list only shows the user's favorites."""
    me = create_user(email="me@test.com", password="pw")
    client.force_login(me)

    my_book = book_factory(title="My Secret Book")
    Favorite.objects.create(user=me, book=my_book)

    other_user = create_user(email="other@test.com", password="pw")
    other_book = book_factory(title="Other Guy's Book")
    Favorite.objects.create(user=other_user, book=other_book)

    url = reverse("myApp:favorite_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "My Secret Book" in str(response.content)
    assert "Other Guy's Book" not in str(response.content)


@pytest.mark.django_db
def test_shopping_list_annotates_favorites(client, create_user, book_factory):
    """Test that the view correctly marks books as favorites in the context."""
    user = create_user(email="context@test.com", password="pw")
    client.force_login(user)

    book_fav = book_factory(title="I Like This")
    book_neutral = book_factory(title="Meh")

    # Create the favorite relation
    Favorite.objects.create(user=user, book=book_fav)
    url = reverse("myApp:shopping")
    response = client.get(url)

    # Extract the books from the context
    books = list(response.context["books"])

    # Find the specific books in the list
    obj_fav = next(b for b in books if b.id == book_fav.id)
    obj_neutral = next(b for b in books if b.id == book_neutral.id)

    # The 'is_favorite' attribute should be dynamically added by the View
    assert getattr(obj_fav, "is_favorite", False) is True
    assert getattr(obj_neutral, "is_favorite", False) is False


@pytest.mark.django_db
def test_shopping_list_clears_session_flag(client, book_factory):
    """Test that visiting the shopping list resets the double-purchase flag."""
    # 1. Set the flag manually (Simulate a user coming from payment)
    session = client.session
    session["prevent_double_purchase"] = True
    session.save()

    # 2. Visit the page
    url = reverse("myApp:shopping")
    client.get(url)

    # 3. Verify flag is gone/False
    assert client.session.get("prevent_double_purchase") is False


@pytest.mark.django_db
def test_update_existing_rating(client, create_user, book_factory):
    """Test that posting again UPDATES the existing rating instead of crashing."""
    user = create_user(email="changer@test.com", password="pw")
    client.force_login(user)
    book = book_factory()

    # 1. Create initial rating (3 stars)
    Rating.objects.create(user=user, book=book, rate=3.0)

    # 2. Post new rating (5 stars)
    url = reverse("myApp:rating", args=[book.id])
    client.post(url, {"rate": 5})

    # 3. Verify DB has updated
    rating = Rating.objects.get(user=user, book=book)
    assert rating.rate == 5.0
    # Ensure we didn't create a duplicate
    assert Rating.objects.count() == 1


@pytest.mark.django_db
def test_submit_invalid_rating(client, create_user, book_factory):
    """Test submitting a rating > 5 fails."""
    user = create_user(email="hacker@test.com", password="pw")
    client.force_login(user)
    book = book_factory()

    url = reverse("myApp:rating", args=[book.id])
    response = client.post(url, {"rate": 6})  # Invalid!

    # Should NOT redirect (Stay on page to show errors)
    assert response.status_code == 200

    # Should NOT save to DB
    assert Rating.objects.exists() is False

    # Should have form errors
    assert "rate" in response.context["form"].errors


@pytest.mark.django_db
def test_staff_can_update_book_stock(client, create_superuser, book_factory):
    """Test that the update view actually saves changes to the DB."""
    admin = create_superuser(email="boss@test.com", password="pw")
    client.force_login(admin)

    book = book_factory(stock=5)
    url = reverse("myApp:update_book", args=[book.id])

    # Change stock to 20
    response = client.post(url, {"stock": 20})

    assert response.status_code == 302  # Success Redirect

    # Refresh from DB
    book.refresh_from_db()
    assert book.stock == 20
