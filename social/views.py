from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from places.models import List, Pin, Review

from .forms import ProfileForm, UserEditForm
from .models import (
    Activity,
    Comment,
    CommentLike,
    Follow,
    Friend,
    Like,
    Notification,
    Profile,
)

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
    
    # Get recent activities for Updates tab (like the main feed)
    from places.models import Review
    from django.db.models import Prefetch, Count
    from .models import Like
    
    # Get filter parameters
    would_go_again = request.GET.get('would_go_again')
    date_filter = request.GET.get('date')
    city_filter = request.GET.get('city')
    
    # Build the base queryset
    activities = (
        Activity.objects
        .select_related("user", "user__profile", "restaurant", "review")
        .filter(user=me, type="review")
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=Comment.objects
                    .select_related("user", "user__profile")
                    .order_by("created_at")
            ),
            "review__photos"
        )
        .annotate(comment_count=Count("comments"))
    )
    
    # Apply filters
    if would_go_again == 'yes':
        activities = activities.filter(review__would_go_again=True)
    elif would_go_again == 'no':
        activities = activities.filter(review__would_go_again=False)
    
    if date_filter == 'week':
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        activities = activities.filter(created_at__gte=week_ago)
    elif date_filter == 'month':
        from datetime import datetime, timedelta
        month_ago = datetime.now() - timedelta(days=30)
        activities = activities.filter(created_at__gte=month_ago)
    elif date_filter == 'year':
        from datetime import datetime, timedelta
        year_ago = datetime.now() - timedelta(days=365)
        activities = activities.filter(created_at__gte=year_ago)
    
    if city_filter:
        activities = activities.filter(restaurant__city__icontains=city_filter)
    
    # Apply ordering and limit
    activities = activities.order_by("-created_at")[:20]
    
    # Add liked_by_me annotation
    liked_ids = set(
        Like.objects.filter(user=me, activity__in=activities)
        .values_list("activity_id", flat=True)
    )
    for a in activities:
        a.liked_by_me = a.id in liked_ids
    
    # Get profile stats
    profile = getattr(me, 'profile', None)
    stats = {
        'avg_rating': profile.avg_rating if profile else None,
        'spots_reviewed': profile.spots_reviewed_count if profile else 0,
        'spots_saved': profile.spots_saved_count if profile else 0,
        'favorite_cuisines': profile.favorite_cuisines if profile else [],
        'favorite_spots': profile.favorite_spots.all() if profile else [],
    }
    
    return render(
        request,
        "social/profile_me.html",
        {
            "me": me, 
            "lists": lists, 
            "active_tab": "profile",
            "activities": activities,
            "stats": stats,
        },
    )


@login_required
def friends(request):
    me = request.user

    # Get accepted friends (both directions)
    accepted_friends = Friend.objects.filter(
        Q(requesting_user=me, status='accepted') | Q(target_user=me, status='accepted')
    ).select_related('requesting_user__profile', 'target_user__profile').order_by('-updated_at')

    # Get pending friend requests sent by me
    pending_requests = Friend.objects.filter(
        requesting_user=me, status='pending'
    ).select_related('target_user__profile').order_by('-updated_at')

    # Get pending friend requests received by me
    received_requests = Friend.objects.filter(
        target_user=me, status='pending'
    ).select_related('requesting_user__profile').order_by('-updated_at')

    # Extract user objects for accepted friends
    friends_list = []
    for friendship in accepted_friends:
        friend_user = friendship.target_user if friendship.requesting_user == me else friendship.requesting_user
        friends_list.append({
            'user': friend_user,
            'friendship': friendship,
            'is_accepted': True
        })

    # Extract user objects for pending requests
    pending_list = []
    for friend_request in pending_requests:
        pending_list.append({
            'user': friend_request.target_user,
            'friendship': friend_request,
            'is_accepted': False
        })

    context = {
        'friends_list': friends_list,
        'pending_requests': pending_list,
        'received_requests': received_requests,
        'friends_count': len(friends_list),
        'pending_count': len(pending_list),
        'received_count': received_requests.count(),
    }

    return render(request, "social/friends.html", context)


@login_required
def profile_public(request, username: str):
    person = get_object_or_404(
        User.objects.select_related("profile"),
        username=username,
    )

    if person.id == request.user.id:
        return redirect("profile_me")

    # Are *you* following this person?
    is_following = Follow.objects.filter(follower=request.user, followee=person).exists()

    # Counts
    restaurants_count = (
        Review.objects.filter(user=person).values("restaurant").distinct().count()
    )
    following_count = Follow.objects.filter(follower=person).count()
    followers_count = Follow.objects.filter(followee=person).count()

    # Recent reviews
    recent_reviews = (
        Review.objects
        .select_related("restaurant", "user")
        .filter(user=person)
        .order_by("-created_at")[:10]
    )

    # ---- Lists (only show all lists if you follow; otherwise only public lists) ----
    base_qs = List.objects.filter(owner=person)
    if not is_following:
        base_qs = base_qs.filter(is_public=True)

    lists = (
        base_qs
        .annotate(places_count=Count("pins", distinct=True))   # number of items in the list
        .prefetch_related(
            # fetch up to N pins with restaurants for a tiny preview row
            Prefetch(
                "pins",
                queryset=Pin.objects
                    .select_related("restaurant")
                    .order_by("-created_at"),
            )
        )
        .order_by("position", "id")[:6]
    )

    return render(
        request,
        "social/profile_public.html",
        {
            "person": person,
            "is_following": is_following,
            "restaurants_count": restaurants_count,
            "following_count": following_count,
            "followers_count": followers_count,
            "recent_reviews": recent_reviews,
            "lists": lists,  # <- NEW
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
        .select_related("user", "user__profile", "restaurant", "review")
        .filter(user_id__in=audience, type="review")
        .prefetch_related(                                                # 👈 add
            Prefetch(
                "comments",
                queryset=Comment.objects
                    .select_related("user", "user__profile")
                    .order_by("created_at")
            ),
            "review__photos"
        )
        .annotate(comment_count=Count("comments"))                         # 👈 add
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
def toggle_comment_like(request, pk):
    """
    HTMX endpoint to like/unlike a comment.
    Returns the replaced comment like button partial.
    """
    comment = get_object_or_404(Comment, pk=pk)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
        liked_by_me = False
    else:
        liked_by_me = True

    # Attach flag expected by the partial
    comment.liked_by_me = liked_by_me

    return render(request, "social/_comment_like_button.html", {"comment": comment})


@require_POST
@login_required
def add_comment(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    text = (request.POST.get("text") or "").strip()
    if text:
        comment = Comment.objects.create(user=request.user, activity=activity, text=text)

        # Create notification for the review author if they're not the commenter
        if activity.user != request.user:
            from .models import Notification
            Notification.objects.create(
                user=activity.user,
                comment=comment,
                activity=activity
            )

    # send the user back to where they were (keeps scroll position with an anchor)
    next_url = request.POST.get("next") or reverse("feed")
    return redirect(next_url)

# ---------- Notifications ----------

@login_required
def notifications(request):
    """Get user's notifications."""
    notifications = request.user.notifications.all()[:10]  # Last 10 notifications
    return render(request, "social/_notifications.html", {"notifications": notifications})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({"status": "success"})

@login_required
def notification_count(request):
    """Get count of unread notifications."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"count": count})

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
@require_http_methods(["POST"])
def delete_friend(request, user_id: int):
    """
    Delete a friendship (for accepted friends).
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot delete yourself")

    target = get_object_or_404(User, pk=user_id)

    # Find the friendship in either direction
    friendship = Friend.objects.filter(
        Q(requesting_user=request.user, target_user=target, status='accepted') |
        Q(requesting_user=target, target_user=request.user, status='accepted')
    ).first()

    if friendship:
        friendship.delete()

    return redirect('friends')


@login_required
@require_http_methods(["POST"])
def cancel_friend_request(request, user_id: int):
    """
    Cancel a pending friend request that the current user sent.
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot cancel request to yourself")

    target = get_object_or_404(User, pk=user_id)

    # Find the pending friend request sent by current user
    friendship = Friend.objects.filter(
        requesting_user=request.user,
        target_user=target,
        status='pending'
    ).first()

    if friendship:
        friendship.delete()

    return redirect('friends')


@login_required
@require_http_methods(["POST"])
def accept_friend_request(request, user_id: int):
    """
    Accept a friend request received by the current user.
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot accept request from yourself")

    requesting_user = get_object_or_404(User, pk=user_id)

    # Find the pending friend request received by current user
    friendship = Friend.objects.filter(
        requesting_user=requesting_user,
        target_user=request.user,
        status='pending'
    ).first()

    if friendship:
        friendship.accept()

    return redirect('friends')


@login_required
@require_http_methods(["POST"])
def reject_friend_request(request, user_id: int):
    """
    Reject a friend request received by the current user.
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot reject request from yourself")

    requesting_user = get_object_or_404(User, pk=user_id)

    # Find the pending friend request received by current user
    friendship = Friend.objects.filter(
        requesting_user=requesting_user,
        target_user=request.user,
        status='pending'
    ).first()

    if friendship:
        friendship.reject()

    return redirect('friends')


@login_required
@require_http_methods(["POST"])
def send_friend_request(request, user_id: int):
    """
    Send a friend request to another user.
    """
    if request.user.id == user_id:
        return HttpResponseBadRequest("Cannot send friend request to yourself")

    target_user = get_object_or_404(User, pk=user_id)

    # Check if any friendship already exists between these users
    existing_friendship = Friend.objects.filter(
        Q(requesting_user=request.user, target_user=target_user) |
        Q(requesting_user=target_user, target_user=request.user)
    ).first()

    if not existing_friendship:
        # Create new friend request
        Friend.objects.create(
            requesting_user=request.user,
            target_user=target_user,
            status='pending'
        )

    # Return to the find friends page
    return redirect('friends_find')


@login_required
def find_friends(request):
    """
    Renders the Find Friends page and performs search when ?q= is present.
    """
    q = (request.GET.get("q") or "").strip()

    users_with_relationships = []
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

        # Get friend relationships for the current user
        if users:
            user_ids = [u.id for u in users]

            # Get all friend relationships involving current user and search results
            friend_relationships = {}
            friends = Friend.objects.filter(
                Q(requesting_user=request.user, target_user__in=user_ids) |
                 Q(requesting_user__in=user_ids, target_user=request.user)
            )

            for friend in friends:
                if friend.requesting_user == request.user:
                    # Current user sent the request
                    friend_relationships[friend.target_user.id] = {
                        'status': friend.status,
                        'is_requester': True
                    }
                else:
                    # Other user sent the request
                    friend_relationships[friend.requesting_user.id] = {
                        'status': friend.status,
                        'is_requester': False
                    }

            # Combine users with their relationship data
            for user in users:
                users_with_relationships.append({
                    'user': user,
                    'relationship': friend_relationships.get(user.id)
                })

    return render(
        request,
        "social/friends_find.html",
        {"q": q, "users_with_relationships": users_with_relationships}
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
