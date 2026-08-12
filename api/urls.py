from django.urls import path
from rest_framework.routers import SimpleRouter

from blog.api_views import PostViewSet
from todos.api_views import TodoViewSet

from . import views

router = SimpleRouter()
router.register("todos", TodoViewSet, basename="api-todo")
router.register("posts", PostViewSet, basename="api-post")

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("auth/signup/", views.SignupAPIView.as_view(), name="api-signup"),
    path("auth/login/", views.LoginAPIView.as_view(), name="api-login"),
    path("auth/logout/", views.LogoutAPIView.as_view(), name="api-logout"),
    path("auth/me/", views.MeAPIView.as_view(), name="api-me"),
] + router.urls
