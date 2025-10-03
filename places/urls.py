from django.urls import path

from . import views

app_name = "places"

urlpatterns = [
    path("", views.home, name="home"),
    path("r/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("r/<int:pk>/pin/", views.toggle_pin, name="toggle_pin"),
]
