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


class EmojiRadioSelect(forms.RadioSelect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({'class': 'flex gap-4'})

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Add emoji to the label
        if value == 'True':
            option['label'] = f'👍 {label}'
        elif value == 'False':
            option['label'] = f'👎 {label}'
        return option


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

    would_go_again = forms.BooleanField(
        widget=EmojiRadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
        label="Would you go again?",
        required=True
    )

    class Meta:
        model = Review
        fields = ["restaurant", "overall_rating", "would_go_again", "food", "service", "value", "atmosphere", "text"]
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
