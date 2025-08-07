from django.urls import path
from .views import VideoListView, HLSPlayListView, HSLSegmentView


urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:pk>/<str:resolution>/index.m3u8', HLSPlayListView.as_view(), name='HSL-playlist'),
    path('video/<int:pk>/<str:resolution>/<str:segment>/', HSLSegmentView.as_view(), name='HSL-segment')
]