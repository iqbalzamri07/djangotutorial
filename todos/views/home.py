from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from todos.forms import TodoForm
from todos.services import (
    apply_todo_filters,
    completion_streak,
    due_soon_todos,
    mark_overdue_todos_completed,
    paginate_todos,
    user_todos,
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
