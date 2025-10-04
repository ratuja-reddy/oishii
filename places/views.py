from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm
from .models import List, Pin, Restaurant, Review


def home(request):
    # optional: show some recent restaurants
    restaurants = list(Restaurant.objects.order_by("-id")[:24])
    pinned_ids = set()
    if request.user.is_authenticated:
        pinned_ids = set(
            Pin.objects.filter(user=request.user, restaurant__in=restaurants)
            .values_list("restaurant_id", flat=True)
        )
    for r in restaurants:
        r.is_pinned = r.id in pinned_ids
    return render(
        request,
        "places/home.html",
        {"restaurants": restaurants, "active_tab": "home"},
    )


def restaurant_detail(request, pk):
    r = get_object_or_404(Restaurant, pk=pk)
    is_pinned = request.user.is_authenticated and Pin.objects.filter(
        user=request.user, restaurant=r
    ).exists()
    reviews = Review.objects.filter(restaurant=r).select_related("user")[:20]
    return render(
        request,
        "places/restaurant_detail.html",
        {"r": r, "pinned": is_pinned, "reviews": reviews},
    )


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


@login_required
def my_restaurants(request):
    lists = (
        List.objects.filter(owner=request.user)
        .order_by("title")
        .prefetch_related("pins__restaurant")
    )
    pins = (
        Pin.objects.select_related("restaurant")
        .filter(user=request.user)
        .order_by("-created_at")[:100]
    )
    return render(
        request,
        "places/my_restaurants.html",
        {"lists": lists, "pins": pins, "active_tab": "my"},
    )


def discover(request):
    restaurants = Restaurant.objects.order_by("-id")[:24]
    return render(
        request,
        "places/discover.html",
        {"restaurants": restaurants, "active_tab": "discover"},
    )


# -------------------
# REVIEWS
# -------------------

@login_required
def review_tab(request):
    """Center tab: create a review and see recent reviews by the user."""
    if request.method == "POST":
        form = ReviewForm(request.POST, user=request.user)
        if form.is_valid():
            # One review per user per restaurant
            review, _created = Review.objects.update_or_create(
                user=request.user,
                restaurant=form.cleaned_data["restaurant"],
                defaults={
                    "overall_rating": form.cleaned_data["overall_rating"],
                    "food": form.cleaned_data.get("food"),
                    "service": form.cleaned_data.get("service"),
                    "value": form.cleaned_data.get("value"),
                    "atmosphere": form.cleaned_data.get("atmosphere"),
                    "text": form.cleaned_data.get("text", ""),
                },
            )
            messages.success(request, "Review saved!")
            return redirect("review_tab")
    else:
        form = ReviewForm(user=request.user)

    my_reviews = (
        Review.objects.filter(user=request.user)
        .select_related("restaurant")
        .order_by("-created_at")[:10]
    )
    return render(
        request,
        "places/review_tab.html",
        {"form": form, "my_reviews": my_reviews, "active_tab": "review"},
    )


@login_required
def review_create_for_restaurant(request, pk):
    """Review form locked to a specific restaurant."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    instance = Review.objects.filter(user=request.user, restaurant=restaurant).first()

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=instance, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.restaurant = restaurant
            review.save()
            messages.success(request, "Review saved!")
            return redirect("places:restaurant_detail", pk=restaurant.pk)
    else:
        form = ReviewForm(instance=instance, user=request.user)
        form.fields["restaurant"].initial = restaurant
        form.fields["restaurant"].widget.attrs["disabled"] = True

    return render(
        request,
        "places/review_form.html",
        {"form": form, "restaurant": restaurant, "active_tab": "review"},
    )

# -------------------
# LISTS
# -------------------

@login_required
def list_picker(request, pk):
    """Return a small modal with the user's lists and add/remove toggles for this restaurant."""
    r = get_object_or_404(Restaurant, pk=pk)
    lists = List.objects.filter(owner=request.user).order_by("title").prefetch_related("pins")
    # which lists already contain this restaurant
    present = set(Pin.objects.filter(list__in=lists, restaurant=r).values_list("list_id", flat=True))
    return render(request, "places/_list_picker.html", {"r": r, "lists": lists, "present": present})

@login_required
def toggle_in_list(request, pk, list_id):
    """Add/remove restaurant pk to/from list_id; returns updated row to swap in the modal."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    r = get_object_or_404(Restaurant, pk=pk)
    lst = get_object_or_404(List, pk=list_id, owner=request.user)
    pin, created = Pin.objects.get_or_create(user=request.user, list=lst, restaurant=r)
    if not created:
        pin.delete()
        is_in = False
    else:
        is_in = True
    # return a small line item snippet for that list
    return render(request, "places/_list_picker_row.html", {"lst": lst, "r": r, "is_in": is_in})

@login_required
def create_list(request):
    """Create a new list from the modal and re-render the whole list picker."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    title = (request.POST.get("title") or "").strip()
    if not title:
        return HttpResponseBadRequest("Title required")
    lst, _ = List.objects.get_or_create(owner=request.user, title=title, defaults={"is_public": False})
    # re-render modal for the same restaurant (passed as hidden field)
    pk = request.POST.get("restaurant_id")
    r = get_object_or_404(Restaurant, pk=pk)
    lists = List.objects.filter(owner=request.user).order_by("title")
    present = set(Pin.objects.filter(list__in=lists, restaurant=r).values_list("list_id", flat=True))
    return render(request, "places/_list_picker.html", {"r": r, "lists": lists, "present": present})

@login_required
def list_detail(request, list_id):
    lst = get_object_or_404(List, pk=list_id, owner=request.user)
    items = (Pin.objects.select_related("restaurant")
             .filter(list=lst).order_by("-created_at"))
    return render(request, "places/list_detail.html", {"lst": lst, "items": items})
