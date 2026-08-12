from django.urls import path
from . import views

# Blog list + single post pages
urlpatterns = [
    path("", views.blog, name="blog"),
    path("post/<slug:slug>/", views.post_detail, name="post_detail"),
]
