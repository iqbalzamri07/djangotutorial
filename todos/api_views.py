from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Todo
from .serializers import TodoSerializer
from .views import apply_todo_filters, mark_overdue_todos_completed


class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mark_overdue_todos_completed(self.request.user)
        todos = Todo.objects.filter(user=self.request.user)
        return apply_todo_filters(todos, self.request)["todos"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
