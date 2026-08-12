from rest_framework import serializers

from .models import Subtask, Tag, Todo


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color"]


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ["id", "title", "completed", "order"]
        read_only_fields = ["id"]


class TodoSerializer(serializers.ModelSerializer):
    duration_label = serializers.CharField(read_only=True)
    recurrence_label = serializers.CharField(
        source="get_recurrence_display",
        read_only=True,
    )
    priority_label = serializers.CharField(
        source="get_priority_display",
        read_only=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_slugs = serializers.SlugRelatedField(
        many=True,
        slug_field="slug",
        queryset=Tag.objects.all(),
        source="tags",
        write_only=True,
        required=False,
    )
    subtasks = SubtaskSerializer(many=True, required=False)

    class Meta:
        model = Todo
        fields = [
            "id",
            "title",
            "notes",
            "completed",
            "completed_at",
            "archived",
            "archived_at",
            "priority",
            "priority_label",
            "tags",
            "tag_slugs",
            "subtasks",
            "start_date",
            "end_date",
            "recurrence",
            "recurrence_until",
            "recurrence_label",
            "duration_label",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "completed_at",
            "archived_at",
            "duration_label",
            "recurrence_label",
            "priority_label",
            "tags",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        recurrence = attrs.get("recurrence", getattr(self.instance, "recurrence", ""))
        recurrence_until = attrs.get(
            "recurrence_until",
            getattr(self.instance, "recurrence_until", None),
        )

        if "start_date" in attrs and start_date and not end_date:
            attrs["end_date"] = start_date
            end_date = start_date
        elif "end_date" in attrs and end_date and not start_date:
            attrs["start_date"] = end_date
            start_date = end_date

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )
        if recurrence and not start_date:
            raise serializers.ValidationError(
                {"start_date": "Recurring tasks need a start date."}
            )
        if recurrence_until and start_date and recurrence_until < start_date:
            raise serializers.ValidationError(
                {"recurrence_until": "Repeat until cannot be before the start date."}
            )
        return attrs

    def _save_subtasks(self, todo, subtasks_data):
        if subtasks_data is None:
            return
        todo.subtasks.all().delete()
        for index, item in enumerate(subtasks_data):
            Subtask.objects.create(
                todo=todo,
                title=item.get("title", ""),
                completed=item.get("completed", False),
                order=item.get("order", index),
            )

    def create(self, validated_data):
        Tag.ensure_defaults()
        subtasks_data = validated_data.pop("subtasks", None)
        tags = validated_data.pop("tags", [])
        todo = Todo.objects.create(**validated_data)
        if tags:
            todo.tags.set(tags)
        self._save_subtasks(todo, subtasks_data)
        return todo

    def update(self, instance, validated_data):
        Tag.ensure_defaults()
        subtasks_data = validated_data.pop("subtasks", None)
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        if subtasks_data is not None:
            self._save_subtasks(instance, subtasks_data)
        return instance
