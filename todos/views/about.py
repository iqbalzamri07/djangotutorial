from blog.models import Post
from django.shortcuts import render

from todos.models import Todo
from todos.services import user_todos


def about(request):
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
