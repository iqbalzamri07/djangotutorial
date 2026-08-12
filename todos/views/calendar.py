import calendar as py_calendar
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from todos.forms import TodoForm
from todos.models import Todo
from todos.services import CalendarItem, mark_overdue_todos_completed, user_todos


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

    window_start = month_start_date - timedelta(days=7)
    window_end = month_end_date + timedelta(days=7)

    actual_todos = user_todos(request.user).filter(
        start_date__isnull=False,
    ).filter(
        Q(end_date__isnull=True, start_date__gte=window_start, start_date__lte=window_end)
        | Q(end_date__isnull=False, start_date__lte=window_end, end_date__gte=window_start)
    ).order_by("start_date", "end_date", "title")

    recurring_todos = user_todos(request.user).filter(
        start_date__isnull=False,
        recurrence__gt="",
    ).order_by("start_date", "id")

    placed = {}
    for todo in actual_todos:
        occ_end = todo.end_date or todo.start_date
        item = CalendarItem(todo, todo.start_date, occ_end, todo.completed, is_virtual=False)
        placed[item.occurrence_key()] = item

    for todo in recurring_todos:
        source_end = todo.end_date or todo.start_date
        for occ_start, occ_end in todo.iter_occurrences(window_start, window_end):
            is_source = occ_start == todo.start_date and occ_end == source_end
            item = CalendarItem(
                todo,
                occ_start,
                occ_end,
                completed=todo.completed if is_source else False,
                is_virtual=not is_source,
            )
            existing = placed.get(item.occurrence_key())
            if existing and not existing.is_virtual:
                continue
            placed[item.occurrence_key()] = item

    todos_by_date = {}
    for item in placed.values():
        span_start = max(item.start_date, window_start)
        span_end = min(item.end_date or item.start_date, window_end)
        current = span_start
        while current <= span_end:
            todos_by_date.setdefault(current, []).append(item)
            current += timedelta(days=1)

    for items in todos_by_date.values():
        items.sort(key=lambda item: (item.start_date, item.title.lower()))

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
    notes_value = ""
    start_date_value = ""
    end_date_value = ""
    recurrence_value = ""
    recurrence_until_value = ""
    priority_value = Todo.PRIORITY_MEDIUM
    form = None
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            form.save_m2m()
            calendar_url = reverse("calendar")
            redirect_date = todo.start_date or date(year, month, 1)
            return redirect(
                f"{calendar_url}?year={redirect_date.year}&month={redirect_date.month}"
            )

        show_modal = True
        title_value = request.POST.get("title", "")
        notes_value = request.POST.get("notes", "")
        start_date_value = request.POST.get("start_date", "")
        end_date_value = request.POST.get("end_date", "")
        recurrence_value = request.POST.get("recurrence", "")
        recurrence_until_value = request.POST.get("recurrence_until", "")
        priority_value = request.POST.get("priority", Todo.PRIORITY_MEDIUM)

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
            "notes_value": notes_value,
            "start_date_value": start_date_value,
            "end_date_value": end_date_value,
            "recurrence_value": recurrence_value,
            "recurrence_until_value": recurrence_until_value,
            "priority_value": priority_value,
            "priority_choices": Todo.PRIORITY_CHOICES,
            "recurrence_choices": Todo.RECURRENCE_CHOICES,
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
            form.save_m2m()
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
