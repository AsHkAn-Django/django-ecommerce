import pytest
from myApp.forms import RatingForm


@pytest.mark.django_db
def test_rating_form_valid():
    """Test that the form is valid with a correct rating (1-5)."""
    # 5 is the max, 1 is the min. Both should pass.
    form = RatingForm(data={"rate": 5})
    assert form.is_valid() is True

    form = RatingForm(data={"rate": 1})
    assert form.is_valid() is True


@pytest.mark.django_db
def test_rating_form_invalid_too_high():
    """Test that the form rejects ratings higher than 5."""
    form = RatingForm(data={"rate": 6})

    assert form.is_valid() is False
    assert "rate" in form.errors
    # The error message comes from the MaxValueValidator on the model
    assert "Ensure this value is less than or equal to 5.0." in form.errors["rate"]


@pytest.mark.django_db
def test_rating_form_invalid_too_low():
    """Test that the form rejects ratings lower than 1."""
    form = RatingForm(data={"rate": 0.9})

    assert form.is_valid() is False
    assert "rate" in form.errors
    assert "Ensure this value is greater than or equal to 1.0." in form.errors["rate"]


@pytest.mark.django_db
def test_rating_form_label():
    """Test that the form has the custom label defined in Meta."""
    form = RatingForm()
    assert form.fields["rate"].label == "Rate between 1-5"
