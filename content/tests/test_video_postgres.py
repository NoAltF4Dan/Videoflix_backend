from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase

import pytest

from content.models import Video


class VideoModelPostgreSQLTestCase(TestCase):
    """PostgreSQL specific test cases for Video model."""

    def setUp(self):
        """Set up test data"""
        self.test_video_content = b'fake video content'
        self.test_video_file = SimpleUploadedFile(
            "test_video.mp4",
            self.test_video_content,
            content_type="video/mp4"
        )

    def test_postgresql_text_search(self):
        """Test PostgreSQL full-text search capabilities (if implemented)."""
        # Create videos with different descriptions
        Video.objects.create(
            title="Action Movie",
            description="Exciting action sequences with explosions",
            category="Action",
            original_video=self.test_video_file
        )

        Video.objects.create(
            title="Comedy Film",
            description="Funny comedy with great jokes",
            category="Comedy",
            original_video=SimpleUploadedFile("test2.mp4", b'content2', "video/mp4")
        )

        # Basic search functionality (can be extended with PostgreSQL full-text search)
        action_videos = Video.objects.filter(description__icontains="action")
        comedy_videos = Video.objects.filter(description__icontains="comedy")

        self.assertEqual(action_videos.count(), 1)
        self.assertEqual(comedy_videos.count(), 1)

    def test_concurrent_video_creation(self):
        """Test concurrent video creation with PostgreSQL."""
        from threading import Thread
        import queue

        results = queue.Queue()

        def create_video(title_suffix):
            try:
                video = Video.objects.create(
                    title=f"Concurrent Video {title_suffix}",
                    description="Test concurrent creation",
                    category="Action",
                    original_video=SimpleUploadedFile(
                        f"test_{title_suffix}.mp4",
                        b'content',
                        "video/mp4"
                    )
                )
                results.put(('success', video.id))
            except Exception as e:
                results.put(('error', str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = Thread(target=create_video, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        successes = 0
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == 'success':
                successes += 1

        self.assertEqual(successes, 3)
        self.assertEqual(Video.objects.count(), 3)

    def test_postgresql_transaction_rollback(self):
        """Test transaction rollback behavior with PostgreSQL."""
        initial_count = Video.objects.count()

        try:
            with transaction.atomic():
                Video.objects.create(
                    title="Transaction Test",
                    description="This should be rolled back",
                    category="Action",
                    original_video=self.test_video_file
                )

                # Force a rollback by raising an exception
                raise ValueError("Force rollback")
        except ValueError:
            pass

        # Video should not be saved due to rollback
        self.assertEqual(Video.objects.count(), initial_count)

    @patch('django.utils.timezone.now')
    def test_postgresql_timezone_handling(self, mock_now):
        """Test timezone handling with PostgreSQL."""
        from django.utils import timezone
        import datetime

        # Mock a specific timezone-aware datetime
        fixed_time = timezone.make_aware(datetime.datetime(2024, 1, 1, 12, 0, 0))
        mock_now.return_value = fixed_time

        # Create video with timezone-aware timestamps
        video = Video.objects.create(
            title="Timezone Test",
            description="Testing timezone handling",
            category="Action",
            original_video=self.test_video_file,
            thumbnail_url=SimpleUploadedFile("thumb.jpg", b'thumb', "image/jpeg")
        )

        # PostgreSQL stores timezone-aware timestamps
        self.assertIsNotNone(video.created_at.tzinfo)
        self.assertIsNotNone(video.updated_at.tzinfo)

        # Test timezone conversion
        self.assertTrue(timezone.is_aware(video.created_at))
        self.assertTrue(timezone.is_aware(video.updated_at))


@pytest.mark.django_db
def test_postgresql_unique_constraint_same_title():
    """Test that creating two Video instances with the same title raises an IntegrityError due to the database unique constraint."""
    Video.objects.create(
        title="Unique Title",
        description="Test description",
        category="Action",
        original_video=SimpleUploadedFile("test1.mp4", b"content1", "video/mp4"),
        thumbnail_url=SimpleUploadedFile("thumb1.jpg", b"img", "image/jpeg"),
    )

    with pytest.raises(IntegrityError):
        Video.objects.create(
            title="Unique Title",
            description="Another description",
            category="Comedy",
            original_video=SimpleUploadedFile("test2.mp4", b"content2", "video/mp4"),
            thumbnail_url=SimpleUploadedFile("thumb2.jpg", b"img", "image/jpeg"),
        )


@pytest.mark.django_db
def test_postgresql_unique_constraint_case_insensitive():
    """Verifies that creating two Video instances with titles differing only in case raises an IntegrityError due to a case-insensitive unique constraint."""
    Video.objects.create(
        title="Unique Title",
        description="Test description",
        category="Action",
        original_video=SimpleUploadedFile("test1.mp4", b"content1", "video/mp4"),
        thumbnail_url=SimpleUploadedFile("thumb1.jpg", b"img", "image/jpeg"),
    )

    with pytest.raises(IntegrityError):
        Video.objects.create(
            title="unique title",
            description="Different description",
            category="Drama",
            original_video=SimpleUploadedFile("test3.mp4", b"content3", "video/mp4"),
            thumbnail_url=SimpleUploadedFile("thumb3.jpg", b"img", "image/jpeg"),
        )
