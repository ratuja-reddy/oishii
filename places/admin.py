from django.contrib import admin

from .models import List, Pin, Restaurant, Review


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "cuisine", "category", "price")
    search_fields = ("name", "city", "cuisine")
    list_filter = ("category", "price")


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_public")
    search_fields = ("title", "owner__username")
    list_filter = ("is_public",)


@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    list_display = ("user", "restaurant", "list", "created_at")
    search_fields = ("user__username", "restaurant__name")
    list_filter = ("created_at",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "user", "overall_rating", "food", "service", "value", "atmosphere", "created_at")
    search_fields = ("restaurant__name", "user__username", "text")
    list_filter = ("overall_rating", "created_at")
