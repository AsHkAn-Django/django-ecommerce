from django import forms
from .models import Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = [
            "rate",
        ]
        labels = {"rate": "Rate between 1-5"}
