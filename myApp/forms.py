from django import forms
from .models import Rating


class RatingForm(forms.Modelform):
    class Meta:
        model = Rating
        fields = "__all__"
        labels = {
            'rate': 'Rate between 1-5'
        }