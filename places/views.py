from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import os

from .forms import ReviewForm
from .models import List, Photo, Pin, Restaurant, Review


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

    # Get reviews from current user and their friends (people they follow)
    if request.user.is_authenticated:
        # Get users that the current user follows
        following_ids = list(
            request.user.following.values_list('followee_id', flat=True)
        )
        # Include current user in the list
        following_ids.append(request.user.id)

        # Get reviews from current user and friends
        reviews = Review.objects.filter(
            restaurant=r,
            user_id__in=following_ids
        ).select_related("user", "user__profile").prefetch_related(
            "activities__comments__user__profile", "photos"
        ).order_by("-created_at")
    else:
        # If not authenticated, show no reviews
        reviews = Review.objects.none()

    return render(
        request,
        "places/restaurant_detail.html",
        {"r": r, "reviews": reviews},
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
    all_lists = list(
        List.objects.filter(owner=request.user)
        .prefetch_related("pins__restaurant")
        .order_by("title")
    )

    def norm(s: str) -> str:
        return (s or "").strip().lower()

    visited = next((lst for lst in all_lists if norm(lst.title) == "visited"), None)
    # Treat either “Saved” or your earlier “Want to go” as the default saved list
    saved = next((lst for lst in all_lists if norm(lst.title) in {"saved", "want to go"}), None)

    custom_lists = [lst for lst in all_lists if lst not in {visited, saved}]

    return render(
        request,
        "places/my_restaurants.html",
        {
            "visited": visited,
            "saved": saved,
            "custom_lists": custom_lists,
            "active_tab": "my",
        },
    )


def discover(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Search in name, cuisine, city, and address
        restaurants = Restaurant.objects.filter(
            models.Q(name__icontains=search_query) |
            models.Q(cuisine__icontains=search_query) |
            models.Q(city__icontains=search_query) |
            models.Q(address__icontains=search_query)
        ).order_by("-id")[:24]
    else:
        restaurants = Restaurant.objects.order_by("-id")[:24]
    
    return render(
        request,
        "places/discover.html",
        {
            "restaurants": restaurants, 
            "active_tab": "discover",
            "search_query": search_query,
            "API_KEY": os.getenv("GOOGLE_MAPS_API_KEY")
        },
    )


# -------------------
# REVIEWS
# -------------------

@login_required
def review_tab(request):
    """Center tab: create a review and see recent reviews by the user."""
    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES, user=request.user)
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

            # Handle photo uploads
            photos = request.FILES.getlist('photos')
            for photo in photos:
                Photo.objects.create(review=review, image=photo)

            messages.success(request, "Review saved!")
            return redirect("places:review_thanks")
    else:
        form = ReviewForm(user=request.user)

    my_reviews = (
        Review.objects.filter(user=request.user)
        .select_related("restaurant")
        .prefetch_related("photos")
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
        form = ReviewForm(request.POST, request.FILES, instance=instance, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.restaurant = restaurant
            review.save()

            # Handle photo uploads
            photos = request.FILES.getlist('photos')
            for photo in photos:
                Photo.objects.create(review=review, image=photo)

            messages.success(request, "Review saved!")
            return redirect("places:review_thanks")
    else:
        form = ReviewForm(instance=instance, user=request.user)
        form.fields["restaurant"].initial = restaurant
        form.fields["restaurant"].widget.attrs["disabled"] = True

    return render(
        request,
        "places/review_form.html",
        {"form": form, "restaurant": restaurant, "active_tab": "review"},
    )


@login_required
def review_edit(request, pk):
    """Edit an existing review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES, instance=review, user=request.user)
        if form.is_valid():
            form.save()

            # Handle new photo uploads
            photos = request.FILES.getlist('photos')
            for photo in photos:
                Photo.objects.create(review=review, image=photo)

            messages.success(request, "Review updated!")
            return redirect("feed")
    else:
        form = ReviewForm(instance=review, user=request.user)
        # Lock the restaurant field since we're editing an existing review
        form.fields["restaurant"].widget.attrs["disabled"] = True

    return render(
        request,
        "places/review_edit.html",
        {"form": form, "review": review, "restaurant": review.restaurant, "active_tab": "review"},
    )


@login_required
def photo_delete(request, pk):
    """Delete a photo from a review."""
    photo = get_object_or_404(Photo, pk=pk, review__user=request.user)

    if request.method == "POST":
        photo.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})

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
    """
    GET -> render small modal with form
    POST -> create list for current user and HTMX-redirect to list detail
    """
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        is_public = (request.POST.get("is_public") == "on")

        errors = {}
        if not title:
            errors["title"] = "Please enter a name."

        # enforce uniqueness per user from your model Meta(unique_together)
        if not errors and List.objects.filter(owner=request.user, title=title).exists():
            errors["title"] = "You already have a list with this name."

        if errors:
            return render(request, "places/_list_create_modal.html", {
                "errors": errors,
                "title_value": title,
                "is_public_value": is_public,
            })

        lst = List.objects.create(owner=request.user, title=title, is_public=is_public)

        # HTMX redirect so the page changes without reloading everything
        resp = HttpResponse("")
        resp["HX-Redirect"] = reverse("list_detail", args=[lst.id])
        return resp

    # GET -> show modal
    return render(request, "places/_list_create_modal.html")
@login_required
def list_detail(request, list_id):
    lst = get_object_or_404(List, pk=list_id, owner=request.user)
    items = (Pin.objects.select_related("restaurant")
             .filter(list=lst).order_by("-created_at"))
    return render(request, "places/list_detail.html", {"lst": lst, "items": items})

@login_required
def delete_pin(request, list_id, pin_id):
    lst = get_object_or_404(List, pk=list_id, owner=request.user)
    pin = get_object_or_404(Pin, pk=pin_id, list=lst)
    pin.delete()

    # If this was an HTMX request, return a tiny fragment that updates the count.
    if request.headers.get("HX-Request"):
        return render(request, "places/_list_count.html", {"lst": lst})

    # Normal navigation fallback
    return redirect("list_detail", list_id=lst.id)

@login_required
def edit_list(request, list_id):
    """
    GET -> render small modal with edit form
    POST -> update list for current user and HTMX-redirect to list detail
    """
    lst = get_object_or_404(List, pk=list_id, owner=request.user)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        is_public = (request.POST.get("is_public") == "on")

        errors = {}
        if not title:
            errors["title"] = "Please enter a name."

        # enforce uniqueness per user from your model Meta(unique_together)
        # but allow keeping the same title for the current list
        if not errors and List.objects.filter(owner=request.user, title=title).exclude(pk=lst.pk).exists():
            errors["title"] = "You already have a list with this name."

        if errors:
            return render(request, "places/_list_edit_modal.html", {
                "errors": errors,
                "title_value": title,
                "is_public_value": is_public,
                "lst": lst,
            })

        lst.title = title
        lst.is_public = is_public
        lst.save()

        # HTMX redirect so the page changes without reloading everything
        resp = HttpResponse("")
        resp["HX-Redirect"] = reverse("list_detail", args=[lst.id])
        return resp

    # GET -> show modal
    return render(request, "places/_list_edit_modal.html", {"lst": lst})

@login_required
def delete_list(request, list_id):
    """Delete a custom list (not the default 'visited' or 'saved' lists)."""
    lst = get_object_or_404(List, pk=list_id, owner=request.user)

    # Don't allow deletion of default lists
    if lst.title.lower() in ['visited', 'saved', 'want to go']:
        return HttpResponseBadRequest("Cannot delete default lists")

    lst.delete()

    # If this was an HTMX request, return empty response to remove the list from UI
    if request.headers.get("HX-Request"):
        return HttpResponse("")

    # Normal navigation fallback
    return redirect("my_restaurants")


@login_required
def review_thanks(request):
    """Thank you page after posting a review with auto-redirect to home feed."""
    return render(
        request,
        "places/review_thanks.html",
        {"active_tab": "home"},
    )
