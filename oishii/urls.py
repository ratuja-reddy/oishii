from django.contrib import admin
from django.urls import include, path

from places import views as pviews
from social import views as sviews

urlpatterns = [
    path("admin/", admin.site.urls),

    # Tabs (these can stay as direct views)
    path("", sviews.feed, name="feed"),
    path("my/", pviews.my_restaurants, name="my_restaurants"),
    path("discover/", pviews.discover, name="discover"),
    path("review/", pviews.review_tab, name="review_tab"),
    path("me/", sviews.profile_me, name="profile_me"),
    path("friends/", sviews.friends, name="friends"),
    path("social/like/<int:pk>/", sviews.toggle_like, name="toggle_like"),

    # Include places URLs UNDER a namespace
    path("", include(("places.urls", "places"), namespace="places")),

    # Auth
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", sviews.signup, name="signup"),
]
