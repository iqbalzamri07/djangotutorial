from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional schedule for timetable/calendar view.
    due_datetime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title