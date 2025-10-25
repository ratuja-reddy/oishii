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
    path("r/<int:pk>/lists/", pviews.list_picker, name="list_picker"),
    path("r/<int:pk>/lists/<int:list_id>/toggle/", pviews.toggle_in_list, name="toggle_in_list"),
    path("lists/create/", pviews.create_list, name="create_list"),
    path("lists/<int:list_id>/", pviews.list_detail, name="list_detail"),
    path("lists/<int:list_id>/edit/", pviews.edit_list, name="edit_list"),
    path("lists/<int:list_id>/delete/", pviews.delete_list, name="delete_list"),
    path("lists/<int:list_id>/pin/<int:pin_id>/delete/", pviews.delete_pin, name="delete_pin"),
    # social views
    path("me/", sviews.profile_me, name="profile_me"),
    path("friends/", sviews.friends, name="friends"),
    path("friends/find/", sviews.find_friends, name="friends_find"),                 # page
    path("friends/find/search/", sviews.find_friends_search, name="friends_find_search"),  # HTMX results
    path("friends/delete/<int:user_id>/", sviews.delete_friend, name="delete_friend"),     # Delete friend
    path("friends/cancel/<int:user_id>/", sviews.cancel_friend_request, name="cancel_friend_request"),  # Cancel request
    path("friends/accept/<int:user_id>/", sviews.accept_friend_request, name="accept_friend_request"),  # Accept request
    path("friends/reject/<int:user_id>/", sviews.reject_friend_request, name="reject_friend_request"),  # Reject request
    path("friends/send/<int:user_id>/", sviews.send_friend_request, name="send_friend_request"),        # Send friend request
    path("social/follow/<int:user_id>/", sviews.toggle_follow, name="toggle_follow"),      # HTMX toggle
    path("social/like/<int:pk>/", sviews.toggle_like, name="toggle_like"),
    path("social/comment-like/<int:pk>/", sviews.toggle_comment_like, name="toggle_comment_like"),
    path("activity/<int:activity_id>/comment/", sviews.add_comment, name="add_comment"),
    # notifications
    path("notifications/", sviews.notifications, name="notifications"),
    path("notifications/count/", sviews.notification_count, name="notification_count"),
    path("notifications/<int:notification_id>/read/", sviews.mark_notification_read, name="mark_notification_read"),
    path("me/", sviews.profile_me, name="profile_me"),
    path("me/edit/", sviews.edit_profile, name="edit_profile"),
    path("u/<str:username>/", sviews.profile_public, name="profile_public"),
    # Include places URLs UNDER a namespace
    path("", include(("places.urls", "places"), namespace="places")),


    # Auth
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", sviews.signup, name="signup"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
