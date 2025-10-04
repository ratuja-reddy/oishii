# social/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from places.models import List

from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        # Default lists
        for title in ["Visited", "Saved"]:
            List.objects.get_or_create(owner=instance, title=title, defaults={"is_public": False})
