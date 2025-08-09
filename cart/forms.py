from django import forms


NUMBER_CHOICES = ((n, str(n)) for n in range(1,21))


class CartAddForm(forms.Form):
    """A form for choosing the number of books user wanna add to cart."""
    quantity = forms.TypedChoiceField(choices=NUMBER_CHOICES, coerce=int)
