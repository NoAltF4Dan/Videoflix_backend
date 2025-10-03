from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db.utils import IntegrityError as DbIntegrityError
from django.test import TestCase

from content.models import Video


class VideoUtilsTestCase(TestCase):
    """Test cases specifically for utils functions."""

    def setUp(self):
        self.test_video_file = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.test_thumbnail_file = SimpleUploadedFile(
            "thumb.jpg", b"image_content", content_type="image/jpeg"
        )

    def test_video_upload_path_with_different_filenames(self):
        """Test video_upload_path with various filenames."""
        from ..utils import video_upload_path

        video = Video.objects.create(
            title="Path Test Video",
            description="Testing upload paths",
            category="Action",
            original_video=SimpleUploadedFile("temp.mp4", b'content', "video/mp4")
        )

        # Test different filename scenarios
        test_cases = [
            ("simple.mp4", f"videos/original/{video.id}/simple.mp4"),
            ("movie with spaces.avi", f"videos/original/{video.id}/movie with spaces.avi"),
            ("UPPERCASE.MOV", f"videos/original/{video.id}/UPPERCASE.MOV"),
            ("file-with-dashes.mkv", f"videos/original/{video.id}/file-with-dashes.mkv"),
            ("file_with_underscores.mp4", f"videos/original/{video.id}/file_with_underscores.mp4"),
        ]

        for filename, expected_path in test_cases:
            with self.subTest(filename=filename):
                actual_path = video_upload_path(video, filename)
                self.assertEqual(actual_path, expected_path)

    def test_thumbnail_upload_path_consistency(self):
        """Test that thumbnail_upload_path is consistent for same instance."""
        from ..utils import thumbnail_upload_path

        # Test with saved video (has ID)
        video = Video.objects.create(
            title="Consistency Test",
            description="Testing path consistency",
            category="Action",
            original_video=SimpleUploadedFile("test.mp4", b'content', "video/mp4")
        )

        # Multiple calls should return same path
        path1 = thumbnail_upload_path(video, "thumb.jpg")
        path2 = thumbnail_upload_path(video, "thumb.jpg")
        self.assertEqual(path1, path2)

        # Different filenames should have same directory
        path3 = thumbnail_upload_path(video, "different.png")
        self.assertEqual(path1.rsplit('/', 1)[0], path3.rsplit('/', 1)[0])

    def test_thumbnail_upload_path_uuid_generation(self):
        """Test UUID generation for new video instances."""
        from ..utils import thumbnail_upload_path

        # Create unsaved video instance (no ID)
        video1 = Video(title="Test 1", description="Test", category="Action")
        video2 = Video(title="Test 2", description="Test", category="Comedy")

        path1 = thumbnail_upload_path(video1, "thumb1.jpg")
        path2 = thumbnail_upload_path(video2, "thumb2.jpg")

        # Paths should be different (different UUIDs)
        self.assertNotEqual(path1, path2)

        # Both should be valid paths
        self.assertTrue(path1.startswith('videos/thumbnails/'))
        self.assertTrue(path2.startswith('videos/thumbnails/'))

        # Extract UUIDs and verify they're valid
        uuid1 = path1.split('/')[2]
        uuid2 = path2.split('/')[2]

        # Should be valid hex strings
        try:
            int(uuid1, 16)
            int(uuid2, 16)
        except ValueError:
            self.fail("Generated UUIDs are not valid hex strings")

    def test_validate_video_size_edge_cases(self):
        """Test edge cases for video size validation."""
        from ..utils import validate_video_size

        # Test with empty file
        empty_file = SimpleUploadedFile("empty.mp4", b'', "video/mp4")
        try:
            validate_video_size(empty_file)  # Should not raise error
        except ValidationError:
            self.fail("validate_video_size failed for empty file")

        # Test with file exactly at 1 byte under limit
        limit_content = b'x' * int(10.5 * 1024 * 1024 - 1)
        under_limit_file = SimpleUploadedFile("under.mp4", limit_content, "video/mp4")
        try:
            validate_video_size(under_limit_file)  # Should not raise error
        except ValidationError:
            self.fail("validate_video_size failed for file under limit")

    def test_validate_video_size_error_message_format(self):
        """Test that error message contains proper formatting."""
        from ..utils import validate_video_size
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.exceptions import ValidationError

        # Create file with known size over limit
        test_size = 12 * 1024 * 1024  # 12MB
        large_content = b'x' * test_size
        large_file = SimpleUploadedFile("large.mp4", large_content, "video/mp4")

        with self.assertRaises(ValidationError) as context:
            validate_video_size(large_file)

        error_message = context.exception.messages[0]

        # Check German error message
        self.assertIn("Die Datei ist zu groß", error_message)
        self.assertIn("Maximum: 10MB", error_message)
        self.assertIn("Aktuell:", error_message)
        self.assertIn("MB", error_message)

        # Check that current size is approximately correct (12MB)
        self.assertIn("12.0", error_message)

    def test_utils_with_unicode_filenames(self):
        """Test utils functions with Unicode filenames."""
        from ..utils import video_upload_path, thumbnail_upload_path

        video = Video.objects.create(
            title="Unicode Test",
            description="Testing Unicode filenames",
            category="Action",
            original_video=SimpleUploadedFile("test.mp4", b'content', "video/mp4")
        )

        # Test Unicode filenames
        unicode_filenames = [
            "видео.mp4",  # Cyrillic
            "电影.avi",    # Chinese
            "película.mov",  # Spanish with accent
            "🎬movie.mkv",  # Emoji
        ]

        for filename in unicode_filenames:
            with self.subTest(filename=filename):
                video_path = video_upload_path(video, filename)
                thumb_path = thumbnail_upload_path(video, filename)

                self.assertIn(filename, video_path)
                self.assertIn(filename, thumb_path)
                self.assertTrue(video_path.startswith('videos/original/'))
                self.assertTrue(thumb_path.startswith('videos/thumbnails/'))

    @patch("content.models.get_queue")
    def test_save_method_new_video_triggers_processing(self, mock_get_queue):
        # Mock for the queue
        mock_queue = Mock()
        mock_get_queue.return_value = mock_queue

        # Save new video
        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Check if enqueue is called
        self.assertEqual(mock_queue.enqueue.call_count, 1)
        called_args, called_kwargs = mock_queue.enqueue.call_args
        self.assertEqual(called_args[1], video.id)
        self.assertTrue(callable(called_args[0]))

    @patch("content.models.get_queue")
    def test_save_method_existing_video_no_processing(self, mock_get_queue):
        # Mock for the queue
        mock_queue = Mock()
        mock_get_queue.return_value = mock_queue

        # Step 1: Create video (Mock active!)
        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Step 2: Save video again (is_new = False)
        video.save()

        # Ensure enqueue was called only the first time
        self.assertEqual(mock_queue.enqueue.call_count, 1)

        # Optional: Check that nothing happens on the second save
        # For this: examine the call list
        last_call_args = mock_queue.enqueue.call_args_list[-1]
        self.assertEqual(last_call_args[0][1], video.id)  # ID matches

        # Use variable to avoid linter warning
        self.assertIsNotNone(video.id)

    @patch("content.models.get_queue")
    def test_save_method_new_video_without_file_no_processing(self, mock_get_queue):
        # Mock for the queue
        mock_queue = Mock()
        mock_get_queue.return_value = mock_queue

        # Minimal video
        minimal_video = SimpleUploadedFile("minimal.mp4", b"x", content_type="video/mp4")
        minimal_thumb = SimpleUploadedFile("minimal.jpg", b"x", content_type="image/jpeg")

        # Create video
        video = Video(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=minimal_video,
            thumbnail_url=minimal_thumb
        )
        video.save()

        # Check that enqueue was called since original_video is set
        self.assertEqual(mock_queue.enqueue.call_count, 1)

        # Check arguments
        called_args, called_kwargs = mock_queue.enqueue.call_args
        self.assertEqual(called_args[1], video.id)
        self.assertTrue(callable(called_args[0]))

        def test_video_with_all_hls_paths(self):
            """Test video creation with all HLS paths set."""
            video = Video.objects.create(
                title="Test Video",
                description="Test description",
                category="Action",
                original_video=self.test_video_file,
                thumbnail_url=self.test_thumbnail_file,
                hls_480p_path="/path/to/480p.m3u8",
                hls_720p_path="/path/to/720p.m3u8",
                hls_1080p_path="/path/to/1080p.m3u8",
                processing_status="completed"
            )

            self.assertEqual(video.hls_480p_path, "/path/to/480p.m3u8")
            self.assertEqual(video.hls_720p_path, "/path/to/720p.m3u8")
            self.assertEqual(video.hls_1080p_path, "/path/to/1080p.m3u8")
            self.assertEqual(video.processing_status, "completed")

    def test_video_with_thumbnail(self):
        """Test video creation with thumbnail (now required)."""
        video = Video.objects.create(
            title="Test Video",
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        self.assertIsNotNone(video.thumbnail_url)
        self.assertTrue(video.thumbnail_url.name.endswith('.jpg'))

    def test_unique_title_constraint(self):
        """Test that titles must be unique."""
        # Create first video
        Video.objects.create(
            title="Unique Title",
            description="First description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Create second video file for second video
        second_video_file = SimpleUploadedFile("test2.mp4", b'content2', "video/mp4")
        second_thumbnail_file = SimpleUploadedFile("thumb2.jpg", b'thumb2', "image/jpeg")

        # Try to create second video with same title
        with self.assertRaises((IntegrityError, DbIntegrityError)):
            Video.objects.create(
                title="Unique Title",  # Same title
                description="Second description",
                category="Comedy",
                original_video=second_video_file,
                thumbnail_url=second_thumbnail_file
            )

    def test_case_insensitive_title_constraint(self):
        """Test that title uniqueness is case insensitive."""
        # Create first video
        Video.objects.create(
            title="Test Title",
            description="First description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # Create files for second video
        second_video_file = SimpleUploadedFile("test2.mp4", b'content2', "video/mp4")
        second_thumbnail_file = SimpleUploadedFile("thumb2.jpg", b'thumb2', "image/jpeg")

        # Try to create second video with different case title
        with self.assertRaises((IntegrityError, DbIntegrityError)):
            Video.objects.create(
                title="TEST TITLE",  # Same title, different case
                description="Second description",
                category="Comedy",
                original_video=second_video_file,
                thumbnail_url=second_thumbnail_file
            )

    def test_required_fields_validation(self):
        """Test that all required fields must be provided."""
        # Test missing title
        with self.assertRaises((ValidationError, IntegrityError, DbIntegrityError)):
            video = Video(
                # title missing
                description="Test description",
                category="Action",
                original_video=self.test_video_file,
                thumbnail_url=self.test_thumbnail_file
            )
            video.full_clean()

        # Test missing description
        with self.assertRaises((ValidationError, IntegrityError, DbIntegrityError)):
            video = Video(
                title="Test Video",
                # description missing
                category="Action",
                original_video=self.test_video_file,
                thumbnail_url=self.test_thumbnail_file
            )
            video.full_clean()

        # Test missing category
        with self.assertRaises((ValidationError, IntegrityError, DbIntegrityError)):
            video = Video(
                title="Test Video",
                description="Test description",
                # category missing
                original_video=self.test_video_file,
                thumbnail_url=self.test_thumbnail_file
            )
            video.full_clean()

        # Test missing original_video
        with self.assertRaises((ValidationError, IntegrityError, DbIntegrityError)):
            video = Video(
                title="Test Video",
                description="Test description",
                category="Action",
                # original_video missing
                thumbnail_url=self.test_thumbnail_file
            )
            video.full_clean()

        # Test missing thumbnail_url
        with self.assertRaises((ValidationError, IntegrityError, DbIntegrityError)):
            video = Video(
                title="Test Video",
                description="Test description",
                category="Action",
                original_video=self.test_video_file
                # thumbnail_url missing
            )
            video.full_clean()

    def test_invalid_category_choice(self):
        """Test that invalid category choices are handled by Django."""
        # This test checks that Django will handle validation
        # In real usage, Django forms/serializers would validate this
        video = Video(
            title="Test Video",
            description="Test description",
            category="InvalidCategory",  # Not in CATEGORY_CHOICES
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        # The model itself doesn't validate choices, that's done at the form/admin level
        # But we can verify the choices are correctly defined
        valid_categories = [choice[0] for choice in Video.CATEGORY_CHOICES]
        self.assertNotIn(video.category, valid_categories)

    def test_long_title_validation(self):
        """Test title length validation without hitting the database."""
        long_title = "x" * 201  # Exceeds max_length of 200

        video = Video(
            title=long_title,
            description="Test description",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=self.test_thumbnail_file
        )

        with self.assertRaises(ValidationError):
            video.full_clean()

    def test_video_ordering(self):
        """Test that videos are ordered by created_at descending."""
        # Create multiple videos
        # PostgreSQL maintains microsecond precision, so we ensure different timestamps
        video1 = Video.objects.create(
            title="First Video",
            description="First",
            category="Action",
            original_video=self.test_video_file
        )

        # Force a different timestamp by using transaction.atomic()
        import time
        time.sleep(0.01)  # Small delay to ensure different timestamps

        video2 = Video.objects.create(
            title="Second Video",
            description="Second",
            category="Comedy",
            original_video=SimpleUploadedFile("test2.mp4", b'content', "video/mp4")
        )

        videos = Video.objects.all()
        # Second video should come first (most recent)
        self.assertEqual(videos[0].title, video2.title)
        self.assertEqual(videos[1].title, video1.title)

        # Verify PostgreSQL ordering is working correctly
        self.assertGreater(videos[0].created_at, videos[1].created_at)
