import pytest
from cart.models import Cart, CartItem


# --- THE FRESH MERGE ---
# Scenario: I am a guest. I add a book. I log in.
# Result: That book should now be in my saved database cart.


@pytest.mark.django_db
def test_signal_merges_session_to_db_new_items(client, create_user, create_book):
    """Test moving items from session to DB on login."""
    # 1. Setup Data
    user = create_user(email="guest@test.com", password="pw")
    book = create_book(title="Session Book", price=10)

    # 2. Simulate Guest Session (The 'Magic' setup)
    # We manually inject the cart into the session before logging in
    session = client.session
    session["cart"] = {str(book.id): 3}  # {book_id: quantity}
    session.save()

    # 3. Perform Login (This triggers the signal)
    client.login(email="guest@test.com", password="pw")

    # 4. Assertions
    # Check Database
    cart = Cart.objects.get(user=user)
    item = CartItem.objects.get(cart=cart, book=book)
    assert item.quantity == 3

    # Check Session is cleared
    assert "cart" not in client.session or client.session["cart"] == {}


# --- THE CUMULATIVE MERGE (The Logic Check) ---
# Scenario: I have 1 book saved in my account.
# I browse as a guest and add 2 MORE of that same book.
# I log in.
# Result: I should have 3 items total.


@pytest.mark.django_db
def test_signal_merges_overlapping_items_sum_quantity(client, create_user, create_book):
    """Test that quantities are SUMMED if item exists in both places."""
    # 1. Setup User with existing DB item
    user = create_user(email="returning@test.com", password="pw")
    book = create_book(title="Popular Book")

    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, book=book, quantity=1)  # Existing: 1

    # 2. Setup Session with SAME book
    session = client.session
    session["cart"] = {str(book.id): 2}  # New: 2
    session.save()

    # 3. Login
    client.login(email="returning@test.com", password="pw")

    # 4. Assertions
    # 1 (DB) + 2 (Session) = 3 Total
    item = CartItem.objects.get(cart=cart, book=book)
    assert item.quantity == 3


# --- 3. THE EMPTY SESSION ---
# Scenario: I log in without adding anything.
# Result: Nothing should break.


@pytest.mark.django_db
def test_signal_does_nothing_if_session_empty(client, create_user):
    """Test login works fine even if session cart is empty."""
    user = create_user(email="clean@test.com", password="pw")

    # Login with empty session
    client.login(email="clean@test.com", password="pw")

    # Assert that NO cart exists (Since signal returns early)
    assert Cart.objects.filter(user=user).exists() is False
