import calendar as py_calendar
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from django.shortcuts import get_object_or_404, render, redirect
from .models import Todo
from .forms import TodoForm


def home(request):
    todos = Todo.objects.all()
    completed_tasks = todos.filter(completed=True).count()
    pending_tasks = todos.filter(completed=False).count()

    if request.method == "POST":
        form = TodoForm(request.POST)

        if form.is_valid():
            form.save()
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


def edit_todos(request):
    todos = Todo.objects.all()

    if request.method == "POST":

        for todo in todos:
            todo.completed = f"completed_{todo.id}" in request.POST
            todo.save()

        return redirect("home")

    return render(request, "todos/edit-todos.html", {
        "todos": todos,
    })


def delete(request,todo_id):
    todo = get_object_or_404(Todo, id=todo_id)

    if request.method == "POST":
        todo.delete()
        return redirect("home")

    return render(request, "todos/delete.html", {
        "todo": todo,
    })


def edit(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)

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
    return render(request, "todos/about.html")


def calendar(request):
    """
    Monthly grid for todos scheduled on a given month.

    GET params:
    - year (YYYY)
    - month (1-12)
    """
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        year = today.year

    try:
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        month = today.month

    # Normalize out-of-range values.
    month = max(1, min(12, month))

    month_start_date = date(year, month, 1)
    next_month_date = (
        date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    )

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(month_start_date, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(next_month_date, time.min), tz)

    todos_in_month = (
        Todo.objects.filter(due_datetime__gte=start_dt, due_datetime__lt=end_dt)
        .order_by("due_datetime")
    )

    todos_by_date = {}
    for todo in todos_in_month:
        local_day = timezone.localtime(todo.due_datetime).date()
        todos_by_date.setdefault(local_day, []).append(todo)

    cal = py_calendar.Calendar(firstweekday=0)  # Monday
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for day_date in week:
            week_cells.append(
                {
                    "date": day_date,
                    "in_month": day_date.month == month,
                    "todos": todos_by_date.get(day_date, []),
                }
            )
        weeks.append(week_cells)

    prev_year = year - 1 if month == 1 else year
    prev_month = 12 if month == 1 else month - 1
    next_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1

    month_title = datetime(year, month, 1).strftime("%B %Y")

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
        },
    )