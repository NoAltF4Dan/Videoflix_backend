from rest_framework import generics
from service_app.models import Video, Profiles, VideoProgress, CurrentVideoConvertProgress
from rest_framework.views import APIView
from .serializers import ProfilesSerializer, VideosSerializer, VideoProgressSerializer, CurrentVideoConvertProgressSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from auth_app.auth import CookieJWTAuthentication
from django.contrib.auth.models import User
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

CACHE_TIMER = os.getenv('CACHE_TIMER', default=0)

class ProfilesListView(generics.ListAPIView):
    queryset = Profiles.objects.all()
    serializer_class = ProfilesSerializer

class ProfilesDetailView(generics.RetrieveAPIView):
    queryset = Profiles.objects.all()
    serializer_class = ProfilesSerializer

class VideosListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def groupFactory(self, serialized, request):
        videos = Video.objects.all()
        amount = Video.objects.count()
        grouped = {}
        if amount == 0:
                return {}
        newest = videos.order_by('-created_at')[:10]
        grouped['newOnVideoflix'] = {
            'title': 'New On Videoflix',
            'content': VideosSerializer(newest, many=True, context={'request': request}).data
        }
        for item in serialized:
            genre = item['genre']
            if genre not in grouped:
                grouped[genre] = {
                    'title': genre.capitalize(),
                    'content': []
                }
            grouped[genre]['content'].append(item)
        return grouped
        
    def get(self, request):
        access_token = request.COOKIES.get('access_key')
        cache_key = 'video_list_view'
        cached_response = cache.get(cache_key)

        if cached_response:
            return Response(cached_response)

        videos = Video.objects.all()
        serialized = VideosSerializer(videos, many=True, context={'request': request}).data
        grouped = self.groupFactory(serialized, request)
        cache.set(cache_key, grouped, timeout=CACHE_TIMER)
        return Response(grouped)
    
    def post(self, request):
        access_token = request.COOKIES.get('access_key')
        serializer = VideosSerializer(data= request.data, context={'request': request})
        if serializer.is_valid():
            cache.delete("video_list_view")
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideosDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideosSerializer

    def perform_destroy(self, instance):
        cache.delete("video_list_view")
        return super().perform_destroy(instance)


class VideoProgressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = VideoProgressSerializer

    def get_queryset(self):
        user = self.request.user
        profile = None
        if not user.is_authenticated:
            return VideoProgress.objects.none()
        profile = user.abstract_user

        if not user.is_authenticated:
            return VideoProgress.objects.none()
        if not profile:
            return VideoProgress.objects.none()
        
        queryset = VideoProgress.objects.filter(profiles=profile)
        video = self.request.query_params.get("videoId")
        if video:
            queryset = queryset.filter(video=video)
        return queryset

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if hasattr(self, 'existing_instance'):
            serializer = self.get_serializer(self.existing_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return response

    def perform_create(self, serializer):
        user = self.request.user
        profiles = user.abstract_user
        video = serializer.validated_data.get('video')
        existing = VideoProgress.objects.filter(profiles=profiles, video=video).first()

        if existing:
            self.existing_instance = existing
            return
        
        serializer.save(profiles=profiles)


class VideoProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = VideoProgressSerializer

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        queryset = VideoProgress.objects.filter(pk=pk)
        return queryset
    
    def perform_update(self, serializer):
        return super().perform_update(serializer)
    
class CurrentVideoConvertProgressListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CurrentVideoConvertProgressSerializer
    queryset = CurrentVideoConvertProgress.objects.all() 

class CurrentVideoConvertProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CurrentVideoConvertProgressSerializer
    queryset = CurrentVideoConvertProgress.objects.all() 
