from django.urls import path
from .views import ProfilesDetailView, ProfilesListView, VideosDetailView, VideosListView, VideoProgressListCreateView, VideoProgressDetailView, CurrentVideoConvertProgressListView, CurrentVideoConvertProgressDetailView

urlpatterns = [
    path("media/", VideosListView.as_view(), name="media_list"),
    path("media/<int:pk>/", VideosDetailView.as_view(), name="media_detail"),
    path("profiles/", ProfilesListView.as_view(), name="profile_list"),
    path("profiles/<int:pk>/", ProfilesDetailView.as_view(), name="profile_detail"),
    path("video/progress/", VideoProgressListCreateView.as_view(), name="video_progress_list"),
    path("video/progress/<int:pk>", VideoProgressDetailView.as_view(), name="video_progress_detail"),
    path("video/current-progress/", CurrentVideoConvertProgressListView.as_view(), name="video_current_progress_list"),
    path("video/current-progress/<int:pk>/", CurrentVideoConvertProgressDetailView.as_view(), name="video_current_progress_detail"),
]