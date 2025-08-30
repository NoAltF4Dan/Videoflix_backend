from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Video
from .serializers import VideoSerializer
from django.http import FileResponse, Http404
import os

class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class VideoHLSManifestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        file_path = f'/app/media/videos/{movie_id}/{resolution}/index.m3u8'
        if not os.path.exists(file_path):
            raise Http404("Video Manifest nicht gefunden")
        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.apple.mpegurl')

class VideoSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        file_path = f'/app/media/videos/{movie_id}/{resolution}/{segment}'
        if not os.path.exists(file_path):
            raise Http404("Videosegment nicht gefunden")
        return FileResponse(open(file_path, 'rb'), content_type='video/MP2T')
