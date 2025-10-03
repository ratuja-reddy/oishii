from django import forms

from .models import Restaurant, Review


class ReviewForm(forms.ModelForm):
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
        super().__init__(*args, **kwargs)
        # Optional fields
        for name in ["food", "service", "value", "atmosphere"]:
            self.fields[name].required = False
            self.fields[name].empty_label = "— (optional)"
        # Nice ordering for restaurants
        self.fields["restaurant"].queryset = Restaurant.objects.order_by("name")
