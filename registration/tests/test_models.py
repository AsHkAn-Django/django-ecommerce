import pytest
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    """
    Test that a user is created successfully with the correct email and password.
    """
    email = 'normal@user.com'
    password = 'foo'
    user  = User.objects.create_user(
        email=email,
        password=password,
        full_name='Normal User'
    )

    assert user.email == email
    assert user.check_password(password) is True
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    """
    Test that a superuser has is_staff and is_superuser set to True.
    """
    email = 'super@user.com'
    password = 'foo'
    admin_user = User.objects.create_superuser(
        email=email,
        password=password,
        full_name='Super User'
    )

    assert admin_user.email == email
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.is_active is True


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Test that creating a user without an email raises a ValueError."""
    with pytest.raises(ValueError) as err:
        User.objects.create_user(
            email=None,
            password='foo'
        )

    assert str(err.value) == 'Users must have an email address'


@pytest.mark.django_db
def test_create_user_email_normalization():
    """Test that email addresses are automatically lowercased."""
    email = "UPPERCASE@Example.COM"
    user = User.objects.create_user(email=email, password="foo")

    assert user.email == "UPPERCASE@example.com"


@pytest.mark.django_db
def test_user_string_representation():
    """Test the __str__ method of the model."""
    user = User.objects.create_user(email="test@str.com", password="foo")
    assert str(user) == "test@str.com"