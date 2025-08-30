from django.urls import path
from .views import VideoListView, VideoHLSManifestView, VideoSegmentView

urlpatterns = [
    path('', VideoListView.as_view(), name='video_list'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', VideoHLSManifestView.as_view(), name='video_hls_manifest'),
    path('<int:movie_id>/<str:resolution>/<str:segment>/', VideoSegmentView.as_view(), name='video_segment'),
]
