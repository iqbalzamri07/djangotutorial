from django.urls import path
from rest_framework.routers import SimpleRouter

from accounts.api_views import LoginAPIView, LogoutAPIView, MeAPIView, SignupAPIView
from blog.api_views import PostViewSet
from todos.api_views import TagListAPIView, TodoViewSet

from . import views

router = SimpleRouter()
router.register("todos", TodoViewSet, basename="api-todo")
router.register("posts", PostViewSet, basename="api-post")

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("auth/signup/", SignupAPIView.as_view(), name="api-signup"),
    path("auth/login/", LoginAPIView.as_view(), name="api-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="api-logout"),
    path("auth/me/", MeAPIView.as_view(), name="api-me"),
    path("tags/", TagListAPIView.as_view(), name="api-tags"),
] + router.urls
