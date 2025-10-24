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
    
    # Handle multiple pins for the same user-restaurant combination
    existing_pins = Pin.objects.filter(user=user, restaurant=r)
    if existing_pins.exists():
        # Update the first pin to be in the visited list
        pin = existing_pins.first()
        pin.list = visited
        pin.save(update_fields=["list"])
    else:
        # Create a new pin
        Pin.objects.create(user=user, restaurant=r, list=visited)

    # Create or update the review activity
    from social.models import Activity  # local import to avoid circular deps
    Activity.objects.update_or_create(
        type="review", user=user, restaurant=r, review=instance,
        defaults={}
    )
