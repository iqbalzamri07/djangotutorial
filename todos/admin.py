from django.contrib import admin
from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "completed", "recurrence", "start_date", "end_date")
    list_filter = ("completed", "recurrence", "user")
    search_fields = ("title", "notes")