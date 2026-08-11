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