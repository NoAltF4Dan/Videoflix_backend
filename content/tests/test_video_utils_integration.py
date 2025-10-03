from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from ..models import Video


class VideoValidatorTestCase(TestCase):
    """Test cases for video file validators."""

    def setUp(self):
        self.test_video_content = b'fake video content'

    def test_validate_video_size_valid_file(self):
        """Test video size validator with valid file size"""
        from ..utils import validate_video_size

        # Create a small test file (under 10MB)
        small_file = SimpleUploadedFile(
            "test.mp4",
            b'small content',
            content_type="video/mp4"
        )

        # Should not raise any exception for small files
        try:
            validate_video_size(small_file)
        except ValidationError:
            self.fail("validate_video_size raised ValidationError for valid file size")

    def test_validate_video_size_large_file(self):
        """Test video size validator with oversized file."""
        from ..utils import validate_video_size

        # Create a mock file that exceeds 10MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large_test.mp4",
            large_content,
            content_type="video/mp4"
        )

        # Should raise ValidationError for large files
        with self.assertRaises(ValidationError) as context:
            validate_video_size(large_file)

        error_message = str(context.exception)
        self.assertIn("Die Datei ist zu groß", error_message)
        self.assertIn("Maximum: 10MB", error_message)
        self.assertIn("MB", error_message)  # Should show current size in MB

    def test_validate_video_size_exactly_max_size(self):
        """Test video size validator with file exactly at max size."""
        from ..utils import validate_video_size

        # Create file exactly at 10.5MB (the actual limit)
        exact_size_content = b'x' * int(10.5 * 1024 * 1024)
        exact_size_file = SimpleUploadedFile(
            "exact_size.mp4",
            exact_size_content,
            content_type="video/mp4"
        )

        # Should not raise exception at exact limit
        try:
            validate_video_size(exact_size_file)
        except ValidationError:
            self.fail("validate_video_size raised ValidationError for file at exact limit")

    def test_validate_video_size_just_over_limit(self):
        """Test video size validator with file just over the limit."""
        from ..utils import validate_video_size

        # Create file just over 10.5MB
        over_limit_content = b'x' * int(10.5 * 1024 * 1024 + 1)
        over_limit_file = SimpleUploadedFile(
            "over_limit.mp4",
            over_limit_content,
            content_type="video/mp4"
        )

        # Should raise ValidationError for file over limit
        with self.assertRaises(ValidationError) as context:
            validate_video_size(over_limit_file)

        error_message = str(context.exception)
        self.assertIn("Die Datei ist zu groß", error_message)

    def test_video_creation_with_valid_size(self):
        """Test creating video with valid file size."""
        small_file = SimpleUploadedFile(
            "valid_size.mp4",
            b'valid content',
            content_type="video/mp4"
        )

        video = Video.objects.create(
            title="Valid Size Video",
            description="Test with valid file size",
            category="Action",
            original_video=small_file
        )

        self.assertEqual(video.title, "Valid Size Video")
        self.assertIsNotNone(video.original_video)

    def test_video_creation_with_invalid_size(self):
        """Test creating video with invalid file size."""
        # Create oversized file
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "invalid_size.mp4",
            large_content,
            content_type="video/mp4"
        )

        # Should raise ValidationError during model validation
        video = Video(
            title="Invalid Size Video",
            description="Test with invalid file size",
            category="Action",
            original_video=large_file
        )

        with self.assertRaises(ValidationError) as context:
            video.full_clean()

        # Check that the error is related to file size
        error_dict = context.exception.message_dict
        self.assertIn('original_video', error_dict)
        error_messages = ' '.join(str(msg) for msg in error_dict['original_video'])
        self.assertIn("Die Datei ist zu groß", error_messages)

    def test_file_extension_validator_valid_extensions(self):
        """Test file extension validation with valid extensions."""
        valid_extensions = ['mp4', 'avi', 'mov', 'mkv']

        for ext in valid_extensions:
            with self.subTest(extension=ext):
                test_file = SimpleUploadedFile(
                    f"test.{ext}",
                    b'valid content',
                    f"video/{ext}"
                )

                video = Video(
                    title=f"Test {ext.upper()} Video",
                    description=f"Test video with {ext} extension",
                    category="Action",
                    original_video=test_file
                )

                # Should not raise validation error for valid extensions
                try:
                    video.full_clean()
                except ValidationError as e:
                    # If validation fails, it shouldn't be due to file extension
                    error_dict = e.message_dict
                    if 'original_video' in error_dict:
                        error_messages = ' '.join(str(msg) for msg in error_dict['original_video'])
                        self.assertNotIn('extension', error_messages.lower())

    def test_file_extension_validator_invalid_extension(self):
        """Test file extension validation with invalid extension."""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b'invalid content',
            "text/plain"
        )

        video = Video(
            title="Invalid Extension Video",
            description="Test video with invalid extension",
            category="Action",
            original_video=invalid_file
        )

        # Should raise ValidationError for invalid extension
        with self.assertRaises(ValidationError) as context:
            video.full_clean()

        error_dict = context.exception.message_dict
        self.assertIn('original_video', error_dict)
        error_messages = ' '.join(str(msg) for msg in error_dict['original_video'])
        self.assertTrue(
            'extension' in error_messages.lower() or 'allowed' in error_messages.lower()
        )

    def test_combined_file_validation(self):
        """Test combined file size and extension validation."""
        # Test file with valid extension but invalid size
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_mp4_file = SimpleUploadedFile(
            "large.mp4",
            large_content,
            "video/mp4"
        )

        video = Video(
            title="Large MP4 Video",
            description="Test large MP4 file",
            category="Action",
            original_video=large_mp4_file
        )

        with self.assertRaises(ValidationError) as context:
            video.full_clean()

        error_dict = context.exception.message_dict
        self.assertIn('original_video', error_dict)
        error_messages = ' '.join(str(msg) for msg in error_dict['original_video'])
        self.assertIn("Die Datei ist zu groß", error_messages)
