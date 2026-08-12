import calendar as py_calendar
from datetime import date, datetime, timedelta

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ProfileForm, SignUpForm, SubtaskFormSet, TodoForm
from .models import Tag, Todo


class CalendarItem:
    def __init__(self, todo, start_date, end_date, completed=False, is_virtual=False):
        self.todo = todo
        self.id = todo.id
        self.title = todo.title
        self.notes = todo.notes
        self.priority = todo.priority
        self.recurrence = todo.recurrence
        self.recurrence_until = todo.recurrence_until
        self.start_date = start_date
        self.end_date = end_date
        self.completed = completed
        self.is_virtual = is_virtual

    def occurrence_key(self):
        return (self.title, self.start_date, self.recurrence or "")

    def duration_label(self):
        if not self.start_date:
            return ""
        if not self.end_date or self.end_date == self.start_date:
            return self.start_date.strftime("%b %d, %Y")
        return f"{self.start_date.strftime('%b %d')} – {self.end_date.strftime('%b %d, %Y')}"

    def get_recurrence_display(self):
        return self.todo.get_recurrence_display()

    def get_priority_display(self):
        return self.todo.get_priority_display()


TODOS_PER_PAGE = 8

STATUS_FILTERS = ("all", "pending", "completed")
WHEN_FILTERS = ("all", "today", "week", "month", "upcoming", "undated", "due_soon")
SORT_FILTERS = ("status", "newest", "oldest", "title", "start", "priority")
PRIORITY_FILTERS = ("all", "low", "medium", "high")
STATUS_LABELS = {
    "all": "All tasks",
    "pending": "Pending",
    "completed": "Completed",
}
WHEN_LABELS = {
    "all": "Any date",
    "today": "Today",
    "week": "This week",
    "month": "This month",
    "upcoming": "Upcoming",
    "undated": "No dates",
    "due_soon": "Due soon",
}
SORT_LABELS = {
    "status": "Status",
    "newest": "Newest",
    "oldest": "Oldest",
    "title": "Title",
    "start": "Start date",
    "priority": "Priority",
}
PRIORITY_LABELS = {
    "all": "Any priority",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}


def month_bounds(today):
    start = today.replace(day=1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    return start, end


def user_todos(user, include_archived=False):
    todos = Todo.objects.filter(user=user)
    if not include_archived:
        todos = todos.filter(archived=False)
    return todos.prefetch_related("tags", "subtasks")


def due_soon_todos(user, today=None):
    today = today or date.today()
    tomorrow = today + timedelta(days=1)
    return (
        user_todos(user)
        .filter(completed=False, end_date__gte=today, end_date__lte=tomorrow)
        .order_by("end_date", "priority", "title")
    )


def apply_todo_filters(todos, request, include_archived=False):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")
    when = request.GET.get("when", "all")
    sort = request.GET.get("sort", "status")
    priority = request.GET.get("priority", "all")
    tag_slug = request.GET.get("tag", "").strip()
    show_archived = request.GET.get("archived", "") == "1" or include_archived

    if status not in STATUS_FILTERS:
        status = "all"
    if when not in WHEN_FILTERS:
        when = "all"
    if sort not in SORT_FILTERS:
        sort = "status"
    if priority not in PRIORITY_FILTERS:
        priority = "all"

    today = date.today()

    if not show_archived:
        todos = todos.filter(archived=False)
    elif request.GET.get("archived") == "1":
        todos = todos.filter(archived=True)

    if query:
        todos = todos.filter(
            Q(title__icontains=query)
            | Q(notes__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(subtasks__title__icontains=query)
        ).distinct()

    if status == "pending":
        todos = todos.filter(completed=False)
    elif status == "completed":
        todos = todos.filter(completed=True)

    if priority != "all":
        todos = todos.filter(priority=priority)

    if tag_slug:
        todos = todos.filter(tags__slug=tag_slug).distinct()

    if when == "today":
        todos = todos.filter(
            Q(start_date=today, end_date__isnull=True)
            | Q(start_date__lte=today, end_date__gte=today)
        )
    elif when == "due_soon":
        tomorrow = today + timedelta(days=1)
        todos = todos.filter(
            completed=False,
            end_date__gte=today,
            end_date__lte=tomorrow,
        )
    elif when == "week":
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        todos = todos.filter(
            Q(
                end_date__isnull=True,
                start_date__gte=week_start,
                start_date__lte=week_end,
            )
            | Q(
                end_date__isnull=False,
                start_date__lte=week_end,
                end_date__gte=week_start,
            )
        )
    elif when == "month":
        month_start, month_end = month_bounds(today)
        todos = todos.filter(
            Q(
                end_date__isnull=True,
                start_date__gte=month_start,
                start_date__lte=month_end,
            )
            | Q(
                end_date__isnull=False,
                start_date__lte=month_end,
                end_date__gte=month_start,
            )
        )
    elif when == "upcoming":
        todos = todos.filter(start_date__gte=today)
    elif when == "undated":
        todos = todos.filter(start_date__isnull=True)

    if sort == "newest":
        todos = todos.order_by("-created_at")
    elif sort == "oldest":
        todos = todos.order_by("created_at")
    elif sort == "title":
        todos = todos.order_by("title")
    elif sort == "start":
        todos = todos.order_by("start_date", "title")
    elif sort == "priority":
        todos = todos.order_by(
            models_priority_order(),
            "completed",
            "start_date",
            "title",
        )
    else:
        todos = todos.order_by("completed", models_priority_order(), "start_date", "title")

    Tag.ensure_defaults()
    return {
        "todos": todos,
        "query": query,
        "status": status,
        "when": when,
        "sort": sort,
        "priority": priority,
        "tag": tag_slug,
        "archived_view": request.GET.get("archived") == "1",
        "all_tags": Tag.objects.all(),
        "filters_active": bool(
            query
            or status != "all"
            or when != "all"
            or sort != "status"
            or priority != "all"
            or tag_slug
            or request.GET.get("archived") == "1"
        ),
        "result_count": todos.count(),
    }


def models_priority_order():
    from django.db.models import Case, IntegerField, When

    return Case(
        When(priority=Todo.PRIORITY_HIGH, then=0),
        When(priority=Todo.PRIORITY_MEDIUM, then=1),
        When(priority=Todo.PRIORITY_LOW, then=2),
        default=3,
        output_field=IntegerField(),
    )


def paginate_todos(queryset, request, per_page=TODOS_PER_PAGE):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("partial", None)
    return {
        "todos": page_obj.object_list,
        "page_obj": page_obj,
        "page_query": params.urlencode(),
    }


def mark_overdue_todos_completed(user=None):
    """
    Auto-complete todos whose end_date is in the past.
    Recurring tasks spawn their next occurrence.
    """
    today = date.today()
    todos = Todo.objects.filter(
        completed=False,
        archived=False,
        end_date__isnull=False,
        end_date__lt=today,
    )
    if user is not None:
        todos = todos.filter(user=user)

    overdue = list(todos)
    if not overdue:
        return

    now = timezone.now()
    Todo.objects.filter(pk__in=[todo.pk for todo in overdue]).update(
        completed=True,
        completed_at=now,
    )
    for todo in overdue:
        todo.completed = True
        todo.completed_at = now
        todo.spawn_next_occurrence()


def completion_streak(user, today=None):
    today = today or date.today()
    days = (
        user_todos(user, include_archived=True)
        .filter(completed=True, completed_at__isnull=False)
        .annotate(day=TruncDate("completed_at"))
        .values_list("day", flat=True)
        .distinct()
    )
    completed_days = {d for d in days if d}
    streak = 0
    cursor = today
    # If nothing completed today, allow streak to count from yesterday.
    if cursor not in completed_days:
        cursor = today - timedelta(days=1)
    while cursor in completed_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


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


@login_required
def home(request):
    mark_overdue_todos_completed(request.user)
    all_todos = user_todos(request.user)
    completed_tasks = all_todos.filter(completed=True).count()
    pending_tasks = all_todos.filter(completed=False).count()
    total_tasks = all_todos.count()
    progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    filtered = apply_todo_filters(all_todos, request)
    filtered.update(paginate_todos(filtered["todos"], request))
    due_soon = due_soon_todos(request.user)

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    if request.method == "POST":
        form = TodoForm(request.POST)

        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            form.save_m2m()
            return redirect("home")
    else:
        form = TodoForm()

    return render(
        request,
        "todos/home.html",
        {
            "form": form,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "total_tasks": total_tasks,
            "progress_percent": progress_percent,
            "greeting": greeting,
            "today": date.today(),
            "due_soon": due_soon,
            "streak": completion_streak(request.user),
            **filtered,
        },
    )


@login_required
def search_todos(request):
    mark_overdue_todos_completed(request.user)
    all_todos = user_todos(request.user, include_archived=True)
    filtered = apply_todo_filters(all_todos, request)
    filtered.update(paginate_todos(filtered["todos"], request))

    counted = user_todos(request.user)
    if filtered["query"]:
        counted = counted.filter(
            Q(title__icontains=filtered["query"]) | Q(notes__icontains=filtered["query"])
        )

    filtered.update(
        {
            "all_count": counted.count(),
            "pending_count": counted.filter(completed=False).count(),
            "completed_count": counted.filter(completed=True).count(),
            "status_label": STATUS_LABELS[filtered["status"]],
            "when_label": WHEN_LABELS[filtered["when"]],
            "sort_label": SORT_LABELS[filtered["sort"]],
            "priority_label": PRIORITY_LABELS[filtered["priority"]],
        }
    )
    if request.GET.get("partial") == "1":
        return render(request, "todos/_search_results.html", filtered)
    return render(request, "todos/search.html", filtered)


@login_required
def edit_todos(request):
    mark_overdue_todos_completed(request.user)
    filtered = apply_todo_filters(
        user_todos(request.user, include_archived=True),
        request,
    )
    filtered.update(paginate_todos(filtered["todos"], request))
    todos = list(filtered["todos"])

    if request.method == "POST":
        action = request.POST.get("bulk_action", "save")
        for todo in todos:
            if action == "archive_selected" and f"selected_{todo.id}" in request.POST:
                todo.archive()
                continue
            if action == "restore_selected" and f"selected_{todo.id}" in request.POST:
                todo.restore()
                continue

            was_completed = todo.completed
            todo.completed = f"completed_{todo.id}" in request.POST
            todo.save()
            if todo.completed and not was_completed:
                todo.spawn_next_occurrence()

        redirect_url = reverse("edit_todos")
        querystring = request.GET.urlencode()
        if querystring:
            redirect_url = f"{redirect_url}?{querystring}"
        return redirect(redirect_url)

    return render(request, "todos/edit-todos.html", filtered)


@login_required
def delete(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "archive")
        if action == "delete_forever":
            todo.delete()
        else:
            todo.archive()
        return redirect("edit_todos")

    return render(request, "todos/delete.html", {
        "todo": todo,
    })


@login_required
def restore_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    if request.method == "POST":
        todo.restore()
    return redirect("edit_todos")


@login_required
def edit(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)

    if request.method == "POST":
        form = TodoForm(request.POST, instance=todo)
        formset = SubtaskFormSet(request.POST, instance=todo)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("edit_todos")
    else:
        form = TodoForm(instance=todo)
        formset = SubtaskFormSet(instance=todo)

    return render(request, "todos/edit.html", {
        "form": form,
        "formset": formset,
        "todo": todo,
    })


@login_required
def activity(request):
    mark_overdue_todos_completed(request.user)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    completed_qs = (
        user_todos(request.user, include_archived=True)
        .filter(completed=True, completed_at__isnull=False)
    )
    week_completed = completed_qs.filter(
        completed_at__date__gte=week_start,
        completed_at__date__lte=today,
    )
    by_day = {
        row["day"]: row["total"]
        for row in week_completed.annotate(day=TruncDate("completed_at"))
        .values("day")
        .annotate(total=Count("id"))
    }
    week_chart = [
        {
            "date": day,
            "label": day.strftime("%a"),
            "count": by_day.get(day, 0),
            "height": max(8, by_day.get(day, 0) * 18),
        }
        for day in week_days
    ]
    max_count = max((item["count"] for item in week_chart), default=0) or 1
    for item in week_chart:
        item["height"] = max(8, int((item["count"] / max_count) * 120))

    month_start, _ = month_bounds(today)
    recent = completed_qs.order_by("-completed_at")[:12]
    priority_breakdown = (
        user_todos(request.user)
        .filter(completed=False)
        .values("priority")
        .annotate(total=Count("id"))
    )
    priority_map = {row["priority"]: row["total"] for row in priority_breakdown}

    return render(
        request,
        "todos/activity.html",
        {
            "today": today,
            "week_chart": week_chart,
            "week_total": week_completed.count(),
            "month_total": completed_qs.filter(completed_at__date__gte=month_start).count(),
            "streak": completion_streak(request.user, today),
            "recent_completed": recent,
            "due_soon": due_soon_todos(request.user, today),
            "high_open": priority_map.get(Todo.PRIORITY_HIGH, 0),
            "medium_open": priority_map.get(Todo.PRIORITY_MEDIUM, 0),
            "low_open": priority_map.get(Todo.PRIORITY_LOW, 0),
            "archived_count": Todo.objects.filter(user=request.user, archived=True).count(),
        },
    )


def about(request):
    from blog.models import Post

    if request.user.is_authenticated:
        todos = user_todos(request.user)
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
