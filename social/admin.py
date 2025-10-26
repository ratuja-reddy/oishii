from django.contrib import admin

from .models import Follow, Friend, Notification


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "created_at")
    search_fields = ("follower__username", "followee__username")
# Register your models here.

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("requesting_user", "target_user", "created_at", "updated_at", "status")
    search_fields = ("user1__username", "user2__username")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "created_at", "is_read", "get_content_preview")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("user__username", "comment__user__username", "like__user__username", "comment_like__user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_content_preview(self, obj):
        """Show a preview of the notification content"""
        if obj.notification_type == 'comment':
            return f"Comment by {obj.comment.user.username if obj.comment else 'N/A'}"
        elif obj.notification_type == 'review_like':
            return f"Review like by {obj.like.user.username if obj.like else 'N/A'}"
        elif obj.notification_type == 'comment_like':
            return f"Comment like by {obj.comment_like.user.username if obj.comment_like else 'N/A'}"
        return "Unknown"

    get_content_preview.short_description = "Content Preview"
