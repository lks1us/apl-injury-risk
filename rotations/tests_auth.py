from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Club


class PlayerCreateAuthTests(TestCase):
    def setUp(self):
        self.club = Club.objects.create(
            name="Auth FC",
            short_name="AFC",
            city="London",
            stadium="Auth Arena",
            medical_budget=Decimal("10.00"),
        )
        self.user = User.objects.create_user(username="analyst", password="testpass123")

    def test_anonymous_user_redirected_from_player_create(self):
        response = self.client.get(reverse("player_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_can_open_player_create(self):
        self.client.login(username="analyst", password="testpass123")
        response = self.client.get(reverse("player_create"))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "strongpass123",
                "password2": "strongpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
