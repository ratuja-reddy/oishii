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

    # Ensure 'Visited' list exists and contains a Pin for this restaurant
    visited, _ = List.objects.get_or_create(owner=user, title="Visited", defaults={"is_public": False})
    Pin.objects.get_or_create(user=user, restaurant=r, defaults={"list": visited})
    # If a Pin already exists with no list, attach it (optional)
    try:
        p = Pin.objects.get(user=user, restaurant=r)
        if p.list is None:
            p.list = visited
            p.save(update_fields=["list"])
    except Pin.DoesNotExist:
        pass

    # Create or update the review activity
    from social.models import Activity  # local import to avoid circular deps
    Activity.objects.update_or_create(
        type="review", user=user, restaurant=r, review=instance,
        defaults={}
    )
