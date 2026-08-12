from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    def duration_label(self):
        if not self.start_date:
            return ""
        if not self.end_date or self.end_date == self.start_date:
            return self.start_date.strftime("%b %d, %Y")
        return f"{self.start_date.strftime('%b %d')} – {self.end_date.strftime('%b %d, %Y')}"
