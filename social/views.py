from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from places.models import Review

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
    me = request.user

    # IDs of people I follow / who follow me
    following_ids = list(Follow.objects.filter(follower=me).values_list("followee_id", flat=True))
    follower_ids  = list(Follow.objects.filter(followee=me).values_list("follower_id", flat=True))

    # ---- Restaurants count (choose ONE of these, keep the other commented) ----
    # If Review.user has related_name="reviews":
    review_join = "reviews"
    # If your Review.user has NO related_name (default -> review_set), then use:
    # review_join = "review_set"

    # People I follow, as User queryset with annotations
    following_users = (
        User.objects
        .filter(id__in=following_ids)
        .annotate(
            restaurants_count=Count(f"{review_join}__restaurant", distinct=True),
            following_count=Count("following", distinct=True),  # Follow rows where this user is follower
            followers_count=Count("followers", distinct=True),  # Follow rows where this user is followee
        )
        .order_by("username")
    )

    # People who follow me, as User queryset with annotations
    followers_users = (
        User.objects
        .filter(id__in=follower_ids)
        .annotate(
            restaurants_count=Count(f"{review_join}__restaurant", distinct=True),
            following_count=Count("following", distinct=True),
            followers_count=Count("followers", distinct=True),
        )
        .order_by("username")
    )

    context = {
        "following_users": following_users,
        "followers_users": followers_users,
        "following_count": len(following_ids),
        "followers_count": len(follower_ids),
        # keep this so we can still show an action button where needed
        "following_ids": set(following_ids),
        "active_tab": "friends",
    }
    return render(request, "social/friends.html", context)


@login_required
def profile_public(request, username: str):
    """
    Read-only profile for any user.
    Shows avatar, name, location, bio, counts, and recent reviews.
    """
    person = get_object_or_404(
        User.objects.select_related("profile"),
        username=username,
    )

    # Counts
    # If Review.user uses related_name="reviews" change "review_set" to "reviews"
    review_join = "review_set"  # or "reviews"
    restaurants_count = (
        Review.objects.filter(user=person).values("restaurant").distinct().count()
    )
    following_count = Follow.objects.filter(follower=person).count()
    followers_count = Follow.objects.filter(followee=person).count()

    # Are *you* following them?
    is_following = Follow.objects.filter(
        follower=request.user, followee=person
    ).exists()

    # Recent activity (limit to reviews for now)
    recent_reviews = (
        Review.objects
        .select_related("restaurant", "user")
        .filter(user=person)
        .order_by("-created_at")[:10]
    )

    return render(
        request,
        "social/profile_public.html",
        {
            "person": person,
            "restaurants_count": restaurants_count,
            "following_count": following_count,
            "followers_count": followers_count,
            "is_following": is_following,
            "recent_reviews": recent_reviews,
        },
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

# ---------- Follow (HTMX) ----------

User = get_user_model()

@login_required
@require_http_methods(["POST"])
def toggle_follow(request, user_id: int):
    """
    HTMX endpoint: follow/unfollow a user.
    Returns the follow button partial so the UI updates in place.
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot follow yourself")

    target = get_object_or_404(User, pk=user_id)

    obj, created = Follow.objects.get_or_create(
        follower=request.user, followee=target
    )
    if not created:
        obj.delete()
        is_following = False
    else:
        is_following = True

    return render(
        request,
        "social/_follow_button.html",
        {"target_user": target, "is_following": is_following},
    )


@login_required
def find_friends(request):
    """
    Renders the Find Friends page and performs search when ?q= is present.
    """
    q = (request.GET.get("q") or "").strip()

    users = None
    if q:
        users = (User.objects
                 .exclude(id=request.user.id)
                 .filter(
                     Q(username__icontains=q) |
                     Q(first_name__icontains=q) |
                     Q(last_name__icontains=q) |
                     Q(email__icontains=q)
                 )
                 .order_by("username")[:25])

    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list("followee_id", flat=True)
    )

    return render(
        request,
        "social/friends_find.html",
        {"q": q, "users": users, "following_ids": following_ids}
    )

@login_required
def find_friends_search(request):
    """
    HTMX endpoint returning a list of users matching ?q=...
    """
    q = (request.GET.get("q") or "").strip()

    users = User.objects.exclude(id=request.user.id)
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    users = users.order_by("username")[:25]

    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list("followee_id", flat=True)
    )

    return render(
        request,
        "social/_people_results.html",
        {"users": users, "following_ids": following_ids},
    )

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
