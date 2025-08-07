import os

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.http import FileResponse

from content_app.models import Video
from .serializers import VideoSerializer

def get_video_base_path(video):
    return os.path.splitext(video.video_file.path)[0]

# Create your views here.
class VideoListView(ListAPIView):
    """
        To list all views
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

class HLSPlayListView(APIView):
    """
        To get HSL playlist
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, resolution):
        try:
            video = Video.objects.get(id=pk)
        except Video.DoesNotExist:
            raise NotFound("Video not found.")
        
        base_path = get_video_base_path(video)
        file_path = f'{base_path}_{resolution}/index.m3u8'

        if not os.path.exists(file_path):
            raise NotFound("HSL Playlist not found.")

        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.apple.mpegurl')
        


class HSLSegmentView(APIView):
    """
        To get single segment
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, resolution, segment):
        try:
            video = Video.objects.get(id=pk)
        except Video.DoesNotExist:
            raise NotFound("Video not found.")
        
        base_path = get_video_base_path(video)
        file_path = f'{base_path}_{resolution}/{segment}'

        if not os.path.exists(file_path):
            raise NotFound("Segment not found.")

        return FileResponse(open(file_path, 'rb'), content_type='video/MP2T')