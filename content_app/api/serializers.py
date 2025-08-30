from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.

    Serializes basic metadata of videos for listing endpoints.
    """
    class Meta:
        model = Video
        fields = [
            'id',           # Unique identifier of the video
            'created_at',   # Timestamp when the video was created
            'title',        # Video title
            'description',  # Short description of the video
            'thumbnail_url',# URL to the video's thumbnail image
            'category'      # Category/genre of the video
        ]
