import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def create_user():
    """
    A fixture that acts as a factory to create users.
    Usage in test: user = create_user(email="test@example.com", password="password")
    """

    def make_user(**kwargs):
        User = get_user_model()
        return User.objects.create_user(**kwargs)

    return make_user


@pytest.fixture
def create_superuser():
    """
    Factory fixture to create superusers.
    """

    def make_superuser(**kwargs):
        User = get_user_model()
        return User.objects.create_superuser(**kwargs)

    return make_superuser
