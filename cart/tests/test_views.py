import pytest
from django.urls import reverse
from cart.models import Cart, CartItem


@pytest.mark.django_db
def test_cart_add_guest_session(client, create_book):
    """Test adding item to session cart (Guest)."""
    book = create_book(title="Guest Book", price=10)
    url = reverse("cart:cart_add", args=[book.id])

    # Post with quantity 2
    response = client.post(url, {"quantity": 2})

    # Should redirect to session cart
    assert response.status_code == 302
    assert response.url == reverse("cart:session_cart")

    # Check Session
    session = client.session
    assert "cart" in session
    assert session["cart"][str(book.id)] == 2


@pytest.mark.django_db
def test_cart_add_authenticated_db(client, create_user, create_book):
    """Test adding item to DB cart (Logged in)."""
    user = create_user(email="auth@test.com", password="pw")
    book = create_book(title="Auth Book", price=20)
    client.force_login(user)

    url = reverse("cart:cart_add", args=[book.id])

    # Post with quantity 3
    response = client.post(url, {"quantity": 3})

    # Should redirect to DB cart list
    assert response.status_code == 302
    assert response.url == reverse("cart:cart_list")

    # Check Database
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    assert item.quantity == 3


@pytest.mark.django_db
def test_cart_delete_item_guest(client, create_book):
    """Test deleting item from session."""
    book = create_book()

    # Manually setup session
    session = client.session
    session["cart"] = {str(book.id): 5}
    session.save()

    url = reverse("cart:delete_item", args=[book.id])
    response = client.get(url)

    assert response.status_code == 302  # redirect after delete

    session = client.session
    assert str(book.id) not in session.get("cart", {})


@pytest.mark.django_db
def test_cart_delete_item_authenticated(client, create_user, create_book):
    """Test deleting item from DB."""
    user = create_user(email="del@test.com", password="pw")
    client.force_login(user)

    cart = Cart.objects.create(user=user)
    book = create_book()
    item = CartItem.objects.create(cart=cart, book=book, quantity=1)

    url = reverse("cart:delete_item", args=[item.id])
    response = client.get(url)

    assert CartItem.objects.filter(id=item.id).exists() is False
    # Assert the Redirection (The User Experience)
    assert response.status_code == 302
    assert response.url == reverse("cart:cart_list")


@pytest.mark.django_db
def test_cart_add_invalid_quantity(client, create_book):
    """Test that 0 or negative quantity is rejected."""
    book = create_book()
    url = reverse("cart:cart_add", args=[book.id])

    # Try adding -5 items
    response = client.post(url, {"quantity": -5})

    # Should warning and redirect to shopping
    # (Checking redirection is enough to know it failed to add)
    assert response.status_code == 302
    assert response.url == reverse("myApp:shopping")

    # Ensure session is still empty
    assert "cart" not in client.session or client.session["cart"] == {}


@pytest.mark.django_db
def test_cart_add_exceeds_stock(client, create_book):
    """Test that adding more items than available stock fails safely."""
    # Create book with only 5 in stock
    book = create_book(title="Rare Book", stock=5)
    url = reverse("cart:cart_add", args=[book.id])

    # Try to add 6 items
    response = client.post(url, {"quantity": 6})

    # Should redirect to shopping (standard error flow in your view)
    assert response.status_code == 302
    assert response.url == reverse("myApp:shopping")

    # Verify session cart is EMPTY (Item was rejected)
    assert "cart" not in client.session or client.session["cart"] == {}


@pytest.mark.django_db
def test_cart_add_accumulates_quantity(client, create_book):
    """Test adding the same item twice sums the quantity (1 + 2 = 3)."""
    book = create_book(stock=10)
    url = reverse("cart:cart_add", args=[book.id])

    # 1. Add 1 item
    client.post(url, {"quantity": 1})

    # 2. Add 2 MORE of the same item
    client.post(url, {"quantity": 2})

    # 3. Check Session
    session = client.session
    assert session["cart"][str(book.id)] == 3


@pytest.mark.django_db
def test_cart_add_non_integer_quantity(client, create_book):
    """Test sending garbage text as quantity."""
    book = create_book()
    url = reverse("cart:cart_add", args=[book.id])

    # Send "abc" instead of number
    response = client.post(url, {"quantity": "abc"})

    # Should redirect safely (your try/except ValueError block)
    assert response.status_code == 302

    # Cart should remain empty
    assert "cart" not in client.session or client.session["cart"] == {}


@pytest.mark.django_db
def test_session_cart_view_context_math(client, create_book):
    """Test that the guest cart page calculates total price correctly."""
    b1 = create_book(price=10)
    b2 = create_book(price=20)

    # Manually inject session data
    session = client.session
    session["cart"] = {str(b1.id): 2, str(b2.id): 1}  # (2*10) + (1*20) = 40
    session.save()

    url = reverse("cart:session_cart")
    response = client.get(url)

    assert response.status_code == 200
    # Check the 'total' variable passed to the template
    assert response.context["total"] == 40


@pytest.mark.django_db
def test_security_cannot_delete_others_item(client, create_user, create_book):
    """
    CRITICAL SECURITY CHECK:
    User A should NOT be able to delete User B's cart item.
    """
    # 1. Setup User A (Attacker) and User B (Victim)
    attacker = create_user(email="hacker@test.com", password="pw")
    victim = create_user(email="victim@test.com", password="pw")

    # 2. Give Victim a cart item
    cart_b = Cart.objects.create(user=victim)
    item_b = CartItem.objects.create(cart=cart_b, book=create_book(), quantity=1)

    # 3. Login as Attacker
    client.force_login(attacker)

    # 4. Try to delete Victim's item
    url = reverse("cart:delete_item", args=[item_b.id])
    response = client.get(url)

    # 5. EXPECTED RESULT: 404 Not Found (or 403 Forbidden)
    # If this returns 302 (Redirect), it means the delete SUCCEEDED (Security Hole!)
    assert response.status_code == 404

    # 6. Verify Item still exists
    assert CartItem.objects.filter(id=item_b.id).exists() is True
