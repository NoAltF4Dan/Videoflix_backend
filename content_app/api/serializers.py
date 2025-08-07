from rest_framework import serializers

from content_app.models import Video 

class VideoSerializer(serializers.ModelSerializer):
    """
        Video Serializer
    """
    class Meta:
        model = Video 
        exclude = ['video_file']
