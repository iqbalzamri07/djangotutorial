from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):
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

    def test_me_requires_auth(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

        login = self.client.post(
            "/api/auth/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["username"], self.user.username)
