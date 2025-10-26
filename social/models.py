from django.conf import settings
from django.db import models
from django.utils import timezone


class Friend(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    requesting_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_sent"
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("requesting_user", "target_user")

    def __str__(self):
        return f"{self.requesting_user} → {self.target_user} ({self.status})"

    def accept(self):
        """Accept the friend request."""
        self.status = "accepted"
        self.save()

    def reject(self):
        """Reject the friend request."""
        self.status = "rejected"
        self.save()

    def is_accepted(self):
        """Check if the friend request is accepted."""
        return self.status == "accepted"

    def is_pending(self):
        """Check if the friend request is pending."""
        return self.status == "pending"

    def is_rejected(self):
        """Check if the friend request is rejected."""
        return self.status == "rejected"


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


class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "comment")

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class Notification(models.Model):
    """Notifications for users when someone comments on their reviews or likes their content."""
    NOTIFICATION_TYPES = [
        ('comment', 'Comment'),
        ('review_like', 'Review Like'),
        ('comment_like', 'Comment Like'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='comment')
    
    # For comment notifications
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    
    # For like notifications
    like = models.ForeignKey(Like, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    comment_like = models.ForeignKey(CommentLike, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    
    # Always have activity for context
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="notifications")
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        if self.notification_type == 'comment':
            return f"Notification for {self.user.username} - {self.comment.user.username} commented"
        elif self.notification_type == 'review_like':
            return f"Notification for {self.user.username} - {self.like.user.username} liked review"
        elif self.notification_type == 'comment_like':
            return f"Notification for {self.user.username} - {self.comment_like.user.username} liked comment"
        return f"Notification for {self.user.username}"

    @property
    def message(self):
        """Generate the notification message."""
        if self.notification_type == 'comment':
            commenter_name = self.comment.user.profile.display_name if self.comment.user.profile.display_name else self.comment.user.username
            return f"{commenter_name} commented on your review!"
        elif self.notification_type == 'review_like':
            liker_name = self.like.user.profile.display_name if self.like.user.profile.display_name else self.like.user.username
            return f"{liker_name} liked your review!"
        elif self.notification_type == 'comment_like':
            liker_name = self.comment_like.user.profile.display_name if self.comment_like.user.profile.display_name else self.comment_like.user.username
            return f"{liker_name} liked your comment!"
        return "You have a new notification"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=80, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # New Goodreads-style fields
    favorite_cuisines = models.JSONField(default=list, blank=True, help_text="List of favorite cuisine types")
    favorite_spots = models.ManyToManyField("places.Restaurant", blank=True, related_name="favorite_of", limit_choices_to={'id__in': []})

    def __str__(self):
        return f"Profile({self.user.username})"

    @property
    def avg_rating(self):
        """Calculate average rating from user's reviews"""
        from places.models import Review
        reviews = Review.objects.filter(user=self.user, overall_rating__isnull=False)
        if not reviews.exists():
            return None
        return round(reviews.aggregate(avg=models.Avg('overall_rating'))['avg'], 1)

    @property
    def spots_reviewed_count(self):
        """Count of spots reviewed by user"""
        from places.models import Review
        return Review.objects.filter(user=self.user).count()

    @property
    def spots_saved_count(self):
        """Count of unique spots saved in lists (excluding 'Visited' list)"""
        from places.models import Pin
        # Get all unique restaurants that this user has pinned to any list EXCEPT 'Visited'
        return Pin.objects.filter(user=self.user).exclude(list__title='Visited').values('restaurant').distinct().count()
