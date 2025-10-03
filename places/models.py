from django.conf import settings
from django.db import models


class Restaurant(models.Model):
    CATEGORY_CHOICES = [
        ("cafe", "Cafe"),
        ("restaurant", "Restaurant"),
        ("bar", "Bar"),
        ("bakery", "Bakery"),
        ("street_food", "Street Food"),
        ("other", "Other"),
    ]

    PRICE_CHOICES = [
        ("$", "Budget"),
        ("$$", "Mid-range"),
        ("$$$", "Expensive"),
        ("$$$$", "Luxury"),
    ]

    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    cuisine = models.CharField(max_length=120, blank=True)  # e.g. Italian, Japanese
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="restaurant",
    )
    price = models.CharField(
        max_length=5,
        choices=PRICE_CHOICES,
        blank=True,
        null=True,
    )

    opening_hours = models.TextField(
        blank=True,
        help_text="Free-text opening hours, e.g. 'Mon–Fri 8am–6pm; Sat 9–2'.",
    )
    website = models.URLField(blank=True)

    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    external_id = models.CharField(
        max_length=120, blank=True, db_index=True
    )  # e.g. Google Place ID

    def __str__(self):
        return self.name


class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    is_public = models.BooleanField(default=True)

    class Meta:
        unique_together = ("owner", "title")

    def __str__(self):
        return f"{self.owner} – {self.title}"


class Pin(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pins"
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="pins"
    )
    list = models.ForeignKey(
        List, null=True, blank=True, on_delete=models.SET_NULL, related_name="pins"
    )
    note = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "restaurant")

    def __str__(self):
        return f"{self.user} → {self.restaurant}"

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1–5

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    restaurant = models.ForeignKey(
        "places.Restaurant", on_delete=models.CASCADE, related_name="reviews"
    )

    overall_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)

    # Optional sub-ratings
    food = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    service = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    value = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    atmosphere = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)

    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "restaurant")  # one review per user per place
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} → {self.restaurant} ({self.overall_rating}★)"
