from django import forms
from django.core.validators import FileExtensionValidator

from .models import Restaurant, Review


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ReviewForm(forms.ModelForm):
    photos = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'w-full border rounded-xl px-3 py-2'
        }),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        help_text="Upload photos of your meal or the restaurant (optional)"
    )

    class Meta:
        model = Review
        fields = ["restaurant", "overall_rating", "food", "service", "value", "atmosphere", "text"]
        widgets = {
            "restaurant": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "overall_rating": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "food": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "service": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "value": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "atmosphere": forms.Select(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "text": forms.Textarea(attrs={"rows": 4, "class": "w-full border rounded-xl px-3 py-2"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # future: personalize options
        super().__init__(*args, **kwargs)
        # Optional fields
        for name in ["food", "service", "value", "atmosphere"]:
            self.fields[name].required = False
            self.fields[name].empty_label = "— (optional)"
        # Nice ordering for restaurants
        self.fields["restaurant"].queryset = Restaurant.objects.order_by("name")
