from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("calendar/", views.calendar, name="calendar"),
    path("calendar/add/", views.calendar_add, name="calendar_add"),

    path("search/", views.search_todos, name="search"),

    # Page showing all todos
    path("edit-todos/", views.edit_todos, name="edit_todos"),

    # Delete one todo
    path("delete/<int:todo_id>/", views.delete, name="delete"),

    # Edit one todo
    path("edit/<int:todo_id>/", views.edit, name="edit"),
]