# social/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from places.models import List

from .models import CommentLike, Like, Notification, Profile

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        # Default lists
        for title in ["Visited", "Saved"]:
            List.objects.get_or_create(owner=instance, title=title, defaults={"is_public": False})


@receiver(post_save, sender=Like)
def create_review_like_notification(sender, instance, created, **kwargs):
    """Create notification when someone likes a review."""
    if created:
        # Don't notify if user likes their own review
        if instance.user != instance.activity.user:
            Notification.objects.create(
                user=instance.activity.user,
                notification_type='review_like',
                like=instance,
                activity=instance.activity
            )
        else:
            # Debug: Log self-like to help troubleshoot
            print(f"DEBUG: Self-like prevented - User {instance.user.username} liked their own review")


@receiver(post_save, sender=CommentLike)
def create_comment_like_notification(sender, instance, created, **kwargs):
    """Create notification when someone likes a comment."""
    if created:
        # Don't notify if user likes their own comment
        if instance.user != instance.comment.user:
            Notification.objects.create(
                user=instance.comment.user,
                notification_type='comment_like',
                comment_like=instance,
                activity=instance.comment.activity
            )
        else:
            # Debug: Log self-like to help troubleshoot
            print(f"DEBUG: Self-like prevented - User {instance.user.username} liked their own comment")
