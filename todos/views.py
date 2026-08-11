import calendar as py_calendar
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from django.urls import reverse

from django.shortcuts import get_object_or_404, render, redirect
from .models import Todo
from .forms import TodoForm


def mark_overdue_todos_completed():
    """
    Auto-complete todos whose due_datetime is in the past.

    This is a "lazy" approach: it runs when pages are visited (home/calendar),
    avoiding extra background jobs for this tutorial project.
    """
    now = timezone.now()
    Todo.objects.filter(
        completed=False,
        due_datetime__isnull=False,
        due_datetime__lt=now,
    ).update(completed=True)


def home(request):
    mark_overdue_todos_completed()
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
    mark_overdue_todos_completed()
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
    mark_overdue_todos_completed()
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

    # Handle "add todo" popup submit without leaving the calendar page.
    show_modal = False
    title_value = ""
    due_datetime_value = ""
    form = None
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save()
            local_due = timezone.localtime(todo.due_datetime)
            calendar_url = reverse("calendar")
            return redirect(
                f"{calendar_url}?year={local_due.year}&month={local_due.month}"
            )

        show_modal = True
        title_value = request.POST.get("title", "")
        due_datetime_value = request.POST.get("due_datetime", "")

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
            "due_datetime_value": due_datetime_value,
            "form": form,
        },
    )


def calendar_add(request):
    """
    Add a Todo with its due_datetime prefilled from a day clicked in the calendar.
    GET params:
      - date=YYYY-MM-DD
    """
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
            todo = form.save()
            local_due = timezone.localtime(todo.due_datetime)
            return redirect(
                "calendar",
                year=local_due.year,
                month=local_due.month,
            )
    else:
        # Prefill time so user only needs to type the title (adjust as you like).
        tz = timezone.get_current_timezone()
        due_local = datetime.combine(selected_date, time(9, 0))
        due_aware = timezone.make_aware(due_local, tz)
        form = TodoForm(initial={"due_datetime": due_aware})

    return render(
        request,
        "todos/calendar_add.html",
        {
            "form": form,
            "selected_date": selected_date,
        },
    )