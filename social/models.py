from django.conf import settings
from django.db import models
from django.utils import timezone


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following"
    )
    followee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "followee")

    def __str__(self):
        return f"{self.follower} → {self.followee}"


class Activity(models.Model):
    """One row per thing that should show up in the feed."""
    TYPE_CHOICES = [
        ("review", "Review"),
        # later: ("pin", "Pin"), ("list", "ListCreated") ...
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    restaurant = models.ForeignKey("places.Restaurant", on_delete=models.CASCADE, related_name="activities")
    # Only for review events:
    review = models.ForeignKey("places.Review", null=True, blank=True, on_delete=models.CASCADE, related_name="activities")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "activity")

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
