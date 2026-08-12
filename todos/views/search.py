from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from todos.services import (
    PRIORITY_LABELS,
    SORT_LABELS,
    STATUS_LABELS,
    WHEN_LABELS,
    apply_todo_filters,
    mark_overdue_todos_completed,
    paginate_todos,
    user_todos,
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
