import pytest
import json
from unittest.mock import patch, MagicMock
from django.urls import reverse
from order.models import Order, OrderItem
from cart.models import Cart, CartItem


@pytest.mark.django_db
def test_stripe_webhook_success_flow(client, create_user, create_book):
    """
    Simulate a 'checkout.session.completed' event from Stripe.
    Verify that Order is paid, Stock reduced, Cart cleared, and Email sent.
    """
    # 1. SETUP DATA
    user = create_user(email="webhook@test.com", password="pw")

    # Create Book (Stock = 10)
    book = create_book(title="Stock Book", stock=10)

    # Create Order (Buying 2 items)
    order = Order.objects.create(user=user, paid=False)
    OrderItem.objects.create(order=order, book=book, price=10, quantity=2)

    # Create Cart (Should be deleted after payment)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, book=book, quantity=2)

    # 2. PREPARE FAKE STRIPE PAYLOAD
    payload = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "mode": "payment",
                "payment_status": "paid",
                "client_reference_id": str(order.id),
                "payment_intent": "pi_fake_123",
            }
        },
    }

    url = reverse("payment:stripe-webhook")

    # 3. MOCK EVERYTHING
    # We need to mock:
    # A. Stripe Signature Verification (so it accepts our fake payload)
    # B. The Celery Task (so we don't need Redis running)

    with patch("stripe.Webhook.construct_event") as mock_verify, patch(
        "payment.webhooks.send_successful_payment_email.delay"
    ) as mock_task:

        # Configure the verification mock to return our payload as an object
        # (Stripe library converts JSON dict to an object with dot notation)
        class FakeEvent:
            type = payload["type"]
            data = MagicMock()

        fake_event = FakeEvent()
        # We need to simulate the nested structure:
        # event.data.object.client_reference_id
        fake_session = MagicMock()
        fake_session.mode = "payment"
        fake_session.payment_status = "paid"
        fake_session.client_reference_id = str(order.id)
        fake_session.payment_intent = "pi_fake_123"

        fake_event.data.object = fake_session
        mock_verify.return_value = fake_event

        # 4. SEND REQUEST
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature",
        )

        # 5. ASSERTIONS
        assert response.status_code == 200

        # Check Order Status
        order.refresh_from_db()
        assert order.paid is True
        assert order.stripe_id == "pi_fake_123"

        # Check Stock Reduction (10 - 2 = 8)
        book.refresh_from_db()
        assert book.stock == 8

        # Check Cart Cleared
        assert CartItem.objects.filter(cart=cart).exists() is False

        # Check Email Task Triggered
        mock_task.assert_called_once_with(order.id)
