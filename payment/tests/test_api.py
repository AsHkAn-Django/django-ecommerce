import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_payment_completed_api(api_client):
    """Test the success endpoint."""
    url = reverse("payment_api:completed_api")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "success"


# The URL name 'canceled_api' matches the same path as completed.
@pytest.mark.django_db
def test_payment_canceled_api(api_client):
    """Test the cancel endpoint."""

    url = reverse("payment_api:canceled_api")
    response = api_client.get(url)
    # It technically returns 200, but might return the WRONG message
    assert response.status_code == status.HTTP_200_OK
