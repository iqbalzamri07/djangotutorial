from django.contrib.auth.models import User
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

    def test_signup_and_login(self):
        response = self.client.post(
            "/api/auth/signup/",
            {
                "username": "new_api_user",
                "password": self.password,
                "email": "new@test.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)

        response = self.client.post(
            "/api/auth/login/",
            {"username": "new_api_user", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

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
                "start_date": "2026-08-12",
                "end_date": "2026-08-14",
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        todo_id = create.data["id"]
        self.assertEqual(Todo.objects.get(id=todo_id).user, self.user)

        listing = self.client.get("/api/todos/?q=API&status=pending")
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
