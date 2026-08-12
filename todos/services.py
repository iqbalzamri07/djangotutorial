from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, When
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Tag, Todo

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


def models_priority_order():
    return Case(
        When(priority=Todo.PRIORITY_HIGH, then=0),
        When(priority=Todo.PRIORITY_MEDIUM, then=1),
        When(priority=Todo.PRIORITY_LOW, then=2),
        default=3,
        output_field=IntegerField(),
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
