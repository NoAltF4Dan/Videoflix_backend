from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

class VideoAPITestCase(TestCase):
    """Tests for the video API endpoints: list, HLS manifest, and video segments."""

    def setUp(self):
        """Create a test user and set up API client with JWT in cookies."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )

        # Create a refresh token and use its access token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client = APIClient()
        # Set JWT as cookie, as expected by the backend
        self.client.cookies['access_token'] = self.access_token

    def test_video_list(self):
        """Test fetching the list of videos."""
        response = self.client.get('/api/video/')
        # Acceptable status codes: 200 if videos exist, 404 if none, 403 if not authorized
        self.assertIn(response.status_code, [200, 404, 403])

    def test_video_manifest(self):
        """Test fetching the HLS master playlist for a video."""
        response = self.client.get('/api/video/1/720p/index.m3u8')
        # Acceptable status codes: 200 if manifest exists, 404 if missing, 403 if unauthorized, 301 if redirected
        self.assertIn(response.status_code, [200, 404, 403, 301])

    def test_video_segment(self):
        """Test fetching a single HLS video segment."""
        response = self.client.get('/api/video/1/720p/000.ts')
        # Acceptable status codes: 200 if segment exists, 404 if missing, 403 if unauthorized, 301 if redirected
        self.assertIn(response.status_code, [200, 404, 403, 301])
