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

    # Ensure the restaurant is in the user's 'Visited' list
    # First, check if there's already a pin in the visited list
    existing_visited_pin = Pin.objects.filter(user=user, restaurant=r, list=visited).first()

    if not existing_visited_pin:
        # Check if there are any other pins for this user-restaurant combination
        other_pins = Pin.objects.filter(user=user, restaurant=r).exclude(list=visited)

        if other_pins.exists():
            # Move the first existing pin to the visited list
            pin = other_pins.first()
            pin.list = visited
            pin.save(update_fields=["list"])
        else:
            # Create a new pin in the visited list
            Pin.objects.create(user=user, restaurant=r, list=visited)

    # Create or update the review activity
    from social.models import Activity  # local import to avoid circular deps
    Activity.objects.update_or_create(
        type="review", user=user, restaurant=r, review=instance,
        defaults={}
    )
