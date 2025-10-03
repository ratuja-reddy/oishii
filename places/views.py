from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Pin, Restaurant


def home(request):
    restaurants = list(Restaurant.objects.order_by("-id")[:24])
    pinned_ids = set()
    if request.user.is_authenticated:
        pinned_ids = set(
            Pin.objects.filter(user=request.user, restaurant__in=restaurants)
            .values_list("restaurant_id", flat=True)
        )
    for r in restaurants:
        r.is_pinned = r.id in pinned_ids
    return render(request, "places/home.html", {"restaurants": restaurants})

def restaurant_detail(request, pk):
    r = get_object_or_404(Restaurant, pk=pk)
    is_pinned = request.user.is_authenticated and \
        Pin.objects.filter(user=request.user, restaurant=r).exists()
    return render(request, "places/restaurant_detail.html", {"r": r, "pinned": is_pinned})

@login_required
def toggle_pin(request, pk):
    r = get_object_or_404(Restaurant, pk=pk)
    pin, created = Pin.objects.get_or_create(user=request.user, restaurant=r)
    if not created:
        pin.delete()
        is_pinned = False
    else:
        is_pinned = True
    return render(request, "places/_pin_button.html", {"r": r, "pinned": is_pinned})
