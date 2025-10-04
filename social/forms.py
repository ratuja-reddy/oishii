from django import forms
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "last_name":  forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "email":      forms.EmailInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "bio", "location", "website", "avatar"]
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "bio":          forms.Textarea(attrs={"class": "w-full border rounded-xl px-3 py-2", "rows": 4}),
            "location":     forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "website":      forms.URLInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            # avatar uses default file input
        }
