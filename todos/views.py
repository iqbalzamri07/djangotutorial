import calendar as py_calendar
from datetime import date, datetime, timedelta

from django.urls import reverse

from django.shortcuts import get_object_or_404, render, redirect
from .models import Todo
from .forms import TodoForm


def mark_overdue_todos_completed():
    """
    Auto-complete todos whose end_date is in the past.

    This is a "lazy" approach: it runs when pages are visited (home/calendar),
    avoiding extra background jobs for this tutorial project.
    """
    today = date.today()
    Todo.objects.filter(
        completed=False,
        end_date__isnull=False,
        end_date__lt=today,
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

    month_end_date = next_month_date - timedelta(days=1)

    todos_in_month = Todo.objects.filter(
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

    cal = py_calendar.Calendar(firstweekday=0)  # Monday
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

    # Handle "add todo" popup submit without leaving the calendar page.
    show_modal = False
    title_value = ""
    start_date_value = ""
    end_date_value = ""
    form = None
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save()
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


def calendar_add(request):
    """
    Add a Todo with start/end dates prefilled from a day clicked in the calendar.
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