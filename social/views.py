from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, UserEditForm
from .models import Activity, Follow, Like, Profile

# ---------- Auth / Profile ----------

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("feed")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile_me(request):
    """Basic profile page; shows lists via reverse relation if present."""
    U = get_user_model()
    me = get_object_or_404(U, pk=request.user.id)
    # If you registered List in places, Django will create me.list_set
    lists = getattr(me, "list_set", None).all().order_by("title") if hasattr(me, "list_set") else []
    return render(
        request,
        "social/profile_me.html",
        {"me": me, "lists": lists, "active_tab": "profile"},
    )


@login_required
def friends(request):
    following = Follow.objects.filter(follower=request.user).select_related("followee")
    followers = Follow.objects.filter(followee=request.user).select_related("follower")
    return render(
        request,
        "social/friends.html",
        {"following": following, "followers": followers, "active_tab": "friends"},
    )


# ---------- Feed ----------

@login_required
def feed(request):
    """
    Show review activities from me + people I follow.
    Also annotate each activity with `liked_by_me` for the like button partial.
    """
    following_ids = list(
        Follow.objects.filter(follower=request.user).values_list("followee_id", flat=True)
    )
    audience = [request.user.id] + following_ids

    activities = (
        Activity.objects
        .select_related("user", "user__profile", "restaurant", "review")  # 👈 pull profile too
        .filter(user_id__in=audience, type="review")
        .order_by("-created_at")[:50]
    )

    liked_ids = set(
        Like.objects.filter(user=request.user, activity__in=activities)
        .values_list("activity_id", flat=True)
    )
    for a in activities:
        a.liked_by_me = a.id in liked_ids

    return render(
        request,
        "social/feed.html",
        {"activities": activities, "active_tab": "home"},
    )


# ---------- Likes (HTMX) ----------

@login_required
def toggle_like(request, pk):
    """
    HTMX endpoint to like/unlike an activity.
    Returns the replaced like button partial.
    """
    activity = get_object_or_404(Activity, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, activity=activity)
    if not created:
        like.delete()
        liked_by_me = False
    else:
        liked_by_me = True

    # Attach flag expected by the partial
    activity.liked_by_me = liked_by_me

    return render(request, "social/_like_button.html", {"a": activity})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        uform = UserEditForm(request.POST, instance=request.user)
        pform = ProfileForm(request.POST, request.FILES, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Profile updated!")
            return redirect("profile_me")
    else:
        uform = UserEditForm(instance=request.user)
        pform = ProfileForm(instance=profile)

    return render(request, "social/edit_profile.html",
                  {"uform": uform, "pform": pform, "active_tab": "profile"})
