from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from todos.forms import SubtaskFormSet, TodoForm
from todos.models import Todo
from todos.services import apply_todo_filters, mark_overdue_todos_completed, paginate_todos, user_todos


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
