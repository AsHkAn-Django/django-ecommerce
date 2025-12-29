import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_signup_view_status_code(client):
    """
    Test that a signup page loads correctly with a 200 status code.
    """
    url = reverse("registration:sign_up")
    response = client.get(url)
    assert response.status_code == 200
    assert "registration/sign_up.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_signup_creates_user(client):
    """
    Test that submitting the form actually creates a new user.
    """
    url = reverse("registration:sign_up")
    data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password1": "complexpassword123",
        "password2": "complexpassword123",
    }

    response = client.post(url, data)

    assert response.status_code == 302

    user = get_user_model().objects.get(email="newuser@example.com")
    assert user.full_name == "New User"
    assert user.check_password("complexpassword123") is True


@pytest.mark.django_db
def test_signup_fails_password_mismatch(client):
    """
    Test that the signup fails when passwords do not match.
    """
    url = reverse("registration:sign_up")
    data = {
        "email": "typo@example.com",
        "full_name": "Typo User",
        "password1": "passwordA",
        "password2": "passwordB",
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert get_user_model().objects.filter(email="typo@example.com").exists() is False
    assert response.context["form"].errors


@pytest.mark.django_db
def test_signup_fails_duplicate_email(client, create_user):
    """
    Test that the signup fails when trying to register with an existing email.
    """
    email = "existing@example.com"
    create_user(email=email, password="password123")

    url = reverse("registration:sign_up")
    data = {
        "email": email,
        "full_name": "Existing User",
        "password1": "newpassword123",
        "password2": "newpassword123",
    }

    response = client.post(url, data)

    assert response.status_code == 200
    errors = response.context["form"].errors
    assert "email" in errors
    # We check for the substring because the error might be wrapped in a list
    assert "Custom user with this Email already exists." in str(errors["email"])


@pytest.mark.django_db
def test_signup_fails_invalid_email_format(client):
    """Test that signup fails if email is not valid."""
    url = reverse("registration:sign_up")
    data = {
        "email": "not-an-email",
        "full_name": "Invalid Email User",
        "password1": "validpassword123",
        "password2": "validpassword123",
    }
    response = client.post(url, data)

    assert response.status_code == 200
    assert "email" in response.context["form"].errors


@pytest.mark.django_db
def test_login_view_loads(client):
    """Test login page renders."""
    url = reverse("registration:login")
    response = client.get(url)
    assert response.status_code == 200
    assert "registration/login.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_login_successful(client, create_user):
    """Test a valid user can login."""
    email = "login@test.com"
    password = "securepassword"
    create_user(email=email, password=password)

    url = reverse("registration:login")
    response = client.post(url, {"username": email, "password": password})

    # Should redirect (302)
    assert response.status_code == 302
    assert (
        int(client.session["_auth_user_id"])
        == get_user_model().objects.get(email=email).id
    )


@pytest.mark.django_db
def test_login_fails_invalid_credentials(client, create_user):
    """Test login fails with wrong password."""
    email = "login@test.com"
    create_user(email=email, password="correct_password")

    # FIX: Use namespace 'registration:login'
    url = reverse("registration:login")
    response = client.post(url, {"username": email, "password": "WRONG_PASSWORD"})

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
