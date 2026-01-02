import pytest
from django.urls import reverse
from rest_framework import status
from myApp.models import Book


# --- Fixture for the URL ---
@pytest.fixture
def books_url():
    """Returns the list URL. Uses reverse() safely at runtime."""
    return reverse("myApp_api:books-list")


# --- GET REQUESTS (Read Only) ---


@pytest.mark.django_db
def test_get_books_list_public(api_client, create_book, books_url):
    """Test that anyone (even anonymous) can see the book list."""
    create_book(title="Book 1")
    create_book(title="Book 2")
    response = api_client.get(books_url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


@pytest.mark.django_db
def test_get_book_detail_public(api_client, create_book):
    """Test getting a single book detail."""
    book = create_book(title="Detail Book")
    url = reverse("myApp_api:books-detail", args=[book.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["title"] == "Detail Book"


# --- FILTERING & ORDERING ---


@pytest.mark.django_db
def test_filter_books_by_title(api_client, create_book, books_url):
    """Test ?title=Harry query param."""
    create_book(title="Harry Potter")
    create_book(title="Lord of the Rings")
    response = api_client.get(books_url, {"title": "Harry"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["title"] == "Harry Potter"


@pytest.mark.django_db
def test_order_books(api_client, create_book, books_url):
    """Test ?ordering=price query param."""
    b1 = create_book(title="Cheap", price=10.00)
    b2 = create_book(title="Expensive", price=50.00)
    response = api_client.get(books_url, {"ordering": "price"})
    assert response.data[0]["id"] == b1.id
    assert response.data[1]["id"] == b2.id
    response = api_client.get(books_url, {"ordering": "-price"})
    assert response.data[0]["id"] == b2.id


# --- PERMISSIONS (The Security Check) ---


@pytest.mark.django_db
def test_create_book_anonymous_forbidden(api_client, books_url):
    """Test that anonymous users CANNOT create books."""
    payload = {"title": "Hacked Book", "price": 10.00, "stock": 5}
    response = api_client.post(books_url, payload)

    # Default DRF IsAuthenticatedOrReadOnly usually returns 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_book_normal_user_forbidden(api_client, create_user, books_url):
    """Test that regular users CANNOT create books."""
    user = create_user(email="user@test.com", password="pw")
    api_client.force_authenticate(user=user)
    payload = {"title": "User Book", "price": 10.00, "stock": 5}
    response = api_client.post(books_url, payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_create_book_admin_allowed(api_client, create_superuser, books_url):
    """Test that Admin (Staff) CAN create books."""
    admin = create_superuser(email="admin@test.com", password="pw")
    api_client.force_authenticate(user=admin)

    payload = {"title": "Admin Book", "price": 25.00, "description": "Created via API"}
    response = api_client.post(books_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert Book.objects.count() == 1
    assert Book.objects.get().title == "Admin Book"


# --- UPDATE PERMISSIONS ---


@pytest.mark.django_db
def test_update_book_admin_allowed(api_client, create_superuser, create_book):
    """Test that Admin can update a book."""
    admin = create_superuser(email="admin@test.com", password="pw")
    api_client.force_authenticate(user=admin)
    book = create_book(title="Old Title")
    url = reverse("myApp_api:books-detail", args=[book.id])
    payload = {"title": "New Title", "price": 20.00}
    response = api_client.put(url, payload)
    assert response.status_code == status.HTTP_200_OK
    book.refresh_from_db()
    assert book.title == "New Title"


# --- DELETE REQUESTS (Destructive) ---


@pytest.mark.django_db
def test_delete_book_admin_allowed(api_client, create_superuser, create_book):
    """Test that Admin can delete a book."""
    admin = create_superuser(email="admin@test.com", password="pw")
    api_client.force_authenticate(user=admin)

    book = create_book()
    url = reverse("myApp_api:books-detail", args=[book.id])

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Book.objects.count() == 0


@pytest.mark.django_db
def test_delete_book_user_forbidden(api_client, create_user, create_book):
    """Test that normal user CANNOT delete a book."""
    user = create_user(email="user@test.com", password="pw")
    api_client.force_authenticate(user=user)

    book = create_book()
    url = reverse("myApp_api:books-detail", args=[book.id])

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Book.objects.count() == 1


# --- PATCH REQUESTS (Partial Updates) ---


@pytest.mark.django_db
def test_patch_book_price_only(api_client, create_superuser, create_book):
    """Test that Admin can update JUST the price without sending title."""
    admin = create_superuser(email="admin@test.com", password="pw")
    api_client.force_authenticate(user=admin)
    book = create_book(title="Original Title", price=10.00)
    url = reverse("myApp_api:books-detail", args=[book.id])
    response = api_client.patch(url, {"price": 50.00})
    assert response.status_code == status.HTTP_200_OK
    book.refresh_from_db()
    assert book.price == 50.00
    assert book.title == "Original Title"


# --- ERROR HANDLING ---


@pytest.mark.django_db
def test_get_404_for_missing_book(api_client):
    """Test requesting a book ID that doesn't exist."""
    url = reverse("myApp_api:books-detail", args=[99999])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_search_returns_empty(api_client, create_book, books_url):
    """Test searching for a term that matches nothing."""
    create_book(title="Python Book")
    response = api_client.get(books_url, {"title": "Java"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0
