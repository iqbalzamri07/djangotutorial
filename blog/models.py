from django.db import models


class Post(models.Model):
    CATEGORY_CHOICES = [
        ("django", "Django"),
        ("productivity", "Productivity"),
        ("learning", "Learning"),
        ("project", "Project Notes"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(max_length=280)
    content = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="learning")
    emoji = models.CharField(max_length=8, default="📝")
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def reading_time(self):
        words = len(self.content.split())
        return max(1, round(words / 180))
