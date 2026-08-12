import calendar as py_calendar
from datetime import date, datetime, timedelta

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import SignUpForm, TodoForm
from .models import Todo


def mark_overdue_todos_completed(user=None):
    """
    Auto-complete todos whose end_date is in the past.
    """
    today = date.today()
    todos = Todo.objects.filter(
        completed=False,
        end_date__isnull=False,
        end_date__lt=today,
    )
    if user is not None:
        todos = todos.filter(user=user)
    todos.update(completed=True)


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
def home(request):
    mark_overdue_todos_completed(request.user)
    todos = Todo.objects.filter(user=request.user)
    completed_tasks = todos.filter(completed=True).count()
    pending_tasks = todos.filter(completed=False).count()

    if request.method == "POST":
        form = TodoForm(request.POST)

        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            return redirect("home")
    else:
        form = TodoForm()

    return render(
        request,
        "todos/home.html",
        {
            "todos": todos,
            "form": form,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
        },
    )


@login_required
def edit_todos(request):
    mark_overdue_todos_completed(request.user)
    todos = Todo.objects.filter(user=request.user)

    if request.method == "POST":
        for todo in todos:
            todo.completed = f"completed_{todo.id}" in request.POST
            todo.save()

        return redirect("home")

    return render(request, "todos/edit-todos.html", {
        "todos": todos,
    })


@login_required
def delete(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        todo.delete()
        return redirect("home")

    return render(request, "todos/delete.html", {
        "todo": todo,
    })


@login_required
def edit(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        form = TodoForm(request.POST, instance=todo)

        if form.is_valid():
            form.save()
            return redirect("edit_todos")

    else:
        form = TodoForm(instance=todo)

    return render(request, "todos/edit.html", {
        "form": form,
        "todo": todo,
    })


def about(request):
    from blog.models import Post

    if request.user.is_authenticated:
        todos = Todo.objects.filter(user=request.user)
    else:
        todos = Todo.objects.none()

    return render(
        request,
        "todos/about.html",
        {
            "total_tasks": todos.count(),
            "completed_tasks": todos.filter(completed=True).count(),
            "pending_tasks": todos.filter(completed=False).count(),
            "post_count": Post.objects.filter(published=True).count(),
        },
    )


@login_required
def calendar(request):
    """
    Monthly grid for todos scheduled on a given month.
    """
    mark_overdue_todos_completed(request.user)
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        year = today.year

    try:
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        month = today.month

    month = max(1, min(12, month))

    month_start_date = date(year, month, 1)
    next_month_date = (
        date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    )
    month_end_date = next_month_date - timedelta(days=1)

    todos_in_month = Todo.objects.filter(
        user=request.user,
        start_date__isnull=False,
        end_date__isnull=False,
        start_date__lte=month_end_date,
        end_date__gte=month_start_date,
    ).order_by("start_date", "end_date", "title")

    todos_by_date = {}
    for todo in todos_in_month:
        span_start = max(todo.start_date, month_start_date - timedelta(days=7))
        span_end = min(todo.end_date, month_end_date + timedelta(days=7))
        current = span_start
        while current <= span_end:
            todos_by_date.setdefault(current, []).append(todo)
            current += timedelta(days=1)

    cal = py_calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for day_date in week:
            week_cells.append(
                {
                    "date": day_date,
                    "in_month": day_date.month == month,
                    "is_today": day_date == today,
                    "todos": todos_by_date.get(day_date, []),
                }
            )
        weeks.append(week_cells)

    prev_year = year - 1 if month == 1 else year
    prev_month = 12 if month == 1 else month - 1
    next_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1

    month_title = datetime(year, month, 1).strftime("%B %Y")

    show_modal = False
    title_value = ""
    start_date_value = ""
    end_date_value = ""
    form = None
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            calendar_url = reverse("calendar")
            redirect_date = todo.start_date or date(year, month, 1)
            return redirect(
                f"{calendar_url}?year={redirect_date.year}&month={redirect_date.month}"
            )

        show_modal = True
        title_value = request.POST.get("title", "")
        start_date_value = request.POST.get("start_date", "")
        end_date_value = request.POST.get("end_date", "")

    return render(
        request,
        "todos/calendar.html",
        {
            "month_title": month_title,
            "selected_year": year,
            "selected_month": month,
            "weeks": weeks,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "show_modal": show_modal,
            "title_value": title_value,
            "start_date_value": start_date_value,
            "end_date_value": end_date_value,
            "form": form,
        },
    )


@login_required
def calendar_add(request):
    selected_date_str = request.GET.get("date")
    today = date.today()

    selected_date = today
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            redirect_date = todo.start_date or selected_date
            calendar_url = reverse("calendar")
            return redirect(
                f"{calendar_url}?year={redirect_date.year}&month={redirect_date.month}"
            )
    else:
        form = TodoForm(initial={
            "start_date": selected_date,
            "end_date": selected_date,
        })

    return render(
        request,
        "todos/calendar_add.html",
        {
            "form": form,
            "selected_date": selected_date,
        },
    )
