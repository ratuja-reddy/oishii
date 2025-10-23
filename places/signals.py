from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import List, Pin, Review


@receiver(post_save, sender=Review)
def on_review_saved(sender, instance: Review, created, **kwargs):
    """
    - Ensure the restaurant is in the user's 'Visited' list (create both if needed).
    - Create/refresh an Activity('review') for the feed.
    """
    user = instance.user
    r = instance.restaurant

    # Ensure 'Visited' list exists
    visited, _ = List.objects.get_or_create(owner=user, title="Visited", defaults={"is_public": False})

    # Check if there's already a Pin for this user+restaurant+visited_list combination
    # If not, create one
    if not Pin.objects.filter(user=user, restaurant=r, list=visited).exists():
        Pin.objects.create(user=user, restaurant=r, list=visited)

    # Create or update the review activity
    from social.models import Activity  # local import to avoid circular deps
    Activity.objects.update_or_create(
        type="review", user=user, restaurant=r, review=instance,
        defaults={}
    )
