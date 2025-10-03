import os
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

import pytest
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from ..api.views import VideoListView, video_manifest, video_segment
from ..models import Video


@pytest.fixture
def user(db):
    """Creates and returns a test user."""
    return User.objects.create_user(username='testuser', password='password')


@pytest.fixture
def video(db):
    """Creates and returns a test video object with predefined HLS paths and a completed processing status."""
    return Video.objects.create(
        id=1,
        processing_status='completed',
        hls_480p_path='videos/1/480p',
        hls_720p_path='videos/1/720p',
        hls_1080p_path='videos/1/1080p'
    )


@pytest.mark.django_db
def test_video_list_view(user, video):
    """Ensures the video list view returns a 200 response and includes the created video."""
    factory = APIRequestFactory()
    request = factory.get('/videos/')
    force_authenticate(request, user=user)

    view = VideoListView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert any(v['id'] == video.id for v in response.data)


@pytest.mark.django_db
def test_video_list_unauthenticated():
    """Unauthenticated users should get a 401 response."""
    client = APIClient()

    url = reverse('video-list')
    response = client.get(url)

    assert response.status_code == 401
    assert "credentials" in response.data["detail"].lower()


@pytest.mark.django_db
@pytest.mark.parametrize("resolution", ['480p', '720p', '1080p'])
def test_video_manifest_success_all_resolutions(user, video, resolution):
    """Confirms that the manifest endpoint returns the correct file content for all supported resolutions."""
    factory = APIRequestFactory()
    request = factory.get(f'/videos/manifest/{video.id}/{resolution}/')
    force_authenticate(request, user=user)

    mock_path = os.path.join(settings.MEDIA_ROOT, getattr(video, f"hls_{resolution}_path"), 'index.m3u8')

    with mock.patch('os.path.exists', side_effect=lambda path: path == mock_path), \
         mock.patch('builtins.open', mock.mock_open(read_data='test content')) as m:
        response = video_manifest(request, movie_id=video.id, resolution=resolution)

    m.assert_called_once_with(mock_path, 'r')
    assert response.status_code == 200
    assert response.content == b'test content'


@pytest.mark.django_db
@pytest.mark.parametrize("resolution", ['480p', '720p', '1080p'])
def test_video_segment_success_all_resolutions(user, video, resolution):
    """Verifies that the segment endpoint correctly serves segment files for all supported resolutions."""
    factory = APIRequestFactory()
    segment_name = 'segment1.ts'
    request = factory.get(f'/videos/segment/{video.id}/{resolution}/{segment_name}')
    force_authenticate(request, user=user)

    segment_file = os.path.join(settings.MEDIA_ROOT, getattr(video, f"hls_{resolution}_path"), segment_name)

    with mock.patch('os.path.exists', side_effect=lambda path: path == segment_file), \
         mock.patch('builtins.open', mock.mock_open(read_data=b'segment content')) as m:
        response = video_segment(request, movie_id=video.id, resolution=resolution, segment=segment_name)

    m.assert_called_once_with(segment_file, 'rb')
    assert response.status_code == 200
    assert response.content == b'segment content'


@pytest.mark.django_db
def test_video_manifest_not_found(user):
    """Checks that requesting a manifest for a non-existent video returns a 404 response."""
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse('video-manifest', kwargs={'movie_id': 999, 'resolution': '720p'})
    response = client.get(url)
    assert response.status_code == 404
    assert response.data["detail"] == "Video not found"


@pytest.mark.django_db
def test_video_manifest_invalid_resolution(user, video):
    """Ensures that requesting a manifest with an unsupported resolution returns a 404 response."""
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse('video-manifest', kwargs={'movie_id': video.id, 'resolution': '999p'})
    response = client.get(url)
    assert response.status_code == 404
    assert "Resolution not available" in response.data["detail"]


@pytest.mark.django_db
def test_video_manifest_file_missing(user, video):
    """Validates that a missing manifest file returns a 404 response."""
    client = APIClient()
    client.force_authenticate(user=user)

    mock_path = os.path.join(settings.MEDIA_ROOT, video.hls_720p_path, 'index.m3u8')

    with mock.patch('os.path.exists', side_effect=lambda path: False if path == mock_path else True):
        url = reverse('video-manifest', kwargs={'movie_id': video.id, 'resolution': '720p'})
        response = client.get(url)
        assert response.status_code == 404
        assert "Manifest file not found" in response.data["detail"]


@pytest.mark.django_db
def test_video_manifest_success(user, video, tmp_path):
    """Checks that a valid manifest file is returned with status 200."""

    media_root = tmp_path
    manifest_dir = media_root / video.hls_720p_path
    manifest_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = manifest_dir / "index.m3u8"
    manifest_content = "#EXTM3U\n#EXT-X-VERSION:3"
    manifest_file.write_text(manifest_content)

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("video-manifest", kwargs={"movie_id": video.id, "resolution": "720p"})

    with override_settings(MEDIA_ROOT=str(media_root)):
        response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/vnd.apple.mpegurl"
    assert manifest_content in response.content.decode()


@pytest.mark.django_db
def test_video_manifest_not_completed(user, video):
    """Ensures that a video which is not yet completed cannot serve a manifest and returns 404."""
    client = APIClient()
    client.force_authenticate(user=user)

    # Set video to "processing" instead of "completed"
    video.processing_status = "processing"
    video.save()

    url = reverse('video-manifest', kwargs={'movie_id': video.id, 'resolution': '720p'})
    response = client.get(url)
    assert response.status_code == 404
    assert response.data["detail"] == "Video not found"


@pytest.mark.django_db
def test_video_segment_not_found(user):
    """Checks that requesting a segment for a non-existent video returns 404."""
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse('video-segment', kwargs={'movie_id': 999, 'resolution': '720p', 'segment': 'segment1.ts'})
    response = client.get(url)
    assert response.status_code == 404
    assert response.data["detail"] == "Video not found"


@pytest.mark.django_db
def test_video_segment_invalid_resolution(user, video):
    """Ensures that requesting a segment with an unsupported resolution returns 404."""
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse('video-segment', kwargs={'movie_id': video.id, 'resolution': '999p', 'segment': 'segment1.ts'})
    response = client.get(url)
    assert response.status_code == 404
    assert "Resolution not available" in response.data["detail"]


@pytest.mark.django_db
def test_video_segment_file_missing(user, video):
    """Validates that a missing segment file triggers a 404 error."""
    client = APIClient()
    client.force_authenticate(user=user)

    segment_file = os.path.join(settings.MEDIA_ROOT, video.hls_720p_path, 'segment1.ts')

    with mock.patch('os.path.exists', side_effect=lambda path: False if path == segment_file else True):
        url = reverse('video-segment', kwargs={'movie_id': video.id, 'resolution': '720p', 'segment': 'segment1.ts'})
        response = client.get(url)
        assert response.status_code == 404
        assert "Segment file not found" in response.data["detail"]


@pytest.mark.django_db
def test_video_segment_success(user, video, tmp_path):
    """Checks that a valid segment file is returned with status 200."""
    client = APIClient()
    client.force_authenticate(user=user)

    media_root = tmp_path
    segment_dir = media_root / video.hls_720p_path
    segment_dir.mkdir(parents=True, exist_ok=True)

    segment_file = segment_dir / "segment1.ts"
    segment_content = b"FAKE_TS_CONTENT"
    segment_file.write_bytes(segment_content)

    url = reverse('video-segment', kwargs={'movie_id': video.id, 'resolution': '720p', 'segment': 'segment1.ts'})

    with override_settings(MEDIA_ROOT=str(media_root)):
        response = client.get(url)

    assert response.status_code == 200
    assert response.content == segment_content
    assert response["Content-Type"] == "video/MP2T"
