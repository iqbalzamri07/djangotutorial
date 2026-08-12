from django.contrib import admin

from .models import Subtask, Tag, Todo


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "priority",
        "completed",
        "archived",
        "recurrence",
        "start_date",
        "end_date",
    )
    list_filter = ("completed", "archived", "priority", "recurrence", "user", "tags")
    search_fields = ("title", "notes")
    filter_horizontal = ("tags",)
    inlines = [SubtaskInline]


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ("title", "todo", "completed", "order")
    list_filter = ("completed",)
