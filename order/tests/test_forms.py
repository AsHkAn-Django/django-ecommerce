from order.forms import OrderForm


def test_order_form_valid():
    data = {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"}
    form = OrderForm(data=data)
    assert form.is_valid() is True


def test_order_form_invalid_missing_email():
    data = {"first_name": "Jane", "last_name": "Doe"}
    form = OrderForm(data=data)
    assert form.is_valid() is False
    assert "email" in form.errors
