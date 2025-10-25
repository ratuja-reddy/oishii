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
    # Common cuisine choices
    CUISINE_CHOICES = [
        ('italian', 'Italian'),
        ('japanese', 'Japanese'),
        ('chinese', 'Chinese'),
        ('indian', 'Indian'),
        ('mexican', 'Mexican'),
        ('thai', 'Thai'),
        ('french', 'French'),
        ('mediterranean', 'Mediterranean'),
        ('korean', 'Korean'),
        ('vietnamese', 'Vietnamese'),
        ('american', 'American'),
        ('spanish', 'Spanish'),
        ('greek', 'Greek'),
        ('lebanese', 'Lebanese'),
        ('ethiopian', 'Ethiopian'),
        ('peruvian', 'Peruvian'),
        ('brazilian', 'Brazilian'),
        ('turkish', 'Turkish'),
        ('moroccan', 'Moroccan'),
        ('other', 'Other'),
    ]
    
    favorite_cuisines = forms.MultipleChoiceField(
        choices=CUISINE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
        required=False,
        help_text="Select your favorite cuisines"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow selection from all restaurants
        from places.models import Restaurant
        self.fields['favorite_spots'].queryset = Restaurant.objects.all().order_by('name')
    
    def clean_favorite_spots(self):
        spots = self.cleaned_data.get('favorite_spots')
        if len(spots) > 3:
            raise forms.ValidationError("You can only select up to 3 favorite spots.")
        return spots
    
    class Meta:
        model = Profile
        fields = ["display_name", "bio", "location", "website", "avatar", "favorite_cuisines", "favorite_spots"]
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "bio":          forms.Textarea(attrs={"class": "w-full border rounded-xl px-3 py-2", "rows": 4}),
            "location":     forms.TextInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "website":      forms.URLInput(attrs={"class": "w-full border rounded-xl px-3 py-2"}),
            "favorite_spots": forms.SelectMultiple(attrs={"class": "w-full border rounded-xl px-3 py-2", "size": "5"}),
            # avatar uses default file input
        }
