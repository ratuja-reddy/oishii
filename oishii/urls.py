from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from places import views as pviews
from social import views as sviews

urlpatterns = [
    path("admin/", admin.site.urls),

    # Tabs (these can stay as direct views)
    # places views
    path("", sviews.feed, name="feed"),
    path("my/", pviews.my_restaurants, name="my_restaurants"),
    path("discover/", pviews.discover, name="discover"),
    path("review/", pviews.review_tab, name="review_tab"),
    # social views
    path("me/", sviews.profile_me, name="profile_me"),
    path("friends/", sviews.friends, name="friends"),
    path("social/like/<int:pk>/", sviews.toggle_like, name="toggle_like"),
    path("me/", sviews.profile_me, name="profile_me"),
    path("me/edit/", sviews.edit_profile, name="edit_profile"),
    # Include places URLs UNDER a namespace
    path("", include(("places.urls", "places"), namespace="places")),

    # Auth
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", sviews.signup, name="signup"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
