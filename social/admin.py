from django.contrib import admin

from .models import Follow, Friend


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "created_at")
    search_fields = ("follower__username", "followee__username")
# Register your models here.

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("requesting_user", "target_user", "created_at", "updated_at", "status")
    search_fields = ("user1__username", "user2__username")