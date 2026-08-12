from rest_framework import serializers

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    reading_time = serializers.IntegerField(read_only=True)
    category_label = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "content",
            "category",
            "category_label",
            "emoji",
            "featured",
            "created_at",
            "reading_time",
        ]
