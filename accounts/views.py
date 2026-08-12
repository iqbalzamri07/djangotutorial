from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.shortcuts import redirect, render

from todos.services import completion_streak, mark_overdue_todos_completed, user_todos

from .forms import ProfileForm, SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get("next") or request.POST.get("next") or "home"
            return redirect(next_url)
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": request.GET.get("next", ""),
        },
    )


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile(request):
    mark_overdue_todos_completed(request.user)
    todos = user_todos(request.user)
    profile_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    profile_saved = False
    password_saved = False

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                profile_saved = True
        elif action == "password":
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                password_form = PasswordChangeForm(request.user)
                password_saved = True

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "profile_saved": profile_saved,
            "password_saved": password_saved,
            "total_tasks": todos.count(),
            "pending_tasks": todos.filter(completed=False).count(),
            "completed_tasks": todos.filter(completed=True).count(),
            "recent_todos": todos.order_by("-created_at")[:5],
            "streak": completion_streak(request.user),
        },
    )
