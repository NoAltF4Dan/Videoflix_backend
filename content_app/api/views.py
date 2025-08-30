from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Video
from .serializers import VideoSerializer
from django.http import FileResponse, Http404
import os

class VideoListView(APIView):
    """
    API endpoint to list all available videos.

    Permissions:
        - Requires JWT authentication.

    GET /api/video/
    Returns:
        - 200: List of videos serialized with VideoSerializer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoHLSManifestView(APIView):
    """
    API endpoint to retrieve HLS master playlist (index.m3u8) for a specific video.

    Permissions:
        - Requires JWT authentication.

    URL parameters:
        - movie_id: int, ID of the video
        - resolution: str, resolution of the video (e.g., '480p', '720p', '1080p')

    GET /api/video/<movie_id>/<resolution>/index.m3u8
    Returns:
        - 200: FileResponse with HLS master playlist
        - 404: If manifest file does not exist
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        file_path = f'/app/media/videos/{movie_id}/{resolution}/index.m3u8'
        if not os.path.exists(file_path):
            raise Http404("Video manifest not found")
        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.apple.mpegurl')


class VideoSegmentView(APIView):
    """
    API endpoint to retrieve a single HLS video segment (.ts) for a specific video.

    Permissions:
        - Requires JWT authentication.

    URL parameters:
        - movie_id: int, ID of the video
        - resolution: str, resolution of the video (e.g., '480p', '720p', '1080p')
        - segment: str, filename of the segment (e.g., '000.ts')

    GET /api/video/<movie_id>/<resolution>/<segment>/
    Returns:
        - 200: FileResponse with video segment (Content-Type: video/MP2T)
        - 404: If segment does not exist
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        file_path = f'/app/media/videos/{movie_id}/{resolution}/{segment}'
        if not os.path.exists(file_path):
            raise Http404("Video segment not found")
        return FileResponse(open(file_path, 'rb'), content_type='video/MP2T')
