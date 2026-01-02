import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from order.models import Order


@pytest.mark.django_db
def test_payment_process_view_renders_template(client, create_user, create_book):
    """Test GET request renders the confirmation page."""
    user = create_user(email="pay@test.com", password="pw")
    client.force_login(user)

    # Create Order
    order = Order.objects.create(user=user, first_name="Test", last_name="Order")

    url = reverse("payment:process", args=[order.id])
    response = client.get(url)

    assert response.status_code == 200
    assert "payment/process.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_payment_process_post_redirects_to_stripe(client, create_user, create_book):
    """
    Test POST request creates a Stripe Session and redirects user.
    """
    user = create_user(email="stripe@test.com", password="pw")
    client.force_login(user)
    order = Order.objects.create(user=user)

    url = reverse("payment:process", args=[order.id])

    # --- MOCK STRIPE ---
    # We replace the real Stripe call with a fake one
    with patch("payment.views.stripe.checkout.Session.create") as mock_create:
        # Create a fake session object with a .url attribute
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test-session"
        mock_create.return_value = mock_session

        # Perform POST
        response = client.post(url)

        # Assert Redirect (303 See Other is often used for payment redirects)
        assert response.status_code == 302
        assert response.url == "https://checkout.stripe.com/test-session"

        # Verify Stripe was called
        mock_create.assert_called_once()
