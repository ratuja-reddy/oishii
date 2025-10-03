from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from places.models import Pin

from .models import Follow


@login_required
def feed(request):
    followees = Follow.objects.filter(follower=request.user).values_list("followee_id", flat=True)
    pins = (Pin.objects.select_related("restaurant","user")
            .filter(user_id__in=followees)
            .order_by("-created_at")[:50])
    return render(request, "social/feed.html", {"pins": pins, "active_tab": "home"})

@login_required
def profile_me(request):
    # show my public-ish profile and lists
    U = get_user_model()
    me = get_object_or_404(U, pk=request.user.id)
    lists = me.list_set.all().order_by("title") if hasattr(me, "list_set") else []
    return render(request, "social/profile_me.html", {"me": me, "lists": lists, "active_tab": "profile"})

@login_required
def friends(request):
    following = Follow.objects.filter(follower=request.user).select_related("followee")
    followers = Follow.objects.filter(followee=request.user).select_related("follower")
    return render(request, "social/friends.html", {
        "following": following, "followers": followers, "active_tab": "friends"
    })

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)   # log them in immediately
            return redirect("feed")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
