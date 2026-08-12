from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("activity/", views.activity, name="activity"),
    path("calendar/", views.calendar, name="calendar"),
    path("calendar/add/", views.calendar_add, name="calendar_add"),
    path("search/", views.search_todos, name="search"),
    path("edit-todos/", views.edit_todos, name="edit_todos"),
    path("delete/<int:todo_id>/", views.delete, name="delete"),
    path("restore/<int:todo_id>/", views.restore_todo, name="restore"),
    path("edit/<int:todo_id>/", views.edit, name="edit"),
]
