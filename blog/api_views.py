from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Post
from .serializers import PostSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        posts = Post.objects.filter(published=True)
        category = self.request.query_params.get("category")
        if category:
            posts = posts.filter(category=category)
        return posts
