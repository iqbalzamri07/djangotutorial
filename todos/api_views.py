from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tag, Todo
from .serializers import TagSerializer, TodoSerializer
from .views import apply_todo_filters, mark_overdue_todos_completed, user_todos


class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mark_overdue_todos_completed(self.request.user)
        Tag.ensure_defaults()
        todos = user_todos(self.request.user, include_archived=True)
        if self.action in {"retrieve", "update", "partial_update", "destroy", "restore", "purge"}:
            return todos
        return apply_todo_filters(todos, self.request)["todos"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        was_completed = serializer.instance.completed
        todo = serializer.save()
        if todo.completed and not was_completed:
            todo.spawn_next_occurrence()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.archive()

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        todo = self.get_object()
        todo.restore()
        return Response(self.get_serializer(todo).data)

    @action(detail=True, methods=["post"])
    def purge(self, request, pk=None):
        todo = self.get_object()
        todo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        Tag.ensure_defaults()
        return Response(TagSerializer(Tag.objects.all(), many=True).data)
