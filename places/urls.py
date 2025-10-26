from django.urls import path

from . import views

app_name = "places"

urlpatterns = [
    path("", views.home, name="home"),
    path("discover/", views.discover, name="discover"),
    path("my/", views.my_restaurants, name="my_restaurants"),
    path("review/", views.review_tab, name="review_tab"),
    path("r/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("r/<int:pk>/pin/", views.toggle_pin, name="toggle_pin"),
    path("r/<int:pk>/review/", views.review_create_for_restaurant, name="review_for_restaurant"),
    path("review/<int:pk>/edit/", views.review_edit, name="review_edit"),
    path("review/thanks/", views.review_thanks, name="review_thanks"),
    path("photo/<int:pk>/delete/", views.photo_delete, name="photo_delete"),
    
    # Lists
    path("list/<int:list_id>/", views.list_detail, name="list_detail"),
    path("list/<int:list_id>/pin/<int:pin_id>/delete/", views.delete_pin, name="delete_pin"),
    path("list/<int:list_id>/edit/", views.edit_list, name="edit_list"),
    path("list/<int:list_id>/delete/", views.delete_list, name="delete_list"),
    path("list/create/", views.create_list, name="create_list"),
    path("r/<int:pk>/list-picker/", views.list_picker, name="list_picker"),
    path("r/<int:pk>/toggle-in-list/<int:list_id>/", views.toggle_in_list, name="toggle_in_list"),
    
    # API endpoints
    path("api/restaurants/autocomplete/", views.restaurant_autocomplete, name="restaurant_autocomplete"),
]
