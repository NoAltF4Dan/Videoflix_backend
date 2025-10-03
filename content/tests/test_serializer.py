from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings


import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from urllib.parse import urljoin

from ..api.serializers import VideoSerializer
from ..models import Video


@pytest.mark.django_db
class TestVideoSerializer:
    def test_validate_title_too_short(self):
        """Ensures validation fails if the video title is shorter than 3 characters."""
        serializer = VideoSerializer()
        with pytest.raises(ValidationError) as excinfo:
            serializer.validate_title("Hi")
        assert "at least 3 characters" in str(excinfo.value)

    def test_validate_title_valid(self):
        """Confirms that a valid title passes validation unchanged."""
        serializer = VideoSerializer()
        assert serializer.validate_title("Valid Title") == "Valid Title"

    def test_get_thumbnail_url_with_request(self):
        """Verifies that the thumbnail URL is built with the request’s host when a request context is provided."""
        factory = APIRequestFactory()
        request = factory.get("/")

        video = Video.objects.create(
            title="Test Video",
            description="desc",
            category="Action",
            original_video=SimpleUploadedFile("video.mp4", b"file_content"),
            thumbnail_url=SimpleUploadedFile("thumb.jpg", b"file_content"),
        )

        serializer = VideoSerializer(video, context={"request": request})
        data = serializer.data
        assert data["thumbnail_url"].startswith("http://testserver/")

    def test_get_thumbnail_url_without_request(self):
        video = Video.objects.create(
            title="Test Video 2",
            description="desc",
            category="Action",
            original_video=SimpleUploadedFile("video2.mp4", b"file_content"),
            thumbnail_url=SimpleUploadedFile("thumb2.jpg", b"file_content"),
        )

        serializer = VideoSerializer(video)  # kein request
        data = serializer.data

        expected_url = urljoin(settings.MEDIA_URL, video.thumbnail_url.name)
        assert data["thumbnail_url"] == expected_url

    def test_get_thumbnail_url_none(self):
        """Ensures that the thumbnail URL is None if no thumbnail is set."""
        video = Video.objects.create(
            title="Test Video 3",
            description="desc",
            category="Action",
            original_video=SimpleUploadedFile("video3.mp4", b"file_content"),
        )
        # Thumbnail ist nicht gesetzt
        serializer = VideoSerializer(video)
        data = serializer.data
        assert data["thumbnail_url"] is None

    def test_serializer_output_fields(self):
        """Validates that the serializer returns all expected fields with correct content and formats."""
        factory = APIRequestFactory()
        request = factory.get("/")

        video = Video.objects.create(
            title="Final Test Video",
            description="some description",
            category="Comedy",
            original_video=SimpleUploadedFile("video_final.mp4", b"file_content"),
            thumbnail_url=SimpleUploadedFile("thumb_final.jpg", b"file_content"),
        )

        serializer = VideoSerializer(video, context={"request": request})
        data = serializer.data

        # Check that all expected fields exist
        expected_fields = {"id", "title", "description", "category", "thumbnail_url", "created_at"}
        assert expected_fields.issubset(data.keys())

        # Field content checks
        assert data["title"] == "Final Test Video"
        assert data["description"] == "some description"
        assert data["category"] == "Comedy"
        assert data["thumbnail_url"].startswith("http://testserver/")
        assert isinstance(data["created_at"], str)  # serialised as ISO string
