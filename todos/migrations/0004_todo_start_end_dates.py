from django.db import migrations, models
from django.utils import timezone


def copy_due_datetime_to_dates(apps, schema_editor):
    Todo = apps.get_model("todos", "Todo")

    for todo in Todo.objects.exclude(due_datetime__isnull=True):
        due = todo.due_datetime
        if timezone.is_aware(due):
            due_date = timezone.localtime(due).date()
        else:
            due_date = due.date()
        todo.start_date = due_date
        todo.end_date = due_date
        todo.save(update_fields=["start_date", "end_date"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("todos", "0003_todo_due_datetime"),
    ]

    operations = [
        migrations.AddField(
            model_name="todo",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="todo",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(copy_due_datetime_to_dates, noop),
        migrations.RemoveField(
            model_name="todo",
            name="due_datetime",
        ),
    ]
