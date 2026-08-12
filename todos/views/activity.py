from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render

from todos.models import Todo
from todos.services import (
    completion_streak,
    due_soon_todos,
    mark_overdue_todos_completed,
    month_bounds,
    user_todos,
)


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
