from rest_framework import serializers

from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    duration_label = serializers.CharField(read_only=True)
    recurrence_label = serializers.CharField(
        source="get_recurrence_display",
        read_only=True,
    )

    class Meta:
        model = Todo
        fields = [
            "id",
            "title",
            "notes",
            "completed",
            "start_date",
            "end_date",
            "recurrence",
            "recurrence_until",
            "recurrence_label",
            "duration_label",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "duration_label", "recurrence_label"]

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
