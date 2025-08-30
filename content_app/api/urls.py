from django.urls import path
from .views import VideoListView, VideoHLSManifestView, VideoSegmentView

urlpatterns = [
    # List all available videos (JWT required)
    path('', VideoListView.as_view(), name='video_list'),

    # Get HLS manifest (.m3u8) for a specific video and resolution
    path('<int:movie_id>/<str:resolution>/index.m3u8', VideoHLSManifestView.as_view(), name='video_hls_manifest'),

    # Get single HLS video segment (.ts) for streaming
    path('<int:movie_id>/<str:resolution>/<str:segment>/', VideoSegmentView.as_view(), name='video_segment'),
]
