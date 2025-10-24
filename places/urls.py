from django.urls import path

from . import views

app_name = "places"

urlpatterns = [
    path("", views.home, name="home"),
    path("r/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("r/<int:pk>/pin/", views.toggle_pin, name="toggle_pin"),
    path("r/<int:pk>/review/", views.review_create_for_restaurant, name="review_for_restaurant"),
    path("review/<int:pk>/edit/", views.review_edit, name="review_edit"),
    path("photo/<int:pk>/delete/", views.photo_delete, name="photo_delete"),
]
