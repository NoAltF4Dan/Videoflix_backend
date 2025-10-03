from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase

from PIL import Image

from ..models import Video


class VideoModelTestCase(TestCase):
    """Test cases for the Video model."""

    def setUp(self):
        """Create a simple test video file."""
        self.test_video_content = b'fake video content'
        self.test_video_file = SimpleUploadedFile(
            "test_video.mp4",
            self.test_video_content,
            content_type="video/mp4"
        )

        # Create a simple test image file for thumbnail (now required)
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_image_file = BytesIO()
        self.test_image.save(self.test_image_file, format='JPEG')
        self.test_image_file.seek(0)
        self.test_thumbnail_file = SimpleUploadedFile(
            "test_thumbnail.jpg",
            self.test_image_file.read(),
            content_type="image/jpeg"
        )

    def test_video_model_creation(self):
        """Test basic video model creation with required fields."""
        video = Video.objects.create(
            title="Test Video",
            description="A test video description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file  # Now required
        )

        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.description, "A test video description")
        self.assertEqual(video.category, "Action")
        self.assertEqual(video.processing_status, "pending")
        self.assertIsNotNone(video.created_at)
        self.assertIsNotNone(video.updated_at)
        self.assertIsNotNone(video.thumbnail_url)

    def test_video_str_method(self):
        """Test the __str__ method returns the title."""
        video = Video.objects.create(
            title="Test Video Title",
            description="Test description",
            category="Comedy",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        self.assertEqual(str(video), "Test Video Title")

    def test_video_model_fields(self):
        """Test all model fields are correctly defined."""
        video = Video()

        # Test field types
        self.assertIsInstance(video._meta.get_field('title'), models.CharField)
        self.assertIsInstance(video._meta.get_field('description'), models.TextField)
        self.assertIsInstance(video._meta.get_field('category'), models.CharField)
        self.assertIsInstance(video._meta.get_field('original_video'), models.FileField)
        self.assertIsInstance(video._meta.get_field('thumbnail_url'), models.ImageField)
        self.assertIsInstance(video._meta.get_field('processing_status'), models.CharField)
        self.assertIsInstance(video._meta.get_field('created_at'), models.DateTimeField)
        self.assertIsInstance(video._meta.get_field('updated_at'), models.DateTimeField)
        self.assertIsInstance(video._meta.get_field('hls_480p_path'), models.CharField)
        self.assertIsInstance(video._meta.get_field('hls_720p_path'), models.CharField)
        self.assertIsInstance(video._meta.get_field('hls_1080p_path'), models.CharField)

    def test_category_choices(self):
        """Test category choices are correctly defined."""
        expected_choices = [
            ('Action', 'Action'),
            ('Comedy', 'Comedy'),
            ('Drama', 'Drama'),
            ('Horror', 'Horror'),
            ('Romance', 'Romance'),
            ('Thriller', 'Thriller'),
            ('Documentary', 'Documentary'),
            ('Animation', 'Animation'),
        ]

        category_field = Video._meta.get_field('category')
        self.assertEqual(category_field.choices, expected_choices)

    def test_processing_status_choices(self):
        """Test processing status choices are correctly defined."""
        expected_choices = [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]

        status_field = Video._meta.get_field('processing_status')
        self.assertEqual(status_field.choices, expected_choices)

    def test_default_processing_status(self):
        """Test default processing status is 'pending'."""
        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        self.assertEqual(video.processing_status, "pending")

    def test_field_max_lengths(self):
        """Test field max lengths."""
        title_field = Video._meta.get_field('title')
        category_field = Video._meta.get_field('category')
        status_field = Video._meta.get_field('processing_status')
        hls_480p_field = Video._meta.get_field('hls_480p_path')
        hls_720p_field = Video._meta.get_field('hls_720p_path')
        hls_1080p_field = Video._meta.get_field('hls_1080p_path')

        self.assertEqual(title_field.max_length, 200)
        self.assertEqual(category_field.max_length, 50)
        self.assertEqual(status_field.max_length, 20)
        self.assertEqual(hls_480p_field.max_length, 500)
        self.assertEqual(hls_720p_field.max_length, 500)
        self.assertEqual(hls_1080p_field.max_length, 500)

    def test_nullable_fields(self):
        """Test fields that can be null/blank vs required fields."""
        # Only HLS path fields should be nullable
        hls_480p_field = Video._meta.get_field('hls_480p_path')
        hls_720p_field = Video._meta.get_field('hls_720p_path')
        hls_1080p_field = Video._meta.get_field('hls_1080p_path')

        # HLS fields are nullable
        self.assertTrue(hls_480p_field.blank)
        self.assertTrue(hls_480p_field.null)
        self.assertTrue(hls_720p_field.blank)
        self.assertTrue(hls_720p_field.null)
        self.assertTrue(hls_1080p_field.blank)
        self.assertTrue(hls_1080p_field.null)

        # Required fields should not be nullable
        title_field = Video._meta.get_field('title')
        description_field = Video._meta.get_field('description')
        category_field = Video._meta.get_field('category')
        original_video_field = Video._meta.get_field('original_video')
        thumbnail_field = Video._meta.get_field('thumbnail_url')

        self.assertFalse(title_field.blank)
        self.assertFalse(title_field.null)
        self.assertFalse(description_field.blank)
        self.assertFalse(description_field.null)
        self.assertFalse(category_field.blank)
        self.assertFalse(category_field.null)
        self.assertFalse(original_video_field.blank)
        self.assertFalse(original_video_field.null)
        self.assertFalse(thumbnail_field.blank)
        self.assertFalse(thumbnail_field.null)

    def test_meta_ordering(self):
        """Test model meta ordering and constraints."""
        self.assertEqual(Video._meta.ordering, ['-created_at'])

        # Check that UniqueConstraint exists
        constraints = Video._meta.constraints
        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]
        self.assertEqual(constraint.name, "unique_title_case_insensitive")
        # Note: The exact structure of the constraint depends on Django version

    def test_auto_timestamps(self):
        """Test auto_now_add and auto_now functionality."""
        created_at_field = Video._meta.get_field('created_at')
        updated_at_field = Video._meta.get_field('updated_at')

        self.assertTrue(created_at_field.auto_now_add)
        self.assertTrue(updated_at_field.auto_now)

    def test_video_upload_path_function(self):
        """Test video_upload_path function generates correct path."""
        from ..utils import video_upload_path

        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Test the upload path function
        filename = "test_video.mp4"
        expected_path = f'videos/original/{video.id}/{filename}'
        actual_path = video_upload_path(video, filename)

        self.assertEqual(actual_path, expected_path)

    def test_thumbnail_upload_path_function_with_id(self):
        """Test thumbnail_upload_path function with existing video ID."""
        from ..utils import thumbnail_upload_path

        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Test thumbnail path with existing ID
        filename = "thumbnail.jpg"
        expected_path = f'videos/thumbnails/{video.id}/{filename}'
        actual_path = thumbnail_upload_path(video, filename)

        self.assertEqual(actual_path, expected_path)

    def test_thumbnail_upload_path_function_without_id(self):
        """Test thumbnail_upload_path function without video ID (new instance)."""
        from ..utils import thumbnail_upload_path

        # Create video instance without saving (no ID yet)
        video = Video(
            title="Test Video",
            description="Test description",
            category="Action"
        )

        filename = "thumbnail.jpg"
        actual_path = thumbnail_upload_path(video, filename)

        # Should use UUID when no ID is available
        self.assertTrue(actual_path.startswith('videos/thumbnails/'))
        self.assertTrue(actual_path.endswith(f'/{filename}'))

        # Extract the identifier part and verify it's a valid hex string
        path_parts = actual_path.split('/')
        identifier = path_parts[2]  # videos/thumbnails/IDENTIFIER/filename

        # Should be a valid hex string (UUID without dashes)
        try:
            int(identifier, 16)  # Try to parse as hex
            self.assertEqual(len(identifier), 32)  # UUID hex length
        except ValueError:
            self.fail(f"Identifier '{identifier}' is not a valid hex string")
