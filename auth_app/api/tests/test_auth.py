from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class AuthTests(APITestCase):
    """Tests for authentication endpoints: login and logout."""

    def setUp(self):
        """Create a test user and set user data for login."""
        self.user_data = {
            "email": "test@example.com",
            "password": "supersecure123"
        }
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="supersecure123"
        )
        self.user.is_active = True
        self.user.save()

    def test_login_sets_cookies(self):
        """Test that login sets access and refresh token cookies."""
        url = reverse("login")
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_logout_blacklists_refresh_token(self):
        """Test that logout invalidates refresh token and clears cookies."""
        # Login first to get refresh token
        login_url = reverse("login")
        response = self.client.post(login_url, self.user_data)
        refresh_token = response.cookies.get("refresh_token").value

        # Logout using refresh token
        logout_url = reverse("logout")
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that cookies are cleared
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")
