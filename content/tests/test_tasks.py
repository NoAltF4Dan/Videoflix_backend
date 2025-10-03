import tempfile
from unittest import mock

import pytest
from django.core.files.base import ContentFile

from content.models import Video
from content.tasks import create_thumbnail, process_video


@pytest.fixture
def video(db):
    """Returns a Video instance with minimal required fields."""
    video = Video.objects.create(
        title="Test Video",
        original_video=ContentFile(b"dummy video content", name="input.mp4"),
        processing_status="pending"
    )
    return video


@pytest.mark.django_db
def test_process_video_success(video, tmp_path, settings):
    """Ensures that a video is processed successfully and status is 'completed'."""

    settings.MEDIA_ROOT = tmp_path

    media_input_dir = tmp_path / "videos" / "original"
    media_input_dir.mkdir(parents=True, exist_ok=True)
    input_file = media_input_dir / "input.mp4"
    input_file.write_text("dummy video content")

    video.original_video.save("input.mp4", ContentFile(b"dummy video content"), save=True)
    video.processing_status = "pending"
    video.save()

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        process_video(video.id)

    video.refresh_from_db()
    assert video.processing_status == "completed"


@pytest.mark.django_db
def test_process_video_ffmpeg_failure(video, tmp_path):
    """Ensures that a video processing failure sets status to 'failed'."""
    fake_input = tmp_path / "input.mp4"
    fake_input.write_text("dummy video content")
    video.original_video.name = str(fake_input)
    video.save()

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Fake FFmpeg error"

        process_video(video.id)

    video.refresh_from_db()
    assert video.processing_status == "failed"


@pytest.mark.django_db
def test_create_thumbnail_success(video, tmp_path):
    """Ensures that thumbnail is created when ffmpeg succeeds."""
    fake_input = tmp_path / "input.mp4"
    fake_input.write_text("dummy video content")

    # Create a fake temp file that simulates ffmpeg output
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
        tmp_thumbnail_path = tmpfile.name

    with mock.patch("subprocess.run") as mock_run, \
         mock.patch("tempfile.NamedTemporaryFile") as mock_tmpfile:

        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        # Patch tempfile so it returns our fake path
        mock_tmpfile.return_value.__enter__.return_value.name = tmp_thumbnail_path

        with open(tmp_thumbnail_path, "wb") as f:
            f.write(b"fakeimage")

        create_thumbnail(video, str(fake_input))

    video.refresh_from_db()
    assert video.thumbnail_url is not None
    assert video.thumbnail_url.name.endswith("thumbnail.jpg")


@pytest.mark.django_db
def test_create_thumbnail_failure(video, tmp_path):
    """Ensures that thumbnail creation failure does not crash and cleans up."""
    fake_input = tmp_path / "input.mp4"
    fake_input.write_text("dummy video content")

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Fake error"

        create_thumbnail(video, str(fake_input))

    video.refresh_from_db()
    assert not video.thumbnail_url
