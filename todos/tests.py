from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from blog.models import Post
from todos.models import Todo


class TodoAPITests(APITestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="api_tester",
            email="api@test.com",
            password=self.password,
        )

    def test_todo_crud_is_scoped_to_user(self):
        login = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")

        create = self.client.post(
            "/api/todos/",
            {
                "title": "API task",
                "notes": "Bring snacks and a notebook.",
                "start_date": "2026-08-12",
                "end_date": "2026-08-14",
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        todo_id = create.data["id"]
        todo = Todo.objects.get(id=todo_id)
        self.assertEqual(todo.user, self.user)
        self.assertEqual(todo.notes, "Bring snacks and a notebook.")

        listing = self.client.get("/api/todos/?q=snacks&status=pending")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.data["count"], 1)

        update = self.client.patch(
            f"/api/todos/{todo_id}/",
            {"completed": True},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertTrue(update.data["completed"])

        delete = self.client.delete(f"/api/todos/{todo_id}/")
        self.assertEqual(delete.status_code, 204)
        self.assertTrue(Todo.objects.get(id=todo_id).archived)

        restore = self.client.post(f"/api/todos/{todo_id}/restore/")
        self.assertEqual(restore.status_code, 200)
        self.assertFalse(Todo.objects.get(id=todo_id).archived)

    def test_posts_are_public(self):
        Post.objects.create(
            title="API note",
            slug="api-note",
            excerpt="A published post for the API.",
            content="Hello from the REST API.",
            published=True,
        )
        response = self.client.get("/api/posts/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_completing_recurring_todo_spawns_next(self):
        login = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")

        create = self.client.post(
            "/api/todos/",
            {
                "title": "Weekly review",
                "start_date": "2026-08-10",
                "end_date": "2026-08-10",
                "recurrence": "weekly",
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        todo_id = create.data["id"]

        update = self.client.patch(
            f"/api/todos/{todo_id}/",
            {"completed": True},
            format="json",
        )
        self.assertEqual(update.status_code, 200)

        next_todo = Todo.objects.get(
            user=self.user,
            title="Weekly review",
            completed=False,
            start_date=date(2026, 8, 17),
        )
        self.assertEqual(next_todo.recurrence, "weekly")


class RecurringTodoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="recurring_user",
            password="StrongPass123!",
        )

    def test_weekly_spawn(self):
        todo = Todo.objects.create(
            user=self.user,
            title="Team standup",
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 10),
            recurrence=Todo.RECURRENCE_WEEKLY,
        )
        nxt = todo.spawn_next_occurrence(today=date(2026, 8, 10))
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.start_date, date(2026, 8, 17))
        self.assertEqual(nxt.end_date, date(2026, 8, 17))
        self.assertFalse(nxt.completed)
        self.assertEqual(nxt.recurrence, Todo.RECURRENCE_WEEKLY)

    def test_stops_after_until(self):
        todo = Todo.objects.create(
            user=self.user,
            title="Daily stretch",
            start_date=date(2026, 8, 11),
            end_date=date(2026, 8, 11),
            recurrence=Todo.RECURRENCE_DAILY,
            recurrence_until=date(2026, 8, 11),
        )
        self.assertIsNone(todo.spawn_next_occurrence(today=date(2026, 8, 11)))

    def test_monthly_end_of_month(self):
        todo = Todo.objects.create(
            user=self.user,
            title="Month close",
            start_date=date(2026, 1, 31),
            end_date=date(2026, 1, 31),
            recurrence=Todo.RECURRENCE_MONTHLY,
        )
        nxt = todo.spawn_next_occurrence(today=date(2026, 1, 31))
        self.assertEqual(nxt.start_date, date(2026, 2, 28))

    def test_skips_overdue_occurrences(self):
        todo = Todo.objects.create(
            user=self.user,
            title="Daily walk",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
            recurrence=Todo.RECURRENCE_DAILY,
        )
        nxt = todo.spawn_next_occurrence(today=date(2026, 8, 12))
        self.assertEqual(nxt.start_date, date(2026, 8, 12))
        self.assertFalse(nxt.completed)

    def test_monthly_occurrences_cover_future_months(self):
        todo = Todo.objects.create(
            user=self.user,
            title="Pay rent",
            start_date=date(2026, 8, 12),
            end_date=date(2026, 8, 12),
            recurrence=Todo.RECURRENCE_MONTHLY,
        )
        occurrences = list(
            todo.iter_occurrences(date(2026, 9, 1), date(2026, 9, 30))
        )
        self.assertEqual(occurrences, [(date(2026, 9, 12), date(2026, 9, 12))])

    def test_calendar_shows_monthly_repeat_in_future_month(self):
        self.client.login(username="recurring_user", password="StrongPass123!")
        Todo.objects.create(
            user=self.user,
            title="Pay rent",
            start_date=date(2026, 8, 12),
            end_date=date(2026, 8, 12),
            recurrence=Todo.RECURRENCE_MONTHLY,
        )
        response = self.client.get("/calendar/?year=2026&month=9")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pay rent")
        self.assertContains(response, 'data-date="2026-09-12"')


class TodoFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="feature_user",
            password="StrongPass123!",
        )
        self.client.login(username="feature_user", password="StrongPass123!")

    def test_priority_tags_subtasks_and_archive(self):
        from todos.models import Subtask, Tag

        Tag.ensure_defaults()
        work = Tag.objects.get(slug="work")
        todo = Todo.objects.create(
            user=self.user,
            title="Ship feature pack",
            priority=Todo.PRIORITY_HIGH,
            start_date=date.today(),
            end_date=date.today(),
        )
        todo.tags.add(work)
        Subtask.objects.create(todo=todo, title="Write models", order=0)
        Subtask.objects.create(todo=todo, title="Wire templates", order=1, completed=True)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ship feature pack")
        self.assertContains(response, "High")
        self.assertContains(response, "Work")
        self.assertContains(response, "1/2 checklist")

        todo.archive()
        response = self.client.get("/edit-todos/?archived=1")
        self.assertContains(response, "Ship feature pack")
        self.assertContains(response, "Archived")

    def test_activity_page_and_due_soon(self):
        from django.utils import timezone

        today = date.today()
        Todo.objects.create(
            user=self.user,
            title="Due tonight",
            end_date=today,
            priority=Todo.PRIORITY_HIGH,
        )
        done = Todo.objects.create(
            user=self.user,
            title="Finished earlier",
            completed=True,
            completed_at=timezone.now(),
            end_date=today,
        )
        self.assertIsNotNone(done.completed_at)

        response = self.client.get("/activity/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Due tonight")
        self.assertContains(response, "Finished earlier")
        self.assertContains(response, "Completed this week")
