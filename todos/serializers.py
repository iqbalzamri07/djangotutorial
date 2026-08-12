from rest_framework import serializers

from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    duration_label = serializers.CharField(read_only=True)

    class Meta:
        model = Todo
        fields = [
            "id",
            "title",
            "completed",
            "start_date",
            "end_date",
            "duration_label",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "duration_label"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))

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
        return attrs
