from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response(
        {
            "auth_signup": reverse("api-signup", request=request, format=format),
            "auth_login": reverse("api-login", request=request, format=format),
            "auth_logout": reverse("api-logout", request=request, format=format),
            "auth_me": reverse("api-me", request=request, format=format),
            "todos": reverse("api-todo-list", request=request, format=format),
            "tags": reverse("api-tags", request=request, format=format),
            "posts": reverse("api-post-list", request=request, format=format),
        }
    )
