import calendar
from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def add_years(value, years):
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, month=2, day=28)


class Tag(models.Model):
    DEFAULT_SLUGS = ("work", "personal", "health", "learning", "errands")

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)
    color = models.CharField(max_length=7, default="#0f766e")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def ensure_defaults(cls):
        defaults = [
            ("Work", "work", "#1d4ed8"),
            ("Personal", "personal", "#0f766e"),
            ("Health", "health", "#16a34a"),
            ("Learning", "learning", "#7c3aed"),
            ("Errands", "errands", "#c2410c"),
        ]
        for name, slug, color in defaults:
            cls.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "color": color},
            )


class Todo(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    RECURRENCE_NONE = ""
    RECURRENCE_DAILY = "daily"
    RECURRENCE_WEEKLY = "weekly"
    RECURRENCE_MONTHLY = "monthly"
    RECURRENCE_YEARLY = "yearly"
    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, "Does not repeat"),
        (RECURRENCE_DAILY, "Daily"),
        (RECURRENCE_WEEKLY, "Weekly"),
        (RECURRENCE_MONTHLY, "Monthly"),
        (RECURRENCE_YEARLY, "Yearly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="todos",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True, default="")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="todos")
    recurrence = models.CharField(
        max_length=16,
        choices=RECURRENCE_CHOICES,
        blank=True,
        default=RECURRENCE_NONE,
        help_text="Shows on every matching day in the calendar. Completing it creates the next occurrence.",
    )
    recurrence_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Repeat until",
        help_text="Optional. Stop creating new occurrences after this date.",
    )

    class Meta:
        ordering = ["completed", "priority", "start_date", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        if not self.completed:
            self.completed_at = None
        if self.archived and not self.archived_at:
            self.archived_at = timezone.now()
        if not self.archived:
            self.archived_at = None
        super().save(*args, **kwargs)

    def archive(self):
        self.archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=["archived", "archived_at"])

    def restore(self):
        self.archived = False
        self.archived_at = None
        self.save(update_fields=["archived", "archived_at"])

    def duration_label(self):
        if not self.start_date:
            return ""
        if not self.end_date or self.end_date == self.start_date:
            return self.start_date.strftime("%b %d, %Y")
        return f"{self.start_date.strftime('%b %d')} – {self.end_date.strftime('%b %d, %Y')}"

    def checklist_progress(self):
        total = self.subtasks.count()
        if not total:
            return None
        done = self.subtasks.filter(completed=True).count()
        return done, total

    def is_due_soon(self, today=None):
        today = today or date.today()
        if self.completed or self.archived or not self.end_date:
            return False
        return today <= self.end_date <= today + timedelta(days=1)

    def iter_occurrences(self, range_start, range_end):
        """Yield (start, end) pairs that overlap the given date range."""
        if not self.start_date:
            return

        occ_start = self.start_date
        occ_end = self.end_date or self.start_date

        if not self.recurrence:
            if occ_start <= range_end and occ_end >= range_start:
                yield occ_start, occ_end
            return

        guard = 0
        while occ_end < range_start:
            moved_start = self.shift_date(occ_start)
            moved_end = self.shift_date(occ_end)
            if moved_start == occ_start:
                return
            occ_start, occ_end = moved_start, moved_end
            if self.recurrence_until and occ_start > self.recurrence_until:
                return
            guard += 1
            if guard > 10000:
                return

        while occ_start <= range_end:
            if self.recurrence_until and occ_start > self.recurrence_until:
                return
            if occ_end >= range_start:
                yield occ_start, occ_end
            moved_start = self.shift_date(occ_start)
            moved_end = self.shift_date(occ_end)
            if moved_start == occ_start:
                return
            occ_start, occ_end = moved_start, moved_end
            guard += 1
            if guard > 10000:
                return

    def shift_date(self, value):
        if not value or not self.recurrence:
            return value
        if self.recurrence == self.RECURRENCE_DAILY:
            return value + timedelta(days=1)
        if self.recurrence == self.RECURRENCE_WEEKLY:
            return value + timedelta(weeks=1)
        if self.recurrence == self.RECURRENCE_MONTHLY:
            return add_months(value, 1)
        if self.recurrence == self.RECURRENCE_YEARLY:
            return add_years(value, 1)
        return value

    def spawn_next_occurrence(self, skip_overdue=True, today=None):
        if not self.recurrence or not self.start_date:
            return None

        today = today or date.today()
        next_start = self.shift_date(self.start_date)
        next_end = self.shift_date(self.end_date) if self.end_date else next_start

        while skip_overdue and next_end and next_end < today:
            moved_start = self.shift_date(next_start)
            moved_end = self.shift_date(next_end)
            if moved_start == next_start:
                break
            next_start, next_end = moved_start, moved_end

        if self.recurrence_until and next_start > self.recurrence_until:
            return None

        already_open = Todo.objects.filter(
            user=self.user,
            title=self.title,
            start_date=next_start,
            completed=False,
            archived=False,
            recurrence=self.recurrence,
        ).exists()
        if already_open:
            return None

        nxt = Todo.objects.create(
            user=self.user,
            title=self.title,
            notes=self.notes,
            completed=False,
            start_date=next_start,
            end_date=next_end,
            priority=self.priority,
            recurrence=self.recurrence,
            recurrence_until=self.recurrence_until,
        )
        tag_ids = list(self.tags.values_list("id", flat=True))
        if tag_ids:
            nxt.tags.set(tag_ids)
        return nxt


class Subtask(models.Model):
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
